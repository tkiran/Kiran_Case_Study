from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, Literal

import pandas as pd


@dataclass
class WeatherConfig:
    """
    Configuration for sheet and column names in the weather Excel file.

    Adjust these if your actual column names differ.
    """

    excel_path: str = "Weather Data Example.xlsx"

    # Sheet names
    daily_sheet: str = "Daily"
    monthly_sheet: str = "Monthly"

    # Daily columns
    col_daily_date: str = "Date"
    col_daily_state: str = "State"
    col_daily_district: str = "District"
    col_daily_precip: str = "Daily Precipitation"

    # Monthly columns
    col_monthly_year: str = "Year"
    col_monthly_month: str = "Month"
    col_monthly_state: str = "State"
    col_monthly_district: str = "District"
    col_monthly_precip: str = "Monthly Precipitation"


def load_weather_data(cfg: WeatherConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load and normalise daily and monthly precipitation tables."""
    xls = pd.ExcelFile(cfg.excel_path)
    daily = pd.read_excel(xls, sheet_name=cfg.daily_sheet)
    monthly = pd.read_excel(xls, sheet_name=cfg.monthly_sheet)

    # Normalise daily
    daily = daily.copy()
    daily[cfg.col_daily_date] = pd.to_datetime(daily[cfg.col_daily_date])
    daily[cfg.col_daily_state] = daily[cfg.col_daily_state].astype(str).str.strip()
    daily[cfg.col_daily_district] = daily[cfg.col_daily_district].astype(str).str.strip()
    daily[cfg.col_daily_precip] = pd.to_numeric(daily[cfg.col_daily_precip], errors="coerce").fillna(0.0)

    # Normalise monthly
    monthly = monthly.copy()
    monthly[cfg.col_monthly_year] = pd.to_numeric(monthly[cfg.col_monthly_year], errors="coerce").astype("Int64")
    monthly[cfg.col_monthly_month] = pd.to_numeric(monthly[cfg.col_monthly_month], errors="coerce").astype("Int64")
    monthly[cfg.col_monthly_state] = monthly[cfg.col_monthly_state].astype(str).str.strip()
    monthly[cfg.col_monthly_district] = monthly[cfg.col_monthly_district].astype(str).str.strip()
    monthly[cfg.col_monthly_precip] = pd.to_numeric(
        monthly[cfg.col_monthly_precip], errors="coerce"
    ).fillna(0.0)

    return daily, monthly


def query_monthly_precip_by_district(
    monthly: pd.DataFrame,
    cfg: WeatherConfig,
    district: str,
    months: Optional[list[int]] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Example query:
      "total precipitation amount of district A in each August and September from year 2001 to 2005"
    """
    df = monthly.copy()
    district_norm = district.strip()
    df = df[df[cfg.col_monthly_district].str.casefold() == district_norm.casefold()]

    if months is not None:
        df = df[df[cfg.col_monthly_month].isin(months)]

    if start_year is not None:
        df = df[df[cfg.col_monthly_year] >= start_year]
    if end_year is not None:
        df = df[df[cfg.col_monthly_year] <= end_year]

    df = df.sort_values([cfg.col_monthly_year, cfg.col_monthly_month])
    return df[
        [
            cfg.col_monthly_year,
            cfg.col_monthly_month,
            cfg.col_monthly_state,
            cfg.col_monthly_district,
            cfg.col_monthly_precip,
        ]
    ]


def query_weekly_precip_by_state(
    daily: pd.DataFrame,
    cfg: WeatherConfig,
    state: str,
    iso_year: int,
    iso_week: int,
) -> pd.DataFrame:
    """
    Compute total precipitation for a given state in a given ISO week of a year.

    Supports questions like:
      "precipitation amount of state A in the second week of Nov 2025"
    (we interpret 'second week of Nov 2025' as ISO week 2 within that month
     by approximation using date ranges.)
    """
    df = daily.copy()
    df["Year"] = df[cfg.col_daily_date].dt.year
    df["ISO_Week"] = df[cfg.col_daily_date].dt.isocalendar().week.astype(int)
    df["Month"] = df[cfg.col_daily_date].dt.month

    state_norm = state.strip()
    df = df[df[cfg.col_daily_state].str.casefold() == state_norm.casefold()]
    df = df[df["Year"] == iso_year]
    df = df[df["ISO_Week"] == iso_week]

    grouped = (
        df.groupby([cfg.col_daily_state, "Year", "ISO_Week"], as_index=False)[cfg.col_daily_precip]
        .sum()
        .rename(columns={cfg.col_daily_precip: "Total Weekly Precipitation"})
    )
    return grouped


# --- Minimal natural-language helper ---

MonthName = Literal[
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


MONTH_NAME_TO_NUM: Dict[MonthName, int] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def parse_question(question: str) -> Dict[str, Any]:
    """
    Very small rule-based parser that recognises patterns similar to the examples.

    It returns a dict with:
      - type: "monthly_district" or "weekly_state" or "unknown"
      - parameters needed for the query.
    """
    import re

    q = question.strip().lower()

    # Pattern 1: district + months + year range (uses monthly table)
    # e.g. "total precipitation amount of district A in each August and September from year 2001 to 2005"
    m = re.search(
        r"district\s+(?P<district>[a-z\s]+?)\s+in\s+each\s+(?P<months>[a-z\s,]+)\s+from\s+year\s+(?P<start>\d{4})\s+to\s+(?P<end>\d{4})",
        q,
    )
    if m:
        district = m.group("district").strip().title()
        months_text = m.group("months")
        month_names = [x.strip() for x in re.split(r"[,\s]+", months_text) if x.strip()]
        month_nums = [
            MONTH_NAME_TO_NUM[name]
            for name in month_names
            if name in MONTH_NAME_TO_NUM
        ]
        return {
            "type": "monthly_district",
            "district": district,
            "months": month_nums,
            "start_year": int(m.group("start")),
            "end_year": int(m.group("end")),
        }

    # Pattern 2: compare two states in given week and month/year
    # Example target: "Compare the precipitation amount of state A and state B in the second week of Nov 2025"
    m = re.search(
        r"state\s+(?P<state_a>[a-z\s]+?)\s+and\s+state\s+(?P<state_b>[a-z\s]+?)\s+in\s+the\s+(?P<week_word>\w+)\s+week\s+of\s+(?P<month>[a-z]+)\s+(?P<year>\d{4})",
        q,
    )
    if m:
        state_a = m.group("state_a").strip().title()
        state_b = m.group("state_b").strip().title()
        month_name = m.group("month")
        year = int(m.group("year"))
        week_word = m.group("week_word")

        week_map = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
        }
        week_num = week_map.get(week_word, 2)

        month_num = MONTH_NAME_TO_NUM.get(month_name, None)

        return {
            "type": "weekly_state_compare",
            "state_a": state_a,
            "state_b": state_b,
            "iso_week": week_num,
            "month": month_num,
            "year": year,
        }

    return {"type": "unknown"}


def answer_question(
    question: str, daily: pd.DataFrame, monthly: pd.DataFrame, cfg: Optional[WeatherConfig] = None
) -> Tuple[str, Optional[pd.DataFrame]]:
    """
    High-level helper: parse a natural-language question and compute an answer.

    Returns a (text_answer, optional_table_df).
    """
    cfg = cfg or WeatherConfig()
    intent = parse_question(question)

    if intent["type"] == "monthly_district":
        df = query_monthly_precip_by_district(
            monthly=monthly,
            cfg=cfg,
            district=intent["district"],
            months=intent["months"],
            start_year=intent["start_year"],
            end_year=intent["end_year"],
        )
        if df.empty:
            return (
                f"No monthly precipitation data found for district {intent['district']} in the requested period.",
                None,
            )

        total = df[cfg.col_monthly_precip].sum()
        text = (
            f"Total precipitation in district {intent['district']} "
            f"for months {intent['months']} from {intent['start_year']} to {intent['end_year']} "
            f"is {total:.2f} units. See table for yearly/monthly breakdown."
        )
        return text, df

    if intent["type"] == "weekly_state_compare":
        df_a = query_weekly_precip_by_state(
            daily=daily,
            cfg=cfg,
            state=intent["state_a"],
            iso_year=intent["year"],
            iso_week=intent["iso_week"],
        )
        df_b = query_weekly_precip_by_state(
            daily=daily,
            cfg=cfg,
            state=intent["state_b"],
            iso_year=intent["year"],
            iso_week=intent["iso_week"],
        )
        if df_a.empty and df_b.empty:
            return "No weekly precipitation data found for the requested states/week.", None

        total_a = (
            df_a["Total Weekly Precipitation"].iloc[0]
            if "Total Weekly Precipitation" in df_a.columns and not df_a.empty
            else 0.0
        )
        total_b = (
            df_b["Total Weekly Precipitation"].iloc[0]
            if "Total Weekly Precipitation" in df_b.columns and not df_b.empty
            else 0.0
        )

        comparison = pd.DataFrame(
            {
                "State": [intent["state_a"], intent["state_b"]],
                "Total Weekly Precipitation": [total_a, total_b],
                "Year": [intent["year"], intent["year"]],
                "ISO_Week": [intent["iso_week"], intent["iso_week"]],
            }
        )

        text = (
            f"In week {intent['iso_week']} of {intent['year']}, "
            f"state {intent['state_a']} had {total_a:.2f} units of precipitation, "
            f"while state {intent['state_b']} had {total_b:.2f} units."
        )
        return text, comparison

    return (
        "I could not understand this question with the simple patterns I support. "
        "Please try phrasing it like the examples in the assessment.",
        None,
    )


