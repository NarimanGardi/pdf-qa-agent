
import os, json, re, fitz, faiss, numpy as np
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
import logging

load_dotenv()
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")

DATA_DIR = Path("data/pdfs")
INDEX_DIR = Path("store/faiss_index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

client = OpenAI()

logging.basicConfig(level=logging.INFO)

def clean_text(t: str) -> str:
    """Clean whitespace from text."""
    t = re.sub(r"\s+", " ", t).strip()
    return t

def pdf_to_pages(pdf_path: Path):
    """Yield (page_number, text) for each page in a PDF."""
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc[i]
            blocks = page.get_text("blocks")
            blocks = sorted(blocks, key=lambda b: (b[1], b[0]))  # by y,x
            text = "\n".join(clean_text(b[4]) for b in blocks if b[4].strip())
            yield i+1, text
        doc.close()
    except Exception as e:
        logging.error(f"Failed to process PDF {pdf_path}: {e}")

def chunk_text(text, chunk_size=900, overlap=150):
    """Chunk text into overlapping segments."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words): break
        start = max(0, end - overlap)
    return chunks

def embed_texts(texts):
    """Embed a list of texts using OpenAI embeddings. Adds diagnostics for debugging."""
    if not texts:
        logging.error("No texts provided for embedding.")
        raise RuntimeError("No texts provided for embedding.")
    try:
        logging.info(f"Requesting embeddings for {len(texts)} texts. First text: {texts[0][:100]}...")
        resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
        if not hasattr(resp, 'data') or not resp.data:
            logging.error(f"OpenAI returned no embedding data. Response: {resp}")
            raise RuntimeError("OpenAI returned no embedding data.")
        vecs = []
        for i, d in enumerate(resp.data):
            if not hasattr(d, 'embedding') or d.embedding is None:
                logging.error(f"Missing embedding for item {i} in response.")
                raise RuntimeError(f"Missing embedding for item {i} in response.")
            vecs.append(np.array(d.embedding, dtype="float32"))
        arr = np.vstack(vecs)
        logging.info(f"Embeddings shape: {arr.shape}")
        return arr
    except Exception as e:
        logging.error(f"Embedding failed: {e}")
        raise RuntimeError(f"Failed to embed texts: {e}")


def run_ingestion():
    """Main ingestion pipeline: process PDFs, chunk, embed, and store index."""
    texts, metas = [], []
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        logging.error("No PDF files found in data/pdfs/.")
        print("No PDF files found. Please add PDFs to data/pdfs/.")
        return False, "No PDF files found. Please add PDFs to data/pdfs/."
    for pdf in pdfs:
        for page_no, page_text in pdf_to_pages(pdf):
            if not page_text or not page_text.strip():
                continue
            for chunk_id, chunk in enumerate(chunk_text(page_text)):
                if len(chunk) < 20:
                    continue
                texts.append(chunk)
                metas.append({
                    "source": str(pdf.name),
                    "page": page_no,
                    "chunk_id": chunk_id
                })

    if not texts:
        logging.error("No text found in PDFs.")
        print("No text found. Put PDFs in data/pdfs/")
        return False, "No text found. Put PDFs in data/pdfs/."

    print(f"Embedding {len(texts)} chunks...")
    try:
        X = embed_texts(texts)
        if X is None or not hasattr(X, 'shape'):
            logging.error("Embedding array is None or missing shape attribute.")
            return False, "Embedding array is invalid."
        dim = X.shape[1]
        if X.shape[0] == 0 or dim == 0:
            logging.error(f"Embedding array has invalid shape: {X.shape}")
            return False, f"Embedding array has invalid shape: {X.shape}"
        index = faiss.IndexFlatIP(dim)
        faiss.normalize_L2(X)
        index.add(X)
    except Exception as e:
        logging.error(f"Failed to build FAISS index: {e}")
        import traceback
        tb = traceback.format_exc()
        print(f"Error: Failed to build FAISS index.\n{tb}")
        return False, f"Error: Failed to build FAISS index. {e}"

    try:
        faiss.write_index(index, str(INDEX_DIR / "index.faiss"))
        with open(INDEX_DIR / "metas.json", "w", encoding="utf-8") as f:
            json.dump(metas, f, ensure_ascii=False)
        with open(INDEX_DIR / "texts.jsonl", "w", encoding="utf-8") as f:
            for t in texts:
                f.write(json.dumps({"text": t}, ensure_ascii=False) + "\n")
    except Exception as e:
        logging.error(f"Failed to write index or metadata: {e}")
        print("Error: Failed to write index or metadata.")
        return False, "Error: Failed to write index or metadata."

    print("Done. Index stored in store/faiss_index/")
    return True, "Done. Index stored in store/faiss_index/."

if __name__ == "__main__":
    try:
        run_ingestion()
    except Exception as e:
        logging.error(f"Fatal error in ingestion: {e}")
        print(f"Fatal error: {e}")
