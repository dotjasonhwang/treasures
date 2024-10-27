import pandas as pd
from pandas.testing import assert_series_equal, assert_frame_equal

import unittest
from unittest.mock import MagicMock

from engine.type import Type
from flp.flp_calculator import FLPCalculator
from src.engine.calculator import Calculator
from src.engine.processor import Processor


class BaseConfigLoaderTest(unittest.TestCase):
    def setUp(self):
        mock_flp_calculator = MagicMock(spec=FLPCalculator)
        mock_flp_calculator.compute_annual_line.return_value = 10000
        data = [
            [
                "2024-01-01",
                "Got some money",
                1000.0,
                "file1.csv",
                "bank1",
                Type.INCOME,
                "income_category1",
            ],
            [
                "2024-01-01",
                "Got paid again",
                100.0,
                "file2.csv",
                "bank1",
                Type.INCOME,
                "income_category2",
            ],
            [
                "2024-01-01",
                "UTILITIES payment",
                -200.0,
                "file3.csv",
                "bank1",
                Type.EXPENSE,
                "expense_category1",
            ],
            [
                "2024-01-01",
                "INTERNET",
                -100.0,
                "file4.csv",
                "bank2",
                Type.GIVING,
                "giving_category1",
            ],
            [
                "2024-01-01",
                "FOOD",
                -50.0,
                "file5.csv",
                "bank2",
                Type.NO_TYPE,
                Processor.NO_CATEGORY,
            ],
        ]
        columns = [
            "date",
            "description",
            "amount",
            "filename",
            "account_name",
            "type",
            "category",
        ]

        self._df = pd.DataFrame(data, columns=columns)
        self._calculator = Calculator(mock_flp_calculator, 2, 50, self._df)

    def test_income_total(self):
        self.assertEqual(self._calculator.income_total(), 1100)

    def test_income_by_category(self):
        expected_series = (
            self._df[self._df["type"] == Type.INCOME]
            .groupby(by="category")["amount"]
            .sum()
        )
        assert_series_equal(self._calculator.income_by_category(), expected_series)

    def test_expense_total(self):
        self.assertEqual(self._calculator.expense_total(), 200)

    def test_expense_by_category(self):
        expense_rows = self._df.loc[self._df["type"] == Type.EXPENSE].copy()
        expense_rows["amount"] *= -1
        expected_series = expense_rows.groupby(by="category")["amount"].sum()
        assert_series_equal(self._calculator.expense_by_category(), expected_series)

    def test_giving_total(self):
        self.assertEqual(self._calculator.giving_total(), 100)

    def test_giving_by_category(self):
        giving_rows = self._df.loc[self._df["type"] == Type.GIVING].copy()
        giving_rows["amount"] *= -1
        expected_series = giving_rows.groupby(by="category")["amount"].sum()
        assert_series_equal(self._calculator.giving_by_category(), expected_series)

    def test_in_minus_out(self):
        self.assertEqual(self._calculator.in_minus_out(), 800.0)

    def test_line(self):
        self.assertAlmostEqual(self._calculator.line(), 833.33, 2)

    def test_line_minus_expenses(self):
        self.assertAlmostEqual(self._calculator.line_minus_expenses(), 633.33, 2)

    def test_no_type_rows(self):
        expected_df = pd.DataFrame(
            columns=["filename", "date", "description", "amount"],
            data=[["file5.csv", "2024-01-01", "FOOD", -50.0]],
        )

        assert_frame_equal(
            self._calculator.no_type_rows().reset_index(drop=True),
            expected_df.reset_index(drop=True),
        )
