from engine.type import Type
from flp.flp_calculator import FLPCalculator
from flp.flp_dataset import Dataset
import pandas as pd


class Calculator:
    """
    Performs the calculation on the given dataframe.
    """

    def __init__(self, household_size: int, percentile: int, df: pd.DataFrame) -> None:
        # Income
        income_rows = df[df["type"] == Type.INCOME]
        self.income_total = income_rows["amount"].sum()
        self.income_by_category = income_rows.groupby(by="category")["amount"].sum()

        # Expenses
        expense_rows = df[df["type"] == Type.EXPENSE]
        expense_rows["amount"] *= -1
        self.expense_total = expense_rows["amount"].sum()
        self.expense_by_category = expense_rows.groupby(by="category")["amount"].sum()

        # Giving
        giving_rows = df[df["type"] == Type.GIVING]
        giving_rows["amount"] *= -1
        self.giving_total = giving_rows["amount"].sum()
        self.giving_by_category = giving_rows.groupby(by="category")["amount"].sum()

        # No Type
        no_type_rows = df[df["type"] == Type.NO_TYPE]
        self.no_type_rows_string = no_type_rows[
            ["filename", "date", "description", "amount"]
        ].to_string(index=False)

        # Cash leftover
        self.in_minus_out = self.income_total - self.expense_total - self.giving_total

        # Line
        self.line = self._compute_monthly_line(household_size, percentile)
        self.line_minus_expenses = self.line - self.expense_total

    def _compute_monthly_line(self, household_size: int, percentile: int) -> float:
        """
        Computes the monthly line (our budget goal) given the household size
        and percentile.

        :param household_size: The number of people in the household.
        :param percentile: The percentile to use for the calculation.
        :return: The monthly line, which is the annual line divided by 12.
        """
        flp_calculator = FLPCalculator(Dataset())
        return flp_calculator.compute_annual_line(household_size, percentile) / 12
