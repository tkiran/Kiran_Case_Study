from __future__ import annotations

from io import BytesIO
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from trading_case.mtm_calculator import generate_daily_mtm_report
from weather_case.weather_analysis import WeatherConfig, load_weather_data, answer_question


app = FastAPI(title="Case Study API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/trading/mtm")
async def trading_mtm(
    file: UploadFile = File(..., description="Excel file with Price and Contracts sheets"),
    valuation_date: Optional[str] = Form(
        None,
        description="Valuation date (YYYY-MM-DD). If omitted, uses latest price date in Price sheet.",
    ),
):
    """
    Compute MTM report for uploaded trading Excel and return data as JSON rows.
    """
    try:
        contents = await file.read()
        in_mem = BytesIO(contents)

        # Use in-memory Excel with pandas
        tmp_path = BytesIO(contents)
        tmp_path.seek(0)
        df = generate_daily_mtm_report(
            excel_path=tmp_path,  # type: ignore[arg-type]
            output_path=BytesIO(),  # discarded; we only use the DataFrame
            valuation_date=valuation_date,
        )

        return {"rows": df.to_dict(orient="records")}
    except Exception as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})


@app.post("/api/weather/answer")
async def weather_answer(
    file: UploadFile = File(..., description="Excel file with Daily and Monthly sheets"),
    question: str = Form(..., description="Natural-language precipitation question"),
):
    """
    Answer a precipitation question using uploaded weather Excel.
    """
    try:
        contents = await file.read()
        buf = BytesIO(contents)
        cfg = WeatherConfig(excel_path=buf)  # type: ignore[arg-type]

        # load_weather_data accepts anything that pandas.ExcelFile accepts
        daily_df, monthly_df = load_weather_data(cfg)

        text_answer, table = answer_question(question, daily=daily_df, monthly=monthly_df, cfg=cfg)

        table_rows = table.to_dict(orient="records") if table is not None else None

        return {"answer": text_answer, "table": table_rows}
    except Exception as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}

