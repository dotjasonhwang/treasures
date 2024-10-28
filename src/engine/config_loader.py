from engine.parser import Parser
from engine.processor import Processor
from engine.type import Type
import json
import logging
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class ConfigKeys:
    FILE_NICKNAMES = "file_nicknames"
    PROCESSORS = "processors"
    NAME = "name"
    FILE_PREFIX = "file_prefix"
    FILE_FORMAT = "file_format"
    SKIP_TRANSACTIONS = "skip_transactions"
    CATEGORIES = "categories"


class ConfigLoader:
    def __init__(self, config_filename: str, parser_by_format: dict[str, type[Parser]]):
        self._parser_by_format = parser_by_format
        with open(config_filename, "r") as f:
            self._config_dict = json.load(f)

    def load_nickname_by_filename(self) -> dict[str, str]:
        """
        Returns a dictionary of file names to nicknames.

        :return: A dictionary of file names to nicknames.
        """
        return self._config_dict[ConfigKeys.FILE_NICKNAMES]

    def load_processors(self) -> list[Processor]:
        """
        Loads the config from its JSON file and returns a list of Processor objects.
        All identifiers are converted to lowercase.

        There are 3 sanity checks performed:
        1. Processor names must be unique.
        2. For each processor, each identifier is found in only one category
        3. Each processor_config must have a valid file format reader

        :param config_filename: The path to the JSON file containing the configuration.
        :return: A list of Processor objects.
        """
        processor_configs = self._config_dict[ConfigKeys.PROCESSORS]
        self._error_if_duplicate_names(processor_configs)

        processors = []
        for processor_config in processor_configs:
            processor_name = processor_config[ConfigKeys.NAME]
            processors.append(
                Processor(
                    name=processor_name,
                    file_prefix=processor_config[ConfigKeys.FILE_PREFIX],
                    parser=self._extract_parser(
                        processor_config[ConfigKeys.FILE_FORMAT], processor_name
                    ),
                    skip_transactions=[
                        identifier.lower()
                        for identifier in processor_config[ConfigKeys.SKIP_TRANSACTIONS]
                    ],
                    type_category_by_identifier=self._extract_inverted_categories(
                        processor_config[ConfigKeys.CATEGORIES], processor_name
                    ),
                )
            )

        return processors

    def _extract_parser(self, file_format: str, processor_name: str) -> type[Processor]:
        """
        Returns the parser for the file format.
        I wish Python had a more elegant computeIfAbsent or something similar.

        Raise an error if the file format is unrecognized.
        """
        if file_format not in self._parser_by_format:
            raise ValueError(
                f"Processor: {processor_name} - Unrecognized file format {file_format}"
            )
        return self._parser_by_format[file_format]

    def _extract_inverted_categories(
        self,
        identifiers_by_categories_by_typestr: dict[str, dict[str, list]],
        processor_name: str,
    ) -> dict[str, tuple[Type, str]]:
        """
        Inverts the identifiers_by_categories_by_typestr dictionary from the configuration file
        into a dictionary mapping each identifier to a tuple of (type, category).

        Raises a ValueError if any identifier is found in multiple categories.

        :param identifiers_by_categories_by_typestr: A dictionary mapping each type to a dictionary
            mapping each category to a list of identifiers.
        :param processor_name: The name of the processor in the configuration file.
        :return: A dictionary mapping each identifier to a tuple of (type, category).
        """
        matching_typestr_category_list_by_identifier = self._invert_dict(
            identifiers_by_categories_by_typestr
        )
        # turn the keys of matching_typestr_category_list_by_identifier into lowercase
        matching_typestr_category_list_by_identifier = {
            k.lower(): v
            for k, v in matching_typestr_category_list_by_identifier.items()
        }
        multiple_type_category_by_identifier = {
            k: v
            for k, v in matching_typestr_category_list_by_identifier.items()
            if len(v) > 1
        }
        if multiple_type_category_by_identifier:
            for identifier, keys in multiple_type_category_by_identifier.items():
                logger.error(
                    f"{identifier} is found in the following (type, category) pairs: {keys}"
                )
            raise ValueError(
                f"Processor: {processor_name} - Each identifier must appear in only one category. See error logs."
            )

        return {
            identifier: (Type(single_keys[0][0]), single_keys[0][1])
            for identifier, single_keys in matching_typestr_category_list_by_identifier.items()
        }

    def _invert_dict(
        self, dict_of_dict_of_lists: dict[str, dict[str, list]]
    ) -> dict[str, list[tuple[str, str]]]:
        """
        Inverts a dictionary of dictionaries of lists into a dictionary of lists of (outer_key, inner_key).

        For example:
            dict_of_dict_of_lists = {
                "a": {
                    "b": ["1", "2"],
                    "c": ["3"]
                },
                "d": {
                    "e": ["4"]
                }
            }

            result = {
                "1": [("a", "b")],
                "2": [("a", "b")],
                "3": [("a", "c")],
                "4": [("d", "e")]
            }

        :param dict_of_dict_of_lists: The dictionary of dictionaries of lists to invert.

        :return: The inverted dictionary.
        """
        result = defaultdict(list)
        for outer_key, inner_dict in dict_of_dict_of_lists.items():
            for inner_key, values in inner_dict.items():
                for value in values:
                    result[value].append((outer_key, inner_key))

        return dict(result)

    def _error_if_duplicate_names(self, processor_configs: list) -> None:
        """
        Checks that all processor names are unique. If any duplicates are found, raises a ValueError.
        """
        duplicate_names = self._find_duplicates(
            [x[ConfigKeys.NAME] for x in processor_configs]
        )
        if duplicate_names:
            raise ValueError(
                f"Processor names must be unique. Duplicates: {duplicate_names}"
            )

    def _find_duplicates(self, list_of_items: list[str]) -> list[str]:
        """
        Finds all items in the list that appear more than once.

        Args:
            list_of_items (list[str]): The list of items to check for duplicates.

        Returns:
            list[str]: A list of all items that appear more than once in the input list.
        """
        count = Counter(list_of_items)
        return [name for name, count in count.items() if count > 1]
