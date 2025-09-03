from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from transformers import pipeline

# --- FastAPI setup ---
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific frontend domain if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Input schema ---
class QueryRequest(BaseModel):
    query: str

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
            "bye": "Goodbye! Have a great day!",
            "good morning": "Good morning! ☀️",
            "good night": "Good night! 🌙",
            "how are you": "I’m doing great, thanks for asking! How about you?",
        }
        return responses.get(query.lower().strip(), "Hello! 👋")
    return None  # Not small talk

# --- RAG setup ---
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-MiniLM-L3-v2")

vectorstore = FAISS.load_local(
    "embeddings_forqa_huggingface/faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

llm = pipeline(
    "text2text-generation",
    model="google/flan-t5-small",
    device=-1  # CPU, change to 0 if GPU available
)

# --- API endpoint ---
@app.post("/query")
async def query(request: QueryRequest):
    try:
        user_query = request.query

        # ✅ Small talk first
        small_talk_answer = chatbot_response(user_query)
        if small_talk_answer:
            return {"answer": small_talk_answer}

        # --- Otherwise run RAG ---
        results = vectorstore.similarity_search(user_query, k=3)
        context = "\n\n".join([doc.page_content for doc in results])
        citations = [
            doc.metadata.get("source", "Unknown") if isinstance(doc.metadata, dict) else str(doc.metadata)
            for doc in results
        ]

        prompt = f"""
        Answer the following question using only the context below.
        If the answer is not in the context, say you don't know.

        Context: {context}

        Question: {user_query}

        Answer:
        """

        response = llm(prompt, max_new_tokens=300)
        final_answer = response[0]["generated_text"].strip()

        return {"answer": final_answer}

    except Exception as e:
        return {"answer": f"⚠️ Error: {str(e)}", "sources": []}

# --- Run server (port 5000) ---
# Run with: uvicorn app:app --host 0.0.0.0 --port 5000 --reload
