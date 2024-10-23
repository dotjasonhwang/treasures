import unittest
import pandas as pd

from engine.parser import BOAParser, ChaseParser


class BaseParserTest(unittest.TestCase):
    def setUp(self):
        pass


class BOAParserTest(BaseParserTest):
    def setUp(self):
        self.parser = BOAParser("test", True)

    def test_rename_columns(self):
        df = pd.DataFrame({"Date": ["2023-01-01"]})
        df = self.parser._rename_columns(df)
        self.assertEqual(df.columns[0], "date")


class ChaseParserTest(BaseParserTest):
    def setUp(self):
        self.parser = ChaseParser("test", True)

    def test_rename_columns(self):
        df = pd.DataFrame({"Transaction Date": ["2023-01-01"]})
        df = self.parser._rename_columns(df)
        self.assertEqual(df.columns[0], "date")
