"""
Conversion of JavaScript to Python & minor adjustments:

MIT License

Copyright (c) 2024 Jason Hwang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

Original Finish Line calculation code:

MIT License

Copyright (c) 2024 Finish Line Ministries and Kealan Hobelmann

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from flp.filing_status import FilingStatus
from flp.flp_dataset import Dataset


class FLPCalculator:
    def __init__(self, dataset: Dataset) -> None:
        self._dataset = dataset

    def compute_annual_line(self, household_size: int, percentile: int) -> float:
        if household_size <= 0:
            raise ValueError("Household size must be positive.")

        if percentile < 1 or percentile > 99:
            raise ValueError("Percentile must be between 1 and 99.")

        filing_status = (
            FilingStatus.INDIVIDUAL if household_size == 1 else FilingStatus.JOINT
        )

        scaled_gross_income = self._calculate_scaled_income(household_size, percentile)

        federal_income_tax = self._calculate_federal_income_tax(
            self._calculate_federal_taxable_income(scaled_gross_income, filing_status),
            filing_status,
        )

        fica_tax = self._calculate_fica_tax(scaled_gross_income)

        state_tax = self._calculate_state_tax(scaled_gross_income)
        return scaled_gross_income - federal_income_tax - fica_tax - state_tax

    def _calculate_scaled_income(
        self,
        household_size: int,
        percentile: int,
    ) -> float:
        """
        Calculates the scaled income, which is the income adjusted to the household size
        using the poverty line as a reference of the curve.
        """
        unscaled_income_for_percentile = self._dataset.income_by_percentile()[
            percentile
        ]

        scale = unscaled_income_for_percentile / (
            self._dataset.poverty_line_base()
            + self._dataset.poverty_line_per_person()
            * self._dataset.avg_household_size()
        )
        scaled_income = (
            self._dataset.poverty_line_base()
            + self._dataset.poverty_line_per_person() * household_size
        ) * scale
        return round(scaled_income)

    def _calculate_federal_taxable_income(
        self, gross_income: float, filing_status: FilingStatus
    ) -> float:
        """
        Calculates the federal taxable income, which is the gross income minus the
        standard deduction.
        """
        if gross_income < 0:
            raise ValueError("Gross income must be non-negative.")

        return max(0, gross_income - self._dataset.deductions()[filing_status])

    def _calculate_federal_income_tax(
        self, taxable_income: float, filing_status: FilingStatus
    ) -> float:
        """
        Calculates the federal income tax based on the given taxable income and filing status.

        Tax owed is calculated by iterating through the federal tax brackets and adding the
        tax owed for each bracket. The taxable income is "clipped" to the upper limit of each
        bracket, so the tax rate is only applied to the income within that bracket.

        :param taxable_income: The total taxable income.
        :param filing_status: The filing status of the individual.
        :return: The federal income tax owed.
        """
        if taxable_income < 0:
            raise ValueError("Taxable income must be non-negative.")

        tax_owed = 0.0
        for lower, upper, rate in self._dataset.federal_tax_brackets()[
            filing_status
        ].itertuples(index=False):
            if taxable_income > lower:
                bracket_income = min(taxable_income, upper) - lower
                tax_owed += bracket_income * rate
            else:
                break
        return tax_owed

    def _calculate_fica_tax(self, gross_income: float) -> float:
        """
        Calculates the FICA tax (social security and medicare) based on the given gross income.

        The social security tax is calculated by multiplying the minimum of the gross income
        and the social security maximum income by the social security rate. The medicare tax is
        calculated by multiplying the gross income by the medicare rate.

        The additional Medicare tax is currently not applied.

        :param gross_income: The total gross income.
        :return: The total FICA tax owed.
        """
        if gross_income < 0:
            raise ValueError("Gross income must be non-negative.")

        social_security_tax = (
            min(gross_income, self._dataset.fica_soc_sec_max_income())
            * self._dataset.fica_soc_sec_rate()
        )

        medicare_tax = gross_income * self._dataset.fica_medicare_rate()

        # Additional Medicare tax, currently not applied to apply, uncomment the below lines and add it to the final sum
        # if gross_income > additional_medicare_threshold:
        #    additional_medicare_tax = (gross_income - additional_medicare_threshold) * additional_medicare_rate

        return social_security_tax + medicare_tax

    def _calculate_state_tax(self, gross_income: float) -> float:
        """
        Calculates the state tax based on the given gross income.

        The state tax is calculated by multiplying the gross income by the state tax rate.

        :param gross_income: The total gross income.
        :return: The total state tax owed.
        """
        if gross_income < 0:
            raise ValueError("Gross income must be non-negative.")

        return self._dataset.state_income_tax_rate() * gross_income
