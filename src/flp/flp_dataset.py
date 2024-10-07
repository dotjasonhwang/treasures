import pandas as pd
import json
from flp.filing_status import FilingStatus


class Dataset:
    def __init__(self, config_file="data/flp/numbers.json") -> None:
        self.config_file = config_file

    def income_by_percentile(self) -> dict[int, float]:
        """
        Returns a dictionary with integer keys from 1 to 99 and float values.
        The keys are percentiles and the values are the income at that percentile.
        """
        return (
            pd.read_csv("data/flp/income_data.csv")
            .set_index("percentile")
            .to_dict()["income"]
        )

    def poverty_line_base(self) -> float:
        return self._load_config()["poverty"]["povLineBase"]

    def poverty_line_per_person(self) -> float:
        """
        Returns the amount the poverty line increases per person.

        :return: The amount the poverty line increases per person.
        """
        return self._load_config()["poverty"]["povLinePerPerson"]

    def avg_household_size(self) -> float:
        return self._load_config()["avgHouseholdSize"]

    def federal_tax_brackets(self) -> dict[FilingStatus, pd.DataFrame]:
        """
        Returns a dictionary with FilingStatus keys and pandas DataFrames as values.
        The DataFrames contain the federal tax brackets.
        """
        config = self._load_config()
        return {
            FilingStatus.INDIVIDUAL: pd.read_csv(
                config["federal_tax_brackets"]["INDIVIDUAL"]
            ),
            FilingStatus.JOINT: pd.read_csv(config["federal_tax_brackets"]["JOINT"]),
        }

    def state_income_tax_rate(self) -> float:
        """Returns the state income tax rate as a float."""
        return self._load_config()["state_income_tax_rate"]

    def fica_soc_sec_rate(self) -> float:
        return self._load_config()["fica"]["socSecRate"]

    def fica_soc_sec_max_income(self) -> float:
        return self._load_config()["fica"]["socSecMaxIncome"]

    def fica_medicare_rate(self) -> float:
        return self._load_config()["fica"]["medicareRate"]

    def deductions(self) -> dict[FilingStatus, float]:
        """
        Returns a dictionary with FilingStatus keys and float values.
        The values are the standard deductions for the given filing status.
        """
        config = self._load_config()
        return {
            FilingStatus.INDIVIDUAL: config["deductions"]["INDIVIDUAL"],
            FilingStatus.JOINT: config["deductions"]["JOINT"],
        }

    def _load_config(self) -> dict:
        """
        Loads the config file from JSON and returns it as a dictionary.

        :return: A dictionary with configuration values.
        """
        with open(self.config_file, "r") as f:
            return json.load(f)
