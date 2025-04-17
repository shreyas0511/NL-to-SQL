import streamlit as st
import requests
import uuid
import os

from memory.message_history import JSONMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

# --------------------------- INITIAL SETUP ---------------------------
st.set_page_config(page_title="NL-to-SQL Agent", layout="wide")

if "bootstrapped" not in st.session_state:
    st.session_state["json_history"] = JSONMessageHistory(root_path="data")
    st.session_state["sessions"] = {}             # uuid → {"title": str, "db_path": str}
    st.session_state["current_session"] = None
    st.session_state["bootstrapped"] = True

history_manager = st.session_state["json_history"]

# --------------------------- SIDEBAR ---------------------------
st.sidebar.title("💬 Chats")

# Create new chat
if st.sidebar.button("➕ New Chat"):
    new_uuid = str(uuid.uuid4())
    st.session_state["current_session"] = new_uuid
    st.session_state["sessions"][new_uuid] = {
        "title": f"Chat {len(st.session_state['sessions'])+1}",
        "db_path": None
    }
    st.rerun()

# List all existing chats
for chat_id, meta in st.session_state["sessions"].items():
    label = meta["title"]
    if st.sidebar.button(label, key=chat_id):
        st.session_state["current_session"] = chat_id
        st.rerun()

# --------------------------- MAIN CONTENT ---------------------------
st.title("🧠 NL-to-SQL Agent")

# If no chat selected
if not st.session_state["current_session"]:
    st.info("Start by creating a new chat from the sidebar ➕")
    st.stop()

chat_id = st.session_state["current_session"]
chat_file = f"{chat_id}.json"
db_file_path = f"data/db/{chat_id}.db"

# --------------------------- DATABASE UPLOAD ---------------------------
st.sidebar.subheader("🗂 Upload Database for this Chat")

uploaded_file = st.sidebar.file_uploader(
    "Upload SQLite DB",
    type=["db", "sqlite"],
    key=f"uploader_{st.session_state['current_session']}"
)


if uploaded_file is not None:
    os.makedirs("data/db", exist_ok=True)
    with open(db_file_path, "wb") as f:
        f.write(uploaded_file.read())
    st.session_state["sessions"][chat_id]["db_path"] = db_file_path
    st.sidebar.success("✅ Database uploaded successfully!")

elif st.session_state["sessions"][chat_id]["db_path"]:
    st.sidebar.info(f"Using existing DB:\n{os.path.basename(st.session_state['sessions'][chat_id]['db_path'])}")
else:
    st.sidebar.warning("⚠️ No database uploaded for this chat.")

# --------------------------- LOAD MEMORY ---------------------------
messages = history_manager.load(chat_file)

# --------------------------- DISPLAY CHAT HISTORY ---------------------------
for msg in messages:
    role = "user" if msg.type == "human" else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

# --------------------------- USER INPUT ---------------------------
prompt = st.chat_input("Ask your question or query the database...")

if prompt:
    if not os.path.exists(db_file_path):
        st.warning("⚠️ Please upload a database before querying.")
        st.stop()

    # 1️⃣ Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2️⃣ Send to FastAPI
    payload = {
        "uuid": chat_id,
        "prompt": prompt
    }

    try:
        response = requests.post("http://localhost:8000/query", json=payload, timeout=120)
        response.raise_for_status()
        answer = response.json().get("answer", "No response received.")
    except Exception as e:
        answer = f"⚠️ Backend error: {e}"

    # 3️⃣ Display assistant response
    with st.chat_message("assistant"):
        st.markdown(answer)

    # 4️⃣ Save messages
    messages.extend([HumanMessage(content=prompt), AIMessage(content=answer)])
    history_manager.save(chat_file, messages)
