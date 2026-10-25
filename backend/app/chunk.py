import json
import re

from app.ingest import ingest_folder, save_jsonl

# A clause starts a line with a number like 4.2 or 03.1, then a space
CLAUSE = re.compile(r"^(\d+(?:\.\d+)+)\s")
# A heading is "4. Time for Completion" or "Section 03 30 00 - Cast-in-Place Concrete"
HEADING = re.compile(r"^(?:\d+\.\s+\D|Section\s+\d)")

MAX_CHARS = 1000


def chunk_page(rec: dict) -> list[dict]:
    """Split one contract/spec page into one chunk per clause."""
    chunks, heading, clause, buf = [], "", "", []

    def flush():
        body = " ".join(buf).strip()
        if not body:
            return
        # Prefix the heading so the chunk makes sense on its own
        text = f"{heading}\n{body}" if heading and not body.startswith(heading) else body
        for k in range(0, len(text), MAX_CHARS):  # safety net for very long clauses
            chunks.append({
                "id": f"{rec['doc_id']}-p{rec['page']}-{len(chunks)}",
                "doc_id": rec["doc_id"], "doc_name": rec["doc_name"],
                "doc_type": rec["doc_type"], "page": rec["page"],
                "section": heading, "clause": clause,
                "text": text[k:k + MAX_CHARS],
            })

    for line in rec["text"].splitlines():
        if HEADING.match(line):
            flush(); buf, clause = [], ""
            heading = line
        elif m := CLAUSE.match(line):
            flush(); buf = [line]
            clause = m.group(1)
        else:
            buf.append(line)
    flush()
    return chunks


def chunk_all(records: list[dict]) -> list[dict]:
    chunks = []
    for rec in records:
        if rec["doc_type"] == "boq":
            # A BOQ row is already one small, self-contained chunk
            chunks.append({**rec, "id": f"{rec['doc_id']}-p{rec['page']}-{rec['item_no']}",
                           "section": "", "clause": rec["item_no"]})
        else:
            chunks.extend(chunk_page(rec))
    return chunks


if __name__ == "__main__":
    chunks = chunk_all(ingest_folder("../data/raw"))
    save_jsonl(chunks, "../data/processed/chunks.jsonl")
    print(f"saved {len(chunks)} chunks")
    for c in chunks:
        print(f"{c['doc_type']:8} p.{c['page']} {c['clause']:5} | {c['text'][:90]!r}")
