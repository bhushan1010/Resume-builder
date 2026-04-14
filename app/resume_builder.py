"""
resume_builder.py  –  ReportLab PDF resume generator
Supports multiple templates and single/multi-page output.

Templates:
  - jakes: Jake's Resume / Deedy style (thin rules, compact spacing)
  - classic: Minimal, plain text, no accent colors
  - modern: Original style with solid accent bars
"""

import os
import tempfile
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    ListFlowable, ListItem, PageTemplate, BaseDocTemplate, Frame, NextPageTemplate,
)
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

# ── Design tokens ────────────────────────────────────────────────────────────
ACCENT      = colors.HexColor('#1B3A5C')
ACCENT_LIGHT= colors.HexColor('#EBF0F5')
BLACK       = colors.HexColor('#1A1A1A')
DARK_GRAY   = colors.HexColor('#3D3D3D')
MED_GRAY    = colors.HexColor('#666666')
LIGHT_GRAY  = colors.HexColor('#999999')
RULE_COLOR  = colors.HexColor('#333333')
WHITE       = colors.white

PAGE_W, PAGE_H = A4
L_MARGIN = R_MARGIN = 12 * mm
T_MARGIN = B_MARGIN = 10 * mm
BODY_WIDTH = PAGE_W - L_MARGIN - R_MARGIN
MAX_URL_DISPLAY = 30

VALID_TEMPLATES = ('jakes', 'classic', 'modern')

# ── Paragraph styles factory ─────────────────────────────────────────────────
def _ps(name, font='Helvetica', size=9, color=BLACK, leading=13,
        align=TA_LEFT, before=0, after=0, left=0, right=0) -> ParagraphStyle:
    return ParagraphStyle(
        name, fontName=font, fontSize=size, textColor=color,
        leading=leading, alignment=align,
        spaceBefore=before, spaceAfter=after, leftIndent=left, rightIndent=right,
    )


