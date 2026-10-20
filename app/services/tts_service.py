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

VOICE_MAP = {
    "hi": "hi-IN-SwaraNeural",
    "en": "en-IN-NeerjaNeural",
    "te": "te-IN-MohanNeural",
    "kn": "kn-IN-GaganNeural",
    "ta": "ta-IN-PallaviNeural",
    "mr": "mr-IN-AarohiNeural",
}

SCRIPTS = {
    "hi": {
        "DANGEROUS_SCAM": (
            "सावधान! कवच ए आई की जांच में यह एक खतरनाक स्कैम और फ्रॉड पाया गया है। "
            "भारतीय कानून में डिजिटल अरेस्ट या वीडियो कॉल पर गिरफ्तारी का कोई नियम नहीं है। "
            "किसी को भी पैसे न भेजें और तुरंत राष्ट्रीय साइबर हेल्पलाइन 1930 पर शिकायत दर्ज करें।"
        ),
        "AUTHENTIC": (
            "कवच ए आई की जांच में यह संदेश प्रामाणिक और सुरक्षित पाया गया है। "
            "इसमें किसी भी प्रकार के फिशिंग या धोखाधड़ी के संकेत नहीं मिले हैं।"
        ),
        "SUSPICIOUS": (
            "ध्यान दें! यह संदेश या पेमेंट संदिग्ध है। किसी भी अनजान लिंक पर क्लिक न करें "
            "और अपना यूपीआई पिन कभी न डालें।"
        ),
    },
    "en": {
        "DANGEROUS_SCAM": (
            "Alert! Kavach AI forensic analysis confirms this is a dangerous scam. "
            "Under Indian law, Digital Arrest or video interrogations do not legally exist. "
            "Do not transfer any money. Report immediately to National Cybercrime Helpline 1930."
        ),
        "AUTHENTIC": (
            "Kavach AI forensic analysis confirms this communication appears authentic and safe. "
            "No phishing indicators, coercive urgency, or fraudulent patterns were detected."
        ),
        "SUSPICIOUS": (
            "Attention! This message or payment request appears suspicious. "
            "Never share your OTP or enter your UPI PIN on unverified requests."
        ),
    },
    "te": {
        "DANGEROUS_SCAM": (
            "హెచ్చరిక! కవచ్ ఏ ఐ ఫోరెన్సిక్ తనిఖీలో ఇది అత్యంత ప్రమాదకరమైన స్కామ్ అని తేలింది. "
            "భారతీయ చట్టం ప్రకారం డిజిటల్ అరెస్ట్ లేదా వీడియో కాల్ అరెస్టులు ఉండవు. "
            "ఎవరికీ డబ్బు పంపవద్దు. వెంటనే జాతీయ సైబర్ హెల్ప్‌లైన్ 1930 కి ఫిర్యాదు చేయండి."
        ),
        "AUTHENTIC": (
            "కవచ్ ఏ ఐ పరిశీలనలో ఈ సందేశం ప్రామాణికమైనది మరియు సురక్షితమైనదని నిర్ధారించబడింది. "
            "ఎటువంటి మోసపూరిత లింకులు లేదా బెదిరింపులు లేవు."
        ),
        "SUSPICIOUS": (
            "గమనిక! ఈ సందేశం లేదా చెల్లింపు అనుమానాస్పదంగా ఉంది. "
            "ఎవరితోనూ మీ ఓటీపీ లేదా యూపీఐ పిన్ పంచుకోవద్దు."
        ),
    },
    "kn": {
        "DANGEROUS_SCAM": (
            "ಎಚ್ಚರಿಕೆ! ಕವಚ ಎ ಐ ವಿಧಿವಿಜ್ಞಾನ ತಪಾಸಣೆಯಲ್ಲಿ ಇದು ಅಪಾಯಕಾರಿ ವಂಚನೆ ಎಂದು ದೃಢಪಟ್ಟಿದೆ. "
            "ಭಾರತೀಯ ಕಾನೂನಿನಲ್ಲಿ ಡಿಜಿಟಲ್ ಬಂಧನ ಅಥವಾ ವೀಡಿಯೊ ಕರೆ ಮೂಲಕ ಬಂಧನ ಎಂಬ ನಿಯಮವೇ ಇಲ್ಲ. "
            "ಯಾರಿಗೂ ಹಣ ಕಳುಹಿಸಬೇಡಿ ಮತ್ತು ತಕ್ಷಣ 1930 ಗೆ ಕರೆ ಮಾಡಿ."
        ),
        "AUTHENTIC": (
            "ಕವಚ ಎ ಐ ತಪಾಸಣೆಯಲ್ಲಿ ಈ ಸಂದೇಶವು ಅಧಿಕೃತ ಮತ್ತು ಸುರಕ್ಷಿತವಾಗಿದೆ ಎಂದು ದೃಢಪಟ್ಟಿದೆ. "
            "ಯಾವುದೇ ವಂಚನೆಯ ಲಕ್ಷಣಗಳಿಲ್ಲ."
        ),
        "SUSPICIOUS": (
            "ಗಮನಿಸಿ! ಈ ಸಂದೇಶ ಅಥವಾ ಪಾವತಿ ಕೋರಿಕೆ ಸಂಶಯಾಸ್ಪದವಾಗಿದೆ. "
            "ಯಾವುದೇ ಕಾರಣಕ್ಕೂ ನಿಮ್ಮ ಒಟಿಪಿ ಅಥವಾ ಯುಪಿಐ ಪಿನ್ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ."
        ),
    },
    "ta": {
        "DANGEROUS_SCAM": (
            "எச்சரிக்கை! கவச் ஏ ஐ சோதனையில் இது ஒரு ஆபத்தான மோசடி என்பது உறுதியாகியுள்ளது. "
            "இந்திய சட்டத்தில் டிஜிட்டல் கைது அல்லது வீடியோ கால் கைது என்ற நடைமுறையே இல்லை. "
            "யாருக்கும் பணம் அனுப்பாதீர்கள், உடனே 1930 என்ற சைபர் உதவி எண்ணை அழைக்கவும்."
        ),
        "AUTHENTIC": (
            "கவச் ஏ ஐ சோதனையில் இந்த தகவல் உண்மையானது மற்றும் பாதுகாப்பானது என உறுதியாகியுள்ளது. "
            "எவ்வித மோசடி அறிகுறிகளும் இல்லை."
        ),
        "SUSPICIOUS": (
            "கவனிக்கவும்! இந்த தகவல் அல்லது கட்டணக் கோரிக்கை சந்தேகத்திற்குரியதாக உள்ளது. "
            "உங்கள் ஓடிபி அல்லது யூபிஐ பின்னை ஒருபோதும் பகிராதீர்கள்."
        ),
    },
    "mr": {
        "DANGEROUS_SCAM": (
            "सावधान! कवच ए आय च्या तपासणीत हा एक धोकादायक घोटाळा असल्याचे स्पष्ट झाले आहे. "
            "भारतीय कायद्यात डिजिटल अटक किंवा व्हिडिओ कॉलवर अटकेची कोणतीही तरतूद नाही. "
            "कोणालाही पैसे पाठवू नका आणि त्वरित राष्ट्रीय सायबर हेल्पलाइन 1930 वर तक्रार करा."
        ),
        "AUTHENTIC": (
            "कवच ए आय च्या तपासणीत हा संदेश अधिकृत आणि सुरक्षित आढळला आहे. "
            "यात कोणत्याही फसवणुकीचे संकेत नाहीत."
        ),
        "SUSPICIOUS": (
            "लक्ष द्या! हा संदेश किंवा पेमेंट संशयास्पद आहे. "
            "कोणासोबतही आपला ओटीपी किंवा यूपीआय पिन शेअर करू नका."
        ),
    },
}


def build_voice_script(reasons: List[str], preferred_language: str = "hi", verdict: str = "DANGEROUS_SCAM") -> str:
    """Compose concise 15-second natural language warning script in requested regional language."""
    lang = preferred_language.lower()
    if lang not in SCRIPTS:
        lang = "en" if lang == "en" else "hi"

    lang_dict = SCRIPTS.get(lang, SCRIPTS["en"])
    return lang_dict.get(verdict, lang_dict.get("SUSPICIOUS", SCRIPTS["en"]["SUSPICIOUS"]))


async def generate_voice_explanation(
    reasons: List[str], preferred_language: str = "hi", verdict: str = "DANGEROUS_SCAM"
) -> Optional[str]:
    """
    Generate audio warning memo using edge-tts and return as base64-encoded string.
    Supports Hindi, English, Telugu, Kannada, Tamil, and Marathi.
    """
    script = build_voice_script(reasons, preferred_language, verdict)
    voice = VOICE_MAP.get(preferred_language.lower(), VOICE_MAP["hi"])

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
            logger.warning(f"Edge-TTS audio synthesis error for {preferred_language}: {e}")

    return None
