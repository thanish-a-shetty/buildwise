import re

from rank_bm25 import BM25Okapi

from app.store import col, embed


def tokenize(text: str) -> list[str]:
    # Lowercase words and codes, so "C30" and "Fe500D" stay whole tokens
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)*", text.lower())


def _all_chunks(doc_type: str | None) -> dict:
    return col.get(where={"doc_type": doc_type} if doc_type else None)


def vector_search(question: str, k: int, doc_type: str | None) -> list[str]:
    res = col.query(query_embeddings=embed([question], "RETRIEVAL_QUERY"), n_results=k,
                    where={"doc_type": doc_type} if doc_type else None)
    return res["ids"][0]


def keyword_search(question: str, k: int, doc_type: str | None) -> list[str]:
    # BM25 is classic keyword ranking: rare words that match exactly score high
    data = _all_chunks(doc_type)
    if not data["ids"]:
        return []
    bm25 = BM25Okapi([tokenize(d) for d in data["documents"]])
    scores = bm25.get_scores(tokenize(question))
    ranked = sorted(zip(data["ids"], scores), key=lambda x: x[1], reverse=True)
    return [i for i, s in ranked[:k] if s > 0]


def rrf(*ranked_lists: list[str], k: int = 60) -> list[str]:
    """Reciprocal rank fusion: merge rankings by position, not by raw score."""
    scores = {}
    for ranked in ranked_lists:
        for rank, chunk_id in enumerate(ranked):
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)


def retrieve(question: str, k: int = 6, doc_type: str | None = None) -> list[dict]:
    """Hybrid search: vector + keyword, fused with RRF. Returns chunks with metadata."""
    fused = rrf(vector_search(question, k * 2, doc_type),
                keyword_search(question, k * 2, doc_type))[:k]
    if not fused:
        return []
    got = col.get(ids=fused)
    by_id = {i: (doc, meta) for i, doc, meta in zip(got["ids"], got["documents"], got["metadatas"])}
    return [{"id": i, "text": by_id[i][0], **by_id[i][1]} for i in fused]


if __name__ == "__main__":
    questions = [
        "What concrete grade is required for footings?",
        "What is the retention percentage?",
        "Fe500D",
        "How long is the defects liability period?",
        "What thickness is the roof waterproofing membrane?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        print("  vector only:", vector_search(q, 3, None))
        for h in retrieve(q, k=3):
            print(f"  hybrid  {h['doc_type']:8} p.{h['page']} {h['clause']:5} {h['text'][:60]!r}")
