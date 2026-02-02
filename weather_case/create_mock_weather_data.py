import pandas as pd
from pathlib import Path


def create_mock_weather_excel(path: str = "Weather Data Example.xlsx") -> None:
    """
    Create a small mock weather Excel file with Daily and Monthly sheets,
    using the structure expected by weather_analysis. This is only for demo/testing.
    """
    # A few days of daily data
    daily_data = [
        # Date, State,          District,   Daily Precipitation
        ["2000-01-01", "Uttar Pradesh", "Lucknow", 2.40],
        ["2000-01-01", "Uttar Pradesh", "Kanpur", 2.35],
        ["2000-01-01", "Maharashtra", "Mumbai", 1.87],
        ["2000-01-01", "Maharashtra", "Pune", 6.52],
        ["2000-08-05", "Uttar Pradesh", "Lucknow", 10.0],
        ["2000-08-06", "Uttar Pradesh", "Lucknow", 12.5],
        ["2000-09-10", "Uttar Pradesh", "Lucknow", 5.0],
        ["2005-11-08", "Uttar Pradesh", "Lucknow", 3.0],
        ["2005-11-09", "Maharashtra", "Mumbai", 8.0],
    ]

    daily_df = pd.DataFrame(
        daily_data,
        columns=["Date", "State", "District", "Daily Precipitation"],
    )

    # Simple monthly aggregates consistent with the example format
    monthly_data = [
        # Year, Month, State,          District,   Monthly Precipitation
        [2000, 1, "Uttar Pradesh", "Lucknow", 138.47],
        [2000, 1, "Uttar Pradesh", "Kanpur", 127.21],
        [2000, 1, "Maharashtra", "Mumbai", 192.72],
        [2000, 1, "Maharashtra", "Pune", 154.38],
        [2001, 8, "Uttar Pradesh", "Lucknow", 210.0],
        [2001, 9, "Uttar Pradesh", "Lucknow", 180.0],
        [2002, 8, "Uttar Pradesh", "Lucknow", 220.0],
        [2002, 9, "Uttar Pradesh", "Lucknow", 190.0],
        [2003, 8, "Uttar Pradesh", "Lucknow", 230.0],
        [2003, 9, "Uttar Pradesh", "Lucknow", 200.0],
        [2004, 8, "Uttar Pradesh", "Lucknow", 240.0],
        [2004, 9, "Uttar Pradesh", "Lucknow", 210.0],
        [2005, 8, "Uttar Pradesh", "Lucknow", 250.0],
        [2005, 9, "Uttar Pradesh", "Lucknow", 220.0],
    ]

    monthly_df = pd.DataFrame(
        monthly_data,
        columns=["Year", "Month", "State", "District", "Monthly Precipitation"],
    )

    out_path = Path(path)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        daily_df.to_excel(writer, sheet_name="Daily", index=False)
        monthly_df.to_excel(writer, sheet_name="Monthly", index=False)

    print(f"Mock weather data Excel created at: {out_path.resolve()}")


if __name__ == "__main__":
    create_mock_weather_excel()

