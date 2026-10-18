# KavachAI (कवच AI) — Universal Forensic Scam Verification Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production-009688.svg)](https://fastapi.tiangolo.com)
[![Expo: React Native](https://img.shields.io/badge/React_Native-Expo_51-black.svg)](https://expo.dev)
[![National Cyber Helpline](https://img.shields.io/badge/Helpline-1930_Active-red.svg)](https://cybercrime.gov.in)

> **KavachAI** is a universal, on-demand scam verification platform. Users can drop an image, PDF document, SMS message, link, or payment QR code and receive an **instant forensic verdict**, **plain-language statutory legal breakdown**, **15-second local-language voice advisory**, and **pre-filled Form 1930 cybercrime dossier**.

---

## 🏛️ System Pipeline Architecture

```text
                    ┌───────────────────────────────┐
                    │       REACT NATIVE / EXPO     │
                    │   Single Universal Input UI   │
                    └───────────────┬───────────────┘
                                    │ (Multipart POST /api/v1/verify)
                                    ▼
                    ┌───────────────────────────────┐
                    │         FASTAPI ROUTER        │
                    │   Input Classifier & Normalizer│
                    └───────┬───────┬───────┬───────┘
                            │       │       │
            ┌───────────────┘       │       └───────────────┐
            ▼                       ▼                       ▼
   ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
   │ 1. LEGAL / DOC  │    │  2. PAYMENT / QR │    │ 3. MESSAGE/LINK  │
   │    PIPELINE     │    │     PIPELINE     │    │     PIPELINE     │
   ├─────────────────┤    ├──────────────────┤    ├──────────────────┤
   │• PaddleOCR      │    │• pyzbar QR parse │    │• Domain age look-│
   │• Regex Entities │    │• UPI URI parser  │    │  up (Whois/RDAP) │
   │• eCourts CNR API│    │• Collect vs Pay  │    │• APK static hash │
   │• Law rule graph │    │  intent check    │    │• Urgency NLP tag │
   └────────┬────────┘    └────────┬─────────┘    └────────┬─────────┘
            │                      │                       │
            └──────────────────────┼───────────────────────┘
                                   ▼
                    ┌───────────────────────────────┐
                    │    EPISTEMIC VERDICT ENGINE   │
                    │   Confidence Score & Reasons  │
                    └──────────────┬────────────────┘
                                   ▼
                    ┌───────────────────────────────┐
                    │       ACTION DISPATCHER       │
                    │ • Local TTS Audio Generator   │
                    │ • 1930 / Cybercrime Dossier   │
                    │ • Emergency Action Checklist  │
                    └───────────────────────────────┘
```

---

## 🔍 Specialized Forensic Pipelines

### 1. Legal / Document Pipeline (`app/engines/legal_engine.py`)
- **Epistemic Law Check**: NetworkX procedural graph encoding impossibility of fictitious judicial concepts like **"Digital Arrest"**, Skype video interrogations, and cash security deposits under the *Bharatiya Nagarik Suraksha Sanhita (BNSS)* and *CrPC*.
- **eCourts CNR Standard**: Validates 16-character High Court and District Court Case Numbers against the National Judicial Data Grid (NJDG) standard regex `[A-Z]{4}\d{12}`.
- **Multimodal OCR**: Hybrid extraction with `PaddleOCR` (English/Hindi) and PDF text parsing.

### 2. Payment / QR Pipeline (`app/engines/payment_engine.py`)
- **Intent Inversion Audit**: Decodes `upi://pay` payloads to alert users when a QR code/link will **DEBIT** money rather than credit or refund.
- **PSP Handle Impersonation**: Audits whether official agencies (Police, CBI, Courts, Electricity) are using personal consumer PSP handles (`@okhdfcbank`, `@okaxis`, `@oksbi`, `@paytm`).

### 3. Message / Phishing / APK Pipeline (`app/engines/text_engine.py`)
- **Urgency NLP Classifier**: Detects psychological manipulation templates (Power-cut tonight, SIM deactivation in 2 hours, bank KYC freeze, lottery winnings).
- **Domain Age & TLD Threat**: Inspects domain registration age (< 72 hours) and suspicious TLDs (`.top`, `.xyz`, `.club`, `.cam`).
- **Android APK Static Audit**: Audits dangerous permission requests (`RECEIVE_SMS`, `READ_SMS`, `BIND_ACCESSIBILITY_SERVICE`, `SYSTEM_ALERT_WINDOW`).

### 4. Action Dispatcher (`app/services/`)
- **Voice Warning Synthesis**: Local Edge-TTS speech generation in **Hindi** (`hi-IN-SwaraNeural`) and **English** (`en-IN-NeerjaNeural`).
- **1930 Dossier Builder**: Creates an evidence-stamped, SHA-256 verified FIR narrative citing relevant sections of the **Bharatiya Nyaya Sanhita (BNS)** and **Information Technology Act, 2000**.

---

## 🚀 Quickstart & Installation

### Backend Server

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run test suite
pytest -v tests/test_kavach.py

# 3. Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server exposes:
- **Interactive Web UI**: `http://localhost:8000/`
- **Forensic Verification Endpoint**: `POST http://localhost:8000/api/v1/verify`
- **JSON Endpoint**: `POST http://localhost:8000/api/v1/verify-json`
- **Health Check**: `GET http://localhost:8000/api/v1/health`

### Mobile App (React Native Expo)

```bash
cd kavach-mobile
npm install
npx expo start
```

---

## 📡 API Reference

### `POST /api/v1/verify`
Multipart form submission accepting text messages, links, and uploaded files.

**Parameters:**
- `text_content` *(optional string)*: Message body, payment link, or URL.
- `file` *(optional file)*: Image (JPG/PNG), Document (PDF), QR Code, or APK.
- `preferred_language` *(optional string)*: `"hi"` (Hindi, default) or `"en"` (English).

**Response Schema (`VerificationResponse`):**
```json
{
  "verdict": "DANGEROUS_SCAM",
  "confidence": 0.99,
  "summary": "This document is a criminal forgery. Indian statutory law does not recognize 'Digital Arrest'.",
  "reasons": [
    "Claimed legal procedure ('Digital Arrest' or Video Deposition) does not legally exist in Indian Law.",
    "Court warrant lacks a verifiable 16-character CNR number mandated by Indian judiciary."
  ],
  "input_modality": "DOCUMENT",
  "audio_base64": "<base64-encoded MP3 audio>",
  "dossier": {
    "dossier_id": "KAVACH-20261018-8A2F1C4E",
    "helpline": "1930",
    "applicable_legal_sections": [
      "Section 66D, Information Technology Act, 2000",
      "Section 318(4), Bharatiya Nyaya Sanhita, 2023 / Sec 420 IPC"
    ],
    "fir_narrative_template": "--- NATIONAL CYBERCRIME REPORTING PORTAL (1930) - FIR NARRATIVE TEMPLATE ---..."
  }
}
```

---

## 🧪 Verification & Test Suite

The test suite validates the entire verification lifecycle:
```bash
pytest -v tests/test_kavach.py
```

Covering:
- ✅ **Classifier Routing**: Directs payloads to Document, Payment, or Text pipelines.
- ✅ **Digital Arrest Notice**: Flags fake Supreme Court/CBI detention notices.
- ✅ **UPI Intent Inversion**: Identifies debit reverse-charge intents and fake consumer VPAs.
- ✅ **Power-Cut Extortion**: Identifies fake electricity disconnection SMS threats.
- ✅ **Benign Communication**: Confirms authentic messages pass with high confidence.
- ✅ **1930 Dossier Formulation**: Verifies SHA-256 evidentiary chain-of-custody and BNS sections.
- ✅ **Edge-TTS Voice Scripts**: Validates Hindi and English natural speech generators.
- ✅ **End-to-End API Routes**: Tests `/api/v1/verify`, `/api/v1/verify-json`, and web dashboard.

---

## ⚖️ Legal Framework

KavachAI aligns with:
- **Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023** (Procedure for arrest and investigation)
- **Bharatiya Nyaya Sanhita (BNS), 2023** (Sections 318(4) Cheating, 308(2) Extortion, 204 Impersonation)
- **Information Technology Act, 2000** (Sections 66, 66D)
- **National Cybercrime Helpline**: Dial **1930** / [cybercrime.gov.in](https://cybercrime.gov.in)
