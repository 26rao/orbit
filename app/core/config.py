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

# VirusTotal API v3 Config (Optional)
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")

# Golden Hour Bank Account Freeze Directory
BANK_FREEZE_DIRECTORY = [
    {
        "bank_name": "State Bank of India (SBI)",
        "helpline": "1800111109 / 18004253800",
        "card_block_sms": "SMS BLOCK <Last 4 digits> to 567676",
        "upi_stop_sms": "SMS STOPUPI to 9223008333",
        "portal_url": "https://www.onlinesbi.sbi",
    },
    {
        "bank_name": "HDFC Bank",
        "helpline": "18001600 / 18002664060",
        "card_block_sms": "Call IVR or SMS BLOCK <Last 4 digits> to 5676712",
        "upi_stop_sms": "Call 18001600 Option 1",
        "portal_url": "https://netbanking.hdfcbank.com",
    },
    {
        "bank_name": "ICICI Bank",
        "helpline": "18001080",
        "card_block_sms": "SMS BLOCK <Last 4 digits> to 5676766",
        "upi_stop_sms": "SMS SUSPEND to 9215676766",
        "portal_url": "https://infinity.icicibank.com",
    },
    {
        "bank_name": "Axis Bank",
        "helpline": "18604195555 / 18605005555",
        "card_block_sms": "SMS BLOCK <Last 4 digits> to 5676782",
        "upi_stop_sms": "Call 18604195555",
        "portal_url": "https://www.axisbank.com",
    },
    {
        "bank_name": "Punjab National Bank (PNB)",
        "helpline": "18001802222 / 18001032222",
        "card_block_sms": "SMS HOT <Card Number> to 5607040",
        "upi_stop_sms": "Call 18001802222",
        "portal_url": "https://netpnb.com",
    },
    {
        "bank_name": "Canara Bank",
        "helpline": "18004250018",
        "card_block_sms": "SMS CANBLOCK <Card Number> to 5607060",
        "upi_stop_sms": "Call 18004250018",
        "portal_url": "https://canarabank.com",
    },
]
