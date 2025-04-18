import os
from dotenv import load_dotenv
from google import genai
from google.api_core import retry
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Langsmith for tracing LLM calls
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Talk2SQL"
os.environ["LANGCHAIN_API_KEY"] = "your_langsmith_key"

# Initialize gemini api key and load gemini model
load_dotenv(override=True)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
gemini_model = "gemini-2.0-flash"

# If using streaming
# llm = ChatGoogleGenerativeAI(
#     temperature=0.0,
#     model="gemini-2.0-flash",
#     streaming=True
# ).configurable_fields(
#     callbacks=ConfigurableField(
#         id="callbacks",
#         name="callbacks",
#         description="A list of callbacks to use for streaming"
#     )
# )

# setup a retry helper
is_retriable = lambda e: (isinstance(e, genai.errors.APIError) and e.code in {429, 503})
genai.models.Models.generate_content = retry.Retry(
    predicate=is_retriable)(genai.models.Models.generate_content)

print("Initializing Gemini LLM...")
# We are not using streaming, because it seems overkill for this task
llm = ChatGoogleGenerativeAI(temperature=0.0, model=gemini_model)

# Input variables in prompt template
# database_schema -> schema of the uploaded database
# input -> natural language query by the user
# chat_history -> chat history
# agent_scratchpad -> to store intermediate computation results
prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an expert SQL query generator assistant. "
        "Given the following database schema: "
        "{database_schema} "
        "and a user query in natural language, "
        "WRITE a valid SQL query (SQLite dialect) to answer the user's question."
        "Once you generate a valid SQL query, Use one of the tools provided to execute the query."
        "The output of the query execution will be provided back to you in the 'scratchpad' below. "
        "If you have a valid answer in the scratchpad, you MUST use the final_answer tool "
        "to provide the final answer back to the user. "
        "In case the generated SQL query does not return a valid answer, an error message will be "
        "provided back to you in the scratchpad. Use that error message to refine your query "
        "and rerun the refined query using one of the tools provided. "
    )),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])