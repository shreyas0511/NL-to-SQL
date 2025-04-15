from langchain_core.tools import tool, StructuredTool
import pandas as pd
from db.init_db import result_df, result_query, db

@tool
def execute_query(sql_query: str) -> str:
    """ Execute the given 'sql_query' against our database """
    global result_df, result_query, db

    try:
        # execute the llm generated sql query against the database and store result in result dataframe
        with db._engine.connect() as conn:
            result_df = pd.read_sql(sql_query, conn)

        # store llm query
        result_query = sql_query

        # Now the summary text to be returned by the tool
        num_rows = len(result_df)

        # number of rows returned might be too many so only display the top 10 rows
        result_df = result_df.head(10)

        # message string to pass to the agent scratchpad in case of successful result
        msg = f"Successfully executed query, returned {num_rows} rows"
        return msg
    except Exception as e:
        # message string to pass to the agent scratchpad in case of error or failed result
        return f"Error executing query: {str(e)}"

@tool
def final_answer(answer: str, tools_used: list[str]) -> dict[str|list[str | None]]:
    """ Use this tool to provide a final answer to the user.
    The answer should be in natural language as this will be provided
    to the user directly. The tools_used must include a list of tool
    names that were used within the `scratchpad`. 
    An example response on success is: 
    'answer': Successfully executed the query, returned x number of rows,
    'tools_used': [execute_query]
    """
    return {"answer":answer, "tools_used":tools_used}

# Adding the tool decorator converts the tools into StructuredTool objects
tools: list[StructuredTool] = [execute_query, final_answer]

# Map tool names to tool function to execute later
tool_func_map = {tool.name : tool.func  for tool in tools}