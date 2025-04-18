import streamlit as st
import requests
import uuid
import os
import pandas as pd

from memory.message_history import JSONMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

# --------------------------- INITIAL SETUP ---------------------------
st.set_page_config(page_title="NL-to-SQL Agent", layout="wide")

if "bootstrapped" not in st.session_state:
    st.session_state["json_history"] = JSONMessageHistory(root_path="data")
    st.session_state["sessions"] = {}
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
        "title": f"Chat {len(st.session_state['sessions']) + 1}",
        "db_path": None,
    }
    st.rerun()

# List all existing chats
for chat_id, meta in st.session_state["sessions"].items():
    if st.sidebar.button(meta["title"], key=chat_id):
        st.session_state["current_session"] = chat_id
        st.rerun()

# --------------------------- MAIN CONTENT ---------------------------
if not st.session_state["current_session"]:
    st.info("Start by creating a new chat from the sidebar ➕")
    st.stop()

chat_id = st.session_state["current_session"]
chat_file = f"{chat_id}.json"
db_file_path = f"data/db/{chat_id}.db"

# Create a unique state key per chat
chat_key = f"chat_messages_{chat_id}"

# --------------------------- DATABASE UPLOAD ---------------------------
st.sidebar.subheader("🗂 Upload Database for this Chat")

uploaded_file = st.sidebar.file_uploader(
    "Upload SQLite DB",
    type=["db", "sqlite"],
    key=f"uploader_{chat_id}",
)

if uploaded_file is not None:
    os.makedirs("data/db", exist_ok=True)
    with open(db_file_path, "wb") as f:
        f.write(uploaded_file.read())
    st.session_state["sessions"][chat_id]["db_path"] = db_file_path
    st.sidebar.success("✅ Database uploaded successfully!")
elif st.session_state["sessions"][chat_id]["db_path"]:
    st.sidebar.info(f"Using existing DB:\n{os.path.basename(db_file_path)}")
else:
    st.sidebar.warning("⚠️ No database uploaded for this chat.")

# --------------------------- LOAD CHAT HISTORY ---------------------------
if chat_key not in st.session_state:
    # Load from file only once per chat
    st.session_state[chat_key] = history_manager.load(chat_file)

# --------------------------- CUSTOM CSS + JS ---------------------------
st.markdown(
    """
<style>
.chat-bubble {
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    border-radius: 12px;
    max-width: 90%;
    line-height: 1.5;
    word-wrap: break-word;
}
.user-bubble {
    background-color: #DCF8C6;
    text-align: right;
}
.assistant-bubble {
    background-color: #E8EAF6;
    text-align: left;
}
.chat-container {
    display: flex;
    flex-direction: column;
}
</style>

<script>
window.addEventListener('load', function() {
    var chatContainer = window.parent.document.querySelector('.main');
    if (chatContainer) {
        chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
    }
});
</script>
""",
    unsafe_allow_html=True,
)

# --------------------------- DISPLAY ALL MESSAGES ---------------------------
messages = st.session_state[chat_key]

for msg in messages:
    if msg.type == "human":
        st.markdown(
            f"<div class='chat-container'><div class='chat-bubble user-bubble'>🧑‍💻 {msg.content}</div></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='chat-container'><div class='chat-bubble assistant-bubble'>🤖 {msg.content}</div></div>",
            unsafe_allow_html=True,
        )

        if hasattr(msg, "metadata"):
            if msg.metadata.get("query"):
                st.markdown("#### 🧾 Executed Query:")
                st.code(msg.metadata["query"], language="sql")

            if msg.metadata.get("result"):
                try:
                    df = pd.DataFrame(
                        msg.metadata["result"],
                        columns=msg.metadata.get("columns"),
                    )
                    st.markdown("#### 📊 Top 10 Rows:")
                    st.dataframe(df.head(10))
                except Exception as err:
                    st.error(f"Error displaying dataframe: {err}")

# --------------------------- USER INPUT ---------------------------
prompt = st.chat_input("Ask your question or query the database...")

if prompt:
    if not os.path.exists(db_file_path):
        st.warning("⚠️ Please upload a database before querying.")
        st.stop()

    # 1️⃣ Display user message immediately
    messages.append(HumanMessage(content=prompt))
    st.markdown(
        f"<div class='chat-container'><div class='chat-bubble user-bubble'>🧑‍💻 {prompt}</div></div>",
        unsafe_allow_html=True,
    )

    # 2️⃣ Send to FastAPI
    payload = {"uuid": chat_id, "prompt": prompt}
    try:
        with st.spinner("🤖 Thinking..."):
            response = requests.post(
                "http://localhost:8000/query", json=payload, timeout=120
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        data = {"answer": f"⚠️ Backend error: {e}"}

    # 3️⃣ Extract parts
    answer_text = data.get("answer", "No response received.")
    query_text = data.get("query")
    result_data = data.get("result")
    columns = data.get("columns")

    # 4️⃣ Display AI message
    st.markdown(
        f"<div class='chat-container'><div class='chat-bubble assistant-bubble'>🤖 <b>AI:</b> {answer_text}</div></div>",
        unsafe_allow_html=True,
    )

    if query_text:
        st.markdown("#### 🧾 Executed Query:")
        st.code(query_text, language="sql")

    if result_data:
        try:
            df = pd.DataFrame(result_data, columns=columns)
            st.markdown("#### 📊 Top 10 Rows:")
            st.dataframe(df.head(10))
        except Exception as err:
            st.error(f"Error displaying dataframe: {err}")

    # 5️⃣ Save conversation with metadata
    ai_message = AIMessage(content=answer_text)
    ai_message.metadata = {
        "query": query_text,
        "result": result_data,
        "columns": columns,
    }

    messages.append(ai_message)
    history_manager.save(chat_file, messages)

    # 6️⃣ Refresh view
    st.rerun()
