

import streamlit as st
from query import answer
import os
from pathlib import Path
from ingest import run_ingestion

PDF_DIR = Path("data/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)


st.set_page_config(page_title="PDF Q&A", page_icon="📄")
st.title("📄 PDF Q&A")


# PDF upload feature
uploaded_file = st.file_uploader("Upload a PDF to add to your knowledge base", type=["pdf"])
if uploaded_file is not None:
    save_path = PDF_DIR / uploaded_file.name
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Uploaded {uploaded_file.name} to {save_path}.")
    with st.spinner("Updating index with new PDF(s)..."):
        success, msg = run_ingestion()
    if success:
        st.success("Ingestion complete. You can now query your new PDF!")
    else:
        st.error(f"Ingestion failed: {msg}")

# --- Chat-like Q&A ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Each item: {"question": str, "answer": str, "sources": list}

def add_to_history(question, answer, sources):
    st.session_state.chat_history.append({
        "question": question,
        "answer": answer,
        "sources": sources,
    })

# Input at the bottom, after previous messages
for idx, msg in enumerate(st.session_state.chat_history):
    st.markdown(f"**You:** {msg['question']}")
    st.markdown("### Answer")
    st.write(msg['answer'])
    if msg['sources']:
        st.markdown("### Sources")
        for i, c in enumerate(msg['sources'], 1):
            with st.expander(f"[{i}] {c.get('source', 'Unknown')} — page {c.get('page', '?')}"):
                st.write(c.get("text", "No text available."))
    st.markdown("---")

# Only show chat input, remove old input/button logic
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask a question about your PDFs:", key="chat_input")
    submitted = st.form_submit_button("Ask")
    if submitted and user_input.strip():
        try:
            with st.spinner("Thinking..."):
                ans, ctx = answer(user_input)
            add_to_history(user_input, ans if ans else "No answer found.", ctx if ctx else [])
        except Exception as e:
            add_to_history(user_input, f"An error occurred: {e}", [])
