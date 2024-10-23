import os
import pandas as pd

from colorama import Fore, Back, init
from cli.argparse import get_args
from cli.printer import Printer
from engine.calculator import Calculator
from engine.config_loader import ConfigLoader
from engine.parser import BOAParser, ChaseParser
import logging

from engine.processor import Processor

logger = logging.getLogger(__name__)


def main():
    # initialize colorama
    init()
    printer = Printer()
    args = get_args()
    file_dir = args.file_dir

    parser_by_format = {"boa": BOAParser(), "chase_credit": ChaseParser()}

    printer.print_message_with_checkmark("Starting up")
    config_loader = ConfigLoader(args.config, parser_by_format)
    nickname_by_filename = config_loader.load_nickname_by_filename()
    processors = config_loader.load_processors()
    dataframes = []
    printer.print_message_with_checkmark("Opening folder")

    for filename in os.listdir(file_dir):
        printer.print_message_with_checkmark(f"\tReading {filename}")
        processor = get_matching_processor(file_dir, processors)

        df = processor.parse(f"{file_dir}/{os.fsdecode(filename)}")
        if filename not in nickname_by_filename:
            raise ValueError(f"{filename} does not have a nickname in the config file")
        df["account_name"] = nickname_by_filename[filename]
        df = processor.remove_skipped_transactions(df)
        df = processor.categorize(df)
        dataframes.append(df)

    combined_df = pd.concat(dataframes)
    calculator = Calculator(args.household_size, args.percentile, combined_df)
    display_stats(printer, calculator)


def get_matching_processor(file_name: str, processors: list[Processor]) -> Processor:
    """
    Given a list of Processors and a filename, return the processor whose prefix matches the filename.
    If no processor matches, raise an exception.
    If multiple processors match, raise an exception.
    """
    matching_processors = [
        processor
        for processor in processors
        if file_name.startswith(processor._file_prefix)
    ]
    if len(matching_processors) == 0:
        raise ValueError(f"No processor prefix matches file: {file_name}")
    if len(matching_processors) > 1:
        raise ValueError(
            f"Multiple processors: {[processor._name for processor in matching_processors]} have prefixes matching file: {file_name}"
        )
    return matching_processors[0]


def display_stats(printer: Printer, calculator: Calculator) -> None:
    printer.print_line()
    print(
        f"You have stored { printer.color_string(Fore.YELLOW, f"{calculator.giving_total:.2f}") } as treasure this month"
    )
    printer.print_line()
    print(f"In: {calculator.income_total:.2f}")
    print(f"Expenses: {calculator.expense_total:.2f}")
    print(f"Giving: {calculator.giving_total:.2f}")
    print(f"In - Out: {printer.format_delta(f"{calculator.in_minus_out:.2f}")}")
    printer.print_line()
    print(
        f"Your line is { printer.color_string(Back.BLUE, f"{calculator.line:.2f}") } "
    )
    print(
        f"Line - Expenses: {printer.format_delta(f"{calculator.line_minus_expenses:.2f}")}"
    )

    printer.print_line()
    print("Income by breakdown:")
    print(calculator.income_by_category)

    printer.print_line()
    print("Expenses by breakdown:")
    print(calculator.expense_by_category)

    printer.print_line()
    print("Giving by breakdown:")
    print(calculator.giving_by_category)

    # 'commit' the change here to the file database


if __name__ == "__main__":
    main()
