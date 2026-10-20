# KavachAI (कवच AI) — Universal Forensic Scam Verification Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production-009688.svg)](https://fastapi.tiangolo.com)
[![Expo: React Native](https://img.shields.io/badge/React_Native-Expo_51-black.svg)](https://expo.dev)
[![National Cyber Helpline](https://img.shields.io/badge/Helpline-1930_Active-red.svg)](https://cybercrime.gov.in)
[![BSA 2023](https://img.shields.io/badge/BSA_2023-Section_63_Admissible-green.svg)](https://cybercrime.gov.in)

> **KavachAI** is an epistemic, universal scam verification platform. Citizens drop court notices, police warrants, UPI links, QR codes, Android .APK apps, SMS messages, or audio voicemails to receive an **instant forensic verdict**, **plain-language statutory legal breakdown**, **15-second regional-language voice de-escalation**, **1-Click Golden Hour Bank Freeze guide**, and **court-admissible Section 63 BSA PDF evidence dossier**.

---

## 🏛️ System Pipeline Architecture

```text
                     ┌────────────────────────────────────────┐
                     │          UNIVERSAL CLIENT INPUT        │
                     │  Web Client & React Native / Expo App  │
                     └───────────────────┬────────────────────┘
                                         │ (Multipart POST /api/v1/verify)
                                         ▼
                     ┌────────────────────────────────────────┐
                     │             FASTAPI ROUTER             │
                     │      Modality Classifier & Router      │
                     └───────┬───────┬───────┬────────┬───────┘
                             │       │       │        │
             ┌───────────────┘       │       │        └───────────────┐
             ▼                       ▼       ▼                        ▼
    ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │ 1. LEGAL / DOC  │    │  2. PAYMENT / QR │    │ 3. MESSAGE/APK   │    │ 4. AUDIO / VOICE │
    │    PIPELINE     │    │     PIPELINE     │    │    & SEBI AUDIT  │    │    DEEPFAKE      │
    ├─────────────────┤    ├──────────────────┤    ├──────────────────┤    ├──────────────────┤
    │• PaddleOCR      │    │• pyzbar QR parse │    │• SHA-256 Hashing │    │• Spectral check  │
    │• Regex Entities │    │• UPI URI parser  │    │• VirusTotal v3   │    │• Vocoder roll-off│
    │• eCourts CNR API│    │• Collect vs Pay  │    │• Offline Manifest│    │• Room acoustics  │
    │• Law rule graph │    │  intent check    │    │• SEBI/Task scam  │    │• Secret challenge│
    └────────┬────────┘    └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
             │                      │                       │                       │
             └──────────────────────┼───────────────────────┼───────────────────────┘
                                    ▼
                     ┌────────────────────────────────────────┐
                     │        EPISTEMIC VERDICT ENGINE        │
                     │    Confidence Score & Evidence Matrix  │
                     └───────────────────┬────────────────────┘
                                         ▼
                     ┌────────────────────────────────────────┐
                     │            ACTION DISPATCHER           │
                     │ • 6-Language Regional Voice Synthesis  │
                     │ • Section 63 BSA PDF Dossier Export    │
                     │ • "Golden Hour" 1-Click Bank Freeze    │
                     │ • 1930 Cybercrime Portal FIR Narrative │
                     └────────────────────────────────────────┘
```

---

## 🔍 Core Capabilities & Specialized Pipelines

### 1. Regional Audio Warnings (6 Languages) (`app/services/tts_service.py`)
Provides immediate spoken de-escalation in victims' native tongues, reassuring them that police never arrest citizens via video calls:
- **Hindi (`hi`)**: `hi-IN-SwaraNeural`
- **English (`en`)**: `en-IN-NeerjaNeural`
- **Telugu (`te`)**: `te-IN-MohanNeural`
- **Kannada (`kn`)**: `kn-IN-GaganNeural`
- **Tamil (`ta`)**: `ta-IN-PallaviNeural`
- **Marathi (`mr`)**: `mr-IN-AarohiNeural`

### 2. Deep APK & VirusTotal Threat Intelligence (`app/engines/text_engine.py`)
Combats malicious "CBI Support" or fake utility APKs sent over WhatsApp/Telegram:
- **SHA-256 Fingerprinting**: Generates immutable cryptographic hashes for evidence and indexing.
- **VirusTotal API v3**: Checks file hashes against 70+ antivirus engines, reporting exact detection ratios (e.g. `42/72 engines flagged`) and malware family labels (e.g. `Trojan-Banker.AndroidOS.Anatsa`).
- **Offline Manifest Fallback**: If an APK is unindexed or zero-day, parses `AndroidManifest.xml` locally to detect high-risk permissions (`BIND_ACCESSIBILITY_SERVICE`, `RECEIVE_SMS`, `READ_SMS`, `SYSTEM_ALERT_WINDOW`, `REQUEST_INSTALL_PACKAGES`).

### 3. "Golden Hour" 1-Click Bank Account Freeze Guide (`app/core/config.py`, `/api/v1/freeze-guide`)
In financial cyber fraud, the first 60–120 minutes are critical:
- **Direct 1930 Auto-Dial**: Deep-links to National Cyber Financial Fraud helpline `tel:1930`.
- **Bank Emergency Directory**: Pre-configured instant SMS shortcodes and toll-free hotlines for major banks (SBI, HDFC, ICICI, Axis, PNB, Canara).
- **Automated Dispute Generator**: Fills bank dispute templates citing victim UTR, debited account, and suspect VPA.

### 4. Voice Clone & Deepfake Audio Interceptor (`app/engines/audio_engine.py`)
Intercepts extortion schemes exploiting cloned voices of children or relatives ("Dad, I've had an accident, send bail money"):
- **Spectral Consistency Check**: Inspects pitch contour stability, zero-crossing rate regularity, and high-frequency roll-off typical of neural vocoders.
- **Room Acoustic Verification**: Flags absolute digital silence (< -65 dB) lacking natural ambient room reverberation.
- **Out-of-Band Family Challenge**: Instructs victims to prompt callers with pre-set family secret passphrases.

### 5. Fake SEBI Investment & "Task Scam" Group Auditor (`app/engines/text_engine.py`)
- **SEBI Regulation Compliance**: Flags illegal guaranteed returns, institutional trading pools, and VIP insider stock tips prohibited under SEBI (PFUTP) Regulations.
- **International Syndicate Numbers**: Detects group admins operating from foreign virtual prefixes (`+84` Vietnam, `+855` Cambodia, `+234` Nigeria, `+92` Pakistan, `+63` Philippines, `+95` Myanmar).
- **Task Scam Detection**: Intercepts "Like YouTube videos / Google reviews for ₹50–₹150" part-time job schemes.

### 6. Section 63 BSA Compliant PDF Evidence Export (`app/services/pdf_service.py`, `/api/v1/dossier/pdf`)
- Converts incident dossiers into court-admissible PDF summaries conforming to **Section 63 of Bharatiya Sakshya Adhiniyam (BSA), 2023** (Section 65B Indian Evidence Act).
- Embeds SHA-256 cryptographic hashes, NJDG CNR checks, statutory sections, suspect identifiers, and formal FIR narratives for police cyber cells.

---

## 🚀 Quickstart & Installation

### Backend Server

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run test suite (16 tests verifying all pipelines)
pytest -v tests/test_kavach.py

# 3. Start development / production server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server exposes:
- **Interactive Web UI**: `http://localhost:8000/`
- **Forensic Verification Endpoint**: `POST http://localhost:8000/api/v1/verify`
- **JSON Endpoint**: `POST http://localhost:8000/api/v1/verify-json`
- **PDF Evidence Export**: `POST http://localhost:8000/api/v1/dossier/pdf`
- **Golden Hour Freeze Guide**: `GET http://localhost:8000/api/v1/freeze-guide`
- **Health Check**: `GET http://localhost:8000/api/v1/health`

### Mobile App (React Native Expo)

```bash
cd kavach-mobile
npm install
npx expo start --web
```

---

## 📡 API Reference

### `POST /api/v1/verify`
Multipart form submission accepting text messages, links, and uploaded files.

**Parameters:**
- `text_content` *(optional string)*: Message body, payment link, or URL.
- `file` *(optional file)*: Image (JPG/PNG), Document (PDF), QR Code, APK, or Audio clip.
- `preferred_language` *(optional string)*: `"hi"`, `"en"`, `"te"`, `"kn"`, `"ta"`, or `"mr"`.

### `POST /api/v1/dossier/pdf`
Accepts dossier JSON and returns court-admissible Section 63 BSA binary PDF stream (`application/pdf`).

### `GET /api/v1/freeze-guide`
Returns 1930 helpline metadata and instant SMS/hotline lock instructions across commercial banks.

---

## 🧪 Verification & Test Suite

The test suite validates the entire verification lifecycle:
```bash
pytest -v tests/test_kavach.py
```

Covering all 16 test modules:
- ✅ **Classifier Routing**: Directs payloads to Document, Payment, Text/APK, or Audio pipelines.
- ✅ **Digital Arrest Notice**: Flags fake Supreme Court/CBI detention notices.
- ✅ **UPI Intent Inversion**: Identifies debit reverse-charge intents and fake consumer VPAs.
- ✅ **Power-Cut Extortion**: Identifies fake electricity disconnection SMS threats.
- ✅ **Benign Communication**: Confirms authentic messages pass with high confidence.
- ✅ **1930 Dossier Formulation**: Verifies SHA-256 evidentiary chain-of-custody and BNS sections.
- ✅ **Regional Voice Scripts**: Validates Hindi, English, Telugu, Kannada, Tamil, and Marathi.
- ✅ **SEBI & Task Scam Auditor**: Audits fake investment pools and cross-border virtual prefixes.
- ✅ **Golden Hour Freeze Guide**: Tests bank directory and 1930 hotline retrieval.
- ✅ **Deepfake Audio Interceptor**: Detects voice clone extortion and family passphrase challenges.
- ✅ **Section 63 BSA PDF Generator**: Validates `%PDF-` document synthesis and download routes.
- ✅ **APK Threat Intel & Manifest**: Tests SHA-256 hashing and offline AndroidManifest analysis.

---

## ⚖️ Legal Framework

KavachAI aligns with:
- **Bharatiya Sakshya Adhiniyam (BSA), 2023** (Section 63: Admissibility of Electronic Records)
- **Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023** (Section 173: Information in Cognizable Cases, Sec 35)
- **Bharatiya Nyaya Sanhita (BNS), 2023** (Sections 318(4) Cheating, 308(2) Extortion, 204 Impersonation)
- **Information Technology Act, 2000** (Sections 43, 66, 66D)
- **National Cybercrime Helpline**: Dial **1930** / [cybercrime.gov.in](https://cybercrime.gov.in)
