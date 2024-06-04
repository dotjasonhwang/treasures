import os
import pandas as pd
import time
import sys

from colorama import Fore, Back, Style, init
from my_argparse import get_args
from parser.parser import Parser, BOAParser, ChaseParser

def the_line():
    return 5000


def print_line():
    print(Fore.GREEN + "-" * 50 + Style.RESET_ALL)


def select_parser(filename: str) -> Parser:
    if filename.startswith("boa"):
        return BOAParser()
    if filename.startswith("chase"):
        return ChaseParser()
    raise Exception(filename)


def print_message_with_checkmark(message, delay=3):
    # Print the initial message without a newline and flush the buffer
    print(f"{Fore.YELLOW + message + Style.RESET_ALL} ⏳", end='', flush=True)
    
    # Wait for the specified delay
    time.sleep(delay)
    
    # Move the cursor back to the beginning of the line and overwrite the message
    sys.stdout.write('\r' + message + Fore.GREEN + ' ✔' + Style.RESET_ALL + '\n')
    sys.stdout.flush()


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
        parser = select_parser(filename)
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
    below_line = the_line() - total_expenses
    print(f"Your line is {Back.BLUE} {the_line():.2f} {Style.RESET_ALL}")
    if below_line > 0:
        print(f"You were {Fore.GREEN} {below_line:.2f} {Style.RESET_ALL} below your finish line")
    elif below_line == 0:
        print("You were exactly on the JOG line!")
    else:
        print(f"You were {Fore.RED} {(below_line * -1):.2f} {Style.RESET_ALL} above your finish line")

    total_above_line = spending[spending["over_line_item"]]["amount"].sum()
    print(f"You have stored {Fore.YELLOW} {total_above_line:.2f} {Style.RESET_ALL} as treasure this month")

    print_line()
    print(combined_df.groupby(by="category")["amount"].sum())

    # 'commit' the change here to the file database

    # print(f"""Starting NLFSlides...\n
    # Using processor version: {args.version}
    # Reading txt files from: {io_handler.input_folder_path()}
    # Savings pptx files to: {io_handler.output_file_path()}\n""")


if __name__ == "__main__":
    main()
