"""KavachAI Configuration Settings."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "KavachAI"
APP_TITLE = APP_NAME
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Universal On-Demand Forensic Scam & Fraud Verification Engine"

HOST = os.getenv("KAVACH_HOST", "0.0.0.0")
PORT = int(os.getenv("KAVACH_PORT", "8000"))

# National Cyber Crime Reporting Portal
CYBERCRIME_HELPLINE = "1930"
HELPLINE_NUMBER = CYBERCRIME_HELPLINE
CYBERCRIME_PORTAL_URL = "https://cybercrime.gov.in"
CYBERCRIME_PORTAL = CYBERCRIME_PORTAL_URL

# eCourts CNR API Endpoint
ECOURTS_API_URL = os.getenv("ECOURTS_API_URL", "https://webapi.ecourtsindia.com/api/partner/case")

# Twilio SMS Config (Optional)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
EMERGENCY_CONTACT = os.getenv("EMERGENCY_CONTACT", "")
