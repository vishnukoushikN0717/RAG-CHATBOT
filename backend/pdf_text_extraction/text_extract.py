from pypdf import PdfReader
import os
import json

# Path to PDFs
pdf_folder = "pdfs"

# Output file
output_file = "text_extracted.json"


# Store extracted data
extracted_data = []

# Loop through all PDFs
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(pdf_folder, filename)
        print(f"Processing: {filename}")
        
        # Read PDF
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        
        # Extract text page by page
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            text = page.extract_text()
            
            if text:  # Only if text is found
                extracted_data.append({
                    "doc_id": filename,
                    "page_number": page_num + 1,
                    "content": text.strip()
                })

# Save as JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(extracted_data, f, indent=4, ensure_ascii=False)

print(f"\n✅ Extraction completed! Saved to {output_file}")
