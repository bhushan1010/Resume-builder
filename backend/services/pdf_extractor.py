import os
import re
import base64
import logging
from typing import Tuple

import fitz  # PyMuPDF
from fastapi import HTTPException

from services.gemini import call_gemini_with_retry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants (configurable via env vars)
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_PDF_SIZE_BYTES", str(5 * 1024 * 1024)))  # 5MB
MAX_PAGES = int(os.getenv("MAX_RESUME_PAGES", "3"))
MIN_TEXT_LENGTH = int(os.getenv("MIN_PDF_TEXT_LENGTH", "200"))   # threshold for clean extraction
VISION_DPI = int(os.getenv("VISION_DPI", "150"))                  # for page rendering


def validate_pdf(pdf_bytes: bytes) -> None:
    """
    Validate PDF file size and format.
    Raises HTTPException if validation fails.
    """
    if len(pdf_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
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
    doc = None
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Check if encrypted/password protected
        if doc.is_encrypted:
            return ("", True)

        # Extract text from first MAX_PAGES pages only
        text_parts = []
        pages_processed = min(len(doc), MAX_PAGES)
        for i in range(pages_processed):
            page = doc[i]
            text_parts.append(page.get_text("text"))

        return ("\n".join(text_parts).strip(), False)

    except Exception as e:
        logger.error(f"PyMuPDF extraction failed: {e}", exc_info=True)
        return ("", False)
    finally:
        # FIXED: always close the document to free native resources
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass


def pdf_pages_to_base64(pdf_bytes: bytes) -> list[str]:
    """
    Convert PDF pages to base64 PNG images for vision API.
    """
    doc = None
    images = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_to_process = min(len(doc), MAX_PAGES)

        for i in range(pages_to_process):
            page = doc[i]
            mat = fitz.Matrix(VISION_DPI / 72, VISION_DPI / 72)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            images.append(b64)

        return images
    finally:
        # FIXED: always close the document
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass


def extract_text_via_vision(pdf_bytes: bytes) -> str:
    """
    Use Gemini Vision to OCR the PDF pages.
    """
    images = pdf_pages_to_base64(pdf_bytes)

    # Build content list for Gemini multimodal call
    # NOTE: This format works with the older google-generativeai SDK shape.
    # If you migrate fully to google-genai (types.Part.from_bytes), update here.
    content = []
    for b64_img in images:
        content.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": b64_img
            }
        })
    content.append({
        "text": (
            "Extract all text from this resume image exactly as it appears. "
            "Preserve the structure — section headers, bullet points, dates, "
            "company names. Return only the extracted text, no commentary."
        )
    })

    response = call_gemini_with_retry(content)
    return response.text.strip()


def assess_extraction_quality(text: str) -> dict:
    """
    Analyze extracted text and return confidence assessment.
    """
    word_count = len(text.split())
    line_count = len([l for l in text.splitlines() if l.strip()])

    # FIXED: detect *actual* encoding failures (replacement char / nulls)
    # rather than flagging every non-ASCII character (which broke for
    # accented names, smart quotes, non-English resumes, etc.)
    has_encoding_issues = bool(re.search(r'[\ufffd\x00]+', text))

    # Additional heuristic: high ratio of non-printable / control chars
    if not has_encoding_issues and text:
        unprintable_count = sum(
            1 for c in text if not (c.isprintable() or c.isspace())
        )
        unprintable_ratio = unprintable_count / max(len(text), 1)
        if unprintable_ratio > 0.05:
            has_encoding_issues = True

    avg_line_length = len(text) / max(line_count, 1)
    very_short_lines = sum(
        1 for l in text.splitlines() if 0 < len(l.strip()) < 4
    )
    short_line_ratio = very_short_lines / max(line_count, 1)

    # Determine confidence
    issues = []
    if word_count < 50:
        issues.append("very_short")
    if has_encoding_issues:
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
        logger.info("PDF is password protected — cannot extract.")
        return {
            "text": "",
            "method": "failed",
            "confidence": "low",
            "confidence_label": "Password protected",
            "is_password_protected": True,
            "fallback_required": True,
            "fallback_message": (
                "This PDF is password protected. "
                "Please remove the password and try again, "
                "or paste your resume text manually."
            )
        }

    # Step 4: Check if PyMuPDF got good text
    if len(text) >= MIN_TEXT_LENGTH:
        quality = assess_extraction_quality(text)

        if quality["confidence"] != "low":
            logger.info(
                f"PyMuPDF extraction succeeded "
                f"(confidence={quality['confidence']}, words={quality['word_count']})"
            )
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
        logger.info(
            f"PyMuPDF returned low-confidence text — falling back to Gemini Vision. "
            f"Issues: {quality['issues']}"
        )
    else:
        logger.info(
            f"PyMuPDF returned only {len(text)} chars (< {MIN_TEXT_LENGTH}). "
            "Falling back to Gemini Vision."
        )

    # Step 5: Try Gemini Vision
    try:
        vision_text = extract_text_via_vision(pdf_bytes)
        quality = assess_extraction_quality(vision_text)

        if quality["word_count"] >= 30:
            logger.info(
                f"Gemini Vision extraction succeeded "
                f"(confidence={quality['confidence']}, words={quality['word_count']})"
            )
            return {
                "text": vision_text,
                "method": "vision",
                "confidence": quality["confidence"],
                "confidence_label": quality["label"],
                "is_password_protected": False,
                "fallback_required": False,
                "fallback_message": None
            }
        else:
            logger.warning(
                f"Gemini Vision returned only {quality['word_count']} words — "
                "treating as failed extraction."
            )
    except Exception as e:
        logger.error(f"Gemini Vision extraction failed: {e}", exc_info=True)

    # Step 6: Both methods failed
    logger.warning("Both PyMuPDF and Gemini Vision failed to extract usable text.")
    return {
        "text": "",
        "method": "failed",
        "confidence": "low",
        "confidence_label": "Extraction failed",
        "is_password_protected": False,
        "fallback_required": True,
        "fallback_message": (
            "We couldn't read this PDF clearly. "
            "Please paste your resume text manually."
        )
    }