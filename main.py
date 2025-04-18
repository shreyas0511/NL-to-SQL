from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
from langchain_community.utilities import SQLDatabase
from handlers.queue_callback_handler import QueueCallbackHandler
from agent.agent_executor import CustomAgentExecutor
import db.init_db as db_state
from pydantic import BaseModel
from memory.message_history import JSONMessageHistory

# Initialize FastAPI app
app = FastAPI(title="NL-to-SQL Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database file upload directory if does not already exist
UPLOAD_DIR = "data/uploaded_dbs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize message history
message_history = JSONMessageHistory('data')

# Initialize the agent executor
agent_executor = CustomAgentExecutor(message_history)

# Health check
@app.get("/")
def health():
    return {"status": "running"}

# Upload DB endpoint
@app.post("/upload_db")
def upload_db(file: UploadFile = File(...)):

    """Save uploaded SQLite DB and cache schema."""
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Build connection URI and extract schema
    db_uri = f"sqlite:///{file_path}"
    db_state.db_uri = db_uri

    db = SQLDatabase.from_uri(db_uri)
    db_state.db = db

    db_state.table_schema_info = db.get_table_info()

    return {
        "message": f"Database {file.filename} uploaded successfully",
        "db_name": file.filename,
    }

# Pydantic model for query endpoint
class QueryRequest(BaseModel):
    uuid: str
    prompt: str

# Natural language query endpoint
@app.post("/query")
def run_query(req: QueryRequest):
    """Run natural language query on uploaded DB."""
    global agent_executor

    # Fetch db file on each request because request can be with different dbs
    # different dbs might be uploaded in different chat sessions
    chat_id = req.uuid
    file_name = chat_id + ".json"
    db_path = f"data/db/{req.uuid}.db"

    db_uri = f"sqlite:///{db_path}"
    db = SQLDatabase.from_uri(db_uri)

    db_schema = db.get_table_info()

    # Retrieve schema + db_uri
    if not db_schema:
        return {"error": "Database schema not found. Please upload the DB first."}

    # Optional streaming queue if using streaming
    # queue = asyncio.Queue()
    # streamer = QueueCallbackHandler(queue)

    # Run the agent (streaming)
    # output = await agent_executor.invoke(
    #     database_schema=table_schema,
    #     input=req.query,
    #     streamer=streamer
    # )

    # without streaming
    output = agent_executor.invoke(db_schema, req.prompt, chat_id)

    if output["answer"] != "No answer found":
        print(db_state.result_query)
        print(db_state.result_df)

    return {
    "answer": output["answer"],
    "query": db_state.result_query,
    "result": db_state.result_df.values.tolist(),
    "columns": db_state.result_df.columns.tolist(),
    }


# Run with:  uvicorn main:app --reload
