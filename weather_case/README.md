## Weather Data Analysis – Precipitation Assistant

This folder groups files related to the **Weather Data Analysis Assessment**.

Main files (located in the project root):
- `weather_analysis.py` – precipitation query engine and simple natural-language parser.
- `run_weather_assistant.py` – CLI assistant for answering questions.
- `weather_app.py` – Streamlit web UI for the assistant.
- `create_mock_weather_data.py` – helper to generate `Weather Data Example.xlsx` mock data.
- `Weather Data Example.xlsx` – example input data produced by the script above.

### Run from the project root

Install dependencies (only once):

```bash
pip install -r requirements.txt
```

Generate mock data (optional, for demo/testing):

```bash
python create_mock_weather_data.py
```

Run the CLI assistant:

```bash
python run_weather_assistant.py --excel "Weather Data Example.xlsx"
```

Run the web UI:

```bash
streamlit run weather_app.py
```

Use this folder as the **logical home** for any extra documentation, notes, or tests you add for the weather case.

