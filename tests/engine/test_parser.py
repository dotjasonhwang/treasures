import unittest
import pandas as pd

from engine.parser import BOADebitParser, ChaseCreditParser


class BaseParserTest(unittest.TestCase):
    def setUp(self):
        pass


class BOADebitParserTest(BaseParserTest):
    def setUp(self):
        self.parser = BOADebitParser()

    def test_rename_columns(self):
        df = pd.DataFrame({"Date": ["2023-01-01"]})
        df = self.parser._rename_columns(df)
        self.assertEqual(df.columns[0], "date")


class ChaseCreditParserTest(BaseParserTest):
    def setUp(self):
        self.parser = ChaseCreditParser()

    def test_rename_columns(self):
        df = pd.DataFrame({"Transaction Date": ["2023-01-01"]})
        df = self.parser._rename_columns(df)
        self.assertEqual(df.columns[0], "date")
