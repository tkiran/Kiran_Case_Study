import argparse

from weather_analysis import WeatherConfig, load_weather_data, answer_question


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simple AI-like assistant for answering precipitation questions from weather data."
    )
    parser.add_argument(
        "--excel",
        "-e",
        type=str,
        default="Weather Data Example.xlsx",
        help="Path to Excel file containing Daily and Monthly precipitation sheets.",
    )
    parser.add_argument(
        "--question",
        "-q",
        type=str,
        required=False,
        help="Question in natural language. If omitted, you will be prompted interactively.",
    )
    parser.add_argument(
        "--output-table",
        "-o",
        type=str,
        required=False,
        help="Optional path to save the answer table as an Excel file.",
    )

    args = parser.parse_args()

    cfg = WeatherConfig(excel_path=args.excel)
    daily_df, monthly_df = load_weather_data(cfg)

    if args.question:
        question = args.question
    else:
        question = input("Enter your precipitation question:\n> ")

    text_answer, table = answer_question(question, daily=daily_df, monthly=monthly_df, cfg=cfg)

    print("\nAnswer:")
    print(text_answer)

    if table is not None:
        print("\nTable preview (first 10 rows):")
        print(table.head(10).to_string(index=False))

        if args.output_table:
            table.to_excel(args.output_table, index=False)
            print(f"\nFull table written to: {args.output_table}")


if __name__ == "__main__":
    main()

