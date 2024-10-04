import time
import sys

from colorama import Fore, Style
from colorama.ansi import AnsiCodes


class Printer:
    def color_string(self, color: AnsiCodes, string: str) -> str:
        """Formats a string with the given color and resets to default afterwards."""
        return f"{color}{string}{Style.RESET_ALL}"

    def format_delta(self, delta: str) -> str:
        """Returns a red or green color string based on the sign of the given float value."""
        color = Fore.RED if float(delta) < 0 else Fore.GREEN
        return f"{color}{delta}{Style.RESET_ALL}"

    def print_line(self) -> None:
        """Prints a green line with 50 hyphens."""
        print(self.color_string(Fore.GREEN, "-" * 50))

    def print_message_with_checkmark(self, message: str, delay: float = 0.5) -> None:
        """
        Prints a message with a yellow color and a timer emoji, waits for the specified delay,
        and then overwrites the message with the same text but with a green checkmark emoji.

        :param message: The message to display
        :param delay: The delay in seconds (default: 0.5)
        :return: None
        """
        print(f"{self.color_string(Fore.YELLOW, message)} ⏳", end="", flush=True)

        # Wait for the specified delay
        time.sleep(delay)

        # Move the cursor back to the beginning of the line and overwrite the message
        sys.stdout.write("\r" + message + self.color_string(Fore.GREEN, " ✔") + "\n")
        sys.stdout.flush()
