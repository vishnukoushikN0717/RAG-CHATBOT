import os
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from transformers import pipeline

def main():
    # Step 1: Reload embeddings (Hugging Face model for embeddings)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Load FAISS index (make sure this path matches your index)
    vectorstore = FAISS.load_local("embeddings/faiss_index", embeddings, allow_dangerous_deserialization=True)

    # Step 2: Ask query from terminal
    query = input("Enter your query: ")

    # Step 3: Retrieve top-3 chunks
    results = vectorstore.similarity_search(query, k=3)

    context = "\n\n".join([doc.page_content for doc in results])
    citations = [doc.metadata for doc in results]

    # Step 4: Hugging Face LLM (you can change to mistral/falcon/llama2 etc.)
    llm = pipeline(
        "text-generation",
        model="tiiuae/falcon-7b-instruct",   # <--- change model if needed
        device_map="auto",
        max_new_tokens=300
    )

    # Step 5: Create a RAG-style prompt
    prompt = f"""You are a helpful assistant.
Use the following context to answer the question.
If the answer is not found in the context, say you don't know.

Context:
{context}

Question: {query}

Answer:"""

    # Step 6: Generate answer
    response = llm(prompt, max_new_tokens=300, do_sample=True, temperature=0.3)

    print("\n=== Final Answer ===")
    print(response[0]["generated_text"].split("Answer:")[-1].strip())

    print("\n=== Sources ===")
    for idx, src in enumerate(citations, 1):
        print(f"Source {idx}: {src}")

if __name__ == "__main__":
    main()