def _make_styles(template='jakes', scale=1.0):
    """Build a styles dict based on template and scale factor."""
    s = scale
    if template == 'jakes':
        return {
            'name': _ps('name', 'Helvetica-Bold', int(18*s), ACCENT, int(22*s), TA_CENTER, after=1),
            'contact': _ps('contact', 'Helvetica', int(8*s), MED_GRAY, int(11*s), TA_CENTER, after=3),
            'sechdr': _ps('sechdr', 'Helvetica-Bold', int(9*s), BLACK, int(11*s), TA_LEFT, after=0),
            'jobtitle': _ps('jobtitle', 'Helvetica-Bold', int(9*s), BLACK, int(12*s)),
            'jobdate': _ps('jobdate', 'Helvetica', int(8*s), MED_GRAY, int(12*s), TA_RIGHT),
            'company': _ps('company', 'Helvetica-Oblique', int(8*s), DARK_GRAY, int(10*s)),
            'location': _ps('loc', 'Helvetica-Oblique', int(8*s), MED_GRAY, int(10*s), TA_RIGHT),
            'bullet': _ps('bullet', 'Helvetica', int(8*s), BLACK, int(11*s), left=0, before=0, after=0),
            'skill': _ps('scat', 'Helvetica', int(8*s), BLACK, int(11*s), before=0, after=0),
            'projname': _ps('projname', 'Helvetica-Bold', int(9*s), BLACK, int(11*s)),
            'projtech': _ps('ptech', 'Helvetica-Oblique', int(7.5*s), MED_GRAY, int(10*s)),
            'cert': _ps('cert', 'Helvetica', int(8*s), DARK_GRAY, int(11*s), before=0, after=0),
        }
    elif template == 'classic':
        return {
            'name': _ps('name', 'Helvetica-Bold', int(20*s), BLACK, int(24*s), TA_CENTER, after=2),
            'contact': _ps('contact', 'Helvetica', int(9*s), DARK_GRAY, int(12*s), TA_CENTER, after=4),
            'sechdr': _ps('sechdr', 'Helvetica-Bold', int(11*s), BLACK, int(14*s), TA_LEFT, after=1),
            'jobtitle': _ps('jobtitle', 'Helvetica-Bold', int(10*s), BLACK, int(13*s)),
            'jobdate': _ps('jobdate', 'Helvetica', int(9*s), MED_GRAY, int(13*s), TA_RIGHT),
            'company': _ps('company', 'Helvetica', int(9*s), DARK_GRAY, int(12*s)),
            'location': _ps('loc', 'Helvetica', int(9*s), MED_GRAY, int(12*s), TA_RIGHT),
            'bullet': _ps('bullet', 'Helvetica', int(9*s), BLACK, int(13*s), left=0, before=1, after=1),
            'skill': _ps('scat', 'Helvetica', int(9*s), BLACK, int(12*s), before=1, after=0),
            'projname': _ps('projname', 'Helvetica-Bold', int(10*s), BLACK, int(13*s)),
            'projtech': _ps('ptech', 'Helvetica', int(9*s), MED_GRAY, int(12*s)),
            'cert': _ps('cert', 'Helvetica', int(9*s), DARK_GRAY, int(12*s), before=1, after=0),
        }
    else:  # modern
        return {
            'name': _ps('name', 'Helvetica-Bold', int(18*s), ACCENT, int(22*s), TA_CENTER, after=1),
            'contact': _ps('contact', 'Helvetica', int(8*s), MED_GRAY, int(11*s), TA_CENTER, after=3),
            'sechdr': _ps('sechdr', 'Helvetica-Bold', int(9*s), WHITE, int(11*s), TA_LEFT, before=6),
            'jobtitle': _ps('jobtitle', 'Helvetica-Bold', int(9*s), BLACK, int(12*s)),
            'jobdate': _ps('jobdate', 'Helvetica', int(8*s), MED_GRAY, int(12*s), TA_RIGHT),
            'company': _ps('company', 'Helvetica-Oblique', int(8*s), DARK_GRAY, int(10*s)),
            'location': _ps('loc', 'Helvetica-Oblique', int(8*s), MED_GRAY, int(10*s), TA_RIGHT),
            'bullet': _ps('bullet', 'Helvetica', int(8*s), BLACK, int(11*s), left=0, before=0, after=0),
            'skill': _ps('scat', 'Helvetica', int(8*s), BLACK, int(11*s), before=0, after=0),
            'projname': _ps('projname', 'Helvetica-Bold', int(9*s), BLACK, int(11*s)),
            'projtech': _ps('ptech', 'Helvetica-Oblique', int(7.5*s), MED_GRAY, int(10*s)),
            'cert': _ps('cert', 'Helvetica', int(8*s), DARK_GRAY, int(11*s), before=0, after=0),
        }


# ── Helper builders ──────────────────────────────────────────────────────────

