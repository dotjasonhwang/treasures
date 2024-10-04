import os
import pandas as pd

from colorama import Fore, Back, init
from cli.argparse import get_args
from cli.printer import Printer
from engine.calculator import Calculator
from processor.processor import Processor, BOAProcessor, ChaseProcessor


def select_processor(filename: str) -> Processor:
    if filename.startswith("boa"):
        return BOAProcessor("boa")
    if filename.startswith("chase"):
        return ChaseProcessor("chase_saph")
    raise ValueError(f"Could not determine processor for {filename}")

def main():
    # initialize colorama
    init()
    printer = Printer()

    printer.print_message_with_checkmark("Starting up ")
    
    args = get_args()
    file_dir = args.file_dir

    dataframes = []
    printer.print_message_with_checkmark("Opening folder")
    for filename in os.listdir(file_dir):
        file_path = f"{file_dir}/{os.fsdecode(filename)}"

        printer.print_message_with_checkmark(f"\tReading {filename}")
        processor = select_processor(filename)
        df = processor.parse(file_path)
        df = processor.categorize(df)
        df = processor.normalize(df)
        df = processor.filter(df)
        df = processor.set_line_flags(df)
        df["card_name"] = processor.card_name
        df["amount"] = abs(df["amount"])

        # duplicate check, and correction workflow
        dataframes.append(df)

    combined_df = pd.concat(dataframes)
    calculator = Calculator(combined_df)
    display_stats(printer, calculator)

def display_stats(printer: Printer, calculator: Calculator) -> None:
    printer.print_line()
    print(f"In: {calculator.income_total:.2f}")
    print(f"Out: {calculator.out_total:.2f}")
    print(f"In - Out: {printer.format_delta(f"{calculator.in_minus_out:.2f}")}")
    
    printer.print_line()
    print(f"Your line is { printer.color_string(Back.BLUE, f"{calculator.line:.2f}") } ")
    print(f"Line - Expenses: {printer.format_delta(f"{calculator.line_minus_expenses:.2f}")}")
    print(f"You have stored { printer.color_string(Fore.YELLOW, f"{calculator.treasures_total:.2f}") } as treasure this month")

    printer.print_line()
    
    print(calculator.breakdown)

    # 'commit' the change here to the file database

if __name__ == "__main__":
    main()
