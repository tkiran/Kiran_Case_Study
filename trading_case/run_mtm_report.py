import argparse
from pathlib import Path
import sys

try:
    from trading_case.mtm_calculator import generate_daily_mtm_report
except ModuleNotFoundError:
    # Support running this script directly (python trading_case\run_mtm_report.py)
    # In that case the script's directory is on sys.path and a package import
    # using the package name will fail; fall back to a local import.
    from mtm_calculator import generate_daily_mtm_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate daily MTM valuation report for iron ore contracts.")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="Trading Case Example Data.xlsx",
        help="Path to input Excel file containing Price and Contracts sheets.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="MTM_valuation_report.xlsx",
        help="Path to output Excel report file.",
    )
    parser.add_argument(
        "--date",
        "-d",
        type=str,
        default=None,
        help="Valuation date (YYYY-MM-DD). If omitted, uses latest price date in Price sheet.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input Excel file not found: {input_path}")

    try:
        mtm_df = generate_daily_mtm_report(
            excel_path=str(input_path),
            output_path=str(output_path),
            valuation_date=args.date,
        )
    except Exception as exc:
        raise SystemExit(f"Failed to generate MTM report: {exc}") from exc

    print(f"MTM report generated: {output_path} ({len(mtm_df)} rows)")


if __name__ == "__main__":
    main()