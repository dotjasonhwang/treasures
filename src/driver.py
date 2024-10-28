import os
import pandas as pd

from colorama import Fore, Back, init
from cli.argparse import get_args
from cli.printer import Printer
from engine.calculator import Calculator
from engine.config_loader import ConfigLoader
from engine.parser import BOADebitParser, ChaseCreditParser, CitiCreditParser
from flp.flp_calculator import FLPCalculator
from flp.flp_dataset import Dataset
import logging

from engine.processor import Processor

logger = logging.getLogger(__name__)

PARSER_BY_FORMAT = {
    "boa_debit": BOADebitParser(),
    "chase_credit": ChaseCreditParser(),
    "citi_credit": CitiCreditParser(),
    "chase_debit": None,
}


def main():
    # initialize colorama
    init()
    printer = Printer()
    args = get_args()
    file_dir = args.file_dir

    printer.print_message_with_checkmark("Starting up")
    config_loader = ConfigLoader(args.config_file, PARSER_BY_FORMAT)
    nickname_by_filename = config_loader.load_nickname_by_filename()
    processors = config_loader.load_processors()
    dataframes = []
    printer.print_message_with_checkmark("Opening folder")

    for filename in os.listdir(file_dir):
        printer.print_message_with_checkmark(f"\tReading {filename}")
        processor = get_matching_processor(filename, processors)

        df = processor.parse(f"{file_dir}/{os.fsdecode(filename)}")
        if filename not in nickname_by_filename:
            raise ValueError(f"{filename} does not have a nickname in the config file")
        df["filename"] = filename
        df["account_name"] = nickname_by_filename[filename]
        df = processor.remove_skipped_transactions(df)
        df = processor.categorize(df)
        df = df[
            [
                "date",
                "description",
                "amount",
                "filename",
                "account_name",
                "type",
                "category",
            ]
        ]
        dataframes.append(df)

    combined_df = pd.concat(dataframes)
    calculator = Calculator(
        FLPCalculator(Dataset()), args.household_size, args.percentile, combined_df
    )
    display_stats(printer, calculator)


def get_matching_processor(filename: str, processors: list[Processor]) -> Processor:
    """
    Given a list of Processors and a filename, return the processor whose prefix matches the filename.
    If no processor matches, raise an exception.
    If multiple processors match, raise an exception.
    """
    matching_processors = [
        processor
        for processor in processors
        if filename.startswith(processor._file_prefix)
    ]
    if len(matching_processors) == 0:
        raise ValueError(f"No processor prefix matches file: {filename}")
    if len(matching_processors) > 1:
        raise ValueError(
            f"Multiple processors: {[processor._name for processor in matching_processors]} have prefixes matching file: {filename}"
        )
    return matching_processors[0]


def display_stats(printer: Printer, calculator: Calculator) -> None:
    printer.print_line()
    print(
        f"You have stored { printer.color_string(Fore.YELLOW, f"{calculator._giving_total:.2f}") } as treasure this month"
    )
    printer.print_line()
    print(f"In: {calculator.income_total():.2f}")
    print(f"Expenses: {calculator.expense_total():.2f}")
    print(f"Giving: {calculator.giving_total():.2f}")
    print(f"In - Out: {printer.format_delta(f"{calculator.in_minus_out():.2f}")}")
    printer.print_line()
    print(
        f"Your line is { printer.color_string(Back.BLUE, f"{calculator.line():.2f}") } "
    )
    print(
        f"Line - Expenses: {printer.format_delta(f"{calculator.line_minus_expenses():.2f}")}"
    )

    printer.print_line()
    print("Income by category:")
    print(calculator.income_by_category())

    printer.print_line()
    print("Expenses by category:")
    print(calculator.expense_by_category())

    printer.print_line()
    print("Giving by category:")
    print(calculator.giving_by_category())

    printer.print_line()
    print(
        "Transactions that did not match any identifiers. Please update the config or the row to make them match an identifier:"
    )
    print(calculator.no_type_rows().to_string(index=False))

    # 'commit' the change here to the file database


if __name__ == "__main__":
    main()
