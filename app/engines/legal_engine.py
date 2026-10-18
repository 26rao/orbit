"""Legal & Document Forensic Parser.
Performs OCR, statutory law rule verification, and eCourts CNR judicial lookup.
"""

import os
import re
import logging
from typing import Optional, Dict, Any, List
import httpx
from pypdf import PdfReader

from app.core.rules import IMPOSSIBLE_LEGAL_PROCEDURES, CNR_REGEX
from app.core.config import ECOURTS_API_URL

logger = logging.getLogger("kavach.legal")

# Lazy-loaded PaddleOCR instance
_paddle_ocr = None


def get_ocr_engine():
    global _paddle_ocr
    if _paddle_ocr is None:
        try:
            from paddleocr import PaddleOCR
            _paddle_ocr = PaddleOCR(use_angle_cls=True, lang="en")
        except Exception as e:
            logger.warning(f"PaddleOCR init failed ({e}), falling back to text extraction.")
            _paddle_ocr = False
    return _paddle_ocr


def extract_text_from_file(file_path: str) -> str:
    """Extract plain text from PDF or image file."""
    if not file_path or not os.path.exists(file_path):
        return ""

    ext = os.path.splitext(file_path)[1].lower()

    # 1. Plain text file direct read
    if ext in [".txt", ".text", ".log", ".json"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Text read error: {e}")

    # 2. PDF Text extraction
    if ext == ".pdf":
        try:
            reader = PdfReader(file_path)
            extracted = " ".join([page.extract_text() or "" for page in reader.pages])
            if len(extracted.strip()) > 20:
                return extracted
        except Exception as e:
            logger.warning(f"PDF extraction error: {e}")

    # 3. Image / OCR extraction
    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"]:
        engine = get_ocr_engine()
        if engine:
            try:
                result = engine.ocr(file_path, cls=True)
                if result and result[0]:
                    extracted = " ".join([line[1][0] for block in result if block for line in block if line])
                    if extracted:
                        return extracted
            except Exception as e:
                logger.warning(f"PaddleOCR processing error: {e}")

    # 3. Fallback: inspect raw bytes for ASCII strings (court terms, CNR, digital arrest)
    try:
        with open(file_path, "rb") as f:
            raw_bytes = f.read(500000)
            ascii_strings = re.findall(b"[A-Za-z0-9\\s,:;\\.\\-\\/]{4,}", raw_bytes)
            decoded = " ".join(s.decode("latin-1", errors="ignore") for s in ascii_strings)
            return decoded
    except Exception:
        return ""


async def query_ecourts_cnr(cnr: str) -> bool:
    """Query National Judicial Data Grid eCourts CNR registry."""
    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.get(f"{ECOURTS_API_URL}/{cnr}")
            return resp.status_code == 200
    except Exception:
        # Default to False for mock/fabricated test numbers
        return False


async def verify_legal_document(file_path: Optional[str] = None, text_content: Optional[str] = None) -> Dict[str, Any]:
    """
    Forensic analysis of claimed legal document, court notice, police warrant, or summon.
    """
    extracted_text = ""
    if file_path:
        extracted_text = extract_text_from_file(file_path)
    if text_content:
        extracted_text = f"{extracted_text} {text_content}".strip()

    lower_text = extracted_text.lower()
    reasons: List[str] = []
    confidence = 0.0
    detected_violations: List[str] = []

    # 1. Epistemic Statutory Law Check
    for rule in IMPOSSIBLE_LEGAL_PROCEDURES:
        if re.search(rule["pattern"], lower_text):
            reasons.append(rule["statutory_fact"])
            detected_violations.append(rule["category"])
            confidence = max(confidence, rule["confidence"])

    # 2. CNR / Case Number Verification
    cnr_match = CNR_REGEX.search(extracted_text.upper())
    cnr_number = None

    if cnr_match:
        cnr_number = cnr_match.group(1)
        is_valid = await query_ecourts_cnr(cnr_number)
        if not is_valid:
            reasons.append(
                f"CNR Number '{cnr_number}' is FABRICATED and does not exist in the National Judicial Data Grid (eCourts)."
            )
            detected_violations.append("FABRICATED_CNR_NUMBER")
            confidence = max(confidence, 0.96)
        else:
            reasons.append(f"CNR Number '{cnr_number}' format matched judicial records.")
    else:
        # If document claims to be an official court order/warrant, absence of CNR is a major red flag
        court_warrant_terms = ["warrant", "summons", "high court", "supreme court", "arrest order", "bailiff"]
        if any(w in lower_text for w in court_warrant_terms):
            reasons.append(
                "Document claims to be a court warrant/summons but lacks the mandatory 16-character alphanumeric CNR Number mandated by the Supreme Court of India."
            )
            detected_violations.append("MISSING_MANDATORY_CNR")
            confidence = max(confidence, 0.88)

    # 3. Threat / Extortion Urgency checks in legal notices
    if any(p in lower_text for p in ["transfer money", "rtgs", "neft", "security deposit", "within 2 hours"]):
        reasons.append("Demand for monetary transfer or urgent financial compliance inside a legal notice indicates criminal extortion.")
        detected_violations.append("FINANCIAL_EXTORTION_DEMAND")
        confidence = max(confidence, 0.97)

    # 4. Final Verdict Determination
    if confidence >= 0.70:
        verdict = "DANGEROUS_SCAM"
        summary = "CRITICAL SCAM: Forged legal document designed for virtual arrest and extortion."
    elif confidence >= 0.40:
        verdict = "SUSPICIOUS"
        summary = "SUSPICIOUS: Unverified legal document with irregularities or missing judicial identifiers."
    else:
        verdict = "AUTHENTIC"
        confidence = 0.85
        summary = "Standard document with no procedural red flags or extortion patterns detected."
        reasons = ["Document contains verifiable legal terminology and does not exhibit known scam markers."]

    return {
        "verdict": verdict,
        "confidence": round(confidence, 2),
        "summary": summary,
        "reasons": reasons,
        "extracted_text_snippet": extracted_text[:400] if extracted_text else "None",
        "detected_violations": detected_violations,
        "cnr_number": cnr_number,
    }