def _section_header(title: str, styles: dict, template: str = 'jakes'):
    """Section title — style varies by template."""
    flowables = []
    flowables.append(Paragraph(title.upper(), styles['sechdr']))
    if template == 'jakes':
        flowables.append(HRFlowable(
            width='100%', thickness=0.8,
            color=RULE_COLOR,
            spaceAfter=2, spaceBefore=0,
        ))
    elif template == 'classic':
        flowables.append(HRFlowable(
            width='100%', thickness=1.0,
            color=BLACK,
            spaceAfter=3, spaceBefore=0,
        ))
    elif template == 'modern':
        cell = Paragraph(f'  {title.upper()}', styles['sechdr'])
        tbl = Table([[cell]], colWidths=[BODY_WIDTH])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,-1), ACCENT),
            ('TOPPADDING',   (0,0), (-1,-1), 3),
            ('BOTTOMPADDING',(0,0), (-1,-1), 3),
            ('LEFTPADDING',  (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        flowables.append(tbl)
    return flowables


def _two_col(left_para, right_para, l_width=0.75):
    """Side-by-side paragraphs with elastic right column."""
    tbl = Table(
        [[left_para, right_para]],
        colWidths=[BODY_WIDTH * l_width, BODY_WIDTH * (1.0 - l_width)],
        hAlign='LEFT',
    )
    tbl.setStyle(TableStyle([
        ('VALIGN',         (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',    (0,0), (-1,-1), 0),
        ('RIGHTPADDING',   (0,0), (-1,-1), 0),
        ('TOPPADDING',     (0,0), (-1,-1), 0),
        ('BOTTOMPADDING',  (0,0), (-1,-1), 0),
    ]))
    return tbl


def _bullet_list(bullets: list, styles: dict):
    """Compact bullet list using ReportLab's built-in bullet support."""
    flowables = []
    for b in bullets:
        flowables.append(Paragraph(f'<bullet bulletFontName="ZapfDingbats" bulletFontSize="7">&#108;</bullet> {b}', styles['bullet']))
    return flowables


def _thin_rule():
    return HRFlowable(
        width='100%', thickness=0.3,
        color=colors.HexColor('#CCCCCC'),
        spaceAfter=1, spaceBefore=1,
    )


def _truncate_url(url: str, max_len: int = MAX_URL_DISPLAY) -> str:
    """Truncate long URLs for display in contact line."""
    if len(url) <= max_len:
        return url
    return url[:max_len - 3] + '...'


# ── Page count checker ───────────────────────────────────────────────────────

def _get_page_count(pdf_path: str) -> int:
    """Return the number of pages in a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception:
        return 1


# ── Multi-page document with header/footer ───────────────────────────────────

class _ResumeDocTemplate(BaseDocTemplate):
    """Custom document template that adds page headers on page 2+."""

    def __init__(self, filename, name='', **kw):
        self._header_name = kw.pop('header_name', '')
        self._header_contact = kw.pop('header_contact', '')
        self._template = kw.pop('template_style', 'jakes')
        BaseDocTemplate.__init__(self, filename, **kw)

        # Define frames for each page
        frame = Frame(
            L_MARGIN, B_MARGIN,
            PAGE_W - L_MARGIN - R_MARGIN,
            PAGE_H - T_MARGIN - B_MARGIN,
            id='normal',
        )

        # Page 1: no header
        self.addPageTemplates(
            PageTemplate(id='first', frames=frame, onPage=self._draw_first_page),
        )
        # Page 2+: with compact header
        self.addPageTemplates(
            PageTemplate(id='later', frames=frame, onPage=self._draw_later_page),
        )

    def _draw_first_page(self, canvas, doc):
        canvas.saveState()
        canvas.restoreState()

    def _draw_later_page(self, canvas, doc):
        canvas.saveState()
        # Compact header on continuation pages
        canvas.setFont('Helvetica-Bold', 9)
        canvas.setFillColor(ACCENT)
        canvas.drawCentredString(PAGE_W / 2, PAGE_H - 8 * mm, self._header_name)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(MED_GRAY)
        canvas.drawCentredString(PAGE_W / 2, PAGE_H - 13 * mm, self._header_contact)
        # Thin rule under header
        canvas.setStrokeColor(RULE_COLOR)
        canvas.setLineWidth(0.5)
        canvas.line(L_MARGIN, PAGE_H - 15 * mm, PAGE_W - R_MARGIN, PAGE_H - 15 * mm)
        # Page number
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(MED_GRAY)
        canvas.drawRightString(PAGE_W - R_MARGIN, 6 * mm, f'Page {doc.page}')
        canvas.restoreState()


# ── Main builder ─────────────────────────────────────────────────────────────

def build_resume_pdf(profile_data: dict, output_path: str,
                     max_pages: int = 1, template: str = 'jakes') -> str:
    """Generate a styled A4 PDF resume and write it to output_path.

    Args:
        profile_data: Resume data dict (basics, education, experience, etc.)
        output_path: Where to write the PDF
        max_pages: Maximum pages allowed (1 = single page, 2 = allow 2 pages)
        template: Template style — 'jakes', 'classic', or 'modern'

    Returns:
        Path to the generated PDF
    """
    if template not in VALID_TEMPLATES:
        raise ValueError(f"Invalid template '{template}'. Must be one of {VALID_TEMPLATES}")

    b = profile_data.get('basics', {})
    education = profile_data.get('education', [])
    experiences = profile_data.get('experience', [])
    projects = profile_data.get('projects', [])
    skills = profile_data.get('skills', {})
    certifications = profile_data.get('certifications', [])
    awards = profile_data.get('awards', [])
    publications = profile_data.get('publications', [])

    if hasattr(skills, '__dict__'):
        skills = vars(skills)

    skill_parts = []
    for label, key in [('Languages', 'languages'), ('Frameworks', 'frameworks'), ('Tools & Platforms', 'tools')]:
        items = skills.get(key, [])
        if items:
            skill_parts.append(f'<b>{label}:</b> {", ".join(items)}')

    has_education = bool(education)
    has_experience = bool(experiences)
    has_projects = bool(projects)
    has_skills = bool(skill_parts)
    has_certifications = bool(certifications)
    has_awards = bool(awards)
    has_publications = bool(publications)

    # Contact line for page headers
    contact_parts = []
    if b.get('email'): contact_parts.append(b['email'])
    if b.get('phone'): contact_parts.append(b['phone'])
    header_contact = ' | '.join(contact_parts)

    # Scaling tiers for overflow handling
    scale_tiers = [1.0, 0.9, 0.8]

    tmp_path = None
    for scale in scale_tiers:
        styles = _make_styles(template, scale)

        story = _build_story(
            b, education, experiences, projects, skills, skill_parts,
            certifications, awards, publications,
            has_education, has_experience, has_projects,
            has_skills, has_certifications, has_awards, has_publications,
            styles, template,
        )

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        if max_pages > 1:
            doc = _ResumeDocTemplate(
                tmp_path,
                pagesize=A4,
                leftMargin=L_MARGIN, rightMargin=R_MARGIN,
                topMargin=T_MARGIN + (10 * mm if max_pages > 1 else 0),
                bottomMargin=B_MARGIN,
                header_name=b.get('name', ''),
                header_contact=header_contact,
                template_style=template,
            )
        else:
            doc = SimpleDocTemplate(
                tmp_path,
                pagesize=A4,
                leftMargin=L_MARGIN, rightMargin=R_MARGIN,
                topMargin=T_MARGIN, bottomMargin=B_MARGIN,
            )

        doc.build(story)
        page_count = _get_page_count(tmp_path)

        if page_count <= max_pages:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            shutil.move(tmp_path, output_path)
            return output_path

        os.unlink(tmp_path)

    # Fallback: use smallest scale anyway
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    if max_pages > 1 and tmp_path:
        shutil.move(tmp_path, output_path)
    elif tmp_path:
        shutil.move(tmp_path, output_path)
    return output_path


def _build_story(b, education, experiences, projects, skills, skill_parts,
                 certifications, awards, publications,
                 has_education, has_experience, has_projects,
                 has_skills, has_certifications, has_awards, has_publications,
                 styles, template='jakes'):
    """Build the story flowables with the given style dict."""
    story = []

    # ── NAME ─────────────────────────────────────────────────────────────────
    story.append(Paragraph(b.get('name', ''), styles['name']))

    # ── CONTACT BAR ──────────────────────────────────────────────────────────
    line1_parts = []
    if b.get('phone'):    line1_parts.append(b['phone'])
    if b.get('email'):    line1_parts.append(f'<a href="mailto:{b["email"]}" color="#1B3A5C">{b["email"]}</a>')
    story.append(Paragraph((' <font color="#999999">|</font> ').join(line1_parts), styles['contact']))

    line2_parts = []
    if b.get('linkedin'): line2_parts.append(f'<a href="https://{b["linkedin"]}" color="#1B3A5C">{_truncate_url(b["linkedin"])}</a>')
    if b.get('github'):   line2_parts.append(f'<a href="https://{b["github"]}" color="#1B3A5C">{_truncate_url(b["github"])}</a>')
    if b.get('leetcode'): line2_parts.append(f'<a href="https://{b["leetcode"]}" color="#1B3A5C">{_truncate_url(b["leetcode"])}</a>')
    if line2_parts:
        story.append(Paragraph((' <font color="#999999">|</font> ').join(line2_parts), styles['contact']))

    # ── EDUCATION ────────────────────────────────────────────────────────────
    if has_education:
        story.extend(_section_header('Education', styles, template))
        for edu in education:
            story.append(_two_col(
                Paragraph(edu.get('institution', ''), styles['jobtitle']),
                Paragraph(f'{edu.get("startDate","")} &ndash; {edu.get("endDate","")}', styles['jobdate']),
            ))
            story.append(_two_col(
                Paragraph(edu.get('degree', ''), styles['company']),
                Paragraph(edu.get('location', ''), styles['location']),
            ))
            story.append(Spacer(1, 2))

    # ── EXPERIENCE ───────────────────────────────────────────────────────────
    if has_experience:
        story.extend(_section_header('Professional Experience', styles, template))
        for i, exp in enumerate(experiences):
            story.append(_two_col(
                Paragraph(exp.get('role', ''), styles['jobtitle']),
                Paragraph(f'{exp.get("startDate","")} &ndash; {exp.get("endDate","")}', styles['jobdate']),
            ))
            story.append(_two_col(
                Paragraph(exp.get('company', ''), styles['company']),
                Paragraph(exp.get('location', ''), styles['location']),
            ))
            if exp.get('bullets'):
                story.extend(_bullet_list(exp['bullets'], styles))
            if i < len(experiences) - 1:
                story.append(_thin_rule())
            else:
                story.append(Spacer(1, 1))

    # ── PROJECTS ─────────────────────────────────────────────────────────────
    if has_projects:
        story.extend(_section_header('Projects', styles, template))
        for proj in projects:
            techs = ' &middot; '.join(proj.get('technologies', []))
            story.append(_two_col(
                Paragraph(f'<b>{proj.get("name","")}</b>', styles['projname']),
                Paragraph(techs, styles['projtech']),
                l_width=0.55,
            ))
            if proj.get('bullets'):
                story.extend(_bullet_list(proj['bullets'], styles))
            story.append(Spacer(1, 1))

    # ── SKILLS ───────────────────────────────────────────────────────────────
    if has_skills:
        story.extend(_section_header('Technical Skills', styles, template))
        for i, part in enumerate(skill_parts):
            story.append(Paragraph(part, styles['skill']))
            if i < len(skill_parts) - 1:
                story.append(Spacer(1, 1))

    # ── CERTIFICATIONS ───────────────────────────────────────────────────────
    if has_certifications:
        story.extend(_section_header('Certifications', styles, template))
        for i, cert in enumerate(certifications):
            cert_text = f'<b>{cert.get("name","")}</b>'
            issuer = cert.get('issuer', '')
            date = cert.get('date', '')
            if issuer:
                cert_text += f' &mdash; {issuer}'
            if date:
                cert_text += f' ({date})'
            story.append(Paragraph(cert_text, styles['cert']))
            if i < len(certifications) - 1:
                story.append(Spacer(1, 1))

    # ── AWARDS ───────────────────────────────────────────────────────────────
    if has_awards:
        story.extend(_section_header('Awards & Honors', styles, template))
        for i, award in enumerate(awards):
            award_text = f'<b>{award.get("title","")}</b>'
            org = award.get('organization', '')
            date = award.get('date', '')
            if org:
                award_text += f' &mdash; {org}'
            if date:
                award_text += f' ({date})'
            desc = award.get('description', '')
            if desc:
                story.append(Paragraph(award_text, styles['cert']))
                story.append(Paragraph(desc, styles['bullet']))
            else:
                story.append(Paragraph(award_text, styles['cert']))
            if i < len(awards) - 1:
                story.append(Spacer(1, 1))

    # ── PUBLICATIONS ─────────────────────────────────────────────────────────
    if has_publications:
        story.extend(_section_header('Publications', styles, template))
        for i, pub in enumerate(publications):
            pub_text = f'<b>{pub.get("title","")}</b>'
            venue = pub.get('venue', '')
            date = pub.get('date', '')
            if venue:
                pub_text += f'. <i>{venue}</i>'
            if date:
                pub_text += f', {date}'
            story.append(Paragraph(pub_text, styles['cert']))
            if i < len(publications) - 1:
                story.append(Spacer(1, 1))

    return story
