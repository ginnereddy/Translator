import pdfplumber
import fitz  # PyMuPDF
import requests
from PIL import Image
import pytesseract
from docx import Document

# Claude 4 (Bedrock) API call template
# You must fill in your API endpoint and key
BEDROCK_API_URL = "https://bedrock.us-east-2.amazonaws.com"  # Replace with actual endpoint
BEDROCK_API_KEY = "your_api_key"  # Replace with your API key

# Translate text using Claude 4 (Bedrock)
def translate_text_claude(text):
    headers = {
        "Authorization": f"Bearer {BEDROCK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": f"Translate the following to English, keep formatting:\n{text}"
    }
    response = requests.post(BEDROCK_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get("completion", "")
    else:
        print(f"Translation error: {response.text}")
        return text

# Extract images, OCR text, translate, and reconstruct PDF
def process_pdf_with_ocr(input_pdf, output_pdf, max_pages=10):
    with pdfplumber.open(input_pdf) as pdf:
        doc = fitz.open()
        for i, page in enumerate(pdf.pages, start=1):
            # Convert PDF page to image for OCR
            page_image = page.to_image(resolution=300)
            pil_img = page_image.original
            ocr_text = pytesseract.image_to_string(pil_img)
            translated_text = translate_text_claude(ocr_text if ocr_text else "")
            # Create new page with same size
            width, height = page.width, page.height
            new_page = doc.new_page(width=width, height=height)
            # Place translated text at top left (customize for layout)
            new_page.insert_text((50, 50), translated_text, fontsize=12)
            # Extract and place images
            for img in page.images:
                img_obj = pdf.pages[i-1].extract_image(img["object_id"])
                img_bytes = img_obj["image"]
                rect = fitz.Rect(img["x0"], img["top"], img["x1"], img["bottom"])
                new_page.insert_image(rect, stream=img_bytes)
            if i == max_pages:
                break
        doc.save(output_pdf)
        print(f"Processed PDF with OCR saved to {output_pdf}")

def extract_pdf_text_to_doc(pdf_path, doc_path, max_pages=10):
    doc = Document()
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            doc.add_heading(f"Page {i}", level=2)
            doc.add_paragraph(text if text else "[No text found]")
            if i == max_pages:
                break
    doc.save(doc_path)
    print(f"Extracted text saved to {doc_path}")

if __name__ == "__main__":
    input_pdf = "Alakkode Thampuran New_correctio_12-6-2025.pdf"
    output_pdf = "translated_output.pdf"
    process_pdf_with_ocr(input_pdf, output_pdf)
    pdf_path = "Alakkode Thampuran New_correctio_12-6-2025.pdf"  # Replace with your PDF file path
    doc_path = "extracted_text.docx"  # Output DOC file
    extract_pdf_text_to_doc(pdf_path, doc_path)