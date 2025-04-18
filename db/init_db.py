from langchain_community.utilities import SQLDatabase
import pandas as pd

# Global dataframe and query string to store executed query and results
result_df: pd.DataFrame = None
result_query: str = ""

# hardcoding for now, will accept from user later
# db = SQLDatabase.from_uri("sqlite:///Chinook_Sqlite.sqlite")

db_uri = ""
db = None

table_schema_info = ""
# print(table_schema_info)