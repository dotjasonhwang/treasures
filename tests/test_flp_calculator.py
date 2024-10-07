import unittest
from unittest.mock import MagicMock
from src.flp.flp_calculator import FLPCalculator
import pandas as pd

from flp.filing_status import FilingStatus


class BaseFLPCalculatorTest(unittest.TestCase):
    def setUp(self):
        self.dataset = MagicMock()
        self.dataset.income_by_percentile.return_value = {25: 30000, 50: 64021}
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
        self.dataset.fica_medicare_rate.return_value = 0.0145
        self.dataset.deductions.return_value = {
            FilingStatus.INDIVIDUAL: 13850,
            FilingStatus.JOINT: 27700,
        }

        self.calculator = FLPCalculator(self.dataset)


class TestCalculateScaledIncome(BaseFLPCalculatorTest):
    def test_webpage_example(self):
        # Using the example on the webpage as of 20241005
        self.assertEqual(self.calculator.calculate_scaled_income(4, 50), 85903)


class TestCalculateFederalTaxableIncome(BaseFLPCalculatorTest):
    def test_individual_under_standard_deduction(self):
        gross_income = 10000
        filing_status = FilingStatus.INDIVIDUAL
        self.assertEqual(
            self.calculator.calculate_federal_taxable_income(
                gross_income, filing_status
            ),
            0,
        )

    def test_individual_equal_standard_deduction(self):
        gross_income = 13850
        filing_status = FilingStatus.INDIVIDUAL
        self.assertEqual(
            self.calculator.calculate_federal_taxable_income(
                gross_income, filing_status
            ),
            0,
        )

    def test_individual_over_standard_deduction(self):
        gross_income = 20000
        filing_status = FilingStatus.INDIVIDUAL
        self.assertEqual(
            self.calculator.calculate_federal_taxable_income(
                gross_income, filing_status
            ),
            6150,
        )

    def test_joint(self):
        gross_income = 30000
        filing_status = FilingStatus.JOINT
        self.assertEqual(
            self.calculator.calculate_federal_taxable_income(
                gross_income, filing_status
            ),
            2300,
        )

    def test_negative_gross_income(self):
        gross_income = -1
        filing_status = FilingStatus.JOINT
        with self.assertRaises(ValueError):
            self.calculator.calculate_federal_taxable_income(
                gross_income, filing_status
            )


class TestCalculateFederalIncomeTax(BaseFLPCalculatorTest):
    def test_first_bracket(self):
        taxable_income = 10000
        filing_status = FilingStatus.INDIVIDUAL
        self.assertAlmostEqual(
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status),
            1000,
        )

    def test_multiple_brackets(self):
        taxable_income = 50000
        filing_status = FilingStatus.INDIVIDUAL
        self.assertAlmostEqual(
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status),
            6307.5,
        )

    def test_last_bracket(self):
        taxable_income = 200000
        filing_status = FilingStatus.INDIVIDUAL
        self.assertAlmostEqual(
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status),
            42832.0,
        )

    def test_joint(self):
        taxable_income = 50000
        filing_status = FilingStatus.JOINT
        self.assertAlmostEqual(
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status),
            5560.0,
        )

    def test_zero_income(self):
        taxable_income = 0
        filing_status = FilingStatus.INDIVIDUAL
        self.assertAlmostEqual(
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status),
            0,
        )

    def test_negative_income(self):
        taxable_income = -1000
        filing_status = FilingStatus.INDIVIDUAL
        with self.assertRaises(ValueError):
            self.calculator.calculate_federal_income_tax(taxable_income, filing_status)


class TestCalculateFICA(BaseFLPCalculatorTest):
    def test_zero_income(self):
        gross_income = 0
        self.assertAlmostEqual(
            self.calculator.calculate_fica_tax(gross_income),
            0,
        )

    def test_at_max_social_security_threshold(self):
        gross_income = 160200
        self.assertAlmostEqual(
            self.calculator.calculate_fica_tax(gross_income),
            12255.3,
        )

    def test_above_max_social_security_threshold(self):
        gross_income = 200000
        self.assertAlmostEqual(
            self.calculator.calculate_fica_tax(gross_income),
            12832.4,
        )


class TestCalculateStateTax(BaseFLPCalculatorTest):
    def test_zero_income(self):
        gross_income = 0
        self.assertAlmostEqual(
            self.calculator.calculate_state_tax(gross_income),
            0,
        )

    def test_income(self):
        gross_income = 100000
        self.assertAlmostEqual(
            self.calculator.calculate_state_tax(gross_income),
            3400,
        )


class TestComputeMonthlyLine(BaseFLPCalculatorTest):
    def test_compute_monthly_line_invalid_household_size(self):
        household_size = 0
        percentile = 50
        with self.assertRaises(ValueError):
            self.calculator.compute_monthly_line(household_size, percentile)

    def test_compute_monthly_line_invalid_percentile(self):
        household_size = 1
        with self.assertRaises(ValueError):
            self.calculator.compute_monthly_line(household_size, 100)

        with self.assertRaises(ValueError):
            self.calculator.compute_monthly_line(household_size, 0)

    def test_compute_monthly_line_individual(self):
        household_size = 1
        percentile = 50
        monthly_line = self.calculator.compute_monthly_line(household_size, percentile)
        self.assertAlmostEqual(monthly_line, 33853.186)

    def test_compute_monthly_line_joint(self):
        household_size = 2
        percentile = 50
        monthly_line = self.calculator.compute_monthly_line(household_size, percentile)
        self.assertAlmostEqual(monthly_line, 47112.2435)

    def test_compute_monthly_line_individual_2(self):
        household_size = 1
        percentile = 25
        monthly_line = self.calculator.compute_monthly_line(household_size, percentile)
        self.assertAlmostEqual(monthly_line, 16755.7755)

    def test_compute_monthly_line_joint_2(self):
        household_size = 2
        percentile = 25
        monthly_line = self.calculator.compute_monthly_line(household_size, percentile)
        self.assertAlmostEqual(monthly_line, 23480.1315)
