"""Message, Phishing Link, and APK Static Forensic Engine.
Analyzes SMS urgency patterns, URL domain age/reputation, and Android APK permissions.
"""

import os
import re
import zipfile
import datetime
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

try:
    import whois
except Exception:
    whois = None

from app.core.rules import URGENCY_PATTERNS, SUSPICIOUS_TLDS, DANGEROUS_APK_PERMISSIONS

logger = logging.getLogger("kavach.text")

URL_REGEX = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*")
PHONE_REGEX = re.compile(r"(?:\+?91[\-\s]?)?[6789]\d{9}")


def analyze_domain_risk(url: str) -> List[str]:
    """Inspect domain age, suspicious TLDs, and typosquatting."""
    reasons = []
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        # 1. IP address hostname check
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
            reasons.append(f"Host '{hostname}' uses a raw IP address instead of a legitimate domain name.")

        # 2. Suspicious TLD check
        for tld in SUSPICIOUS_TLDS:
            if hostname.endswith(tld):
                reasons.append(f"Domain uses high-risk TLD '{tld}', frequently used in disposable phishing infrastructure.")
                break

        # 3. Typosquatting / deceptive subdomains
        target_brands = ["sbi", "hdfc", "icici", "axis", "punjab", "incometax", "trai", "epfo", "digilocker"]
        for brand in target_brands:
            if brand in hostname and not hostname.endswith(f".{brand}.com") and not hostname.endswith(f".{brand}.co.in") and not hostname.endswith(".gov.in"):
                reasons.append(f"Deceptive Brand Spoofing: Host '{hostname}' impersonates '{brand.upper()}' on an unauthorized third-party domain.")

        # 4. URL Shortener check
        if hostname in ["bit.ly", "tinyurl.com", "cutt.ly", "t.co", "is.gd", "rb.gy"]:
            reasons.append(f"Obfuscated Link: Uses URL shortener '{hostname}' to hide the true phishing destination.")

        # 5. Whois Domain Age Check
        if whois and "." in hostname and not re.match(r"^\d", hostname):
            try:
                w = whois.whois(hostname)
                creation_date = w.creation_date
                if isinstance(creation_date, list):
                    creation_date = creation_date[0]
                if creation_date and isinstance(creation_date, datetime.datetime):
                    # Remove timezone info for comparison
                    creation_clean = creation_date.replace(tzinfo=None)
                    age_days = (datetime.datetime.utcnow() - creation_clean).days
                    if age_days < 7:
                        reasons.append(f"NEWLY REGISTERED DOMAIN: '{hostname}' was created only {age_days} days ago (typical of disposable phishing campaigns).")
            except Exception as e:
                logger.debug(f"Whois query error for {hostname}: {e}")

    except Exception as e:
        logger.warning(f"Domain analysis failed for {url}: {e}")

    return reasons


def analyze_apk_file(file_path: str) -> Dict[str, Any]:
    """Inspect Android APK file for deceptive names and high-risk permissions."""
    reasons = []
    found_permissions = []
    is_malicious = False

    if not file_path or not os.path.exists(file_path):
        return {"is_malicious": False, "reasons": []}

    try:
        with zipfile.ZipFile(file_path, "r") as apk:
            file_list = apk.namelist()
            if "AndroidManifest.xml" not in file_list:
                return {"is_malicious": True, "reasons": ["Corrupt or obfuscated Android package."]}

            # Read Manifest binary stream for known permission strings
            manifest_bytes = apk.read("AndroidManifest.xml")
            manifest_text = manifest_bytes.decode("latin-1", errors="ignore")

            for perm in DANGEROUS_APK_PERMISSIONS:
                clean_perm = perm.split(".")[-1]
                if perm in manifest_text or clean_perm in manifest_text:
                    found_permissions.append(perm)

            if any(p in found_permissions for p in ["android.permission.RECEIVE_SMS", "android.permission.READ_SMS"]):
                reasons.append("HIGH RISK MALWARE: APK requests SMS reading permissions (used to intercept banking OTPs).")
                is_malicious = True

            if "android.permission.BIND_ACCESSIBILITY_SERVICE" in found_permissions:
                reasons.append("CRITICAL SPYWARE: APK requests Accessibility Service control to capture keystrokes and PINs.")
                is_malicious = True

    except Exception as e:
        reasons.append(f"Error inspecting APK payload: {e}")

    return {
        "is_malicious": is_malicious,
        "found_permissions": found_permissions,
        "reasons": reasons,
    }


