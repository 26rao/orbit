import os
import re
import zipfile
import datetime
import hashlib
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

try:
    import whois
except Exception:
    whois = None

import httpx

from app.core.config import VIRUSTOTAL_API_KEY
from app.core.rules import (
    URGENCY_PATTERNS,
    SUSPICIOUS_TLDS,
    DANGEROUS_APK_PERMISSIONS,
    HIGH_RISK_ADMIN_PREFIXES,
    SEBI_REGISTRATION_REGEX,
    SEBI_TASK_SCAM_PATTERNS,
)

logger = logging.getLogger("kavach.text")

URL_REGEX = re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,4}[\-\s]?)?[6789]\d{9}")
INTL_PHONE_REGEX = re.compile(r"\+(\d{1,4})[\s\-]?\d{6,12}")


def compute_file_sha256(file_path: str) -> str:
    """Compute cryptographic SHA-256 hash of a file for threat intel and evidence."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


async def check_virustotal_threat_intel(sha256_hash: str) -> Optional[Dict[str, Any]]:
    """Query VirusTotal API v3 for file hash threat intelligence."""
    if not VIRUSTOTAL_API_KEY:
        return None

    try:
        url = f"https://www.virustotal.com/api/v3/files/{sha256_hash}"
        headers = {"x-apikey": VIRUSTOTAL_API_KEY}
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                attrs = data.get("attributes", {})
                stats = attrs.get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values()) if stats else 0
                threat_class = attrs.get("popular_threat_classification", {})
                family = threat_class.get("suggested_threat_label") or "Trojan.AndroidOS.Generic"

                return {
                    "is_indexed": True,
                    "malicious_count": malicious,
                    "total_engines": total,
                    "detection_ratio": f"{malicious}/{total}",
                    "malware_family": family,
                    "is_malicious": malicious >= 3,
                }
    except Exception as e:
        logger.warning(f"VirusTotal lookup error for {sha256_hash}: {e}")

    return None


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
                    if creation_date.tzinfo is not None:
                        age_days = (datetime.datetime.now(datetime.timezone.utc) - creation_date).days
                    else:
                        age_days = (datetime.datetime.now() - creation_date).days
                    if age_days < 7:
                        reasons.append(f"NEWLY REGISTERED DOMAIN: '{hostname}' was created only {age_days} days ago (typical of disposable phishing campaigns).")
            except Exception as e:
                logger.debug(f"Whois query error for {hostname}: {e}")

    except Exception as e:
        logger.warning(f"Domain analysis failed for {url}: {e}")

    return reasons


async def analyze_apk_file(file_path: str) -> Dict[str, Any]:
    """
    Inspect Android APK file:
    1. Cryptographic SHA-256 generation
    2. VirusTotal API v3 threat intelligence (detection ratio & malware family)
    3. Offline Manifest Fallback for zero-day packages (Accessibility & SMS permissions)
    """
    reasons = []
    found_permissions = []
    is_malicious = False

    if not file_path or not os.path.exists(file_path):
        return {"is_malicious": False, "reasons": []}

    # 1. Cryptographic SHA-256 Hashing
    sha256_hash = compute_file_sha256(file_path)

    # 2. VirusTotal API v3 Lookup
    vt_result = await check_virustotal_threat_intel(sha256_hash)
    if vt_result and vt_result.get("is_indexed"):
        ratio = vt_result["detection_ratio"]
        family = vt_result["malware_family"]
        if vt_result["is_malicious"]:
            is_malicious = True
            reasons.append(
                f"VIRUSTOTAL THREAT INTELLIGENCE: {ratio} security engines flagged this APK as malicious (Identified Malware Family: {family})."
            )

    # 3. Offline Manifest Fallback Analysis
    try:
        with zipfile.ZipFile(file_path, "r") as apk:
            file_list = apk.namelist()
            if "AndroidManifest.xml" not in file_list:
                return {
                    "is_malicious": True,
                    "sha256": sha256_hash,
                    "reasons": ["Corrupt or obfuscated Android package."],
                }

            manifest_bytes = apk.read("AndroidManifest.xml")
            manifest_text = manifest_bytes.decode("latin-1", errors="ignore")

            for perm in DANGEROUS_APK_PERMISSIONS:
                clean_perm = perm.split(".")[-1]
                if perm in manifest_text or clean_perm in manifest_text:
                    found_permissions.append(perm)

            if any(p in found_permissions for p in ["android.permission.RECEIVE_SMS", "android.permission.READ_SMS"]):
                reasons.append("HIGH RISK PERMISSION: APK requests SMS reading/receiving permissions (used to intercept banking OTPs).")
                is_malicious = True

            if "android.permission.BIND_ACCESSIBILITY_SERVICE" in found_permissions:
                reasons.append("CRITICAL SPYWARE: APK requests BIND_ACCESSIBILITY_SERVICE to read on-screen banking PINs and bypass security overlays.")
                is_malicious = True

            if "android.permission.SYSTEM_ALERT_WINDOW" in found_permissions:
                reasons.append("OVERLAY PHISHING CAPABILITY: Requests SYSTEM_ALERT_WINDOW to draw deceptive phishing dialogs over legitimate banking apps.")
                is_malicious = True

            if "android.permission.REQUEST_INSTALL_PACKAGES" in found_permissions:
                reasons.append("DROPPER BEHAVIOR: Requests permission to install secondary unverified packages in background.")
                is_malicious = True

    except Exception as e:
        reasons.append(f"Error inspecting APK manifest: {e}")

    return {
        "is_malicious": is_malicious,
        "sha256": sha256_hash,
        "found_permissions": found_permissions,
        "virustotal": vt_result,
        "reasons": reasons,
    }


def audit_sebi_and_task_scam(content: str) -> List[str]:
    """
    Audit for fake SEBI investment schemes, guaranteed stock tip groups,
    and WhatsApp/Telegram task scam networks.
    """
    reasons = []
    content_lower = content.lower()

    # 1. Fake SEBI Registration / Institutional Trading Pools
    sebi_reg = SEBI_REGISTRATION_REGEX.findall(content)
    has_sebi_keyword = "sebi" in content_lower
    has_guarantee = any(w in content_lower for w in ["guaranteed return", "guaranteed profit", "100% profit", "200% return", "upper circuit", "insider tip", "pre-ipo"])

    if has_sebi_keyword or sebi_reg:
        if has_guarantee or any(w in content_lower for w in ["whatsapp group", "telegram channel", "vip institutional", "institutional account"]):
            reasons.append(
                "ILLEGAL SEBI INVESTMENT POOL: Under SEBI (PFUTP) Regulations, guaranteed stock returns and private WhatsApp/Telegram institutional trading pools are strictly illegal. Genuine SEBI intermediaries never solicit retail funds through social messaging."
            )

    # 2. Task Scam Patterns
    task_keywords = ["youtube", "google review", "hotel rating", "review task", "task", "part-time", "video"]
    earning_keywords = ["earn", "daily", "per day", "income", "telegram", "vip"]

    matches_pattern = any(re.search(pat, content_lower) for pat in SEBI_TASK_SCAM_PATTERNS)
    has_task_cues = any(k in content_lower for k in ["like", "rating", "review", "task"]) and any(k in content_lower for k in ["youtube", "video", "telegram", "part-time", "earn rs", "rs 150", "rs 50", "daily income"])

    if matches_pattern or has_task_cues:
        reasons.append(
            "PREDATOR TASK SCAM: 'Like videos / Rate hotels / Google reviews for ₹50-₹150' part-time jobs are a known cyber extortion trap. Victims receive tiny payouts before being coerced into depositing lakhs for 'VIP tasks'."
        )

    return reasons


async def verify_text_and_links(
    text_content: Optional[str] = None,
    file_path: Optional[str] = None,
    text_data: Optional[str] = None
) -> Dict[str, Any]:
    """
    Forensic analysis of SMS messages, WhatsApp alerts, URLs, APK downloads,
    SEBI investment auditor, and foreign syndicate detection.
    """
    content = text_content or text_data or ""
    reasons: List[str] = []
    confidence = 0.0
    urgency_detected: List[str] = []

    # 1. APK Threat Intel & Manifest Analysis if uploaded file is APK
    apk_info = None
    if file_path and file_path.lower().endswith(".apk"):
        apk_info = await analyze_apk_file(file_path)
        if apk_info.get("is_malicious"):
            confidence = 0.99
            reasons.extend(apk_info["reasons"])
        elif apk_info.get("sha256"):
            reasons.append(f"APK Cryptographic Hash verified: SHA256:{apk_info['sha256'][:16]}... No overt permissions flagged.")

    # 2. Extract URLs and analyze domain threats
    extracted_urls = URL_REGEX.findall(content)
    gov_urls = []
    unverified_urls = []
    for url in extracted_urls:
        domain_reasons = analyze_domain_risk(url)
        if domain_reasons:
            reasons.extend(domain_reasons)
            confidence = max(confidence, 0.95)
        else:
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()
            if hostname.endswith(".gov.in") or hostname.endswith(".nic.in") or hostname.endswith(".ac.in") or hostname.endswith(".res.in"):
                gov_urls.append(url)
            else:
                unverified_urls.append(url)

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

    # 4. Fake SEBI Investment & Task Scam Auditor
    sebi_reasons = audit_sebi_and_task_scam(content)
    if sebi_reasons:
        reasons.extend(sebi_reasons)
        confidence = max(confidence, 0.96)

    # 5. Extract Phone Numbers & Inspect Foreign Virtual Country Codes
    extracted_phones = PHONE_REGEX.findall(content)
    for prefix, country_desc in HIGH_RISK_ADMIN_PREFIXES.items():
        if prefix in content:
            reasons.append(
                f"CROSS-BORDER SCAM SYNDICATE: Group administrator or sender operates from virtual prefix '{prefix}' ({country_desc}), orchestrating unauthorized domestic schemes."
            )
            confidence = max(confidence, 0.95)

    # 6. Final Verdict Determination
    if confidence >= 0.70:
        verdict = "DANGEROUS_SCAM"
        summary = "CRITICAL THREAT: Fraudulent phishing message / malicious payload designed to induce panic and steal credentials."
    elif confidence >= 0.40 or len(unverified_urls) > 0:
        verdict = "SUSPICIOUS"
        confidence = max(confidence, 0.60)
        summary = "SUSPICIOUS: Message contains unverified links or urgency signals. Do not click links or call the sender."
        if not reasons:
            reasons.append("Contains unverified external links from an unknown sender.")
    elif len(gov_urls) > 0:
        verdict = "AUTHENTIC"
        confidence = 0.98
        gov_domains = [urlparse(u).hostname for u in gov_urls if urlparse(u).hostname]
        summary = f"AUTHENTIC: Legitimate official communication from verified government portal ({', '.join(gov_domains)})."
        reasons = [
            f"Official domain verified: Link '{gov_urls[0]}' belongs to authenticated Government of India infrastructure (.gov.in / .nic.in).",
            "Message language is administrative/transactional with no coercive urgency or credential-stealing indicators."
        ]
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
        "gov_urls": gov_urls,
        "unverified_urls": unverified_urls,
        "urgency_triggers": urgency_detected,
        "apk_risk": apk_info,
        "extracted_contacts": extracted_phones,
    }
