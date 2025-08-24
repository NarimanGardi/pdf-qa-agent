
# 📄 PDF Q&A Agent

A lightweight **PDF Question-Answering (RAG) Agent** built with **Python, FAISS, and OpenAI models**. It ingests your PDF documents, indexes them into a vector store, and allows you to ask natural language questions with **grounded answers and citations**.

---

## 🚀 Features

- 🔍 **Ingest PDFs** → parses text, chunks, and embeds.
- 📚 **Vector search (FAISS)** → efficient similarity search across documents.
- 🤖 **LLM-powered answers** → grounded in your PDFs, with inline `[citations]`.
- 🖥️ **Streamlit UI** → ask questions in a simple web interface.
- 📑 **Citations** → answers reference original file + page.
- 🛠️ **Modular codebase** → extend easily with OCR, rerankers, or custom tools.

---

## 📂 Project Structure

pdf-qa/
├─ data/
│   └─ pdfs/           # Upload or drop your PDFs here (via UI or manually)
├─ store/
│   └─ faiss_index/    # Vector index & metadata (auto-updated after upload)
├─ ingest.py           # Ingestion logic (now callable from app)
├─ query.py            # CLI Q&A tool
├─ app.py              # Streamlit web app (upload, Q&A, auto-ingest)
├─ requirements.txt    # Python dependencies
└─ .env                # API keys + config

---

## 🏗️ Architecture

1. **Ingest**
   - Parse PDFs with [PyMuPDF](https://pymupdf.readthedocs.io/).
   - Chunk text with overlap.
   - Generate embeddings (`text-embedding-3-large` by default).
   - Store vectors in [FAISS](https://github.com/facebookresearch/faiss).

2. **Query**
   - Embed query → search top-k chunks.
   - Build context block.
   - LLM (`gpt-4o-mini` by default) answers with citations.

3. **Serve**
   - CLI for direct Q&A.
   - Streamlit app for a user-friendly interface.

---

## 📦 Repository

[NarimanGardi/pdf-qa-agent](https://github.com/NarimanGardi/pdf-qa-agent)

---

## ⚙️ Setup

### 1. Clone repo

```bash
git clone https://github.com/NarimanGardi/pdf-qa-agent.git
cd pdf-qa-agent
```

### 2. Create environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Create `.env`:

```env
OPENAI_API_KEY=sk-...
EMBED_MODEL=text-embedding-3-large
CHAT_MODEL=gpt-4o-mini
```

---

## 📥 Ingest PDFs

Drop files in `data/pdfs/`

Run:

```bash
python ingest.py
```

This:

- Parses text
- Chunks and embeds
- Builds FAISS index in `store/faiss_index/`

---

## ❓ Ask Questions

### CLI

```bash
python query.py "What does the refund policy say?"
```

Example output:

```
Refunds are available within 30 days [1], but not after product activation [2].

Sources:
[1] Policy.pdf p.4
[2] Policy.pdf p.7
```

### Web App

```bash
streamlit run app.py
```

Open: [http://localhost:8501](http://localhost:8501)

---

## 🛡️ Tips & Best Practices

- **Chunking** → current: ~900 words w/ overlap. Adjust in `ingest.py`.
- **Citations** → stored per file + page for traceability.
- **OCR** → if PDFs are scanned images, add Tesseract fallback.
- **Cost control** → start with gpt-4o-mini, upgrade only if needed.
- **Security** → never commit your `.env`.

---

## 🔧 Extensions

- 🔄 Swap OpenAI embeddings → `sentence-transformers` for local/offline use.
- 🔐 Secure UI → add auth middleware or deploy behind a proxy.
- 📊 Better retrieval → integrate rerankers (e.g., bge-reranker-large).
- 🌍 Multi-user → namespace vector stores (one per corpus).
- 🧪 Evals → keep a regression set of Q→expected answer pages.

---

## 📜 License

MIT License. Use freely, modify, and share.

---

## 🤝 Contributing

PRs welcome! If you build OCR support, UI enhancements, or new chunking strategies, open a PR.

---

## 🧑‍💻 Author

Built by Nariman Gardi · Software developer & agent builder.

---