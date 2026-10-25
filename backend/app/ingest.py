import hashlib
import pathlib
import re
import pymupdf
import pdfplumber  # put this with the other imports at the top

def to_number(s: str) -> float:
    return float(s.replace(",", ""))

def load_boq(path: str) -> list[dict]:
    p = pathlib.Path(path)
    doc_id = hashlib.md5(p.name.encode()).hexdigest()[:8]
    rows = []
    with pdfplumber.open(p) as pdf:
        for i, page in enumerate(pdf.pages):
            for table in page.extract_tables():
                for row in table[1:]:          # [1:] skips the header row
                    item, desc, unit, qty, rate, amount = row
                    desc = desc.replace("\n", " ")
                    rows.append({
                        "doc_id": doc_id, "doc_name": p.name, "doc_type": "boq",
                        "page": i + 1, "item_no": item, "unit": unit,
                        "qty": to_number(qty), "rate": to_number(rate),
                        # TODO B: a readable sentence, e.g.
                        # "BOQ item 2.2: RCC grade C25 in isolated footings..., 185 m3 at 140 per m3"
                        "text": f"BOQ item {item}: {desc}, {qty} {unit} at {rate} per {unit}",
                    })
    return rows
def guess_type(name: str) -> str:
    n = name.lower()
    # TODO 1: return "boq", "spec" or "contract" based on words in the filename
    if "boq" in n:
        return "boq"
    if "spec" in n:
        return "spec"
    return "contract"

def clean(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if " | " in line or re.match(r"^Page \d+$", line):
            continue
        lines.append(line.strip())
    return "\n".join(l for l in lines if l)

def load_pdf(path: str) -> list[dict]:
    p = pathlib.Path(path)
    doc_id = hashlib.md5(p.name.encode()).hexdigest()[:8]
    records = []
    with pymupdf.open(p) as pdf:
        for i, page in enumerate(pdf):
            # TODO 3: append a dict with doc_id, doc_name, doc_type, page (1-based!), text (cleaned)
            records.append({
                "doc_id": doc_id,
                "doc_name": p.name,
                "doc_type": guess_type(p.name),
                "page": i + 1,
                "text": clean(page.get_text()),
            })
            
    return records


import json  # add to the imports at the top

def ingest_folder(folder: str) -> list[dict]:
    records = []
    for path in sorted(pathlib.Path(folder).glob("*.pdf")):
        # TODO: if guess_type(path.name) is "boq", use load_boq(path), otherwise load_pdf(path)
        #       then add the results to records (hint: records.extend(...))
        
        ...
        if guess_type(path.name) == "boq":
            records.extend(load_boq(path))
        else:
            records.extend(load_pdf(path))
            
    return records


def save_jsonl(records: list[dict], out: str) -> None:
    with open(out, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
            
            
if __name__ == "__main__":
    records = ingest_folder("../data/raw")
    save_jsonl(records, "../data/processed/pages.jsonl")
    print(f"saved {len(records)} records")