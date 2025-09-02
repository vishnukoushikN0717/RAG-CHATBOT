import os
import json
import re
from typing import List, Dict

# ==== config ====
INPUT_FOLDER = "extracted_ocr_jsons"   # your per-PDF page JSONs
OUTPUT_FOLDER = "chunks_500words_pdfs"          # where we’ll write per-PDF chunk JSONs
CHUNK_WORDS = 500                      # words per chunk
OVERLAP_WORDS = 50                     # sliding-window overlap
MIN_WORDS_TO_KEEP_LAST = 50            # drop tiny tail chunks (< this), or set to 0 to keep all
# ===============

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def normalize_text(text: str) -> str:
    """
    light cleanup so chunking is cleaner:
    - fix hyphenation at line breaks
    - collapse newlines/spaces
    """
    if not text:
        return ""
    # join hyphenated breaks: "trans-\nmission" -> "transmission"
    text = re.sub(r"-\s*\n\s*", "", text)
    # newlines -> space
    text = re.sub(r"\s*\n\s*", " ", text)
    # collapse multiple spaces
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def load_pages(json_path: str) -> List[Dict]:
    """
    expects a list like:
    [
      {"doc_id": "...", "page_number": 1, "content": "..."},
      ...
    ]
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # sort by page_number just in case
    data.sort(key=lambda x: x.get("page_number", 0))
    return data

def build_word_stream(pages: List[Dict]):
    """
    flattens pages into a word stream while tracking which page each word came from
    returns: words[], page_map[]  (same length)
    """
    words = []
    page_map = []
    for p in pages:
        page_no = p.get("page_number")
        text = normalize_text(p.get("content", ""))
        if not text:
            continue
        tokens = text.split()  # whitespace word split (keeps punctuation attached)
        words.extend(tokens)
        page_map.extend([page_no] * len(tokens))
    return words, page_map

def make_chunks(words: List[str], page_map: List[int],
                chunk_words: int, overlap_words: int):
    """
    sliding-window over the word stream
    returns list of dicts: each dict is a chunk with text + page metadata
    """
    chunks = []
    n = len(words)
    if n == 0:
        return chunks

    step = max(1, chunk_words - overlap_words)
    start = 0
    idx = 0

    while start < n:
        end = min(start + chunk_words, n)
        chunk_tokens = words[start:end]
        # optionally drop tiny tail
        if end == n and len(chunk_tokens) < MIN_WORDS_TO_KEEP_LAST:
            break

        # pages covered by this chunk
        pages_in_chunk = page_map[start:end]
        page_set = sorted(set(pages_in_chunk))
        chunk_text = " ".join(chunk_tokens)

        chunks.append({
            "chunk_index": idx,
            "content": chunk_text,
            "n_words": len(chunk_tokens),
            "pages": page_set,
            "page_range": [page_set[0], page_set[-1]] if page_set else None
        })

        idx += 1
        start += step

    return chunks

def process_one_file(input_path: str, filename: str):
    base = os.path.splitext(filename)[0]
    pages = load_pages(input_path)
    if not pages:
        print(f"⚠️  {filename}: no pages found, skipping.")
        return

    # ensure doc_id consistency
    doc_id = pages[0].get("doc_id", base)

    words, page_map = build_word_stream(pages)
    chunks = make_chunks(words, page_map, CHUNK_WORDS, OVERLAP_WORDS)

    # decorate chunks with doc metadata and stable chunk_ids
    for i, ch in enumerate(chunks):
        ch["doc_id"] = doc_id
        ch["source_file"] = filename
        ch["chunk_id"] = f"{base}-{i:04d}"

    out_path = os.path.join(OUTPUT_FOLDER, f"{base}_chunks.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=4, ensure_ascii=False)

    print(f"✅ {filename}: {len(chunks)} chunks → {out_path}")

def main():
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".json")]
    if not files:
        print(f"no JSON files found in {INPUT_FOLDER}")
        return
    for fname in files:
        process_one_file(os.path.join(INPUT_FOLDER, fname), fname)

if __name__ == "__main__":
    main()
