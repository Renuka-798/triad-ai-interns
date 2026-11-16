import io
import os

# import fitz  # PyMuPDF
import pymupdf
import pytesseract
from PIL import Image


# Configure the Tesseract executable on Windows
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text(file_bytes, filename):
    """
    Extract text from PDF and image files.

    For PDFs:
    1. Extract existing selectable text.
    2. If a page has no selectable text, use OCR.

    For images:
    Use Tesseract OCR directly.
    """

    extension = os.path.splitext(filename)[1].lower()

    try:

        # PDF processing
        if extension == ".pdf":

            pdf_document = pymupdf.open(
                stream=file_bytes,
                filetype="pdf"
            )

            extracted_pages = []

            for page_number, page in enumerate(pdf_document):

                # First try normal PDF text extraction
                page_text = page.get_text().strip()

                # If no selectable text exists, perform OCR
                if not page_text:

                    pix = page.get_pixmap(
                        matrix=pymupdf.Matrix(2, 2),
                        alpha=False
                    )

                    image = Image.open(
                        io.BytesIO(pix.tobytes("png"))
                    )

                    page_text = pytesseract.image_to_string(
                        image,
                        lang="eng"
                    ).strip()

                extracted_pages.append(page_text)

            pdf_document.close()

            return "\n".join(extracted_pages).strip()

        # Image processing
        elif extension in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"]:

            image = Image.open(
                io.BytesIO(file_bytes)
            )

            extracted_text = pytesseract.image_to_string(
                image,
                lang="eng"
            )

            return extracted_text.strip()

        else:
            return ""

    except Exception as e:
        print("OCR Error:", str(e))
        return ""