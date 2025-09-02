# rag_local_cpu.py
import os
from typing import List, Tuple
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

from sentence_transformers import CrossEncoder
from transformers import AutoTokenizer, AutoModelForQuestionAnswering, pipeline

# ---------- Helpers ----------
def truncate_to_tokens(text: str, tokenizer, max_tokens: int) -> str:
    """Trim text to fit the model's max input length."""
    ids = tokenizer.encode(text, add_special_tokens=False, truncation=True, max_length=max_tokens)
    return tokenizer.decode(ids, skip_special_tokens=True)

def pretty_src(meta: dict) -> str:
    """Compact source print (customize for your metadata keys)."""
    # common keys: 'source', 'page', 'file', 'path'
    parts = []
    for k in ("source", "file", "path", "page"):
        if k in meta:
            parts.append(f"{k}={meta[k]}")
    return ", ".join(parts) if parts else str(meta)

# ---------- Main ----------
def main():
    # 1) Load the same embedding model you used to build the FAISS index
    # If you embedded with another model, switch it here to match exactly.
    embed = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 2) Load FAISS index
    vectorstore = FAISS.load_local(
        "embeddings/faiss_index",
        embed,
        allow_dangerous_deserialization=True
    )

    # 3) Ask query
    query = input("Enter your query: ").strip()

    # 4) Retrieve more than you need, we’ll rerank and keep top-3
    retrieved_docs = vectorstore.similarity_search(query, k=8)

    # 5) Re-rank with a CPU-friendly cross-encoder (boosts accuracy a lot)
    reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")
    pairs = [(query, d.page_content) for d in retrieved_docs]
    scores = reranker.predict(pairs)  # higher = more relevant
    reranked = sorted(zip(retrieved_docs, scores), key=lambda x: x[1], reverse=True)[:3]
    top_docs = [d for d, _ in reranked]

    # 6) CPU extractive reader (accurate, small)
    # qa_model_name = "deepset/roberta-base-squad2"
    qa_model_name = "deepset/roberta-base-squad2"
    qa_tok = AutoTokenizer.from_pretrained(qa_model_name)
    qa_model = AutoModelForQuestionAnswering.from_pretrained(qa_model_name)
    qa = pipeline("question-answering", model=qa_model, tokenizer=qa_tok, device=-1)

    # roberta-base-squad2 has 512-token limit; reserve ~112 for question + special tokens
    MAX_CTX_TOKENS = 400

    best = {"answer": "", "score": -1.0, "source_idx": -1}
    per_doc_answers: List[Tuple[int, str, float]] = []

    for i, doc in enumerate(top_docs, start=1):
        ctx = truncate_to_tokens(doc.page_content, qa_tok, MAX_CTX_TOKENS)
        qa_input = {"question": query, "context": ctx}
        out = qa(qa_input)
        per_doc_answers.append((i, out["answer"], float(out.get("score", 0.0))))
        if out.get("score", 0.0) > best["score"]:
            best = {"answer": out["answer"], "score": float(out["score"]), "source_idx": i}

    # 7) Print result + citations
    print("\n=== FINAL ANSWER (extractive) ===")
    if best["score"] <= 0:
        print("Sorry, I couldn’t find a grounded answer in your indexed documents.")
    else:
        print(best["answer"])
        print(f"(confidence ~ {best['score']:.2f}, from Source {best['source_idx']})")

    print("\n=== CITATIONS ===")
    for i, doc in enumerate(top_docs, start=1):
        print(f"Source {i}: {pretty_src(doc.metadata)}")
        snippet = doc.page_content[:200].replace("\n", " ")
        print(f"  Snippet: {snippet}...")
    print()

    # Optional: show per-source scores
    print("Per-source reader scores:")
    for i, ans, sc in per_doc_answers:
        print(f"  Source {i}: score={sc:.3f}, answer='{ans}'")

if __name__ == "__main__":
    main()
