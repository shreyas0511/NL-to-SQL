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

# Initialize database file upload directory if does not already exists
UPLOAD_DIR = "data/uploaded_dbs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

message_history = JSONMessageHistory('data')

# single shared executor (thread-safe for simple demo)
agent_executor = CustomAgentExecutor(message_history)

# db uri
db_uri = None
db = None
db_schema = None

# Health check
@app.get("/")
def health():
    return {"status": "running"}

# Upload DB endpoint
@app.post("/upload_db")
def upload_db(file: UploadFile = File(...)):
    global db_uri, db, db_schema

    """Save uploaded SQLite DB and cache schema."""
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Build connection URI and extract schema
    db_uri = f"sqlite:///{file_path}"
    db = SQLDatabase.from_uri(db_uri)
    db_state.db = db
    db_schema = db.get_table_info()

    return {
        "message": f"Database {file.filename} uploaded successfully",
        "db_name": file.filename,
    }

class QueryRequest(BaseModel):
    uuid: str
    prompt: str

# Natural language query endpoint
@app.post("/query")
def run_query(req: QueryRequest):
    """Run natural language query on uploaded DB."""
    global agent_executor

    file_name = f"{req.uuid}.json"
    db_path = f"data/db/{req.uuid}.db"

    db_uri = f"sqlite:///{db_path}"
    db = SQLDatabase.from_uri(db_uri)

    db_schema = db.get_table_info()

    # Retrieve schema + db_uri
    if not db_schema:
        return {"error": "Database schema not found. Please upload the DB first."}

    # Recreate SQLDatabase for this session
    # db = SQLDatabase.from_uri(db_uri)

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
    output = agent_executor.invoke(db_schema, req.prompt, file_name)

    if output["answer"] != "No answer found":
        print(db_state.result_query)
        print(db_state.result_df)

    return {
        "answer": output,
        "query": db_state.result_query,
    }

# Run with:  uvicorn main:app --reload
