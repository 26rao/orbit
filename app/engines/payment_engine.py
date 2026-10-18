"""Payment Intent & QR Auditor.
Detects UPI reverse-charge intent inversion, fraudulent QR codes, and VPA impersonation.
"""

import os
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs
from PIL import Image

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
except Exception:
    pyzbar_decode = None

try:
    import cv2
except Exception:
    cv2 = None

from app.core.rules import CONSUMER_VPA_HANDLES, OFFICIAL_IMPERSONATION_KEYWORDS


def extract_qr_string(file_path: str) -> Optional[str]:
    """Decode QR code string from image file using pyzbar or OpenCV."""
    if not file_path or not os.path.exists(file_path):
        return None

    # Method 1: pyzbar
    if pyzbar_decode:
        try:
            img = Image.open(file_path)
            decoded = pyzbar_decode(img)
            if decoded:
                return decoded[0].data.decode("utf-8")
        except Exception:
            pass

    # Method 2: OpenCV QR Detector
    if cv2:
        try:
            cv_img = cv2.imread(file_path)
            if cv_img is not None:
                detector = cv2.QRCodeDetector()
                val, _, _ = detector.detectAndDecode(cv_img)
                if val:
                    return val
        except Exception:
            pass

    return None


async def verify_payment_data(file_path: Optional[str] = None, text_data: Optional[str] = None) -> Dict[str, Any]:
    """
    Forensic analysis of payment QR codes, UPI URIs, and VPA requests.
    """
    payload_str = text_data or ""

    # If an image was supplied, extract QR payload
    if file_path:
        qr_text = extract_qr_string(file_path)
        if qr_text:
            payload_str = qr_text

    reasons: List[str] = []
    confidence = 0.0
    intent_inversion = False
    impersonation_detected = False

    vpa = ""
    payee_name = ""
    amount = None
    note = ""

    # Check for UPI Pay URI
    if payload_str.startswith("upi://pay") or "pa=" in payload_str:
        # Normalize into proper URI if needed
        clean_url = payload_str if payload_str.startswith("upi://") else f"upi://pay?{payload_str}"
        parsed = urlparse(clean_url)
        params = parse_qs(parsed.query)

        vpa = params.get("pa", [""])[0]
        payee_name = params.get("pn", [""])[0]
        amount = params.get("am", [None])[0]
        note = params.get("tn", [""])[0]

        # 1. Reverse-Charge / Intent Inversion Audit
        # Crucial Scam Vector: User thinks they are receiving money, but QR code DEBITS money
        reasons.append(
            "INTENT INVERSION: This QR Code / Link is hardcoded to DEBIT (withdraw) funds from your bank account. In Indian banking (NPCI UPI), you NEVER need to scan a QR code or enter your UPI PIN to receive money."
        )
        intent_inversion = True
        confidence = max(confidence, 0.95)

        # 2. Institutional Impersonation on Personal Consumer VPA
        vpa_lower = vpa.lower()
        name_lower = payee_name.lower()
        note_lower = note.lower()

        is_impersonating = any(
            k in vpa_lower or k in name_lower or k in note_lower
            for k in OFFICIAL_IMPERSONATION_KEYWORDS
        )
        is_consumer_handle = any(vpa_lower.endswith(f"@{h}") for h in CONSUMER_VPA_HANDLES)

        if is_impersonating and is_consumer_handle:
            impersonation_detected = True
            reasons.append(
                f"IMPERSONATION: The recipient name '{payee_name}' or note claims to represent an official authority (Police/Electricity/Tax/Refund), but the payment address '{vpa}' is a private personal consumer account on {vpa_lower.split('@')[-1].upper()}."
            )
            confidence = 0.99

        # 3. Transaction note deception
        if any(w in note_lower for w in ["refund", "cashback", "lottery", "kyc approved", "gift"]):
            reasons.append(
                f"Deceptive Transaction Note: '{note}' is designed to trick you into believing this is an incoming credit."
            )
            confidence = max(confidence, 0.98)

        verdict = "DANGEROUS_SCAM"
        summary = (
            f"FRAUDULENT PAYMENT REQUEST: Authorizing this will immediately transfer "
            f"{'₹' + amount if amount else 'funds'} to private account '{vpa}' ({payee_name or 'Scammer'})."
        )

        return {
            "verdict": verdict,
            "confidence": round(confidence, 2),
            "summary": summary,
            "reasons": reasons,
            "vpa": vpa,
            "payee_name": payee_name,
            "amount": amount,
            "transaction_note": note,
            "intent_inversion": intent_inversion,
            "intent_direction": "DEBIT",
            "impersonation_detected": impersonation_detected,
        }

    # If it's a standalone VPA string (e.g. cyber.police@okhdfcbank)
    vpa_match = re.search(r"\b([a-zA-Z0-9\.\-_]+@([a-zA-Z0-9]+))\b", payload_str)
    if vpa_match:
        vpa = vpa_match.group(1)
        vpa_lower = vpa.lower()
        if any(k in vpa_lower for k in OFFICIAL_IMPERSONATION_KEYWORDS) and any(vpa_lower.endswith(f"@{h}") for h in CONSUMER_VPA_HANDLES):
            return {
                "verdict": "DANGEROUS_SCAM",
                "confidence": 0.98,
                "summary": f"Scam VPA: '{vpa}' is a private consumer account impersonating public authorities.",
                "reasons": [
                    f"'{vpa}' uses official keywords on a personal consumer handle.",
                    "No legitimate government department uses consumer UPI handles for fees or penalties."
                ],
                "vpa": vpa,
                "payee_name": "Unknown",
                "amount": None,
                "intent_inversion": False,
                "impersonation_detected": True,
            }

    # Malformed or unrecognized payment data
    return {
        "verdict": "SUSPICIOUS",
        "confidence": 0.55,
        "summary": "Malformed or non-standard payment payload.",
        "reasons": [
            "The payment artifact could not be verified against official NPCI UPI specifications.",
            "Do not enter your UPI PIN on unverified payment requests."
        ],
        "vpa": vpa or "N/A",
        "payee_name": payee_name or "N/A",
        "amount": amount,
        "intent_inversion": False,
        "impersonation_detected": False,
    }
