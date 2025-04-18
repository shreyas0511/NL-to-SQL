from langchain_core.tools import tool, StructuredTool
import pandas as pd
import db.init_db as db_state

@tool
def execute_query(sql_query: str) -> str:
    """ Execute the given 'sql_query' against our database """
    try:
        # execute the llm generated sql query against the database and store result in result dataframe
        with db_state.db._engine.connect() as conn:
            db_state.result_df = pd.read_sql(sql_query, conn)

        # store llm generated query
        db_state.result_query = sql_query

        # Now the summary text to be returned by the tool
        num_rows = len(db_state.result_df)

        # number of rows returned might be too many so only display the top 10 rows
        db_state.result_df = db_state.result_df.head(10)

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
    The answer MUST be a summary of the result and not the result itself.
    provide answer similar to the example responses provided below:
    An example response on success is: 
    'answer': Successfully executed the query, returned x number of rows,
    'tools_used': [execute_query]
    An example response on failure is:
    'answer': Error, could not execute the query
    'tools_used':[execute_query]
    or
    'answer': Error, invalid table column, please recheck query
    'tools_used':[execute_query]
    """
    return {"answer":answer, "tools_used":tools_used}

# Adding the tool decorator converts the tools into StructuredTool objects
tools: list[StructuredTool] = [execute_query, final_answer]

# Map tool names to tool function to execute later
tool_func_map = {tool.name : tool.func  for tool in tools}