async def verify_text_and_links(
    text_content: Optional[str] = None,
    file_path: Optional[str] = None,
    text_data: Optional[str] = None
) -> Dict[str, Any]:
    """
    Forensic analysis of SMS messages, WhatsApp alerts, URLs, and APK downloads.
    """
    content = text_content or text_data or ""
    reasons: List[str] = []
    confidence = 0.0
    urgency_detected: List[str] = []

    # 1. APK Analysis if uploaded file is APK
    apk_info = None
    if file_path and file_path.lower().endswith(".apk"):
        apk_info = analyze_apk_file(file_path)
        if apk_info.get("is_malicious"):
            confidence = 0.99
            reasons.extend(apk_info["reasons"])

    # 2. Extract URLs and analyze domain threats
    extracted_urls = URL_REGEX.findall(content)
    for url in extracted_urls:
        domain_reasons = analyze_domain_risk(url)
        if domain_reasons:
            reasons.extend(domain_reasons)
            confidence = max(confidence, 0.95)

    # 3. Urgency / Coercion NLP Patterns
    content_lower = content.lower()
    for pattern in URGENCY_PATTERNS:
        if re.search(pattern, content_lower):
            urgency_detected.append(pattern)
            confidence = max(confidence, 0.90)

    if urgency_detected:
        if any("electricity" in p for p in urgency_detected):
            reasons.append(
                "POWER CUT SCAM: Claim that electricity will be disconnected tonight due to unpaid bill is a known extortion template. Discoms never send disconnection threats via private phone numbers."
            )
        elif any("sim" in p or "mobile" in p for p in urgency_detected):
            reasons.append(
                "SIM DEACTIVATION SCAM: Threatening SIM card blocking within hours is a tactic to induce panic and force remote app installation."
            )
        elif any("pan" in p or "bank" in p for p in urgency_detected):
            reasons.append(
                "BANKING / KYC PHISHING: Demanding urgent PAN or Aadhaar card linking under threat of account blocking is fraudulent."
            )
        elif any("won" in p or "lottery" in p for p in urgency_detected):
            reasons.append(
                "LOTTERY / PRIZE FRAUD: Unsolicited lottery winnings or KBC cash awards requiring a processing fee are fraudulent."
            )
        elif any("apk" in p for p in urgency_detected):
            reasons.append(
                "MALICIOUS APK DOWNLOAD: Message urges downloading an unverified third-party .apk application to steal banking credentials."
            )

    # 4. Extract Contact Numbers
    extracted_phones = PHONE_REGEX.findall(content)

    # 5. Final Verdict Determination
    if confidence >= 0.70:
        verdict = "DANGEROUS_SCAM"
        summary = "CRITICAL THREAT: Fraudulent phishing message / malicious payload designed to induce panic and steal credentials."
    elif confidence >= 0.40 or len(extracted_urls) > 0:
        verdict = "SUSPICIOUS"
        confidence = max(confidence, 0.60)
        summary = "SUSPICIOUS: Message contains unverified links or urgency signals. Do not click links or call the sender."
        if not reasons:
            reasons.append("Contains unverified external links from an unknown sender.")
    else:
        verdict = "AUTHENTIC"
        confidence = 0.85
        summary = "Standard communication. No known phishing templates, deceptive URLs, or urgency markers detected."
        reasons = ["Message language is informative and does not employ coercive urgency or malicious links."]

    return {
        "verdict": verdict,
        "confidence": round(confidence, 2),
        "summary": summary,
        "reasons": reasons,
        "extracted_urls": extracted_urls,
        "urgency_triggers": urgency_detected,
        "apk_risk": apk_info,
        "extracted_contacts": extracted_phones,
    }
