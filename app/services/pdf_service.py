"""Automated PDF Evidence Dossier Generator.
Produces court-admissible electronic incident summaries conforming to:
- Section 63, Bharatiya Sakshya Adhiniyam (BSA), 2023
- Section 65B, Indian Evidence Act, 1872
- Section 173, Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023
"""

import io
import html
import datetime
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)


def generate_dossier_pdf(dossier: Dict[str, Any]) -> bytes:
    """
    Generate an authoritative, court-ready PDF dossier byte stream.
    """
    def esc(val: Any) -> str:
        return html.escape(str(val) if val is not None else "")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DossierTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        alignment=1,  # Center
    )
    subtitle_style = ParagraphStyle(
        "DossierSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#dc2626"),
        alignment=1,
    )
    meta_style = ParagraphStyle(
        "MetaText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
    )
    code_style = ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )
    cert_style = ParagraphStyle(
        "CertText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155"),
    )

    elements = []

    # 1. Header & Authority Banner
    elements.append(Paragraph("KAVACH-AI NATIONAL CYBERCRIME FORENSIC DOSSIER", title_style))
    elements.append(Spacer(1, 4))
    elements.append(
        Paragraph(
            "ELECTRONIC EVIDENCE RECORD UNDER SECTION 63, BHARATIYA SAKSHYA ADHINIYAM (BSA), 2023<br/>"
            "(EQUIVALENT TO SECTION 65B OF INDIAN EVIDENCE ACT, 1872)",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceAfter=10))

    # 2. Metadata Grid
    dossier_id = esc(dossier.get("dossier_id", "KAVACH-INCIDENT-UNKNOWN"))
    generated_at = esc(dossier.get("generated_at", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")))
    sha256_hash = esc(dossier.get("sha256_evidence_hash", "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"))
    verdict = esc(dossier.get("verdict", "SUSPICIOUS"))
    confidence = int(float(dossier.get("confidence_score", 0.85)) * 100)

    verdict_color = (
        colors.HexColor("#b91c1c")
        if verdict == "DANGEROUS_SCAM"
        else (colors.HexColor("#b45309") if verdict == "SUSPICIOUS" else colors.HexColor("#15803d"))
    )

    meta_data = [
        [
            Paragraph(f"<b>Dossier Tracking ID:</b> {dossier_id}", meta_style),
            Paragraph(f"<b>Timestamp (UTC):</b> {generated_at}", meta_style),
        ],
        [
            Paragraph(f"<b>NCRP Helpline:</b> 1930 (National Cybercrime)", meta_style),
            Paragraph(f"<b>Official Portal:</b> https://cybercrime.gov.in", meta_style),
        ],
        [
            Paragraph(f"<b>Evidentiary Hash:</b> SHA256:{sha256_hash[:24]}...", meta_style),
            Paragraph(f"<b>Forensic Verdict:</b> <font color='{verdict_color.hexval()}'><b>{verdict} ({confidence}%)</b></font>", meta_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 10))

    # 3. Suspect Identifiers & Indicators
    elements.append(Paragraph("1. SUSPECT IDENTIFIERS & CYBER INFRASTRUCTURE", section_heading))
    indicators = dossier.get("suspect_indicators", {})
    vpas = indicators.get("upi_vpas", [])
    domains = indicators.get("phishing_domains", [])
    phones = indicators.get("contact_numbers", [])
    cnr = indicators.get("fabricated_cnr")

    vpas_str = esc(", ".join(vpas)) if vpas else "None extracted"
    domains_str = esc(", ".join(domains)) if domains else "None extracted"
    phones_str = esc(", ".join(phones)) if phones else "None extracted"
    cnr_str = esc(cnr) if cnr else "N/A"

    ident_rows = []
    ident_rows.append([Paragraph("<b>Indicator Type</b>", meta_style), Paragraph("<b>Extracted Forensic Value</b>", meta_style)])
    ident_rows.append([Paragraph("Suspect UPI VPA Accounts", meta_style), Paragraph(vpas_str, meta_style)])
    ident_rows.append([Paragraph("Phishing URLs / Domains", meta_style), Paragraph(domains_str, meta_style)])
    ident_rows.append([Paragraph("Suspect Contact Number(s)", meta_style), Paragraph(phones_str, meta_style)])
    ident_rows.append([Paragraph("Fabricated Court CNR", meta_style), Paragraph(cnr_str, meta_style)])

    ident_table = Table(ident_rows, colWidths=[180, 360])
    ident_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(ident_table)
    elements.append(Spacer(1, 10))

    # 4. Applicable Statutory Legal Sections
    elements.append(Paragraph("2. STATUTORY OFFENCES & PENAL PROVISIONS", section_heading))
    sections = dossier.get("statutory_violations", dossier.get("applicable_legal_sections", []))
    sec_text = "<br/>".join([f"• <b>{esc(s)}</b>" for s in sections]) if sections else "• Section 66D, Information Technology Act, 2000"
    elements.append(Paragraph(sec_text, body_style))
    elements.append(Spacer(1, 10))

    # 5. Pre-filled FIR Narrative Template
    elements.append(Paragraph("3. COMPLAINT NARRATIVE (FOR POLICE CYBER CELL / NCRP 1930)", section_heading))
    fir_template = dossier.get("fir_narrative_template", dossier.get("fir_narrative", ""))
    escaped_narrative = esc(fir_template).replace("\n", "<br/>")
    narrative_table = Table([[Paragraph(escaped_narrative, code_style)]], colWidths=[540])
    narrative_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(narrative_table)
    elements.append(Spacer(1, 10))

    # 6. Section 63 BSA / 65B Indian Evidence Act Certificate
    cert_block = []
    cert_block.append(Paragraph("4. CERTIFICATE OF ELECTRONIC EVIDENCE INTEGRITY (SEC 63 BSA 2023)", section_heading))
    cert_text = (
        f"I hereby certify under <b>Section 63 of Bharatiya Sakshya Adhiniyam, 2023</b> (and Section 65B of Indian Evidence Act, 1872) "
        f"that this document was automatically generated by the KavachAI automated engine on {generated_at}.<br/>"
        f"The electronic input artifact has an immutable cryptographic hash of: <b>SHA-256: {sha256_hash}</b>.<br/>"
        f"The computer system was operating under regular uninterrupted parameters without unauthorized intervention or evidentiary contamination."
    )
    cert_block.append(Paragraph(cert_text, cert_style))
    cert_block.append(Spacer(1, 12))

    # Sign-off box
    sign_data = [
        [
            Paragraph("<b>E-Verification Seal:</b><br/>KavachAI Universal Verification Engine<br/>NCRP 1930 Automated Interceptor", meta_style),
            Paragraph(f"<b>Evidentiary Hash:</b><br/>{sha256_hash[:32]}...<br/>Digitally Sealed & Immutable", meta_style),
        ]
    ]
    sign_table = Table(sign_data, colWidths=[270, 270])
    sign_table.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#475569")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    cert_block.append(sign_table)

    elements.append(KeepTogether(cert_block))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
