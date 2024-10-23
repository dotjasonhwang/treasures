import unittest
import pandas as pd
from engine.processor import Processor


class BaseProcessorTest(unittest.TestCase):
    def setUp(self):
        self.processor1 = Processor(
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
        )
        self.processor2 = Processor(
            name="Bank2 Credit",
            file_prefix="bank2_credit",
            parser="mock_parser2",
            skip_transactions=["miscellaneous"],
            type_category_by_identifier={
                "store_1": ("expense", "groceries"),
                "store_2": ("expense", "groceries"),
                "payment_company_1": ("expense", "misc expenses"),
            },
        )


class TestEQ(BaseProcessorTest):
    def test_eq(self):
        processor1Equivalent = Processor(
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
        )
        self.assertEqual(self.processor1, processor1Equivalent)

    def test_neq(self):
        self.assertNotEqual(self.processor1, self.processor2)


class TestRemoveSkippedTransactions(BaseProcessorTest):
    def test_found(self):
        df = pd.DataFrame(
            {
                "description": [
                    "manual pay 1",
                    "random pay 2",
                    "auto pay 3",
                    "Auto Pay 4",
                ]
            }
        )
        result = self.processor1.remove_skipped_transactions(df)
        self.assertEqual(len(result), 2)
        self.assertEqual(
            result["description"].tolist(), ["manual pay 1", "random pay 2"]
        )

    def test_not_found(self):
        df = pd.DataFrame({"description": ["manual pay 1", "random pay 2"]})
        result = self.processor1.remove_skipped_transactions(df)
        self.assertEqual(len(result), 2)
        self.assertEqual(
            result["description"].tolist(), ["manual pay 1", "random pay 2"]
        )


class TestCategorize(BaseProcessorTest):
    def test_no_matching_identifiers(self):
        df = pd.DataFrame({"description": ["No matching identifier"]})
        result = self.processor1.categorize(df)
        self.assertEqual(result["type"].tolist(), [Processor.NO_TYPE])
        self.assertEqual(result["category"].tolist(), [Processor.NO_CATEGORY])

    def test_one_matching_identifier(self):
        df = pd.DataFrame({"description": ["Contains payment_company_1"]})
        result = self.processor1.categorize(df)
        self.assertEqual(result["type"].tolist(), ["income"])
        self.assertEqual(result["category"].tolist(), ["income source 1"])

    def test_multiple_matching_identifiers(self):
        df = pd.DataFrame(
            {"description": ["Contains payment_company_1 and payment_company_2"]}
        )
        with self.assertRaises(ValueError):
            self.processor1.categorize(df)

    def test_empty_dataframe(self):
        df = pd.DataFrame({"description": []})
        result = self.processor1.categorize(df)
        self.assertEqual(len(result), 0)


class TestCategorizeRow(BaseProcessorTest):

    def test_no_matching_identifiers(self):
        row = pd.Series({"description": "No matching identifier"})
        result = self.processor1._categorize_row(row)
        self.assertEqual(
            result, {"type": Processor.NO_TYPE, "category": Processor.NO_CATEGORY}
        )

    def test_one_matching_identifier(self):
        row = pd.Series({"description": "1234 payment_company_1"})
        result = self.processor1._categorize_row(row)
        self.assertEqual(result, {"type": "income", "category": "income source 1"})

    def test_multiple_matching_identifiers(self):
        row = pd.Series(
            {"description": "Contains payment_company_1 and payment_company_2"}
        )
        with self.assertRaises(ValueError):
            self.processor1._categorize_row(row)


class TestFindMatchingIdentifiers(BaseProcessorTest):
    def test_one_match(self):
        self.assertEqual(
            ["ab"],
            Processor._find_matching_identifiers("abcd", ["ab", "abcde"]),
        )

    def test_no_match(self):
        self.assertEqual(
            [],
            Processor._find_matching_identifiers("abcd", ["dcba", "e"]),
        )


class TestWordContainsSubstring(BaseProcessorTest):
    def test_contains(self):
        self.assertTrue(Processor._word_contains_any_substring("abc", ["ab"]))

    def test_not_contains(self):
        self.assertFalse(Processor._word_contains_any_substring("ab", ["abc"]))
