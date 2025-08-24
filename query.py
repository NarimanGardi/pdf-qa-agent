
import os, json, faiss, numpy as np
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import logging

load_dotenv()
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")

INDEX_DIR = Path("store/faiss_index")
client = OpenAI()

logging.basicConfig(level=logging.INFO)

def load_store():
    """Load FAISS index, metadata, and texts from disk."""
    try:
        index = faiss.read_index(str(INDEX_DIR / "index.faiss"))
    except Exception as e:
        logging.error(f"Failed to load FAISS index: {e}")
        raise RuntimeError("Could not load vector index. Please run ingest.py first.")
    try:
        with open(INDEX_DIR / "metas.json", "r", encoding="utf-8") as f:
            metas = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load metas.json: {e}")
        raise RuntimeError("Could not load metadata. Please check your index files.")
    texts = []
    try:
        with open(INDEX_DIR / "texts.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                try:
                    texts.append(json.loads(line)["text"])
                except Exception as e:
                    logging.warning(f"Malformed line in texts.jsonl: {e}")
    except Exception as e:
        logging.error(f"Failed to load texts.jsonl: {e}")
        raise RuntimeError("Could not load texts. Please check your index files.")
    return index, metas, texts

def embed_query(q: str):
    """Embed a query string using the OpenAI embedding model."""
    if not q or not isinstance(q, str):
        raise ValueError("Query must be a non-empty string.")
    try:
        v = client.embeddings.create(model=EMBED_MODEL, input=[q]).data[0].embedding
        v = np.array(v, dtype="float32")
        faiss.normalize_L2(v.reshape(1, -1))
        return v
    except Exception as e:
        logging.error(f"Embedding failed: {e}")
        raise RuntimeError("Failed to embed query.")

def retrieve(q, k=6):
    """Retrieve top-k relevant chunks for a query."""
    try:
        index, metas, texts = load_store()
        qv = embed_query(q)
        D, I = index.search(qv.reshape(1, -1), k)
        I = I[0].tolist()
        results = []
        for rank, idx in enumerate(I):
            if idx >= len(metas) or idx >= len(texts):
                logging.warning(f"Index {idx} out of range in metas/texts.")
                continue
            meta = metas[idx]
            results.append({
                "rank": rank+1,
                "text": texts[idx],
                "source": meta.get("source", "Unknown"),
                "page": meta.get("page", "?"),
                "chunk_id": meta.get("chunk_id", "?")
            })
        return results
    except Exception as e:
        logging.error(f"Retrieval failed: {e}")
        return []

def answer(q):
    """Generate an answer to the query using retrieved context and OpenAI chat completion."""
    ctx = retrieve(q)
    if not ctx:
        return "Sorry, I couldn't find any relevant information.", []
    context_block = "\n\n".join(
        f"[{i+1}] ({c['source']} p.{c['page']})\n{c['text']}"
        for i, c in enumerate(ctx)
    )
    system = (
        "You are a precise document QA assistant. "
        "Use ONLY the provided context to answer. "
        "Cite sources like [1], [2] corresponding to the context items. "
        "If missing, say you don't know."
    )
    user = f"Question: {q}\n\nContext:\n{context_block}"
    try:
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":user}
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content, ctx
    except Exception as e:
        logging.error(f"OpenAI chat completion failed: {e}")
        return "Sorry, there was an error generating the answer.", ctx

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "What is the main conclusion?"
    try:
        ans, ctx = answer(q)
        print(ans)
        print("\nSources:")
        for i, c in enumerate(ctx, 1):
            print(f"[{i}] {c['source']} p.{c['page']}")
    except Exception as e:
        print(f"Error: {e}")
