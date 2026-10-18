"""Comprehensive Test Suite for KavachAI Forensic Verification System.
Validates:
1. Epistemic Statutory Law & CNR checks (Legal Engine)
2. UPI Intent Inversion & VPA Impersonation (Payment Engine)
3. Urgency NLP, Domain age, and APK checks (Text Engine)
4. Local-language audio synthesis & script composing (TTS Service)
5. Pre-filled 1930 / cybercrime.gov.in complaint format (Dossier Service)
6. End-to-end FastAPI endpoint integration (HTTP tests)
"""

import os
import sys
import asyncio
import tempfile
import pytest
from fastapi.testclient import TestClient

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.engines.classifier import classify_payload
from app.engines.legal_engine import verify_legal_document
from app.engines.payment_engine import verify_payment_data
from app.engines.text_engine import verify_text_and_links
from app.services.tts_service import build_voice_script
from app.services.dossier import build_cybercrime_dossier, determine_bns_it_sections

client = TestClient(app)


def test_classifier_routing():
    """Verify input modality classifier routes correctly."""
    # Text with UPI link
    assert classify_payload("upi://pay?pa=scammer@oksbi&pn=Police&am=5000", None) == "PAYMENT"
    # Text with court summons
    assert classify_payload("High Court of Delhi arrest warrant summons", None) == "DOCUMENT"
    # Phishing text
    assert classify_payload("Your electricity will be disconnected tonight. Call 9876543210", None) == "MESSAGE_LINK_APK"


@pytest.mark.asyncio
async def test_legal_engine_digital_arrest():
    """Verify legal engine detects systemic impossibility of Digital Arrest."""
    # Create temporary text document containing the fake summons
    fake_summons = (
        "SUPREME COURT OF INDIA / CBI HEADQUARTERS NOTICE\n"
        "You are placed under immediate 24-hour Digital Arrest for illegal money laundering.\n"
        "Do not disconnect. Skype video deposition required. Pay security clearance fee to RBI.\n"
    )
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as f:
        f.write(fake_summons)
        temp_path = f.name

    try:
        result = await verify_legal_document(temp_path)
        assert result["verdict"] == "DANGEROUS_SCAM"
        assert result["confidence"] >= 0.90
        assert any("Digital Arrest" in r for r in result["reasons"])
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pytest.mark.asyncio
async def test_payment_engine_intent_inversion_and_impersonation():
    """Verify UPI parser catches debit reverse-charge and consumer handle impersonation."""
    upi_payload = "upi://pay?pa=cybercrime-police@okhdfcbank&pn=CyberPoliceHeadquarters&am=10000&cu=INR&tn=FIR_Bail_Deposit"
    result = await verify_payment_data(file_path=None, text_data=upi_payload)

    assert result["verdict"] == "DANGEROUS_SCAM"
    assert result["confidence"] >= 0.95
    assert result["vpa"] == "cybercrime-police@okhdfcbank"
    assert result["intent_direction"] == "DEBIT"
    assert any("DEBIT" in r and "bank account" in r for r in result["reasons"])
    assert any("impersonat" in r.lower() for r in result["reasons"])


@pytest.mark.asyncio
async def test_text_engine_power_cut_scam():
    """Verify SMS parser detects the electricity bill power-cut scam pattern."""
    power_cut_sms = (
        "Dear Consumer, your electricity power will be disconnected tonight at 9.30 PM from "
        "electricity office because your previous month bill was not updated. "
        "Please immediately contact our power officer 9876543210."
    )
    result = await verify_text_and_links(text_data=power_cut_sms)

    assert result["verdict"] == "DANGEROUS_SCAM"
    assert result["confidence"] >= 0.85
    assert any("POWER CUT SCAM" in r for r in result["reasons"])
    assert len(result["extracted_contacts"]) >= 1


@pytest.mark.asyncio
async def test_text_engine_authentic_message():
    """Verify non-scam benign messages are graded as Authentic / Low Risk."""
    benign_text = "Hi Neha, reminder that our project team meeting is scheduled for tomorrow at 3 PM in Conference Room B."
    result = await verify_text_and_links(text_data=benign_text)

    assert result["verdict"] == "AUTHENTIC"
    assert result["confidence"] >= 0.70


def test_dossier_sections_and_fir():
    """Verify BNS and IT Act sections and SHA256 chain-of-custody in dossier."""
    mock_result = {
        "verdict": "DANGEROUS_SCAM",
        "confidence": 0.98,
        "summary": "Criminal impersonation and extortion.",
        "reasons": ["Impersonating police officer", "Demanding extortion fee"],
        "vpa": "fraudster@okhdfcbank",
        "payee_name": "Cyber Cell Escrow",
        "extracted_urls": ["http://fake-police.xyz"]
    }
    raw_input = "Transfer Rs 50,000 to fraudster@okhdfcbank"
    dossier = build_cybercrime_dossier(mock_result, raw_input)

    assert dossier["incident_category"] == "Identity Theft & Extortion"
    assert any("Section 66D" in s for s in dossier["statutory_violations"])
    assert any("Section 318(4)" in s for s in dossier["statutory_violations"])
    assert any("Section 308(2)" in s for s in dossier["statutory_violations"])
    assert dossier["suspect_indicators"]["upi_vpas"] == ["fraudster@okhdfcbank"]
    assert "FIR NARRATIVE TEMPLATE" in dossier["fir_narrative_template"]


def test_tts_voice_scripts():
    """Verify Hindi and English warning voice script generation."""
    hi_script = build_voice_script(["Fake summons"], preferred_language="hi", verdict="DANGEROUS_SCAM")
    en_script = build_voice_script(["Fake summons"], preferred_language="en", verdict="DANGEROUS_SCAM")

    assert "सावधान! कवच ए आई" in hi_script
    assert "डिजिटल अरेस्ट" in hi_script
    assert "Alert! Kavach AI" in en_script
    assert "Digital Arrest" in en_script


def test_api_health_endpoint():
    """Verify /api/v1/health returns active status and helpline."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["helpline"] == "1930"


def test_api_dashboard_endpoint():
    """Verify GET / serves the interactive HTML dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "KavachAI" in response.text


def test_api_verify_json_endpoint():
    """Verify POST /api/v1/verify-json with a digital arrest threat."""
    payload = {
        "text_content": "CBI Video Surveillance Notice: Digital Arrest in effect. Transfer Rs 2,00,000 clearance deposit to RBI account.",
        "preferred_language": "en"
    }
    response = client.post("/api/v1/verify-json", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "DANGEROUS_SCAM"
    assert data["confidence"] >= 0.90
    assert data["dossier"] is not None
    assert "1930" in data["dossier"]["fir_narrative_template"]


def test_api_verify_multipart_endpoint():
    """Verify POST /api/v1/verify with multipart form data."""
    response = client.post(
        "/api/v1/verify",
        data={
            "text_content": "Dear Consumer, electricity power disconnected tonight. Call 9876543210.",
            "preferred_language": "hi"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "DANGEROUS_SCAM"
    assert any("POWER CUT SCAM" in r for r in data["reasons"])


if __name__ == "__main__":
    pytest.main(["-v", __file__])
