import io

import pandas as pd
import streamlit as st

from weather_analysis import WeatherConfig, load_weather_data, answer_question


st.set_page_config(page_title="Weather Precipitation Assistant", layout="wide")

st.title("Weather Data – Precipitation AI Assistant")
st.markdown(
    "Upload a weather Excel file with **Daily** and **Monthly** precipitation data, "
    "then ask questions in natural language (similar to the case-study examples)."
)


@st.cache_data(show_spinner=False)
def _load_data_from_bytes(data: bytes, filename: str):
    cfg = WeatherConfig(excel_path=filename)
    # pandas can read from a file-like object; we still pass cfg.excel_path only for metadata
    xls = pd.ExcelFile(io.BytesIO(data))
    daily = pd.read_excel(xls, sheet_name=cfg.daily_sheet)
    monthly = pd.read_excel(xls, sheet_name=cfg.monthly_sheet)

    # Reuse normalisation logic by mimicking load_weather_data
    from weather_analysis import (
        WeatherConfig as _Cfg,
        load_weather_data as _load_from_path,
    )

    # Write to an in-memory buffer as a workaround to reuse existing function
    # (simpler for this small demo than refactoring the library code).
    tmp_buf = io.BytesIO()
    with pd.ExcelWriter(tmp_buf, engine="openpyxl") as writer:
        daily.to_excel(writer, sheet_name=cfg.daily_sheet, index=False)
        monthly.to_excel(writer, sheet_name=cfg.monthly_sheet, index=False)
    tmp_buf.seek(0)

    # load_weather_data accepts anything that pandas.ExcelFile accepts (including BytesIO)
    cfg2 = _Cfg(excel_path=tmp_buf)
    daily_norm, monthly_norm = _load_from_path(cfg2)
    return daily_norm, monthly_norm


uploaded = st.file_uploader(
    "Upload weather Excel file", type=["xlsx"], help="Should contain 'Daily' and 'Monthly' sheets."
)

question = st.text_area(
    "Enter your precipitation question",
    value="What is the total precipitation amount of district Lucknow in each August and September from year 2001 to 2005?",
    height=80,
)

col_run, col_info = st.columns([1, 3])

with col_run:
    run_btn = st.button("Get answer")

with col_info:
    st.markdown(
        "- Example 1: `What is the total precipitation amount of district Pune in each August and September from year 2001 to 2005?`  \n"
        "- Example 2: `Compare the precipitation amount of state Uttar Pradesh and state Maharashtra in the second week of Nov 2005 in a table format.`"
    )

if run_btn:
    if uploaded is None:
        st.error("Please upload a weather Excel file first.")
    else:
        data = uploaded.read()
        with st.spinner("Loading data and answering your question..."):
            daily_df, monthly_df = _load_data_from_bytes(data, uploaded.name)
            text_answer, table = answer_question(question, daily=daily_df, monthly=monthly_df)

        st.subheader("Answer")
        st.write(text_answer)

        if table is not None and not table.empty:
            st.subheader("Result table")
            st.dataframe(table)

            # Allow download as Excel
            out_buf = io.BytesIO()
            with pd.ExcelWriter(out_buf, engine="openpyxl") as writer:
                table.to_excel(writer, sheet_name="Answer", index=False)
            out_buf.seek(0)

            st.download_button(
                "Download table as Excel",
                data=out_buf,
                file_name="weather_answer.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("No data matched your question. Try adjusting the wording or data range.")

