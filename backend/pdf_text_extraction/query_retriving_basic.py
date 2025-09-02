import os
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

# Step 1: Reload embeddings (using Hugging Face model)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Load FAISS index you already created
vectorstore = FAISS.load_local("embeddings/faiss_index", embeddings, allow_dangerous_deserialization=True)

# Step 2: Run a semantic search
# query = "What does the Missouri Department of Health say about water sampling?"
query=input("Enter your query: ")
results = vectorstore.similarity_search(query, k=3)

# Step 3: Print retrieved chunks + sources
for idx, doc in enumerate(results):
    print(f"🔹 Result {idx+1}")
    print("Text:", doc.page_content[:300], "...")
    print("Source:", doc.metadata)
    print()
