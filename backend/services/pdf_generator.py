import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from fastapi import HTTPException

# Outputs folder — all generated PDFs are persisted here
OUTPUTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
os.makedirs(OUTPUTS_DIR, exist_ok=True)


def save_to_outputs(pdf_bytes: bytes, session_id: int | None = None) -> str:
    """
    Save PDF bytes to the outputs folder.
    Returns the absolute path of the saved file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"session_{session_id}_" if session_id is not None else "resume_"
    filename = f"{prefix}{timestamp}.pdf"
    filepath = os.path.join(OUTPUTS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)
    return filepath


def generate(resume_json: dict) -> bytes:
    """
    Generate PDF from resume JSON using ReportLab.
    Returns PDF as bytes.
    """
    try:

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        name_style = ParagraphStyle(
            "Name",
            parent=styles["Normal"],
            fontSize=20,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#111827"),
            alignment=TA_CENTER,
            spaceAfter=2,
        )
        contact_style = ParagraphStyle(
            "Contact",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica",
            textColor=colors.HexColor("#6B7280"),
            alignment=TA_CENTER,
            spaceAfter=4,
        )
        section_heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontSize=10,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1D4ED8"),
            spaceBefore=8,
            spaceAfter=2,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica",
            textColor=colors.HexColor("#374151"),
            spaceAfter=3,
            leading=13,
        )
        entry_title_style = ParagraphStyle(
            "EntryTitle",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#111827"),
            spaceAfter=1,
        )
        entry_meta_style = ParagraphStyle(
            "EntryMeta",
            parent=styles["Normal"],
            fontSize=8,
            fontName="Helvetica-Oblique",
            textColor=colors.HexColor("#6B7280"),
            spaceAfter=2,
        )
        bullet_style = ParagraphStyle(
            "Bullet",
            parent=styles["Normal"],
            fontSize=8.5,
            fontName="Helvetica",
            textColor=colors.HexColor("#374151"),
            leftIndent=10,
            spaceAfter=1,
            leading=12,
        )
        skill_style = ParagraphStyle(
            "Skill",
            parent=styles["Normal"],
            fontSize=8.5,
            fontName="Helvetica",
            textColor=colors.HexColor("#374151"),
            spaceAfter=2,
        )

        story = []

        # ── Header ──────────────────────────────────────────────────────────
        header = resume_json.get("header", {})
        name = header.get("name", "").strip() or "Resume"
        story.append(Paragraph(name, name_style))

        contact_parts = []
        if header.get("email"):
            contact_parts.append(header["email"])
        if header.get("phone"):
            contact_parts.append(header["phone"])
        if header.get("linkedin"):
            contact_parts.append(header["linkedin"])
        if header.get("github"):
            contact_parts.append(header["github"])
        if contact_parts:
            story.append(Paragraph("  |  ".join(contact_parts), contact_style))

        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E5E7EB")))

        # ── Summary ──────────────────────────────────────────────────────────
        summary = resume_json.get("summary", "").strip()
        if summary:
            story.append(Paragraph("SUMMARY", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
            story.append(Spacer(1, 2))
            story.append(Paragraph(summary, body_style))

        # ── Experience / Internship ──────────────────────────────────────────
        internships = resume_json.get("internship", [])
        if internships:
            story.append(Paragraph("EXPERIENCE", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
            story.append(Spacer(1, 2))
            for exp in internships:
                company = exp.get("company", "").strip()
                role = exp.get("role", "").strip()
                duration = exp.get("duration", "").strip()
                bullets = exp.get("bullets", [])
                if company:
                    story.append(Paragraph(f"{company} — {role}" if role else company, entry_title_style))
                if duration:
                    story.append(Paragraph(duration, entry_meta_style))
                for b in bullets:
                    story.append(Paragraph(f"• {b}", bullet_style))
                story.append(Spacer(1, 3))

        # ── Projects ─────────────────────────────────────────────────────────
        projects = resume_json.get("projects", [])
        if projects:
            story.append(Paragraph("PROJECTS", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
            story.append(Spacer(1, 2))
            for proj in projects:
                proj_name = proj.get("name", "").strip()
                url = proj.get("url", "").strip()
                duration = proj.get("duration", "").strip()
                bullets = proj.get("bullets", [])
                title_text = proj_name
                if url:
                    title_text = f'<a href="{url}" color="#1D4ED8">{proj_name}</a>'
                if proj_name:
                    story.append(Paragraph(title_text, entry_title_style))
                if duration:
                    story.append(Paragraph(duration, entry_meta_style))
                for b in bullets:
                    story.append(Paragraph(f"• {b}", bullet_style))
                story.append(Spacer(1, 3))

        # ── Education ─────────────────────────────────────────────────────────
        education = resume_json.get("education", [])
        if education:
            story.append(Paragraph("EDUCATION", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
            story.append(Spacer(1, 2))
            for edu in education:
                institution = edu.get("institution", "").strip()
                degree = edu.get("degree", "").strip()
                duration = edu.get("duration", "").strip()
                if institution:
                    story.append(Paragraph(institution, entry_title_style))
                if degree:
                    story.append(Paragraph(degree, entry_meta_style))
                if duration:
                    story.append(Paragraph(duration, entry_meta_style))
                story.append(Spacer(1, 3))

        # ── Skills ────────────────────────────────────────────────────────────
        skills = resume_json.get("skills", [])
        if skills:
            story.append(Paragraph("SKILLS", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
            story.append(Spacer(1, 2))
            for skill in skills:
                category = skill.get("category", "").strip()
                items = skill.get("items", "").strip()
                if category and items:
                    story.append(Paragraph(f"<b>{category}:</b> {items}", skill_style))
                elif items:
                    story.append(Paragraph(items, skill_style))

        # ── Certifications ────────────────────────────────────────────────────
        certs = resume_json.get("certifications", [])
        if certs:
            story.append(Paragraph("CERTIFICATIONS", section_heading_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E5E7EB")))
            story.append(Spacer(1, 2))
            for cert in certs:
                cert_name = cert.get("name", "").strip()
                url = cert.get("url", "").strip()
                duration = cert.get("duration", "").strip()
                display = cert_name
                if url:
                    display = f'<a href="{url}" color="#1D4ED8">{cert_name}</a>'
                line = display
                if duration:
                    line += f"  ({duration})"
                if cert_name:
                    story.append(Paragraph(f"• {line}", bullet_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Persist to outputs/ folder
        save_to_outputs(pdf_bytes)

        return pdf_bytes

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )