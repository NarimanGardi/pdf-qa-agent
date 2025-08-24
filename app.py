

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

query = st.text_input("Ask a question about your PDFs:")
if st.button("Ask") and query.strip():
    try:
        with st.spinner("Thinking..."):
            ans, ctx = answer(query)
        st.markdown("### Answer")
        st.write(ans if ans else "No answer found.")

        if ctx:
            st.markdown("### Sources")
            for i, c in enumerate(ctx, 1):
                with st.expander(f"[{i}] {c.get('source', 'Unknown')} — page {c.get('page', '?')}"):
                    st.write(c.get("text", "No text available."))
        else:
            st.info("No sources found for this answer.")
    except Exception as e:
        st.error(f"An error occurred: {e}")