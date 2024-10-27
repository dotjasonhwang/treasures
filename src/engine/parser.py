import pandas as pd


class Parser:
    def __init__(self, income_is_positive: bool) -> None:
        """
        Initializes the Parser with a flag indicating whether the raw file
        contains income as positive. If and only if income_is_positive is False,
        the amount will be flipped so that income is positive and expenses are negative.

        :param income_is_positive: A boolean indicating whether income is positive
            in the raw file.
        """
        self._income_is_positive = income_is_positive

    def parse_and_normalize_column_names(self, file_path: str) -> pd.DataFrame:
        """
        Reads a file, normalizes the column names, and returns a DataFrame.
        If the raw file's income is negative, the amount will be flipped so that
        income is positive and expenses are negative.

        Each file format should implement this method to read the file and rename
        any required columns.

        The following columns are required:

        - "description" (str)
        - "date" (datetime64[ns])
        - "amount" (float64)
            - Positive amounts are income, negative amounts are expenses

        :param file_path: The path to the file to read.
        :return: A DataFrame with the normalized columns.
        """
        df = self._parse(file_path)
        df = self._rename_columns(df)
        if not self._income_is_positive:
            df["amount"] *= -1
        return df

    def _parse(self, file_path: str) -> pd.DataFrame:
        """
        Reads a file and returns a DataFrame.

        Subclasses should implement this method to read the file.

        The following columns are required:

        - "Date" (datetime64[ns])
        - "Description" (str)
        - "Amount" (float64)
            - Positive amounts are income, negative amounts are expenses

        :param file_path: The path to the file to read.
        :return: A DataFrame with the required columns.
        """
        raise NotImplementedError

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Renames the columns of a parsed DataFrame to the normalized column names.

        Subclasses should implement this method to rename the columns of the parsed
        DataFrame to the normalized column names.

        The normalized column names are:

        - "description" (str)
        - "date" (datetime64[ns])
        - "amount" (float64)
            - Positive amounts are income, negative amounts are expenses

        :param df: The DataFrame to rename the columns of.
        :return: The DataFrame with the normalized column names.
        """
        raise NotImplementedError


class BOADebitParser(Parser):
    def __init__(self) -> None:
        super().__init__(True)

    def _parse(self, file_path: str) -> pd.DataFrame:
        df = pd.read_csv(
            file_path,
            header=5,
            usecols=["Date", "Description", "Amount"],
            dtype={"Amount": float},
            parse_dates=["Date"],
            thousands=",",
        )
        return df

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.str.lower()
        return df


class ChaseCreditParser(Parser):
    def __init__(self) -> None:
        super().__init__(True)

    def _parse(self, file_path: str) -> pd.DataFrame:
        df = pd.read_csv(
            file_path,
            usecols=["Transaction Date", "Description", "Category", "Type", "Amount"],
            dtype={"Amount": float},
            parse_dates=["Transaction Date"],
        )
        return df

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.rename(
            columns={
                "Transaction Date": "date",
                "Category": "chase_category",
                "Type": "chase_type",
            }
        )
        df.columns = df.columns.str.lower()
        return df
