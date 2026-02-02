import io
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from trading_case.mtm_calculator import generate_daily_mtm_report


st.set_page_config(page_title="Trading MTM Valuation Assistant", layout="wide")

st.title("Trading Case – MTM Valuation Assistant")
st.markdown(
    "Upload a **Trading Case Example Data** Excel file (with `Price` and `Contracts` sheets), "
    "choose a valuation date, and generate a daily MTM valuation report."
)


def _save_uploaded_file(uploaded_file) -> Path:
    """Save uploaded Excel to a temporary path under the current directory."""
    data = uploaded_file.read()
    path = Path(f"uploaded_{uploaded_file.name}")
    path.write_bytes(data)
    return path


uploaded = st.file_uploader(
    "Upload trading Excel file", type=["xlsx"], help="Should contain 'Price' and 'Contracts' sheets."
)

use_default = st.checkbox(
    "Use existing 'Trading Case Example Data.xlsx' from this folder (ignore upload)", value=False
)

val_date = st.date_input("Valuation date (leave as default to use latest price date)", value=None)

run_btn = st.button("Generate MTM report")

if run_btn:
    try:
        if use_default:
            excel_path = Path("Trading Case Example Data.xlsx")
            if not excel_path.exists():
                st.error("Could not find 'Trading Case Example Data.xlsx' in the current folder.")
                st.stop()
        else:
            if uploaded is None:
                st.error("Please upload an Excel file or tick the checkbox to use the default file.")
                st.stop()
            excel_path = _save_uploaded_file(uploaded)

        valuation_date_str = None
        if isinstance(val_date, date):
            valuation_date_str = val_date.isoformat()

        with st.spinner("Calculating MTM valuation..."):
            output_path = Path("MTM_valuation_report_streamlit.xlsx")
            mtm_df = generate_daily_mtm_report(
                excel_path=str(excel_path),
                output_path=str(output_path),
                valuation_date=valuation_date_str,
            )

        st.success(f"MTM report generated ({len(mtm_df)} rows).")

        st.subheader("MTM report preview")
        st.dataframe(mtm_df.head(50))

        # Prepare download
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            mtm_df.to_excel(writer, sheet_name="MTM Report", index=False)
        buf.seek(0)

        st.download_button(
            "Download full MTM report as Excel",
            data=buf,
            file_name="MTM_valuation_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as exc:
        st.error(f"Error generating MTM report: {exc}")

