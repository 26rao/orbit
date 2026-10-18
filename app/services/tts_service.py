"""Voice Memo Synthesis Service.
Generates local-language audio warnings in Hindi and English for instant playback.
"""

import base64
import os
import tempfile
import logging
from typing import Optional, List

try:
    import edge_tts
except Exception:
    edge_tts = None

logger = logging.getLogger("kavach.tts")

VOICE_HINDI = "hi-IN-SwaraNeural"
VOICE_ENGLISH = "en-IN-NeerjaNeural"


def build_voice_script(reasons: List[str], preferred_language: str = "hi", verdict: str = "DANGEROUS_SCAM") -> str:
    """Compose concise 15-second natural language warning script."""
    if preferred_language == "hi":
        if verdict == "DANGEROUS_SCAM":
            script = (
                "सावधान! कवच ए आई की जांच में यह एक खतरनाक स्कैम और फ्रॉड पाया गया है। "
                "भारतीय कानून में डिजिटल अरेस्ट या वीडियो कॉल पर गिरफ्तारी का कोई नियम नहीं है। "
                "किसी को भी पैसे न भेजें और तुरंत राष्ट्रीय साइबर हेल्पलाइन 1930 पर शिकायत दर्ज करें।"
            )
        else:
            script = (
                "ध्यान दें! यह संदेश या पेमेंट संदिग्ध है। किसी भी अनजान लिंक पर क्लिक न करें "
                "और अपना यूपीआई पिन कभी न डालें।"
            )
    else:
        if verdict == "DANGEROUS_SCAM":
            script = (
                "Alert! Kavach AI forensic analysis confirms this is a dangerous scam. "
                "Under Indian law, Digital Arrest or video interrogations do not legally exist. "
                "Do not transfer any money. Report immediately to National Cybercrime Helpline 1930."
            )
        else:
            script = (
                "Attention! This message or payment request appears suspicious. "
                "Never share your OTP or enter your UPI PIN on unverified requests."
            )

    return script


async def generate_voice_explanation(
    reasons: List[str], preferred_language: str = "hi", verdict: str = "DANGEROUS_SCAM"
) -> Optional[str]:
    """
    Generate audio warning memo using edge-tts and return as base64-encoded string.
    """
    script = build_voice_script(reasons, preferred_language, verdict)
    voice = VOICE_HINDI if preferred_language == "hi" else VOICE_ENGLISH

    if edge_tts:
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_audio_path = f.name

            communicate = edge_tts.Communicate(script, voice)
            await communicate.save(temp_audio_path)

            with open(temp_audio_path, "rb") as audio_file:
                encoded = base64.b64encode(audio_file.read()).decode("utf-8")

            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

            return encoded
        except Exception as e:
            logger.warning(f"Edge-TTS audio synthesis error: {e}")

    return None
