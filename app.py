import streamlit as st
from pathlib import Path
from ingest import run_ingestion
from query import answer

PDF_DIR = Path("data/pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="PDF Q&A", page_icon="📄")
st.title("📄 PDF Q&A")

# --- state init ---
if "chat_history" not in st.session_state:
    # list of dicts: {"role": "user"|"assistant", "content": str, "sources": list|None}
    st.session_state.chat_history = []

def add_msg(role: str, content: str, sources=None):
    st.session_state.chat_history.append({
        "role": role,
        "content": content,
        "sources": sources or []
    })

# --- uploader (kept at the top) ---
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

st.divider()

# --- INPUT AT BOTTOM ---
# Note: st.chat_input is always rendered at the bottom of the page by Streamlit.
user_prompt = st.chat_input("Ask a question about your PDFs...")

# If the user just sent a new message, process it BEFORE rendering history
if user_prompt:
    # 1) Show the user's message in history
    add_msg("user", user_prompt, sources=[])
    # 2) Get the answer (no rerun, no form submit state)
    with st.spinner("Thinking..."):
        try:
            ans, ctx = answer(user_prompt)
        except Exception as e:
            ans, ctx = f"An error occurred: {e}", []
    # 3) Store assistant reply (with sources)
    add_msg("assistant", ans if ans else "No answer found.", sources=ctx)

# --- RENDER HISTORY (after we've possibly added new messages above) ---
for msg in st.session_state.chat_history:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        if msg["role"] == "assistant":
            st.markdown("### Answer")
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            st.markdown("### Sources")
            for i, c in enumerate(msg["sources"], 1):
                with st.expander(f"[{i}] {c.get('source', 'Unknown')} — page {c.get('page', '?')}"):
                    st.write(c.get("text", "No text available."))

# 👇 Scroll to the last element
st.markdown(
    """
    <div id="scroll-to-bottom"></div>
    <script>
        var el = document.getElementById("scroll-to-bottom");
        if (el) { el.scrollIntoView({behavior: "smooth"}); }
    </script>
    """,
    unsafe_allow_html=True
)
