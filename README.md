# Kiran_Case_Study

This repository contains two case-study apps:

- Trading MTM valuation (in `trading_case`)
- Weather precipitation assistant (in `weather_case`)

<img width="1327" height="812" alt="Screenshot 2026-02-02 183710" src="https://github.com/user-attachments/assets/aace8d25-a277-4000-8fae-a4a502b5402b" />

<img width="533" height="428" alt="Screenshot 2026-02-02 183820" src="https://github.com/user-attachments/assets/fe4f670b-b0e9-4c49-a3a5-54a232c98f69" />

<img width="540" height="436" alt="Screenshot 2026-02-02 183845" src="https://github.com/user-attachments/assets/982103e6-65ca-4240-884e-3fd7d9659b6b" />




Quick start (Windows / cmd.exe)

1) Clone and open the repo root

```cmd
git clone <repo-url>
cd Kiran_Case_Study
```

2) Create and activate a virtual environment

```cmd
python -m venv .venv
.venv\Scripts\activate
```

3) Install dependencies

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

4) Run the trading MTM report (CLI)

```cmd
python trading_case\run_mtm_report.py -i "trading_case\Trading Case Example Data.xlsx" -o "MTM_valuation_report.xlsx"
```

5) Run the Trading Streamlit UI

```cmd
streamlit run trading_case\trading_app.py --server.port 8502
```

- The UI looks for `trading_case\Trading Case Example Data.xlsx` by default. You can upload your own `.xlsx` with `Price` and `Contracts` sheets.

6) Run the Weather Streamlit UI

```cmd
streamlit run weather_case\weather_app.py --server.port 8503
```

- Upload an Excel with `Daily` and `Monthly` sheets, then ask a natural-language question.

Troubleshooting

- If Streamlit complains `set_page_config` must be first, ensure you run `streamlit run` from the project root; the repository's apps are configured correctly.
- If a port is already used, pick another port (e.g., `--server.port 8504`).
- If imports fail, confirm you are running commands from the repo root and your venv is activated.

Remove duplicate Streamlit entrypoint

- A duplicate file `trading_case/streamlit_app.py` was neutralized to avoid confusion; the canonical entrypoint is `trading_case/trading_app.py`.

Contact / Next steps

If you want, I can:
- Start both Streamlit servers for you and verify they load.
- Add example screenshots or make small UI improvements.
