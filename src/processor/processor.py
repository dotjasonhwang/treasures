import pandas as pd

class Processor:
    IGNORE = 'ignore'

    # def __init__(self, is_debit: bool) -> None:
        # self.card_name
        # self.is_debit = is_debit

    def parse(self, file_path: str) -> pd.DataFrame:
        raise NotImplementedError
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        TODO this can be a separate class, and also maybe instead of dataframe, should be standardized dictionary/class
        """
        raise NotImplementedError
    
    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df['category'] != Processor.IGNORE]

    def set_line_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        df['is_income'] = df['category'].isin(['income'])
        df['over_line_item'] = df['category'].isin(["giving", "tithe"])
        return df


def word_contains_substring(word: str, substrings: list[str]) -> bool:
    return any(substring in word for substring in substrings)


class BOAProcessor(Processor):
    # def __init__(self) -> None:
    #     super(True)

    def parse(self, file_path: str) -> pd.DataFrame:
        df = pd.read_csv(
            file_path,
            header=5,
            usecols=["Date", "Description", "Amount"],
            dtype=
                {
                    "Amount": float
                },
            parse_dates=['Date'],
            thousands=',',
            )
        
        return df


    def categorize(self, df: pd.DataFrame) -> pd.DataFrame:
        def categorize_row(row: pd.Series) -> str:
            lowercase_desc = row["Description"].lower()
            if word_contains_substring(lowercase_desc, ["mortgage"]):
                return "home"
            if word_contains_substring(lowercase_desc, ["hoa"]):
                return "hoa"
            elif word_contains_substring(lowercase_desc, ["job"]):
                return "income"
            elif word_contains_substring(lowercase_desc, ["church"]):
                return "giving"
            elif word_contains_substring(lowercase_desc, ["zelle"]):
                return "business"
            elif word_contains_substring(lowercase_desc, ["lightning elec"]):
                return "utilities"
            elif word_contains_substring(lowercase_desc, ["credit card payment"]):
                return Processor.IGNORE
            else:
                return "misc expenses"
        

        df["category"] = df.apply(categorize_row, axis=1)
        return df
        
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.rename(columns={
            "Date": "date",
            "Amount": "amount"
        })

        return df

            

class ChaseProcessor(Processor):
    # def __init__(self) -> None:
    #     super(False)
    
    def parse(self, file_path: str) -> pd.DataFrame:
        df = pd.read_csv(
            file_path,
            usecols=['Transaction Date', 'Description', 'Category', 'Type', 'Amount'],
            dtype=
                {
                    "Amount": float
                },
            parse_dates=['Transaction Date'],
        )
        
        return df

    def categorize(self, df: pd.DataFrame) -> pd.DataFrame:
        def categorize_row(row: pd.Series) -> str:
            lowercase_desc = row["Description"].lower()
            if word_contains_substring(lowercase_desc, ["automatic payment - thank"]):
                return "card payment"
            elif word_contains_substring(lowercase_desc, ["amazon prime"]):
                return "subscriptions"
            elif word_contains_substring(lowercase_desc, ["computer", "amazon", "travel"]):
                return "goods"
            elif word_contains_substring(lowercase_desc, ["heb", "costco"]):
                return "groceries"
            elif word_contains_substring(lowercase_desc, ["restaurant"]):
                return "dining"
            else:
                return None
        

        df["category"] = df.apply(categorize_row, axis=1)
        return df

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.rename(columns={
            "Transaction Date": "date",
            "Amount": "amount"
        })
        
        return df
