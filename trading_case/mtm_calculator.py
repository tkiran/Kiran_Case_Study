from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class MTMConfig:
    """
    Configuration for column names used in the input Excel.

    Adjust these if your actual column names differ.
    """

    price_sheet: str = "Price"
    contracts_sheet: str = "Contracts"

    # Price sheet columns
    col_price_date: str = "Price Date"
    col_price_index_name: str = "Index Name"
    col_price_tenor: str = "Tenor"
    col_price_value: str = "Price"

    # Contracts sheet columns (match your 10 headers)
    col_contract_id: str = "Contract_Ref"
    col_contract_index_name: str = "Base Index"
    col_contract_tenor: str = "Tenor"
    col_contract_typical_fe: str = "Typical Fe"
    # Your sheet does not have an explicit Fe Adj flag column; we treat all as adjustable
    col_contract_fe_adj_flag: str = "Fe Adj Flag"
    col_contract_cost: str = "Cost"
    col_contract_discount: str = "Discount"
    col_contract_quantity: str = "Quantity"
    col_contract_unit: str = "Unit"  # "DMT" or "WMT"
    col_contract_moisture: str = "Moisture"

    # Output
    col_report_date: str = "Valuation Date"


def _normalise_price_df(df: pd.DataFrame, cfg: MTMConfig) -> pd.DataFrame:
    df = df.copy()
    df[cfg.col_price_date] = pd.to_datetime(df[cfg.col_price_date])
    df[cfg.col_price_index_name] = df[cfg.col_price_index_name].astype(str).str.strip()
    df[cfg.col_price_tenor] = df[cfg.col_price_tenor].astype(str).str.strip()
    df[cfg.col_price_value] = pd.to_numeric(df[cfg.col_price_value], errors="coerce")
    return df


