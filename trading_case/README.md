## Trading Case – MTM Valuation

This folder groups files related to the **Trading Case Assessment (MTM valuation)**.

Main files (located in the project root):
- `mtm_calculator.py` – core MTM valuation logic.
- `run_mtm_report.py` – CLI script to generate `MTM_valuation_report.xlsx`.
- `Trading Case Example Data.xlsx` – input data (Price & Contracts).
- `MTM_valuation_report.xlsx` – example output report.

How to run from the project root:

```bash
pip install -r requirements.txt
python run_mtm_report.py \
  --input "Trading Case Example Data.xlsx" \
  --output "MTM_valuation_report.xlsx"
```

Use this folder as the **logical home** for any extra documentation, notes, or tests you add for the trading case.

