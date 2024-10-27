from engine.type import Type
from flp.flp_calculator import FLPCalculator
import pandas as pd


class Calculator:
    """
    Performs the calculation on the given dataframe.
    """

    def __init__(
        self,
        flp_calculator: FLPCalculator,
        household_size: int,
        percentile: int,
        df: pd.DataFrame,
    ) -> None:
        self._flp_calculator = flp_calculator

        # Income
        income_rows = df[df["type"] == Type.INCOME]
        self._income_total = income_rows["amount"].sum()
        self._income_by_category = income_rows.groupby(by="category")["amount"].sum()

        # Expenses
        expense_rows = df.loc[df["type"] == Type.EXPENSE].copy()
        expense_rows["amount"] *= -1
        self._expense_total = expense_rows["amount"].sum()
        self._expense_by_category = expense_rows.groupby(by="category")["amount"].sum()

        # Giving
        giving_rows = df.loc[df["type"] == Type.GIVING].copy()
        giving_rows["amount"] *= -1
        self._giving_total = giving_rows["amount"].sum()
        self._giving_by_category = giving_rows.groupby(by="category")["amount"].sum()

        # No Type
        no_type_rows = df[df["type"] == Type.NO_TYPE]
        self._no_type_rows = no_type_rows[["filename", "date", "description", "amount"]]

        # Line
        self._line = self._compute_monthly_line(household_size, percentile)

    def income_total(self) -> float:
        return self._income_total

    def income_by_category(self) -> pd.Series:
        return self._income_by_category

    def expense_total(self) -> float:
        return self._expense_total

    def expense_by_category(self) -> pd.Series:
        return self._expense_by_category

    def giving_total(self) -> float:
        return self._giving_total

    def giving_by_category(self) -> pd.Series:
        return self._giving_by_category

    def in_minus_out(self) -> float:
        return self.income_total() - self.expense_total() - self.giving_total()

    def line(self) -> float:
        return self._line

    def line_minus_expenses(self) -> float:
        return self._line - self._expense_total

    def no_type_rows(self) -> pd.DataFrame:
        return self._no_type_rows

    def _compute_monthly_line(self, household_size: int, percentile: int) -> float:
        """
        Computes the monthly line (our budget goal) given the household size
        and percentile.

        :param household_size: The number of people in the household.
        :param percentile: The percentile to use for the calculation.
        :return: The monthly line, which is the annual line divided by 12.
        """
        return self._flp_calculator.compute_annual_line(household_size, percentile) / 12
