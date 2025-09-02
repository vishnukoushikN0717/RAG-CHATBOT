import os
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from transformers import pipeline


def main():
    # Step 1: Reload embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/multi-qa-mpnet-base-dot-v1")
    vectorstore = FAISS.load_local("embeddings_forqa_huggingface/faiss_index", embeddings, allow_dangerous_deserialization=True)

    # Step 2: Ask query from terminal
    query = input("Enter your query: ")

    # Step 3: Retrieve top-3 chunks
    results = vectorstore.similarity_search(query, k=3)

    context = "\n\n".join([doc.page_content for doc in results])
    citations = [doc.metadata for doc in results]

    # Step 4: Load a lightweight Hugging Face LLM (runs fine on CPU)
    llm = pipeline(
        "text2text-generation",
        model="google/flan-t5-base",   # 👈 small model, fast on CPU
        device=-1                     # force CPU
    )

    # Step 5: Create a RAG-style prompt
    prompt = f"""Answer the following question using only the context below.
If the answer is not in the context, say you don't know.

Context:
{context}

Question: {query}

Answer:"""

    # Step 6: Generate answer
    response = llm(prompt, max_new_tokens=300)

    print("\n=== Final Answer ===")
    print(response[0]["generated_text"].strip())

    print("\n=== Sources ===")
    for idx, src in enumerate(citations, 1):
        print(f"Source {idx}: {src}")

if __name__ == "__main__":
    main()
