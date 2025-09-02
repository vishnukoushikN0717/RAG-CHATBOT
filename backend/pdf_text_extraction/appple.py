from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import pipeline

# Flask setup
app = Flask(__name__)
CORS(app)

# --- Small talk handling ---
def is_small_talk(query: str) -> bool:
    small_talk_keywords = ["hi", "hello", "hey", "thanks", "bye", "good morning", "good night", "how are you"]
    return query.lower().strip() in small_talk_keywords

def chatbot_response(query: str):
    if is_small_talk(query):
        responses = {
            "hi": "Hello! How can I help you today?",
            "hello": "Hi there! 😊",
            "hey": "Hey! How’s it going?",
            "thanks": "You're welcome!",
            "bye": "Goodbye! Have a great day!"
        }
        return responses.get(query.lower().strip(), "Hello! 👋")
    return None   # if not small talk, return None so we run RAG

# --- RAG setup ---
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/multi-qa-mpnet-base-dot-v1")
vectorstore = FAISS.load_local(
    "embeddings_forqa_huggingface/faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

llm = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    device=-1
)

@app.route("/query", methods=["POST"])
def query():
    try:
        data = request.json
        user_query = data.get("query", "")

        # ✅ Check for small talk first
        small_talk_answer = chatbot_response(user_query)
        if small_talk_answer:
            return jsonify({"answer": small_talk_answer})

        # --- Otherwise run RAG ---
        results = vectorstore.similarity_search(user_query, k=3)

        context = "\n\n".join([doc.page_content for doc in results])
        citations = [doc.metadata.get("source", "Unknown") if isinstance(doc.metadata, dict) else str(doc.metadata) for doc in results]

        prompt = f"""Answer the following question using only the context below.
If the answer is not in the context, say you don't know.

Context:
{context}

Question: {user_query}

Answer:"""

        response = llm(prompt, max_new_tokens=300)
        final_answer = response[0]["generated_text"].strip()

        return jsonify({"answer": final_answer, "sources": citations})

    except Exception as e:
        return jsonify({"answer": f"⚠️ Error: {str(e)}", "sources": []})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
