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

from app.main import app
from app.engines.classifier import classify_payload
from app.engines.legal_engine import verify_legal_document
from app.engines.payment_engine import verify_payment_data
from app.engines.text_engine import verify_text_and_links, analyze_apk_file
from app.engines.audio_engine import verify_audio_deepfake
from app.services.tts_service import build_voice_script
from app.services.dossier import build_cybercrime_dossier, determine_bns_it_sections
from app.services.pdf_service import generate_dossier_pdf

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
    auth_script_en = build_voice_script([], preferred_language="en", verdict="AUTHENTIC")
    auth_script_hi = build_voice_script([], preferred_language="hi", verdict="AUTHENTIC")

    assert "सावधान! कवच ए आई" in hi_script
    assert "डिजिटल अरेस्ट" in hi_script
    assert "Alert! Kavach AI" in en_script
    assert "Digital Arrest" in en_script
    assert "authentic and safe" in auth_script_en
    assert "प्रामाणिक और सुरक्षित" in auth_script_hi


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


def test_regional_audio_scripts():
    """Verify Telugu, Kannada, Tamil, and Marathi regional voice scripts."""
    te_script = build_voice_script([], preferred_language="te", verdict="DANGEROUS_SCAM")
    kn_script = build_voice_script([], preferred_language="kn", verdict="DANGEROUS_SCAM")
    ta_script = build_voice_script([], preferred_language="ta", verdict="DANGEROUS_SCAM")
    mr_script = build_voice_script([], preferred_language="mr", verdict="DANGEROUS_SCAM")

    assert "కవచ్" in te_script and "1930" in te_script
    assert "ಕವಚ" in kn_script and "1930" in kn_script
    assert "கவச்" in ta_script and "1930" in ta_script
    assert "कवच" in mr_script and "1930" in mr_script


@pytest.mark.asyncio
async def test_sebi_and_task_scam_detection():
    """Verify fake SEBI investment scheme and WhatsApp task scam detection."""
    sebi_msg = (
        "SEBI REGISTERED INSTITUTIONAL VIP POOL: Guaranteed 200% daily returns! "
        "Exclusive upper circuit quota. Contact admin +84 9123456789 (Vietnam desk)."
    )
    result = await verify_text_and_links(text_data=sebi_msg)
    assert result["verdict"] == "DANGEROUS_SCAM"
    assert any("SEBI" in r for r in result["reasons"])
    assert any("CROSS-BORDER" in r or "+84" in r for r in result["reasons"])

    task_msg = "Earn Rs 5000 daily! Like 3 YouTube videos to earn Rs 150 immediately. Join Telegram VIP task channel."
    task_res = await verify_text_and_links(text_data=task_msg)
    assert task_res["verdict"] == "DANGEROUS_SCAM"
    assert any("TASK SCAM" in r for r in task_res["reasons"])


def test_golden_hour_bank_freeze_guide():
    """Verify /api/v1/freeze-guide returns bank directories and 1930 helpline."""
    response = client.get("/api/v1/freeze-guide")
    assert response.status_code == 200
    data = response.json()
    assert data["helpline"] == "1930"
    assert len(data["banks"]) >= 4
    bank_names = [b["bank_name"] for b in data["banks"]]
    assert any("SBI" in name for name in bank_names)
    assert any("HDFC" in name for name in bank_names)


@pytest.mark.asyncio
async def test_deepfake_audio_interceptor():
    """Verify voice clone extortion detection and out-of-band secret challenge."""
    res = await verify_audio_deepfake(
        file_path=None,
        text_content="Dad, I've had a terrible accident. Police arrested me, send bail money immediately!"
    )
    assert res["verdict"] in ["DANGEROUS_SCAM", "SUSPICIOUS"]
    assert "family_challenge" in res
    assert "secret passphrase" in res["family_challenge"]


def test_pdf_dossier_generation_and_endpoint():
    """Verify Section 63 BSA PDF generation and /api/v1/dossier/pdf endpoint."""
    mock_dossier = {
        "dossier_id": "KAVACH-20261020-TEST",
        "generated_at": "2026-10-20 12:00:00 UTC",
        "sha256_evidence_hash": "A" * 64,
        "verdict": "DANGEROUS_SCAM",
        "confidence_score": 0.99,
        "suspect_indicators": {
            "upi_vpas": ["fraudster@okhdfcbank"],
            "phishing_domains": ["http://phish-bank.xyz"],
            "contact_numbers": ["9876543210"],
        },
        "statutory_violations": [
            "Section 66D, Information Technology Act, 2000",
            "Section 318(4), Bharatiya Nyaya Sanhita, 2023"
        ],
        "fir_narrative_template": "FORMAL COMPLAINT UNDER SECTION 173 BNSS...",
    }

    # Test direct PDF generator
    pdf_bytes = generate_dossier_pdf(mock_dossier)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000

    # Test HTTP endpoint
    response = client.post("/api/v1/dossier/pdf", json=mock_dossier)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_apk_manifest_and_sha256():
    """Verify offline AndroidManifest fallback extracts high-risk permissions."""
    import zipfile
    with tempfile.NamedTemporaryFile(suffix=".apk", delete=False) as f:
        apk_path = f.name

    try:
        # Create a mock APK containing AndroidManifest.xml
        with zipfile.ZipFile(apk_path, "w") as z:
            manifest_content = b'android.permission.BIND_ACCESSIBILITY_SERVICE android.permission.RECEIVE_SMS'
            z.writestr("AndroidManifest.xml", manifest_content)

        apk_info = await analyze_apk_file(apk_path)
        assert apk_info["is_malicious"] is True
        assert len(apk_info["sha256"]) == 64
        assert any("BIND_ACCESSIBILITY_SERVICE" in r for r in apk_info["reasons"])
        assert any("SMS" in r for r in apk_info["reasons"])
    finally:
        if os.path.exists(apk_path):
            os.remove(apk_path)


def test_voice_memo_endpoint():
    """Verify POST /api/v1/voice-memo returns regional audio in requested language."""
    for lang in ["te", "kn", "ta", "mr", "hi", "en"]:
        resp = client.post(
            "/api/v1/voice-memo",
            json={
                "reasons": ["Test finding"],
                "preferred_language": lang,
                "verdict": "DANGEROUS_SCAM"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == lang
        assert data["audio_base64"] is not None
        assert len(data["audio_base64"]) > 500


if __name__ == "__main__":
    pytest.main(["-v", __file__])

