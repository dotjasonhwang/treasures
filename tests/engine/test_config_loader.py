import pathlib
import unittest
from engine.config_loader import ConfigLoader
from engine.processor import Processor


class BaseConfigLoaderTest(unittest.TestCase):
    def setUp(self):
        mock_parser_by_format = {"bank1": "mock_parser1", "bank2": "mock_parser2"}
        test_config_file = str(
            pathlib.Path(__file__).parent.parent / "data/valid_config.json"
        )
        self.config_loader = ConfigLoader(test_config_file, mock_parser_by_format)


class TestLoadNicknames(BaseConfigLoaderTest):
    def test_expected(self):
        self.assertEqual(
            {"bank1_debit1234": "Travel Card", "bank2_credit1234": "Personal Card"},
            self.config_loader.load_nickname_by_filename(),
        )


class TestLoadProcessors(BaseConfigLoaderTest):
    def test_expected(self):
        self.assertEqual(
            [
                Processor(
                    name="Bank1 Debit",
                    file_prefix="bank1_debit",
                    parser="mock_parser1",
                    skip_transactions=["auto pay"],
                    type_category_by_identifier={
                        "payment_company_1": ("income", "income source 1"),
                        "payment_company_2": ("income", "income source 2"),
                        "volunteer 1": ("giving", "non profit 1"),
                        "payment_company_1_expense": ("expense", "misc expenses"),
                    },
                ),
                Processor(
                    name="Bank2 Credit",
                    file_prefix="bank2_credit",
                    parser="mock_parser2",
                    skip_transactions=["miscellaneous"],
                    type_category_by_identifier={
                        "store_1": ("expense", "groceries"),
                        "store_2": ("expense", "groceries"),
                        "payment_company_1": ("expense", "misc expenses"),
                    },
                ),
            ],
            self.config_loader.load_processors(),
        )

    def test_invalid_config(self):
        test_config_file = str(
            pathlib.Path(__file__).parent.parent
            / "data/duplicate_processor_names_config.json"
        )
        config_loader = ConfigLoader(test_config_file, {})
        with self.assertRaises(ValueError):
            config_loader.load_processors()


class TestExtractParser(BaseConfigLoaderTest):
    def test_expected(self):
        self.assertEqual(
            "mock_parser1",
            self.config_loader._extract_parser("bank1", "mock_name"),
        )

    def test_invalid_processor(self):
        with self.assertRaises(ValueError):
            self.config_loader._extract_parser("unknown_bank", "mock_name")


class TestExtractInvertedCategories(BaseConfigLoaderTest):
    def test_expected(self):
        categories1 = {
            "income": {
                "income source 1": ["payment_company_1"],
                "income source 2": ["payment_company_2"],
            },
            "giving": {"non profit 1": ["volunteer 1"]},
            "expense": {"misc expenses": ["payment_company_1_expense"]},
        }

        expected_result = {
            "payment_company_1": ("income", "income source 1"),
            "payment_company_2": ("income", "income source 2"),
            "volunteer 1": ("giving", "non profit 1"),
            "payment_company_1_expense": ("expense", "misc expenses"),
        }

        self.assertEqual(
            expected_result,
            self.config_loader._extract_inverted_categories(categories1, "mock_name"),
        )

    def test_expected_convert_lowercase(self):
        categories1 = {
            "income": {
                "income source 1": ["PAYment_company_1"],
                "income source 2": ["payMENT_company_2"],
            },
            "giving": {"non profit 1": ["VOLUNTEER 1"]},
            "expense": {"misc expenses": ["payment_company_1_expense"]},
        }

        expected_result = {
            "payment_company_1": ("income", "income source 1"),
            "payment_company_2": ("income", "income source 2"),
            "volunteer 1": ("giving", "non profit 1"),
            "payment_company_1_expense": ("expense", "misc expenses"),
        }

        self.assertEqual(
            expected_result,
            self.config_loader._extract_inverted_categories(categories1, "mock_name"),
        )

    def test_no_categories(self):
        self.assertEqual(
            {}, self.config_loader._extract_inverted_categories({}, "mock_name")
        )

    def test_invalid_processor(self):
        invalid_categories = {
            "income": {},
            "giving": {},
            "expense": {
                "utilities": ["store_1", "electricity"],
                "groceries": ["store_1", "store_2"],
            },
        }
        with self.assertRaises(ValueError):
            self.config_loader._extract_inverted_categories(
                invalid_categories, "mock_name"
            )


class TestInvertDict(BaseConfigLoaderTest):
    def test_expected(self):
        dict_to_invert = {
            "a": {"b": ["1", "2"], "c": ["3"]},
            "d": {"e": ["4"]},
        }

        expected_result = {
            "1": [("a", "b")],
            "2": [("a", "b")],
            "3": [("a", "c")],
            "4": [("d", "e")],
        }

        self.assertEqual(
            expected_result, self.config_loader._invert_dict(dict_to_invert)
        )

    def test_empty_dict(self):
        dict_to_invert = {}
        self.assertEqual({}, self.config_loader._invert_dict(dict_to_invert))

    def test_duplicate_inner_items(self):
        dict_to_invert = {
            "a": {"b": ["1", "2"], "c": ["1"]},
            "d": {"e": ["1"]},
        }

        expected_result = {
            "1": [("a", "b"), ("a", "c"), ("d", "e")],
            "2": [("a", "b")],
        }

        self.assertEqual(
            expected_result, self.config_loader._invert_dict(dict_to_invert)
        )


class TestErrorIfDuplicateNames(BaseConfigLoaderTest):
    def test_no_duplicates(self):
        processor_configs = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        self.config_loader._error_if_duplicate_names(processor_configs)

    def test_with_duplicates(self):
        processor_configs = [{"name": "a"}, {"name": "b"}, {"name": "b"}]
        with self.assertRaises(ValueError):
            self.config_loader._error_if_duplicate_names(processor_configs)

    def test_empty_list(self):
        processor_configs = []
        self.config_loader._error_if_duplicate_names(processor_configs)


class TestFindDuplicates(BaseConfigLoaderTest):

    def test_no_duplicates(self):
        list_of_items = ["a", "b", "c"]
        self.assertEqual([], self.config_loader._find_duplicates(list_of_items))

    def test_with_duplicates(self):
        list_of_items = ["a", "b", "b", "c", "c", "c"]
        self.assertEqual(["b", "c"], self.config_loader._find_duplicates(list_of_items))

    def test_empty_list(self):
        list_of_items = []
        self.assertEqual([], self.config_loader._find_duplicates(list_of_items))
