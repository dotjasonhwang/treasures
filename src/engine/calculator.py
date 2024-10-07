from flp.flp_calculator import FLPCalculator
from flp.flp_dataset import Dataset
import pandas as pd


class Calculator:
    """
    Performs the calculation on the given dataframe.
    All relevant values should be made public by making them attributes
    """

    def __init__(
        self, household_size: int, percentile: int, combined_df: pd.DataFrame
    ) -> None:
        self.line = self.compute_monthly_line(household_size, percentile)

        # TODO: Group by category and also purpose/bucket
        self.breakdown = combined_df.groupby(by="category")["amount"].sum()

        # Income
        self.income_total = combined_df[combined_df["is_income"]]["amount"].sum()
        # Non income
        out = combined_df[~combined_df["is_income"]]
        self.out_total = out["amount"].sum()

        # Cash leftover
        self.in_minus_out = self.income_total - self.out_total

        # Line tracker values
        self.expenses_total = out[~out["over_line_item"]]["amount"].sum()
        self.line_minus_expenses = self.line - self.expenses_total

        # Gold!
        self.treasures_total = out[out["over_line_item"]]["amount"].sum()

    def compute_monthly_line(self, household_size: int, percentile: int) -> float:
        flp_calculator = FLPCalculator(Dataset())
        return flp_calculator.compute_annual_line(household_size, percentile) / 12