def _normalise_contracts_df(df: pd.DataFrame, cfg: MTMConfig) -> pd.DataFrame:
    df = df.copy()
    df[cfg.col_contract_index_name] = df[cfg.col_contract_index_name].astype(str).str.strip()
    df[cfg.col_contract_tenor] = df[cfg.col_contract_tenor].astype(str).str.strip()

    for col in [
        cfg.col_contract_typical_fe,
        cfg.col_contract_cost,
        cfg.col_contract_discount,
        cfg.col_contract_quantity,
        cfg.col_contract_moisture,
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if cfg.col_contract_unit in df.columns:
        df[cfg.col_contract_unit] = df[cfg.col_contract_unit].astype(str).str.upper().str.strip()

    if cfg.col_contract_fe_adj_flag in df.columns:
        df[cfg.col_contract_fe_adj_flag] = df[cfg.col_contract_fe_adj_flag].astype(str).str.strip()

    return df


def _lookup_base_price_for_contracts(
    prices: pd.DataFrame, contracts: pd.DataFrame, valuation_date: pd.Timestamp, cfg: MTMConfig
) -> pd.Series:
    """
    For each contract, find the base index price applicable for the given valuation_date.

    Assumption:
    - Price sheet has one row per (Date, Index Name, Tenor).
    - For a past tenor, we take the last available price on/ before valuation_date
      for the matching (Index Name, Tenor).
    """
    prices = prices.copy()
    prices = prices[prices[cfg.col_price_date] <= valuation_date]

    # Sort so that groupby().tail(1) gives us the latest available price per (index, tenor)
    prices = prices.sort_values([cfg.col_price_index_name, cfg.col_price_tenor, cfg.col_price_date])
    latest_prices = (
        prices.groupby([cfg.col_price_index_name, cfg.col_price_tenor]).tail(1).set_index(
            [cfg.col_price_index_name, cfg.col_price_tenor]
        )
    )

    # Build a MultiIndex from contracts to align with latest_prices index
    idx = pd.MultiIndex.from_arrays(
        [
            contracts[cfg.col_contract_index_name].astype(str).str.strip(),
            contracts[cfg.col_contract_tenor].astype(str).str.strip(),
        ],
        names=[cfg.col_price_index_name, cfg.col_price_tenor],
    )

    base_prices = latest_prices.reindex(idx)[cfg.col_price_value]
    base_prices.index = contracts.index  # Align back to contracts index
    return base_prices


def _compute_fe_adjustment_ratio(contracts: pd.DataFrame, cfg: MTMConfig) -> pd.Series:
    """
    Fe Adjustment Ratio:
      - If Fe Adj Flag indicates 'NoAdj' (case-insensitive match), ratio = 1.0
      - Otherwise ratio = Typical Fe / 62
    """
    flag = contracts.get(cfg.col_contract_fe_adj_flag)
    typical_fe = contracts.get(cfg.col_contract_typical_fe)

    no_adj_mask = flag.astype(str).str.upper().eq("NOADJ") if flag is not None else False

    ratio = pd.Series(1.0, index=contracts.index, dtype="float64")

    if typical_fe is not None:
        # Compute Typical Fe / 62, falling back to 1.0 where data is missing
        ratio_loc = typical_fe / 62.0
        ratio = ratio_loc.fillna(1.0)

    if isinstance(no_adj_mask, pd.Series):
        ratio = ratio.where(~no_adj_mask, 1.0)

    return ratio


def _compute_quantity_dmt(contracts: pd.DataFrame, cfg: MTMConfig) -> pd.Series:
    """
    Quantity (DMT):
      - If Unit == 'DMT': use Quantity directly
      - If Unit == 'WMT': Quantity * (1 - Moisture)
    """
    qty = contracts.get(cfg.col_contract_quantity)
    unit = contracts.get(cfg.col_contract_unit)
    moisture = contracts.get(cfg.col_contract_moisture)

    if qty is None:
        return pd.Series(dtype="float64", index=contracts.index)

    qty_dmt = pd.to_numeric(qty, errors="coerce")

    if unit is None:
        return qty_dmt

    unit_upper = unit.astype(str).str.upper().str.strip()
    wmt_mask = unit_upper.eq("WMT")

    if moisture is not None:
        m = pd.to_numeric(moisture, errors="coerce").fillna(0.0)
        wmt_qty = qty_dmt * (1.0 - m)
        qty_dmt = qty_dmt.where(~wmt_mask, wmt_qty)

    return qty_dmt


def compute_mtm_for_date(
    excel_path: str,
    valuation_date: Optional[str | pd.Timestamp] = None,
    cfg: Optional[MTMConfig] = None,
) -> pd.DataFrame:
    """
    Compute MTM valuation for all contracts for a given valuation_date.

    Parameters
    ----------
    excel_path : str
        Path to the Excel file containing Price and Contracts sheets.
    valuation_date : str or pd.Timestamp, optional
        Date for which to compute MTM. If None, use the latest price date in the Price sheet.
    cfg : MTMConfig, optional
        Configuration of sheet and column names.

    Returns
    -------
    pd.DataFrame
        Contracts data with additional MTM-related columns, including 'MTM Value'.
    """
    cfg = cfg or MTMConfig()

    # Load data
    xls = pd.ExcelFile(excel_path)
    prices_raw = pd.read_excel(xls, sheet_name=cfg.price_sheet)
    contracts_raw = pd.read_excel(xls, sheet_name=cfg.contracts_sheet)

    prices = _normalise_price_df(prices_raw, cfg)
    contracts = _normalise_contracts_df(contracts_raw, cfg)

    if valuation_date is None:
        valuation_date = prices[cfg.col_price_date].max()
    valuation_date = pd.to_datetime(valuation_date)

    base_price_series = _lookup_base_price_for_contracts(prices, contracts, valuation_date, cfg)
    fe_adj_ratio = _compute_fe_adjustment_ratio(contracts, cfg)
    qty_dmt = _compute_quantity_dmt(contracts, cfg)

    cost = contracts.get(cfg.col_contract_cost, pd.Series(0.0, index=contracts.index))
    discount = contracts.get(cfg.col_contract_discount, pd.Series(1.0, index=contracts.index))

    cost = pd.to_numeric(cost, errors="coerce").fillna(0.0)
    discount = pd.to_numeric(discount, errors="coerce").fillna(1.0)

    # MTM Value = (Base Index Price x Fe Adjustment Ratio + Cost) x Discount x Quantity(DMT)
    mtm_value = (base_price_series * fe_adj_ratio + cost) * discount * qty_dmt

    result = contracts.copy()
    result["Base Index Price"] = base_price_series
    result["Fe Adjustment Ratio"] = fe_adj_ratio
    result["Quantity (DMT)"] = qty_dmt
    result["MTM Value"] = mtm_value
    result[cfg.col_report_date] = valuation_date.normalize()

    return result


def generate_daily_mtm_report(
    excel_path: str,
    output_path: str,
    valuation_date: Optional[str | pd.Timestamp] = None,
    cfg: Optional[MTMConfig] = None,
) -> pd.DataFrame:
    """
    High-level helper to compute MTM and write a daily report to Excel.

    Parameters
    ----------
    excel_path : str
        Input data Excel (Price & Contracts).
    output_path : str
        Path to write the MTM report (Excel).
    valuation_date : str or pd.Timestamp, optional
        Valuation date. If None, uses latest price date.
    cfg : MTMConfig, optional
        Configuration of sheet/column names.
    """
    cfg = cfg or MTMConfig()
    mtm_df = compute_mtm_for_date(excel_path=excel_path, valuation_date=valuation_date, cfg=cfg)
    mtm_df.to_excel(output_path, index=False, sheet_name="MTM Report")
    return mtm_df
