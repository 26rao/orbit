"""Input Modality Classifier.
Routes incoming payload to:
- DOCUMENT: Court notices, warrants, police letters, FIRs (PDF / Document images)
- PAYMENT: QR codes, UPI links, payment intents
- MESSAGE_LINK_APK: SMS messages, WhatsApp forwards, phishing URLs, Android APKs
"""

import os
import re
from typing import Optional
from PIL import Image

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
except Exception:
    pyzbar_decode = None

try:
    import cv2
except Exception:
    cv2 = None


def is_qr_image(file_path: str) -> bool:
    """Check if the provided image contains a readable QR code."""
    try:
        # Method 1: pyzbar
        if pyzbar_decode:
            img = Image.open(file_path)
            decoded = pyzbar_decode(img)
            if decoded:
                return True

        # Method 2: OpenCV QR Detector
        if cv2:
            cv_img = cv2.imread(file_path)
            if cv_img is not None:
                detector = cv2.QRCodeDetector()
                val, _, _ = detector.detectAndDecode(cv_img)
                if val and len(val) > 0:
                    return True
    except Exception:
        pass
    return False


def classify_payload(text_content: Optional[str], file_path: Optional[str]) -> str:
    """
    Classify input payload into DOCUMENT, PAYMENT, or MESSAGE_LINK_APK.
    """
    # 1. File inspection
    if file_path and os.path.exists(file_path):
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".apk":
            return "MESSAGE_LINK_APK"

        if ext in [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac"]:
            return "AUDIO_VOICE"

        if ext == ".pdf":
            return "DOCUMENT"

        if ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
            # Check if this image is a payment QR code
            if is_qr_image(file_path):
                return "PAYMENT"
            return "DOCUMENT"

    # 2. Text inspection
    if text_content:
        cleaned = text_content.strip()

        # UPI Intent Link or standalone VPA
        if cleaned.lower().startswith("upi://pay") or re.match(r"^[\w\.\-]+@[\w\-]+$", cleaned):
            return "PAYMENT"

        # Explicit payment keywords
        if any(w in cleaned.lower() for w in ["upi://", "scan qr", "pay via upi", "gpay to"]):
            return "PAYMENT"

        # Legal notice / warrant text
        legal_keywords = [
            "warrant", "summons", "digital arrest", "police", "court",
            "cbi", "narcotics", "high court", "supreme court", "fir",
            "investigation officer", "section 41a", "bnss", "crpc"
        ]
        if any(w in cleaned.lower() for w in legal_keywords):
            return "DOCUMENT"

    return "MESSAGE_LINK_APK"
