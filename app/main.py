from pathlib import Path
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

from app.core.config import APP_TITLE, APP_VERSION, HELPLINE_NUMBER, CYBERCRIME_PORTAL, BANK_FREEZE_DIRECTORY
from app.core.rules import IMPOSSIBLE_LEGAL_PROCEDURES, URGENCY_PATTERNS
from app.engines.classifier import classify_payload
from app.engines.legal_engine import verify_legal_document
from app.engines.payment_engine import verify_payment_data
from app.engines.text_engine import verify_text_and_links
from app.engines.audio_engine import verify_audio_deepfake
from app.services.tts_service import generate_voice_explanation
from app.services.dossier import build_cybercrime_dossier
from app.services.pdf_service import generate_dossier_pdf

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
    input_modality: str = Field(..., description="DOCUMENT | PAYMENT | MESSAGE_LINK_APK | AUDIO_VOICE")
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
    elif input_type == "AUDIO_VOICE":
        result = await verify_audio_deepfake(file_path=temp_path, text_content=text_content)
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
        "pipelines": [
            "LEGAL_DOCUMENT",
            "PAYMENT_INTENT_QR",
            "MESSAGE_PHISHING_APK",
            "AUDIO_VOICE_DEEPFAKE",
            "SEBI_TASK_SCAM"
        ]
    }


@app.post("/api/v1/dossier/pdf")
async def generate_dossier_pdf_endpoint(dossier: Dict[str, Any]):
    """Generate Section 63 BSA / 65B compliant electronic evidence PDF."""
    try:
        pdf_bytes = generate_dossier_pdf(dossier)
        dossier_id = dossier.get("dossier_id", "INCIDENT")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="KavachAI_Dossier_{dossier_id}.pdf"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


class VoiceMemoRequest(BaseModel):
    reasons: List[str] = Field(default_factory=list)
    preferred_language: str = "hi"
    verdict: str = "DANGEROUS_SCAM"


@app.post("/api/v1/voice-memo")
async def generate_voice_memo_endpoint(req: VoiceMemoRequest):
    """Generate audio memo on-the-fly for any regional language (te, kn, ta, mr, hi, en)."""
    audio_base64 = await generate_voice_explanation(
        reasons=req.reasons,
        preferred_language=req.preferred_language,
        verdict=req.verdict
    )
    if not audio_base64:
        raise HTTPException(status_code=500, detail="Voice synthesis failed.")
    return {"audio_base64": audio_base64, "language": req.preferred_language}


@app.get("/api/v1/freeze-guide")
async def freeze_guide_endpoint():
    """Golden Hour 1-Click Bank Account Freeze Guide."""
    return {
        "helpline": HELPLINE_NUMBER,
        "emergency_dial": "tel:1930",
        "golden_hour_window": "First 60-120 minutes post transaction",
        "banks": BANK_FREEZE_DIRECTORY
    }


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Interactive, visually striking KavachAI web client."""
    return HTMLResponse(content=INDEX_HTML)


TEMPLATES_DIR = Path(__file__).parent / "templates"
INDEX_HTML_PATH = TEMPLATES_DIR / "index.html"
INDEX_HTML = INDEX_HTML_PATH.read_text(encoding="utf-8") if INDEX_HTML_PATH.exists() else ""
