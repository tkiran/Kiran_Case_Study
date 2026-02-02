## MTM Valuation Case – Python Solution

This folder contains a simple **Python + pandas** implementation of the MTM (mark‑to‑market) valuation case for iron ore cargoes.

The solution reads an input Excel file with two sheets:
- **`Price`** – daily market prices for indices.
- **`Contracts`** – contract data required for MTM calculation.

It then produces a **daily MTM valuation report** as a new Excel file.

### 1. Environment setup

From this folder, create and activate a virtual environment (optional but recommended), then install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Expected input structure

By default, the code expects an Excel file named `Trading Case Example Data.xlsx` in this directory with:

- **Sheet `Price`** containing at least:
  - `Date`
  - `Index Name`
  - `Tenor`
  - `Price`

- **Sheet `Contracts`** containing at least:
  - `Contract ID`
  - `Base Index Name`
  - `Tenor`
  - `Typical Fe`
  - `Fe Adj Flag` (e.g. `NoAdj` or any other string meaning “adjust by Fe”)
  - `Cost`
  - `Discount`
  - `Quantity`
  - `Unit` (`DMT` or `WMT`)
  - `Moisture`

If your actual column names differ, you can adapt them by editing the `MTMConfig` dataclass in `mtm_calculator.py`.

### 3. How the MTM is calculated

The implementation follows the case-study formula:

\[
\text{MTM Value} = (\text{Base Index Price} \times \text{Fe Adjustment Ratio} + \text{Cost}) \times \text{Discount} \times \text{Quantity (DMT)}
\]

Key rules:
- **Base Index Price** is looked up from the `Price` sheet by matching **Index Name** and **Tenor** and taking the **latest available price on or before the valuation date**.
- **Fe Adjustment Ratio**:
  - If `Fe Adj Flag` is `NoAdj` → ratio = 1.0
  - Otherwise → ratio = `Typical Fe / 62`
- **Quantity (DMT)**:
  - If `Unit` is `DMT` → use `Quantity` directly.
  - If `Unit` is `WMT` → `Quantity × (1 − Moisture)`.

The resulting report includes the contract data plus:
- `Base Index Price`
- `Fe Adjustment Ratio`
- `Quantity (DMT)`
- `MTM Value`
- `Valuation Date`

### 4. Generating the MTM report (CLI)

Run the CLI script from this folder:

```bash
python run_mtm_report.py \
  --input "Trading Case Example Data.xlsx" \
  --output "MTM_valuation_report.xlsx" \
  --date 2025-12-02
```

Arguments:
- `--input` / `-i` – path to the input Excel file (default: `Trading Case Example Data.xlsx`)
- `--output` / `-o` – path for the output report (default: `MTM_valuation_report.xlsx`)
- `--date` / `-d` – valuation date in `YYYY-MM-DD` format. If omitted, the script uses the **latest `Date` in the `Price` sheet**.

After running, you will get an Excel file (e.g. `MTM_valuation_report.xlsx`) that you can submit as the **example report** for the assessment.

### 5. Running as an API service (deployable)

The project also exposes a small **FastAPI** service (see `api_main.py`) so the MTM report can be generated
by other applications (e.g. a React UI or scheduler).

Start the API locally:

```bash
uvicorn api_main:app --reload
```

Key endpoints:
- `GET /api/health` – simple health check.
- `POST /api/trading/mtm` – form-data with:
  - `file`: Excel file (`Price` + `Contracts` sheets),
  - `valuation_date` (optional `YYYY-MM-DD`).
  - Returns JSON: `{ "rows": [ { ...columns... } ] }`.

There is also a Dockerfile so you can run the service as a container:

```bash
docker build -t mtm-weather-service .
docker run -p 8000:8000 mtm-weather-service
```

The same container also serves the **weather** API (see below).

### 6. GenAI appendix (template)

