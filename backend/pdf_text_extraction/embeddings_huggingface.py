import os
import json
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# ===============================
# CONFIG
# ===============================
CHUNKS_DIR = "chunks_500words_using_semantic"
OUTPUT_DIR = "embeddings_forqa_huggingface"
INDEX_PATH = os.path.join(OUTPUT_DIR, "faiss_index")
METADATA_FILE = os.path.join(OUTPUT_DIR, "metadata.json")

# Use a local Hugging Face embedding model
# MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2" # small + fast
MODEL_NAME = "sentence-transformers/multi-qa-mpnet-base-dot-v1" # better for Q&A tasks
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)

# ===============================
# LOAD CHUNKS
# ===============================
def load_chunks():
    texts, metadatas = [], []
    for filename in os.listdir(CHUNKS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(CHUNKS_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                file_name = data.get("file", filename)
                for idx, chunk in enumerate(data.get("chunks", [])):
                    if chunk.strip():
                        texts.append(chunk.strip())
                        metadatas.append({
                            "source": file_name,
                            "chunk_id": idx,
                            "model": MODEL_NAME
                        })
    return texts, metadatas

# ===============================
# CREATE EMBEDDINGS
# ===============================
def create_embeddings():
    texts, metadatas = load_chunks()
    print(f"✅ Loaded {len(texts)} chunks from {CHUNKS_DIR}")

    # Create FAISS vector store
    vectorstore = FAISS.from_texts(
        texts,
        embeddings,
        metadatas=metadatas
    )

    # Save FAISS index locally
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    vectorstore.save_local(INDEX_PATH)
    print(f"✅ FAISS index saved at {INDEX_PATH}")

    # Save metadata
    meta = {
        "model": MODEL_NAME,
        "num_chunks": len(texts),
        "index_path": INDEX_PATH
    }
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"✅ Metadata saved at {METADATA_FILE}")

if __name__ == "__main__":
    create_embeddings()
