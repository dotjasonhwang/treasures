import argparse

def get_args():
    parser = argparse.ArgumentParser(
        description="""TODO""")
    parser.add_argument(
        '-f', '--file_dir',
        help="Location of the bank transactions")
    return parser.parse_args()
