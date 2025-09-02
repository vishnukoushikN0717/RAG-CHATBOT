import os
import json
import re
from sentence_transformers import SentenceTransformer, util
import nltk
from nltk.tokenize import sent_tokenize

# Download NLTK punkt tokenizer if not already
nltk.download("punkt")
nltk.download('punkt_tab')

# Configs
CHUNK_WORDS = 500
MIN_WORDS_TO_KEEP_LAST = 50
SIMILARITY_THRESHOLD = 0.75  # tweakable

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def semantic_chunk_text(text):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for i, sentence in enumerate(sentences):
        words = sentence.split()
        if current_length + len(words) <= CHUNK_WORDS:
            current_chunk.append(sentence)
            current_length += len(words)
        else:
            # Check semantic overlap with next sentence
            overlap = []
            if i < len(sentences) - 1:
                last_sent_emb = model.encode(current_chunk[-1], convert_to_tensor=True)
                next_sent_emb = model.encode(sentences[i], convert_to_tensor=True)
                similarity = util.pytorch_cos_sim(last_sent_emb, next_sent_emb).item()

                if similarity >= SIMILARITY_THRESHOLD:
                    overlap.append(current_chunk[-1])  # keep last semantically close sentence

            # Save current chunk
            chunk_text = " ".join(current_chunk)
            if len(chunk_text.split()) >= MIN_WORDS_TO_KEEP_LAST:
                chunks.append(chunk_text)

            # Start new chunk
            current_chunk = overlap + [sentence]
            current_length = sum(len(s.split()) for s in current_chunk)

    # Add final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        if len(chunk_text.split()) >= MIN_WORDS_TO_KEEP_LAST:
            chunks.append(chunk_text)

    return chunks

def process_pdf_texts(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".json"):  # using the jsons you created earlier
            file_path = os.path.join(input_folder, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):  
                text = clean_text(" ".join(page.get("content", "") for page in data)) 
            elif isinstance(data, dict):  
                text = clean_text(data.get("content", data.get("text", "")))
            else:  
                text = ""
            chunks = semantic_chunk_text(text)

            output_data = {"file": file_name, "chunks": chunks}
            output_file = os.path.join(output_folder, file_name)
            with open(output_file, "w", encoding="utf-8") as out:
                json.dump(output_data, out, indent=4, ensure_ascii=False)

            print(f"✅ Processed {file_name} into {len(chunks)} semantic chunks")

# Example usage
if __name__ == "__main__":
    input_folder = "extracted_ocr_jsons"      # folder from text extraction step
    output_folder = "chunks_500words_using_semantic"
    process_pdf_texts(input_folder, output_folder)
