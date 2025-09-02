from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import os
import json

# Update this with your Poppler bin path
POPPLER_PATH = r"C:\poppler\poppler-25.07.0\Library\bin"

# Path to Tesseract (only for Windows users, update this if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Input folders
pdf_folder = "pdfs"       # contains PDFs
image_folder = "images"   # optional: contains standalone images (jpg/png)

# Output folder
output_folder = "extracted_ocr_jsons"
os.makedirs(output_folder, exist_ok=True)

def extract_from_pdf(pdf_path, filename):
    """Extract text from PDF (both text-based and scanned)"""
    extracted_data = []
    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)

    for page_num in range(num_pages):
        page = reader.pages[page_num]
        text = page.extract_text()

        if text and text.strip():  # if text layer exists
            extracted_data.append({
                "doc_id": filename,
                "page_number": page_num + 1,
                "content": text.strip()
            })
        else:
            # OCR fallback
            print(f"⚡ OCR needed for {filename} (Page {page_num+1})")
            images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1,poppler_path=POPPLER_PATH)
            for img in images:
                ocr_text = pytesseract.image_to_string(img)
                if ocr_text.strip():
                    extracted_data.append({
                        "doc_id": filename,
                        "page_number": page_num + 1,
                        "content": ocr_text.strip()
                    })

    return extracted_data

def extract_from_image(image_path, filename):
    """Extract text from standalone images"""
    extracted_data = []
    img = Image.open(image_path)
    ocr_text = pytesseract.image_to_string(img)

    if ocr_text.strip():
        extracted_data.append({
            "doc_id": filename,
            "page_number": 1,
            "content": ocr_text.strip()
        })

    return extracted_data

# Process PDFs
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(pdf_folder, filename)
        print(f"Processing PDF: {filename}")
        extracted_data = extract_from_pdf(pdf_path, filename)

        # Save per PDF
        output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=4, ensure_ascii=False)

        print(f"✅ Saved to {output_file}")


    
# Process Images
if os.path.exists(image_folder):
    for filename in os.listdir(image_folder):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(image_folder, filename)
            print(f"Processing Image: {filename}")
            extracted_data = extract_from_image(img_path, filename)

            output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=4, ensure_ascii=False)

            print(f"✅ Saved to {output_file}")

print("\n🎉 All PDFs & Images processed with OCR where needed!")
