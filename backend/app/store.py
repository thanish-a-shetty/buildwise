import os
import time

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from app.chunk import chunk_all
from app.ingest import ingest_folder

load_dotenv()

# Model names live in .env so a rename by Google is a one-line fix
EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma")

client = genai.Client()
db = chromadb.PersistentClient(path=CHROMA_PATH)
col = db.get_or_create_collection("buildwise", metadata={"hnsw:space": "cosine"})


def with_retry(fn, tries: int = 5):
    """Retry on rate limits (429) and overload (5xx), waiting 2s, 4s, 8s, ..."""
    for attempt in range(tries):
        try:
            return fn()
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or attempt == tries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"  Gemini returned {e.code}, retrying in {wait}s")
            time.sleep(wait)


def embed(texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Turn texts into vectors. Use RETRIEVAL_QUERY for questions."""
    vectors = []
    for i in range(0, len(texts), 50):
        batch = texts[i:i + 50]
        resp = with_retry(lambda: client.models.embed_content(
            model=EMBED_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type=task),
        ))
        vectors += [e.values for e in resp.embeddings]
    return vectors


def to_metadata(chunk: dict) -> dict:
    # Chroma metadata must be str, int, float or bool, and not None
    return {k: v for k, v in chunk.items()
            if k not in ("id", "text") and isinstance(v, (str, int, float, bool))}


def index(chunks: list[dict]) -> None:
    # upsert = insert or replace by id, so re-running never creates duplicates
    col.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=embed([c["text"] for c in chunks]),
        metadatas=[to_metadata(c) for c in chunks],
    )


if __name__ == "__main__":
    chunks = chunk_all(ingest_folder("../data/raw"))
    index(chunks)
    print(f"indexed {len(chunks)} chunks, collection now holds {col.count()}")

    question = "What concrete grade is required for footings?"
    res = col.query(query_embeddings=embed([question], "RETRIEVAL_QUERY"), n_results=5)
    print(f"\nQ: {question}")
    for meta, dist, doc in zip(res["metadatas"][0], res["distances"][0], res["documents"][0]):
        print(f"  {1 - dist:.3f}  {meta['doc_type']:8} p.{meta['page']} {meta['clause']:5} {doc[:70]!r}")
