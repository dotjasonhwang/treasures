from flp.filing_status import FilingStatus
from flp.flp_dataset import Dataset


class FLPCalculator:
    def __init__(self, dataset: Dataset) -> None:
        self.dataset = dataset

    def compute_annual_line(self, household_size: int, percentile: int) -> float:
        if household_size <= 0:
            raise ValueError("Household size must be positive.")

        if percentile < 1 or percentile > 99:
            raise ValueError("Percentile must be between 1 and 99.")

        filing_status = (
            FilingStatus.INDIVIDUAL if household_size == 1 else FilingStatus.JOINT
        )

        scaled_gross_income = self.calculate_scaled_income(household_size, percentile)

        federal_income_tax = self.calculate_federal_income_tax(
            self.calculate_federal_taxable_income(scaled_gross_income, filing_status),
            filing_status,
        )

        fica_tax = self.calculate_fica_tax(scaled_gross_income)

        state_tax = self.calculate_state_tax(scaled_gross_income)
        return scaled_gross_income - federal_income_tax - fica_tax - state_tax

    def calculate_scaled_income(
        self,
        household_size: int,
        percentile: int,
    ) -> float:
        """
        Calculates the scaled income, which is the income adjusted to the household size
        using the poverty line as a reference of the curve.
        """
        unscaled_income_for_percentile = self.dataset.income_by_percentile()[percentile]

        scale = unscaled_income_for_percentile / (
            self.dataset.poverty_line_base()
            + self.dataset.poverty_line_per_person() * self.dataset.avg_household_size()
        )
        scaled_income = (
            self.dataset.poverty_line_base()
            + self.dataset.poverty_line_per_person() * household_size
        ) * scale
        return round(scaled_income)

    def calculate_federal_taxable_income(
        self, gross_income: float, filing_status: FilingStatus
    ) -> float:
        """
        Calculates the federal taxable income, which is the gross income minus the
        standard deduction.
        """
        if gross_income < 0:
            raise ValueError("Gross income must be non-negative.")

        return max(0, gross_income - self.dataset.deductions()[filing_status])

    def calculate_federal_income_tax(
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
        for lower, upper, rate in self.dataset.federal_tax_brackets()[
            filing_status
        ].itertuples(index=False):
            if taxable_income > lower:
                bracket_income = min(taxable_income, upper) - lower
                tax_owed += bracket_income * rate
            else:
                break
        return tax_owed

    def calculate_fica_tax(self, gross_income: float) -> float:
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
            min(gross_income, self.dataset.fica_soc_sec_max_income())
            * self.dataset.fica_soc_sec_rate()
        )

        medicare_tax = gross_income * self.dataset.fica_medicare_rate()

        # Additional Medicare tax, currently not applied to apply, uncomment the below lines and add it to the final sum
        # if gross_income > additional_medicare_threshold:
        #    additional_medicare_tax = (gross_income - additional_medicare_threshold) * additional_medicare_rate

        return social_security_tax + medicare_tax

    def calculate_state_tax(self, gross_income: float) -> float:
        """
        Calculates the state tax based on the given gross income.

        The state tax is calculated by multiplying the gross income by the state tax rate.

        :param gross_income: The total gross income.
        :return: The total state tax owed.
        """
        if gross_income < 0:
            raise ValueError("Gross income must be non-negative.")

        return self.dataset.state_income_tax_rate() * gross_income
