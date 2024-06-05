import os
import pandas as pd

from colorama import Fore, Back, init
from cli.argparse import get_args
from cli.printer import print_line, color_string
from cli.printer import print_message_with_checkmark
from processor.processor import Processor, BOAProcessor, ChaseProcessor

def compute_line(household_size: int, percentile: int) -> float:
    return 5000

def select_processor(filename: str) -> Processor:
    if filename.startswith("boa"):
        return BOAProcessor()
    if filename.startswith("chase"):
        return ChaseProcessor()
    raise Exception(filename)


def main():
    # initialize colorama
    init()

    print_message_with_checkmark("Starting up ")
    
    args = get_args()
    file_dir = args.file_dir

    dfs = []
    print_message_with_checkmark("Opening folder")
    for filename in os.listdir(file_dir):
        file_path = file_dir + '/' + os.fsdecode(filename)

        print_message_with_checkmark(f"\tReading {filename}")
        parser = select_processor(filename)
        df = parser.parse(file_path)
        df = parser.categorize(df)
        df = parser.normalize(df)
        df = parser.filter(df)
        df = parser.set_line_flags(df)
        df = df[df["date"] >= "2024-04-01"]
        df = df[["date", "category", "amount", "is_income", "over_line_item"]]
        df["amount"] = abs(df["amount"])
        dfs.append(df)

    combined_df = pd.concat(dfs)
    income = combined_df[combined_df["is_income"]]
    total_income = income["amount"].sum()

    spending = combined_df[~combined_df["is_income"]]
    total_spending = spending["amount"].sum()

    print_line()
    print(f"In: {total_income:.2f}")
    print(f"Out: {total_spending:.2f}")

    surplus = total_income - total_spending
    if surplus > 0:
        print(f"Surplus: {surplus:.2f}")
    else:
        print(f"Deficit: {(surplus * -1):.2f}")
    
    print_line()

    total_expenses = spending[~spending["over_line_item"]]["amount"].sum()
    line = compute_line(None, None)
    below_line = line - total_expenses
    print(f"Your line is { color_string(Back.BLUE, f"{line:.2f}") } ")
    if below_line > 0:
        print(f"You were { color_string(Fore.GREEN, f"{below_line:.2f}") } below your finish line")
    elif below_line == 0:
        print("You were exactly on the JOG line!")
    else:
        print(f"You were { color_string(Fore.RED, f"{(below_line * -1):.2f}") } above your finish line")

    total_above_line = spending[spending["over_line_item"]]["amount"].sum()
    print(f"You have stored { color_string(Fore.YELLOW, f"{total_above_line:.2f}") } as treasure this month")

    print_line()
    print(combined_df.groupby(by="category")["amount"].sum())

    # 'commit' the change here to the file database

if __name__ == "__main__":
    main()
