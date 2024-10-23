from engine.parser import Parser
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class Processor:
    NO_TYPE = "no type"
    NO_CATEGORY = "no category"

    def __init__(
        self,
        name: str,
        file_prefix: str,
        parser: Parser,
        skip_transactions: list[str],
        type_category_by_identifier: dict[str, tuple[str, str]],
    ):
        self._name = name
        self._file_prefix = file_prefix
        self._parser = parser
        self._skip_transactions = skip_transactions
        self._type_category_by_identifier = type_category_by_identifier
        self._identifiers = type_category_by_identifier.keys()

    def __eq__(self, other):
        return (
            self._name == other._name
            and self._file_prefix == other._file_prefix
            and self._parser == other._parser
            and self._skip_transactions == other._skip_transactions
            and self._type_category_by_identifier == other._type_category_by_identifier
            and self._identifiers == other._identifiers
        )

    def parse(self, file_path: str) -> pd.DataFrame:
        """
        Reads a file, normalizes the column names, and returns a DataFrame.
        """
        df = self._parser.parse_and_normalize_column_names(file_path)
        return df

    def remove_skipped_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Removes rows from the DataFrame that have descriptions matching any of the
        skip_transactions.

        This method converts the description to lowercase and checks if it contains any
        of the strings in skip_transactions using the _word_contains_any_substring method.

        :param df: A pandas DataFrame with a "description" column containing transaction details.
        :return: A DataFrame with rows removed that match any skip_transactions.
        """
        skip_filter = (
            df["description"]
            .str.lower()
            .apply(
                lambda desc: Processor._word_contains_any_substring(
                    desc, self._skip_transactions
                )
            )
        )
        logger.debug(f"Skipping transactions: {df[skip_filter]}")
        return df[~skip_filter]

    def categorize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Categorizes each row in the DataFrame based on its description.

        This method applies the _categorize_row function to each row in the DataFrame,
        which assigns a type and category to each transaction based on known identifiers.
        The resulting DataFrame will have separate columns for the type and category of
        each transaction.

        :param df: A pandas DataFrame with a "description" column containing transaction details.
        :return: A DataFrame with additional columns for "type" and "category".
        """
        return df.apply(lambda row: pd.Series(self._categorize_row(row)), axis=1)

    def _categorize_row(self, row: pd.Series) -> str:
        """
        Categorizes a row based on its description by matching it against known identifiers.

        The function converts the description to lowercase and attempts to find matching identifiers.
        If no matching identifiers are found, it categorizes the row as having no type and no category.
        If multiple matching identifiers are found, it ensures they belong to the same category,
        otherwise raises a ValueError.

        :param row: A pandas Series representing a single transaction row with a "description" field.
        :return: A dictionary with "type" and "category" keys representing the type and category
                of the transaction.
        :raises ValueError: If multiple identifiers from different categories are found in the description.
        """
        lowercase_desc = row["description"].lower()
        matching_identifiers = Processor._find_matching_identifiers(
            lowercase_desc, self._identifiers
        )
        if not matching_identifiers:
            logger.info(f"No category found for {row['description']}")
            return {"type": Processor.NO_TYPE, "category": Processor.NO_CATEGORY}

        if len(matching_identifiers) > 1:
            type_categories = set()
            for matching_identifier in matching_identifiers:
                type_categories.add(
                    self._type_category_by_identifier[matching_identifier]
                )

            if len(type_categories) > 1:
                logger.error(row)
                raise ValueError(
                    f"Transaction contained identifiers across multiple categories: {matching_identifiers}"
                )

        type, category = self._type_category_by_identifier[matching_identifiers[0]]
        return {"type": type, "category": category}

    def _find_matching_identifiers(
        lowercase_desc: str, identifiers: list[str]
    ) -> list[str]:
        """
        Finds all identifiers in the given list of identifiers that are substrings of
        in the given lowercase description.
        """
        return [
            identifier for identifier in identifiers if identifier in lowercase_desc
        ]

    def _word_contains_any_substring(word: str, substrings: list[str]) -> bool:
        """
        Checks if any of the substrings are in the given word.

        Parameters
        ----------
        word : str
            The word to check
        substrings : list[str]
            The list of substrings to check

        Returns
        -------
        bool
            True if any of the substrings are in the word, False otherwise.
        """
        return any(substring in word for substring in substrings)
