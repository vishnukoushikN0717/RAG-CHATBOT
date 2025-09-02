from pypdf import PdfReader
import os
import json

# Input and output folders
pdf_folder = "pdfs"
output_folder = "seperate_jsons"

# Create output folder if not exists
os.makedirs(output_folder, exist_ok=True)

# Loop through all PDFs
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(pdf_folder, filename)
        print(f"Processing: {filename}")
        
        # Read PDF
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        
        # Store extracted data for this PDF
        extracted_data = []
        
        # Extract text page by page
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            text = page.extract_text()
            
            if text:
                extracted_data.append({
                    "doc_id": filename,
                    "page_number": page_num + 1,
                    "content": text.strip()
                })
        
        # Save JSON for this PDF
        output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Saved extracted text to {output_file}")

print("\n🎉 All PDFs processed!")
