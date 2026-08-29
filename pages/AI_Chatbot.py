import streamlit as st
import pandas as pd
from db import get_engine

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# ============================================================
# HEADER
# ============================================================

st.title("🤖 AI Assistant")
st.caption("Ask questions about your ERP data")

# ============================================================
# DATABASE
# ============================================================

try:
    engine = get_engine()
    db_connected = True
except Exception as e:
    db_connected = False
    st.error(f"Database connection failed: {e}")

# ============================================================
# CHAT HISTORY
# ============================================================

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ============================================================
# CHAT INPUT
# ============================================================

question = st.chat_input(
    "Ask something about your ERP data..."
)

if question:

    # Show user question
    st.session_state.chat_messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    # --------------------------------------------------------
    # Temporary response
    # --------------------------------------------------------

    response = (
        "I received your question. "
        "The AI connection will be added next."
    )

    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": response
    })

    with st.chat_message("assistant"):
        st.markdown(response)