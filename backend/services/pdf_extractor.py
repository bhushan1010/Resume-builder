import fitz  # PyMuPDF
import base64
import json
import re
from typing import Tuple
from fastapi import HTTPException
from .gemini import call_gemini_with_retry

# Constants
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024   # 5MB
MAX_PAGES = 2
MIN_TEXT_LENGTH = 200   # threshold for clean extraction
VISION_DPI = 150        # for page rendering


def validate_pdf(pdf_bytes: bytes) -> None:
    """
    Validate PDF file size and format.
    Raises HTTPException if validation fails.
    """
    if len(pdf_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 5MB."
        )
    
    # Check if it's a valid PDF by looking for PDF header
    if len(pdf_bytes) < 4 or pdf_bytes[:4] != b'%PDF':
        raise HTTPException(
            status_code=400,
            detail="Invalid file. Please upload a PDF."
        )


def extract_text_pymupdf(pdf_bytes: bytes) -> Tuple[str, bool]:
    """
    Extract text from PDF using PyMuPDF.
    Returns (extracted_text, is_password_protected).
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Check if encrypted/password protected
        if doc.is_encrypted:
            return ("", True)
        
        # Extract text from first MAX_PAGES pages only
        text = ""
        pages_processed = min(len(doc), MAX_PAGES)
        for i in range(pages_processed):
            page = doc[i]
            text += page.get_text("text") + "\n"
        
        return (text.strip(), False)
    
    except Exception:
        return ("", False)


def pdf_pages_to_base64(pdf_bytes: bytes) -> list[str]:
    """
    Convert PDF pages to base64 PNG images for vision API.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    pages_to_process = min(len(doc), MAX_PAGES)
    
    for i in range(pages_to_process):
        page = doc[i]
        mat = fitz.Matrix(VISION_DPI/72, VISION_DPI/72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        images.append(b64)
    
    return images


def extract_text_via_vision(pdf_bytes: bytes) -> str:
    """
    Use Gemini Vision to OCR the PDF pages.
    """
    images = pdf_pages_to_base64(pdf_bytes)
    
    # Build content list for Gemini multimodal call
    content = []
    for b64_img in images:
        content.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": b64_img
            }
        })
    content.append({
        "text": """Extract all text from this resume image exactly 
        as it appears. Preserve the structure — section headers, 
        bullet points, dates, company names. Return only the 
        extracted text, no commentary."""
    })
    
    response = call_gemini_with_retry(content)
    return response.text.strip()


def assess_extraction_quality(text: str) -> dict:
    """
    Analyze extracted text and return confidence assessment.
    """
    word_count = len(text.split())
    line_count = len([l for l in text.splitlines() if l.strip()])
    
    # Garbled text signals
    has_weird_chars = bool(re.search(r'[^\x00-\x7F]{10,}', text))
    avg_line_length = len(text) / max(line_count, 1)
    very_short_lines = sum(1 for l in text.splitlines() 
                         if 0 < len(l.strip()) < 4)
    short_line_ratio = very_short_lines / max(line_count, 1)
    
    # Determine confidence
    issues = []
    if word_count < 50:
        issues.append("very_short")
    if has_weird_chars:
        issues.append("encoding_issues")
    if short_line_ratio > 0.4:
        issues.append("fragmented_lines")  # typical of two-column PDFs
    if avg_line_length < 15:
        issues.append("column_layout_detected")
    
    if len(issues) == 0:
        confidence = "high"
        label = "Clean extraction"
    elif len(issues) == 1:
        confidence = "medium"
        label = "Complex layout detected"
    else:
        confidence = "low"
        label = "Extraction may be incomplete"
    
    return {
        "confidence": confidence,   # "high" | "medium" | "low"
        "label": label,
        "word_count": word_count,
        "issues": issues
    }


def extract_resume_from_pdf(pdf_bytes: bytes) -> dict:
    """
    Main entry point for PDF resume extraction.
    Returns extraction result dictionary.
    """
    # Step 1: Validate
    validate_pdf(pdf_bytes)
    
    # Step 2: Try PyMuPDF
    text, is_protected = extract_text_pymupdf(pdf_bytes)
    
    # Step 3: Handle password protected
    if is_protected:
        return {
            "text": "",
            "method": "failed",
            "confidence": "low",
            "confidence_label": "Password protected",
            "is_password_protected": True,
            "fallback_required": True,
            "fallback_message": "This PDF is password protected. "
                              "Please remove the password and try again, "
                              "or paste your resume text manually."
        }
    
    # Step 4: Check if PyMuPDF got good text
    if len(text) >= MIN_TEXT_LENGTH:
        quality = assess_extraction_quality(text)
        
        if quality["confidence"] != "low":
            return {
                "text": text,
                "method": "pymupdf",
                "confidence": quality["confidence"],
                "confidence_label": quality["label"],
                "is_password_protected": False,
                "fallback_required": False,
                "fallback_message": None
            }
        # else: fall through to vision
    
    # Step 5: Try Gemini Vision
    try:
        vision_text = extract_text_via_vision(pdf_bytes)
        quality = assess_extraction_quality(vision_text)
        
        if quality["word_count"] >= 30:
            return {
                "text": vision_text,
                "method": "vision",
                "confidence": quality["confidence"],
                "confidence_label": quality["label"],
                "is_password_protected": False,
                "fallback_required": False,
                "fallback_message": None
            }
    except Exception:
        pass
    
    # Step 6: Both methods failed
    return {
        "text": "",
        "method": "failed",
        "confidence": "low",
        "confidence_label": "Extraction failed",
        "is_password_protected": False,
        "fallback_required": True,
        "fallback_message": "We couldn't read this PDF clearly. "
                          "Please paste your resume text manually."
    }