import time
import sys

from colorama import Fore, Style
from colorama.ansi import AnsiCodes

def color_string(color: AnsiCodes, string: str) -> str:
    return f"{color}{string}{Style.RESET_ALL}"


def print_line():
    print(color_string(Fore.GREEN, "-" * 50))


def print_message_with_checkmark(message, delay=0.5):
    # Print the initial message without a newline and flush the buffer
    print(f"{color_string(Fore.YELLOW, message)} ⏳", end='', flush=True)

    # Wait for the specified delay
    time.sleep(delay)

    # Move the cursor back to the beginning of the line and overwrite the message
    sys.stdout.write('\r' + message + color_string(Fore.GREEN, ' ✔') + '\n')
    sys.stdout.flush()