Create a separate document (e.g. `GenAI_Appendix.md`) listing:
- The GenAI product: e.g. “OpenAI ChatGPT / Cursor Assistant”.
- Each prompt you used, with a short note on how its response was used (e.g. “Helped design MTM calculation logic and project structure.”).

You can copy relevant prompts directly from your chat history and paste them into that appendix document.

---

## Weather Data Analysis – Precipitation Assistant

This part of the project implements a simple **AI‑style assistant** that can answer natural‑language questions
about precipitation using **daily** and **monthly** data tables.

It is designed to handle questions similar to the assessment examples, such as:
- “What is the total precipitation amount of district A in each August and September from year 2001 to 2005?”
- “Compare the precipitation amount of state A and state B in the second week of Nov 2025 in a table format.”

### 1. Expected input structure

By default, the assistant expects an Excel file named `Weather Data Example.xlsx` with two sheets:

- **Sheet `Daily`**:
  - `Date` – date (e.g. `1/1/2000`)
  - `State`
  - `District`
  - `Daily Precipitation` – float

- **Sheet `Monthly`**:
  - `Year` – integer year (e.g. `2000`)
  - `Month` – integer month (1–12)
  - `State`
  - `District`
  - `Monthly Precipitation` – float (sum of related daily precipitation)

If your actual sheet/column names differ, you can adjust them in the `WeatherConfig` dataclass inside `weather_analysis.py`.

### 2. How the assistant works

- `weather_analysis.py`:
  - Loads and normalises the **daily** and **monthly** tables with `pandas`.
  - Provides:
    - `query_monthly_precip_by_district(...)` – returns rows for a district over selected months and year range.
    - `query_weekly_precip_by_state(...)` – aggregates daily data into weekly totals per state.
  - Implements a small, rule‑based `parse_question(...)` function that looks for patterns like:
    - “total precipitation amount of district X in each August and September from year 2001 to 2005”
    - “compare the precipitation amount of state A and state B in the second week of Nov 2025”
  - `answer_question(...)` uses the parsed intent to:
    - Run the appropriate query,
    - Return a **textual summary** plus an optional **data table** as a `DataFrame`.

- `run_weather_assistant.py`:
  - Command‑line entry point that:
    - Loads the Excel file,
    - Accepts a natural‑language question (as an argument or interactively),
    - Prints a text answer and shows a preview table,
    - Optionally writes the full table to an Excel file.

### 3. Running the weather assistant (CLI)

Ensure dependencies are installed (same `requirements.txt` as the MTM case):

```bash
pip install -r requirements.txt
```

Then run, from this folder:

```bash
python run_weather_assistant.py \
  --excel "Weather Data Example.xlsx" \
  --question "What is the total precipitation amount of district Lucknow in each August and September from year 2001 to 2005?" \
  --output-table "weather_example_report.xlsx"
```

- `--excel` / `-e` – path to the Excel file with `Daily` and `Monthly` sheets.
- `--question` / `-q` – your natural‑language question.
- `--output-table` / `-o` – optional path to save the answer table as an Excel file (this can be your **example report**).

If you omit `--question`, the script will prompt you to type one at the terminal.

### 4. Running the weather assistant via API

The FastAPI service in `api_main.py` also exposes:

- `POST /api/weather/answer` – form-data with:
  - `file`: Excel file (`Daily` + `Monthly` sheets),
  - `question`: natural‑language question.
  - Returns JSON: `{ "answer": "...", "table": [ { ...row... } ] }`.

Use the same `uvicorn` / Docker commands as in the MTM section.

### 5. Example questions you can try

- `What is the total precipitation amount of district Pune in each August and September from year 2001 to 2005?`
- `Compare the precipitation amount of state Uttar Pradesh and state Maharashtra in the second week of Nov 2005 in a table format.`

For each query, the assistant:
- Prints a **short natural‑language answer** (totals and comparison),
- And, when requested, writes a **table** (per year/month or per state/week) that you can submit as the assessment’s example report.

