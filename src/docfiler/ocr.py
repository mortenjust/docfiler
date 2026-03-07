"""PDF/A conversion, OCR, and text extraction."""

import os
import subprocess

import pikepdf
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

LANGUAGES = "eng+deu+dan"


def is_pdfa(filepath):
    """Check PDF/A status via XMP metadata."""
    try:
        pdf = pikepdf.open(filepath)
        xmp = pdf.open_metadata()
        part = xmp.get("{http://www.aiim.org/pdfa/ns/id/}part", "")
        return bool(part)
    except Exception:
        return False


def ensure_pdfa(filepath):
    """Convert PDF to PDF/A with OCR if not already. Returns the final path."""
    if is_pdfa(filepath):
        print("  Already PDF/A, skipping OCR.")
        return filepath

    print("  Converting to PDF/A with OCR...")
    tmp = filepath + ".pdfa.pdf"
    result = subprocess.run(
        ["ocrmypdf", "-l", LANGUAGES, "--rotate-pages", "--deskew",
         "--output-type", "pdfa", "--jobs", "4",
         "--skip-text", filepath, tmp],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ocrmypdf warning: {result.stderr.strip()}")
        if os.path.exists(tmp):
            os.remove(tmp)
        return filepath  # non-fatal, keep going

    os.replace(tmp, filepath)
    print("  PDF/A conversion done.")
    return filepath


def extract_pdf_text(filepath):
    """Extract text from the first page of a PDF."""
    return extract_text(filepath, page_numbers=[0], laparams=LAParams()).strip()


def ocr_image(filepath):
    """OCR an image file with tesseract."""
    result = subprocess.run(
        ["tesseract", "-l", LANGUAGES, filepath, "stdout"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def extract_text_from_file(filepath):
    """Extract text from any supported file. Returns (text, updated_filepath)."""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        filepath = ensure_pdfa(filepath)
        text = extract_pdf_text(filepath)
    elif ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"):
        text = ocr_image(filepath)
    elif ext in (".txt", ".html", ".htm", ".csv"):
        with open(filepath, "r", errors="replace") as f:
            text = f.read(5000)
    else:
        text = ""

    return text[:3000].strip(), filepath


SUPPORTED_EXT = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic",
    ".txt", ".html", ".htm", ".csv",
}
