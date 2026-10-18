"""KavachAI - Universal On-Demand Scam Verification Engine
Production FastAPI Application
"""

import os
import shutil
import tempfile
import base64
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.config import APP_TITLE, APP_VERSION, HELPLINE_NUMBER, CYBERCRIME_PORTAL
from app.core.rules import IMPOSSIBLE_LEGAL_PROCEDURES, URGENCY_PATTERNS
from app.engines.classifier import classify_payload
from app.engines.legal_engine import verify_legal_document
from app.engines.payment_engine import verify_payment_data
from app.engines.text_engine import verify_text_and_links
from app.services.tts_service import generate_voice_explanation
from app.services.dossier import build_cybercrime_dossier

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Universal on-demand scam verification app: drop an image, PDF, message, link, or payment request for instant forensic verdict."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VerificationResponse(BaseModel):
    verdict: str = Field(..., description="DANGEROUS_SCAM | SUSPICIOUS | AUTHENTIC")
    confidence: float = Field(..., description="Epistemic confidence level (0.0 to 1.0)")
    summary: str = Field(..., description="Plain-language forensic verdict summary")
    reasons: List[str] = Field(..., description="Explanatory forensic findings")
    input_modality: str = Field(..., description="DOCUMENT | PAYMENT | MESSAGE_LINK_APK")
    audio_base64: Optional[str] = Field(None, description="Base64-encoded MP3 voice warning")
    dossier: Optional[Dict[str, Any]] = Field(None, description="Pre-filled 1930 / cybercrime.gov.in complaint dossier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VerifyJsonRequest(BaseModel):
    text_content: Optional[str] = None
    file_base64: Optional[str] = None
    file_name: Optional[str] = None
    preferred_language: str = "hi"


async def process_verification(
    text_content: Optional[str],
    temp_path: Optional[str],
    preferred_language: str = "hi",
    original_filename: Optional[str] = None
) -> Dict[str, Any]:
    """Execute classification, forensic verification pipeline, audio warning, and dossier formatting."""
    # 1. Determine payload modality
    input_type = classify_payload(text_content, temp_path)

    # 2. Route to specialized forensic engines
    if input_type == "DOCUMENT":
        result = await verify_legal_document(file_path=temp_path, text_content=text_content)
    elif input_type == "PAYMENT":
        result = await verify_payment_data(file_path=temp_path, text_data=text_content)
    else:  # MESSAGE, LINK, OR APK
        result = await verify_text_and_links(text_content=text_content, file_path=temp_path)

    verdict = result.get("verdict", "SUSPICIOUS")
    reasons = result.get("reasons", [])
    confidence = float(result.get("confidence", 0.5))
    summary = result.get("summary", "Forensic analysis complete.")

    # 3. Generate local-language voice memo
    audio_data = None
    try:
        audio_data = await generate_voice_explanation(
            reasons=reasons,
            preferred_language=preferred_language,
            verdict=verdict
        )
    except Exception as e:
        # Voice memo failure should never block forensic verdict
        pass

    # 4. Format pre-filled report for 1930 / cybercrime.gov.in
    evidence_text = (text_content or "") + (f" [Uploaded file: {original_filename}]" if original_filename else "")
    dossier = build_cybercrime_dossier(result, evidence_text)

    return {
        "verdict": verdict,
        "confidence": confidence,
        "summary": summary,
        "reasons": reasons,
        "input_modality": input_type,
        "audio_base64": audio_data,
        "dossier": dossier,
        "metadata": {
            "preferred_language": preferred_language,
            "filename": original_filename,
            "has_audio": audio_data is not None
        }
    }


@app.post("/api/v1/verify", response_model=VerificationResponse)
async def verify_endpoint(
    text_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    preferred_language: str = Form("hi")
):
    """Multipart endpoint accepting text/links and uploaded documents/QR codes/APKs."""
    if not text_content and not file:
        raise HTTPException(status_code=400, detail="Provide text, link, or upload an artifact (image, PDF, QR, APK).")

    temp_path = None
    original_filename = file.filename if file else None

    try:
        if file:
            suffix = os.path.splitext(file.filename)[1] if file.filename else ".tmp"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as buffer:
                temp_path = buffer.name
                shutil.copyfileobj(file.file, buffer)

        response_data = await process_verification(
            text_content=text_content,
            temp_path=temp_path,
            preferred_language=preferred_language,
            original_filename=original_filename
        )
        return VerificationResponse(**response_data)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@app.post("/api/v1/verify-json", response_model=VerificationResponse)
async def verify_json_endpoint(payload: VerifyJsonRequest):
    """JSON API endpoint accepting raw text and optional base64-encoded files."""
    if not payload.text_content and not payload.file_base64:
        raise HTTPException(status_code=400, detail="Provide text_content or file_base64.")

    temp_path = None
    original_filename = payload.file_name or "artifact"

    try:
        if payload.file_base64:
            suffix = os.path.splitext(original_filename)[1] or ".bin"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as buffer:
                temp_path = buffer.name
                buffer.write(base64.b64decode(payload.file_base64))

        response_data = await process_verification(
            text_content=payload.text_content,
            temp_path=temp_path,
            preferred_language=payload.preferred_language,
            original_filename=original_filename
        )
        return VerificationResponse(**response_data)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "app": APP_TITLE,
        "version": APP_VERSION,
        "helpline": HELPLINE_NUMBER,
        "portal": CYBERCRIME_PORTAL,
        "pipelines": ["LEGAL_DOCUMENT", "PAYMENT_INTENT_QR", "MESSAGE_PHISHING_APK"]
    }


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Interactive, visually striking KavachAI web client."""
    return HTMLResponse(content=INDEX_HTML)


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KavachAI — Universal Scam & Fraud Forensics</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --surface: #101626;
            --surface-elevated: #162035;
            --border: #23314f;
            --border-hover: #3b5080;
            --accent: #ff4d4d;
            --accent-glow: rgba(255, 77, 77, 0.25);
            --primary: #3b82f6;
            --primary-glow: rgba(59, 130, 246, 0.25);
            --warning: #f59e0b;
            --success: #10b981;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --radius-lg: 16px;
            --radius-md: 12px;
            --radius-sm: 8px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            line-height: 1.5;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 15% 10%, rgba(59, 130, 246, 0.12), transparent 40%),
                radial-gradient(circle at 85% 15%, rgba(255, 77, 77, 0.10), transparent 45%),
                radial-gradient(circle at 50% 90%, rgba(16, 185, 129, 0.08), transparent 50%);
        }

        .header-bar {
            padding: 24px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(12px);
            background: rgba(9, 13, 22, 0.7);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }

        .shield-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #ff4d4d, #3b82f6);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 20px rgba(255, 77, 77, 0.4);
        }

        .brand h1 {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(90deg, #ffffff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand span {
            color: #ff4d4d;
        }

        .badge-1930 {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 77, 77, 0.12);
            border: 1px solid rgba(255, 77, 77, 0.3);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            color: #ff8080;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background: #ff4d4d;
            border-radius: 50%;
            box-shadow: 0 0 8px #ff4d4d;
            animation: pulse 1.8s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 77, 77, 0.7); }
            70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(255, 77, 77, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 77, 77, 0); }
        }

        .container {
            max-width: 1080px;
            margin: 0 auto;
            padding: 40px 24px 80px;
        }

        .hero {
            text-align: center;
            margin-bottom: 40px;
        }

        .hero h2 {
            font-size: 40px;
            font-weight: 800;
            margin-bottom: 12px;
            letter-spacing: -1px;
            line-height: 1.2;
        }

        .hero p {
            font-size: 17px;
            color: var(--text-muted);
            max-width: 640px;
            margin: 0 auto;
        }

        .preset-bar {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }

        .preset-chip {
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .preset-chip:hover {
            border-color: var(--primary);
            color: var(--text-main);
            transform: translateY(-1px);
        }

        .main-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 28px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            margin-bottom: 32px;
        }

        .input-group {
            margin-bottom: 20px;
        }

        .input-label {
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 8px;
        }

        textarea {
            width: 100%;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 16px;
            color: var(--text-main);
            font-family: inherit;
            font-size: 15px;
            resize: vertical;
            min-height: 110px;
            outline: none;
            transition: border-color 0.2s;
        }

        textarea:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-glow);
        }

        .dropzone {
            border: 2px dashed var(--border);
            border-radius: var(--radius-md);
            padding: 24px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            background: rgba(16, 22, 38, 0.5);
        }

        .dropzone:hover, .dropzone.dragover {
            border-color: var(--primary);
            background: rgba(59, 130, 246, 0.05);
        }

        .dropzone-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }

        .dropzone-icon {
            font-size: 28px;
        }

        .dropzone-title {
            font-size: 15px;
            font-weight: 600;
        }

        .dropzone-sub {
            font-size: 13px;
            color: var(--text-muted);
        }

        .file-preview {
            display: none;
            align-items: center;
            justify-content: space-between;
            background: var(--surface-elevated);
            padding: 10px 16px;
            border-radius: var(--radius-sm);
            margin-top: 12px;
            font-size: 14px;
        }

        .remove-file {
            color: #ff6b6b;
            cursor: pointer;
            font-weight: bold;
        }

        .controls-row {
            display: flex;
            gap: 16px;
            align-items: center;
            justify-content: space-between;
            margin-top: 24px;
            flex-wrap: wrap;
        }

        .lang-toggle {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: var(--text-muted);
        }

        .lang-btn {
            background: var(--surface-elevated);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 6px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }

        .lang-btn.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .verify-btn {
            background: linear-gradient(135deg, #ff4d4d, #dc2626);
            color: white;
            border: none;
            padding: 14px 36px;
            border-radius: var(--radius-md);
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 0.5px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 20px var(--accent-glow);
            transition: all 0.2s ease;
        }

        .verify-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(255, 77, 77, 0.4);
        }

        .verify-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* Results Card */
        .verdict-card {
            display: none;
            border-radius: var(--radius-lg);
            padding: 32px;
            margin-top: 32px;
            animation: slideUp 0.35s ease;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .verdict-DANGEROUS_SCAM {
            background: linear-gradient(180deg, rgba(61, 18, 20, 0.95), rgba(28, 10, 12, 0.95));
            border: 1px solid #f85149;
        }

        .verdict-SUSPICIOUS {
            background: linear-gradient(180deg, rgba(58, 39, 7, 0.95), rgba(30, 20, 4, 0.95));
            border: 1px solid #d29922;
        }

        .verdict-AUTHENTIC {
            background: linear-gradient(180deg, rgba(16, 50, 30, 0.95), rgba(8, 25, 15, 0.95));
            border: 1px solid #10b981;
        }

        .verdict-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 16px;
        }

        .verdict-title-box h3 {
            font-size: 26px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .verdict-score {
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            padding: 6px 14px;
            border-radius: 20px;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .verdict-summary {
            font-size: 18px;
            font-weight: 600;
            line-height: 1.4;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .reasons-title {
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 12px;
            font-weight: 700;
        }

        .reasons-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 28px;
        }

        .reasons-list li {
            background: rgba(0, 0, 0, 0.25);
            padding: 12px 16px;
            border-radius: var(--radius-sm);
            border-left: 4px solid #f85149;
            font-size: 15px;
            line-height: 1.5;
        }

        .action-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-top: 24px;
        }

        .action-card {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: var(--radius-md);
            padding: 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .action-card h4 {
            font-size: 15px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .action-card p {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 14px;
        }

        .btn-audio {
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: var(--radius-sm);
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-size: 14px;
        }

        .btn-audio:hover {
            background: #1d4ed8;
        }

        .btn-dossier {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 10px 16px;
            border-radius: var(--radius-sm);
            font-weight: 600;
            cursor: pointer;
            font-size: 14px;
        }

        .btn-dossier:hover {
            background: rgba(255, 255, 255, 0.15);
        }

        /* Dossier Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(8px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .modal-content {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            max-width: 760px;
            width: 100%;
            max-height: 85vh;
            overflow-y: auto;
            padding: 28px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.6);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text-muted);
            font-size: 24px;
            cursor: pointer;
        }

        .dossier-box {
            background: #090d16;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 18px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12.5px;
            color: #cbd5e1;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 380px;
            margin-bottom: 20px;
        }

        .footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 13px;
            margin-top: 60px;
        }

        .spinner {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>

    <header class="header-bar">
        <a href="/" class="brand">
            <div class="shield-icon">🛡️</div>
            <h1>KAVACH<span>AI</span></h1>
        </a>
        <div class="badge-1930">
            <span class="pulse-dot"></span>
            National Cyber Helpline 1930 Active
        </div>
    </header>

    <main class="container">
        <section class="hero">
            <h2>Instant Scam Forensic Verification</h2>
            <p>Drop a court notice, police summons, QR code, UPI handle, electricity SMS, or APK file. Receive statutory legal validation and evidence-backed fraud verdicts in seconds.</p>

            <div class="preset-bar">
                <div class="preset-chip" onclick="loadSample('digital_arrest')">⚖️ Test "Digital Arrest" Notice</div>
                <div class="preset-chip" onclick="loadSample('power_cut')">⚡ Test Electricity Power-Cut SMS</div>
                <div class="preset-chip" onclick="loadSample('upi_refund')">💸 Test UPI Refund QR / Intent Inversion</div>
                <div class="preset-chip" onclick="loadSample('sim_block')">📱 Test SIM Block Phishing</div>
            </div>
        </section>

        <section class="main-card">
            <div class="input-group">
                <div class="input-label">
                    <span>Message Text, Payment Link, or UPI URI</span>
                    <span id="charCount">0 chars</span>
                </div>
                <textarea id="textContent" placeholder="Paste suspicious SMS, WhatsApp message, UPI ID (e.g. cybercrime-police@okhdfcbank), or payment link here..."></textarea>
            </div>

            <div class="input-group">
                <div class="input-label">
                    <span>Upload Artifact (Image, PDF, QR Code, or APK)</span>
                </div>
                <div class="dropzone" id="dropzone">
                    <input type="file" id="fileInput" style="display: none;" accept="image/*,.pdf,.apk">
                    <div class="dropzone-content">
                        <div class="dropzone-icon">📥</div>
                        <div class="dropzone-title">Click to upload or drag & drop artifact</div>
                        <div class="dropzone-sub">Supports Fake Court Summons (PDF/JPG), UPI QR codes, or Suspicious .APK files</div>
                    </div>
                </div>
                <div class="file-preview" id="filePreview">
                    <span id="fileNameDisplay">file.pdf</span>
                    <span class="remove-file" onclick="clearFile()">✕ Remove</span>
                </div>
            </div>

            <div class="controls-row">
                <div class="lang-toggle">
                    <span>Voice Memo Language:</span>
                    <button type="button" class="lang-btn active" id="btnHi" onclick="setLang('hi')">हिंदी (Hindi)</button>
                    <button type="button" class="lang-btn" id="btnEn" onclick="setLang('en')">English</button>
                </div>

                <button class="verify-btn" id="verifyBtn" onclick="runVerification()">
                    <span id="btnIcon">⚡</span>
                    <span id="btnText">VERIFY FORENSICS</span>
                </button>
            </div>
        </section>

        <!-- Verdict Display -->
        <section class="verdict-card" id="verdictCard">
            <div class="verdict-header">
                <div class="verdict-title-box">
                    <h3 id="verdictHeading">🚨 DANGEROUS SCAM DETECTED</h3>
                    <div style="font-size: 14px; color: var(--text-muted); margin-top: 4px;" id="modalityLabel">Modality: Legal Document</div>
                </div>
                <div class="verdict-score" id="confidenceBadge">Confidence: 99%</div>
            </div>

            <div class="verdict-summary" id="verdictSummary">
                This document is a criminal forgery. Indian statutory law does not recognize "Digital Arrest" or Skype court depositions.
            </div>

            <div class="reasons-title">Forensic Evidence & Statues Triggered</div>
            <ul class="reasons-list" id="reasonsList">
                <!-- Generated dynamically -->
            </ul>

            <div class="action-grid">
                <div class="action-card">
                    <div>
                        <h4>🔊 Audio Voice Memo</h4>
                        <p>15-second plain-language audio advisory for senior citizens or urgent family warning.</p>
                    </div>
                    <button class="btn-audio" id="playAudioBtn" onclick="playVoiceWarning()">
                        <span>▶</span> Play Voice Warning
                    </button>
                </div>

                <div class="action-card">
                    <div>
                        <h4>📋 1930 Cybercrime Dossier</h4>
                        <p>Pre-filled incident complaint with BNS & IT Act legal sections ready for cybercrime.gov.in.</p>
                    </div>
                    <button class="btn-dossier" onclick="openDossierModal()">
                        View Formal Report
                    </button>
                </div>
            </div>
        </section>

        <footer class="footer">
            KavachAI Forensic Engine · Compliant with Bharatiya Nyaya Sanhita (BNS) & IT Act, 2000 · Emergency Helpline 1930
        </footer>
    </main>

    <!-- Dossier Modal -->
    <div class="modal-overlay" id="dossierModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>National Cybercrime Reporting Dossier (Form 1930)</h3>
                <button class="modal-close" onclick="closeDossierModal()">&times;</button>
            </div>
            <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 14px;">
                Copy this pre-formatted complaint directly into <a href="https://cybercrime.gov.in" target="_blank" style="color: #3b82f6;">cybercrime.gov.in</a> or dictate it when calling 1930.
            </p>
            <div class="dossier-box" id="dossierTextContent"></div>
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button class="btn-dossier" onclick="copyDossier()">📋 Copy Incident FIR</button>
                <button class="btn-audio" onclick="closeDossierModal()">Done</button>
            </div>
        </div>
    </div>

    <script>
        let selectedFile = null;
        let preferredLang = 'hi';
        let currentAudioBase64 = null;
        let currentDossier = null;
        let currentAudioObj = null;

        const dropzone = document.getElementById('dropzone');
        const fileInput = document.getElementById('fileInput');
        const filePreview = document.getElementById('filePreview');
        const fileNameDisplay = document.getElementById('fileNameDisplay');
        const textContent = document.getElementById('textContent');
        const charCount = document.getElementById('charCount');

        textContent.addEventListener('input', () => {
            charCount.textContent = `${textContent.value.length} chars`;
        });

        dropzone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                selectedFile = e.target.files[0];
                fileNameDisplay.textContent = `${selectedFile.name} (${Math.round(selectedFile.size / 1024)} KB)`;
                filePreview.style.display = 'flex';
            }
        });

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                selectedFile = e.dataTransfer.files[0];
                fileNameDisplay.textContent = `${selectedFile.name} (${Math.round(selectedFile.size / 1024)} KB)`;
                filePreview.style.display = 'flex';
            }
        });

        function clearFile() {
            selectedFile = null;
            fileInput.value = '';
            filePreview.style.display = 'none';
        }

        function setLang(lang) {
            preferredLang = lang;
            document.getElementById('btnHi').classList.toggle('active', lang === 'hi');
            document.getElementById('btnEn').classList.toggle('active', lang === 'en');
        }

        function loadSample(type) {
            clearFile();
            if (type === 'digital_arrest') {
                textContent.value = "SUPREME COURT OF INDIA / CBI HEADQUARTERS NOTICE: You are placed under 24-hour Digital Arrest for illegal money laundering. Do not leave your room. Join Skype video interrogation at 10 AM. Transfer security clearance deposit of Rs 1,50,000 to RBI Clearance Escrow: rbi-escrow@okhdfcbank.";
            } else if (type === 'power_cut') {
                textContent.value = "Dear Consumer, your electricity power will be disconnected tonight at 09:30 PM because your previous month bill was not updated. Immediately contact our electricity officer Mr. Sharma at 9876543210 or install our quick bill app from http://bijli-bill-update.online/app.apk";
            } else if (type === 'upi_refund') {
                textContent.value = "upi://pay?pa=refund-desk@okhdfcbank&pn=ElectricityRefundDesk&am=5000&cu=INR&tn=Click_to_receive_cashback_refund";
            } else if (type === 'sim_block') {
                textContent.value = "URGENT: Your mobile SIM card service will be permanently blocked in 2 hours due to unverified KYC. Click http://sim-kyc-verify.xyz/update to verify Aadhaar now or call 9123456789.";
            }
            charCount.textContent = `${textContent.value.length} chars`;
        }

        async function runVerification() {
            const text = textContent.value.trim();
            if (!text && !selectedFile) {
                alert('Please enter text/link or upload an artifact to verify.');
                return;
            }

            const verifyBtn = document.getElementById('verifyBtn');
            const btnText = document.getElementById('btnText');
            const btnIcon = document.getElementById('btnIcon');

            verifyBtn.disabled = true;
            btnText.textContent = "VERIFYING FORENSICS...";
            btnIcon.innerHTML = `<span class="spinner"></span>`;

            const formData = new FormData();
            if (text) formData.append('text_content', text);
            if (selectedFile) formData.append('file', selectedFile);
            formData.append('preferred_language', preferredLang);

            try {
                const resp = await fetch('/api/v1/verify', {
                    method: 'POST',
                    body: formData
                });

                if (!resp.ok) {
                    const err = await resp.json();
                    throw new Error(err.detail || 'Forensic verification failed.');
                }

                const data = await resp.json();
                renderVerdict(data);
            } catch (err) {
                alert('Error: ' + err.message);
            } finally {
                verifyBtn.disabled = false;
                btnText.textContent = "VERIFY FORENSICS";
                btnIcon.textContent = "⚡";
            }
        }

        function renderVerdict(data) {
            const card = document.getElementById('verdictCard');
            card.style.display = 'block';
            card.className = `verdict-card verdict-${data.verdict}`;

            const heading = document.getElementById('verdictHeading');
            if (data.verdict === 'DANGEROUS_SCAM') {
                heading.textContent = '🚨 DANGEROUS SCAM DETECTED';
            } else if (data.verdict === 'SUSPICIOUS') {
                heading.textContent = '⚠️ SUSPICIOUS ACTIVITY DETECTED';
            } else {
                heading.textContent = '✅ AUTHENTIC / LOW RISK';
            }

            document.getElementById('modalityLabel').textContent = `Pipeline: ${data.input_modality.replace('_', ' ')}`;
            document.getElementById('confidenceBadge').textContent = `Confidence: ${(data.confidence * 100).toFixed(0)}%`;
            document.getElementById('verdictSummary').textContent = data.summary;

            const list = document.getElementById('reasonsList');
            list.innerHTML = '';
            (data.reasons || []).forEach(r => {
                const li = document.createElement('li');
                li.textContent = r;
                list.appendChild(li);
            });

            currentAudioBase64 = data.audio_base64;
            currentDossier = data.dossier;

            const playAudioBtn = document.getElementById('playAudioBtn');
            if (currentAudioBase64) {
                playAudioBtn.style.opacity = '1';
                playAudioBtn.disabled = false;
            } else {
                playAudioBtn.style.opacity = '0.5';
                playAudioBtn.disabled = true;
            }

            card.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function playVoiceWarning() {
            if (!currentAudioBase64) {
                alert('Audio warning is currently unavailable.');
                return;
            }

            if (currentAudioObj) {
                currentAudioObj.pause();
                currentAudioObj = null;
            }

            currentAudioObj = new Audio('data:audio/mp3;base64,' + currentAudioBase64);
            currentAudioObj.play().catch(e => console.log('Audio autoplay blocked:', e));
        }

        function openDossierModal() {
            if (!currentDossier) {
                alert('Dossier is not ready.');
                return;
            }
            const modal = document.getElementById('dossierModal');
            const box = document.getElementById('dossierTextContent');
            box.textContent = currentDossier.fir_narrative_template || JSON.stringify(currentDossier, null, 2);
            modal.style.display = 'flex';
        }

        function closeDossierModal() {
            document.getElementById('dossierModal').style.display = 'none';
        }

        function copyDossier() {
            const text = document.getElementById('dossierTextContent').textContent;
            navigator.clipboard.writeText(text).then(() => {
                alert('Copied to clipboard! Ready to paste into 1930 / cybercrime.gov.in portal.');
            });
        }
    </script>
</body>
</html>
"""
