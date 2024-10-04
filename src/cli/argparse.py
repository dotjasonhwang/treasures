import argparse


def get_args() -> argparse.Namespace:
    """Parses command line arguments and returns the parsed namespace"""
    parser = argparse.ArgumentParser(description="Treasures")
    parser.add_argument(
        "-n", "--household_size", help="Household size", required=True, type=int
    )
    parser.add_argument(
        "-p",
        "--percentile",
        help="Target percentile of income",
        required=True,
        type=int,
    )
    parser.add_argument(
        "-f",
        "--file_dir",
        help="Location of the bank transactions",
        required=True,
    )
    return parser.parse_args()
