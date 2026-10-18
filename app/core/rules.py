"""KavachAI Knowledge & Epistemic Law Rule Engine.
Stores statutory facts, impossible legal procedures, threat signatures, and heuristics.
"""

import re
import networkx as nx
from typing import List, Dict, Any, Tuple

# ---------------------------------------------------------------------------
# 1. Epistemic Indian Law Facts & Statutory Impossibilities
# ---------------------------------------------------------------------------

IMPOSSIBLE_LEGAL_PROCEDURES = [
    {
        "pattern": r"digital\s+arrest",
        "category": "DIGITAL_ARREST_EXTORTION",
        "statutory_fact": "There is NO provision for 'Digital Arrest' under the Bharatiya Nagarik Suraksha Sanhita (BNSS), Code of Criminal Procedure (CrPC), or Indian Penal Code / BNS. Law enforcement agencies CANNOT place any citizen under virtual or digital detention.",
        "confidence": 0.99
    },
    {
        "pattern": r"(cbi|police|ed|nia|customs)\s+(video\s+surveillance|skype\s+deposition|whatsapp\s+investigation)",
        "category": "VIRTUAL_DEPOSITION_FRAUD",
        "statutory_fact": "Police, CBI, ED, or court magistrates NEVER conduct formal depositions, interrogations, or arrests via Skype, WhatsApp, Zoom, or Telegram.",
        "confidence": 0.98
    },
    {
        "pattern": r"(asset|account)\s+freezing\s+clearance\s+(fee|deposit|charge)",
        "category": "CLEARANCE_FEE_EXTORTION",
        "statutory_fact": "No statutory agency or court demands a 'clearance fee' or 'security deposit' to unfreeze accounts. Account freezing orders are issued directly to commercial banks via Section 106 BNSS / 102 CrPC, never negotiated for cash with citizens.",
        "confidence": 0.98
    },
    {
        "pattern": r"reserve\s+bank\s+(of\s+india\s+)?(verification|safety|monitoring)\s+account",
        "category": "RBI_ACCOUNT_IMPERSONATION",
        "statutory_fact": "The Reserve Bank of India (RBI) is a central regulatory bank and NEVER holds individual consumer accounts, 'safety accounts', or 'verification vaults'.",
        "confidence": 0.99
    },
    {
        "pattern": r"(supreme\s+court|high\s+court|district\s+court)\s+(online\s+bail|bail\s+transfer|bail\s+upi)",
        "category": "COURT_BAIL_EXTORTION",
        "statutory_fact": "Courts in India do NOT accept bail bond payments via UPI, personal bank transfers, or payment gateways. Bail sureties must be deposited physically with the Court Registrar.",
        "confidence": 0.99
    },
    {
        "pattern": r"(trai|telecom\s+regulatory|dot)\s+(phone\s+disconnection|mobile\s+deactivation\s+warrant)",
        "category": "TRAI_DISCONNECTION_FRAUD",
        "statutory_fact": "TRAI (Telecom Regulatory Authority of India) does NOT issue disconnection notices or arrest warrants for illegal telecast or cybercrime directly to consumers.",
        "confidence": 0.97
    },
    {
        "pattern": r"(narcotics\s+control\s+bureau|ncb|customs)\s+parcel\s+(drugs|mdma|passport|illegal\s+items)",
        "category": "FEDEX_CUSTOMS_PARCEL_SCAM",
        "statutory_fact": "Customs and NCB do NOT call citizens demanding payment to settle seized parcels containing contraband. Seized goods lead to physical summons served under the NDPS / Customs Act.",
        "confidence": 0.97
    }
]

# 16-character National Judicial Data Grid CNR Standard
CNR_REGEX = re.compile(r"\b([A-Z]{4}\d{12})\b")

# ---------------------------------------------------------------------------
# 2. Payment Intent & UPI VPA Rules
# ---------------------------------------------------------------------------

# Consumer Payment Service Provider (PSP) handles
CONSUMER_VPA_HANDLES = [
    "okhdfcbank", "okaxis", "oksbi", "okicici", "paytm", "ybl", "ibl",
    "apl", "axl", "federal", "kotak", "idfcbank", "postbank", "airtel"
]

# Official keywords that scammers falsely use in personal VPAs
OFFICIAL_IMPERSONATION_KEYWORDS = [
    "police", "cbi", "customs", "cyber", "court", "challan", "echallan",
    "traffic", "bijli", "electricity", "refund", "cashback", "kyc",
    "helpline", "income.tax", "incometax", "rbi", "bsnl", "airtel"
]

# ---------------------------------------------------------------------------
# 3. Message, Link & Malware Threat Signatures
# ---------------------------------------------------------------------------

URGENCY_PATTERNS = [
    r"electricity\s+(?:bill\s+unpaid|power\s+(?:will\s+be\s+)?disconnected|disconnection|cut\s+tonight)",
    r"electricity\s+power\s+disconnected",
    r"power\s+(?:will\s+be\s+)?disconnected",
    r"(?:sim|mobile)\s+(?:card\s+will\s+be\s+deactivated|blocked|deactivated)",
    r"(?:bank\s+account|debit\s+card|netbanking)\s+(?:suspended|blocked|deactivated)",
    r"(?:pan|aadhaar)\s+(?:not\s+updated|link\s+immediately|penalty\s+of\s+rs)",
    r"(?:won|winner|lottery|congratulations)\s+rs\.\s*[\d,]+",
    r"part-time\s+job\s+earn\s+rs\.\s*[\d,]+\s+(?:per\s+day|daily)",
    r"apk\s+(?:file|download|update|install)"
]

SUSPICIOUS_TLDS = [
    ".top", ".xyz", ".club", ".work", ".click", ".live", ".loan",
    ".cam", ".link", ".buzz", ".guru", ".vip", ".gq", ".ml", ".cf"
]

DANGEROUS_APK_PERMISSIONS = [
    "android.permission.RECEIVE_SMS",
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.BIND_ACCESSIBILITY_SERVICE",
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.READ_CALL_LOG",
    "android.permission.RECORD_AUDIO"
]

# ---------------------------------------------------------------------------
# 4. NetworkX Procedural Law Graph Builder
# ---------------------------------------------------------------------------

def build_legal_procedure_graph() -> nx.DiGraph:
    """Build directed graph encoding authentic legal procedures vs illegal fraud constructs."""
    g = nx.DiGraph()

    # Valid Judicial Authorities
    g.add_node("Supreme Court of India", legal_entity=True)
    g.add_node("High Court", legal_entity=True)
    g.add_node("District Court", legal_entity=True)
    g.add_node("CBI", legal_entity=True)
    g.add_node("State Police", legal_entity=True)

    # Valid vs Fraudulent Actions
    g.add_edge("District Court", "Physical Summons", status="LEGAL", section="Sec 61 CrPC / Sec 63 BNSS")
    g.add_edge("District Court", "CNR Registration", status="LEGAL", system="NJDG")
    g.add_edge("State Police", "Sec 41A Notice", status="LEGAL", section="Sec 35 BNSS")

    # Impossible Fraud Actions (Flagged as Scams)
    g.add_edge("CBI", "Digital Arrest", status="IMPOSSIBLE_SCAM")
    g.add_edge("State Police", "Skype Deposition", status="IMPOSSIBLE_SCAM")
    g.add_edge("Supreme Court of India", "UPI Bail Payment", status="IMPOSSIBLE_SCAM")
    g.add_edge("Customs", "WhatsApp Clearance Fee", status="IMPOSSIBLE_SCAM")

    return g

PROCEDURAL_LAW_GRAPH = build_legal_procedure_graph()
