import unittest
from unittest.mock import MagicMock
from src.flp.flp_calculator import FLPCalculator
import pandas as pd

from flp.filing_status import FilingStatus


class TestFLPCalculator(unittest.TestCase):
    def setUp(self):
        self.dataset = MagicMock()
        self.dataset.income_by_percentile.return_value = {10: 20000, 50: 64021}
        self.dataset.poverty_line_base.return_value = 7820
        self.dataset.poverty_line_per_person.return_value = 4320
        self.dataset.avg_household_size.return_value = 2.52

        self.dataset.federal_tax_brackets.return_value = {
            FilingStatus.INDIVIDUAL: pd.DataFrame(
                [
                    {"lower": 0, "upper": 11000, "rate": 0.10},
                    {"lower": 11000, "upper": 44725, "rate": 0.12},
                    {"lower": 44725, "upper": 95375, "rate": 0.22},
                    {"lower": 95375, "upper": 182100, "rate": 0.24},
                    {"lower": 182100, "upper": 231250, "rate": 0.32},
                    {"lower": 231250, "upper": 578125, "rate": 0.35},
                    {"lower": 578125, "upper": None, "rate": 0.37},
                ]
            ),
            FilingStatus.JOINT: pd.DataFrame(
                [
                    {"lower": 0, "upper": 22000, "rate": 0.10},
                    {"lower": 22000, "upper": 89450, "rate": 0.12},
                    {"lower": 89450, "upper": 190750, "rate": 0.22},
                    {"lower": 190750, "upper": 364200, "rate": 0.24},
                    {"lower": 364200, "upper": 462500, "rate": 0.32},
                    {"lower": 462500, "upper": 693750, "rate": 0.35},
                    {"lower": 693750, "upper": None, "rate": 0.37},
                ]
            ),
        }
        self.dataset.state_income_tax_rate.return_value = 0.034
        self.dataset.fica_soc_sec_rate.return_value = 0.062
        self.dataset.fica_soc_sec_max_income.return_value = 160200
        self.dataset.medicare_rate.return_value = 0.0145
        self.dataset.deductions.return_value = {
            FilingStatus.INDIVIDUAL: 13850,
            FilingStatus.JOINT: 27700,
        }

        self.calculator = FLPCalculator(self.dataset)

    def test_calculate_scaled_income(self):
        # Using the example on the webpage as of 20241005
        self.assertEqual(self.calculator.calculate_scaled_income(4, 50), 85903)

    def test_calculate_federal_taxable_income(self):
        # Test case 1: Gross income is less than the standard deduction
        gross_income = 10000
        filing_status = FilingStatus.INDIVIDUAL
        self.assertEqual(
            self.calculator.calculate_federal_taxable_income(
                gross_income, filing_status
            ),
            0,
        )

        # Test case 2: Gross income is equal to the standard deduction
        gross_income = 13850
        filing_status = FilingStatus.INDIVIDUAL
        self.assertEqual(
            self.calculator.calculate_federal_taxable_income(
                gross_income, filing_status
            ),
            0,
        )

        # Test case 3: Gross income is greater than the standard deduction
        gross_income = 20000
        filing_status = FilingStatus.INDIVIDUAL
        self.assertEqual(
            self.calculator.calculate_federal_taxable_income(
                gross_income, filing_status
            ),
            6150,
        )

        # Test case 4: Joint filing status
        gross_income = 30000
        filing_status = FilingStatus.JOINT
        self.assertEqual(
            self.calculator.calculate_federal_taxable_income(
                gross_income, filing_status
            ),
            2300,
        )

        # Test case 5: Negative gross_income
        gross_income = -1
        filing_status = FilingStatus.JOINT
        with self.assertRaises(ValueError):
            self.calculator.calculate_federal_taxable_income(
                gross_income, filing_status
            )

    def test_calculate_federal_income_tax(self):
        # Test case 1: Taxable income is in the first tax bracket
        taxable_income = 10000
        filing_status = FilingStatus.INDIVIDUAL
        self.assertAlmostEqual(
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status),
            1000,
        )

        # Test case 2: Taxable income is in multiple tax brackets
        taxable_income = 50000
        filing_status = FilingStatus.INDIVIDUAL
        self.assertAlmostEqual(
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status),
            6307.5,
        )

        # Test case 3: Taxable income is above all tax brackets
        taxable_income = 200000
        filing_status = FilingStatus.INDIVIDUAL
        self.assertAlmostEqual(
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status),
            42832.0,
        )

        # Test case 4: Joint filing status
        taxable_income = 50000
        filing_status = FilingStatus.JOINT
        self.assertAlmostEqual(
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status),
            5560.0,
        )

        # Test case 5: Zero taxable income
        taxable_income = 0
        filing_status = FilingStatus.INDIVIDUAL
        self.assertAlmostEqual(
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status),
            0,
        )

        # Test case 6: Negative taxable income (should raise an error)
        taxable_income = -1000
        filing_status = FilingStatus.INDIVIDUAL
        with self.assertRaises(ValueError):
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status)


if __name__ == "__main__":
    unittest.main()
