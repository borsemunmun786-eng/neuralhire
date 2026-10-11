"""One-time script: converts all .txt resumes in data/resumes/ to properly formatted PDFs."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER

RESUMES_DIR = Path("data/resumes")

# ── Colour palette matching NeuralHire brand
VIOLET    = colors.HexColor("#7c3aed")
INK       = colors.HexColor("#0f172a")
INK_2     = colors.HexColor("#1e293b")
MUTED     = colors.HexColor("#64748b")
BG_LIGHT  = colors.HexColor("#f5f3ff")

def make_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["name"] = ParagraphStyle(
        "name", fontName="Helvetica-Bold", fontSize=20, textColor=INK,
        spaceAfter=2, alignment=TA_LEFT, leading=24,
    )
    styles["title"] = ParagraphStyle(
        "title", fontName="Helvetica", fontSize=11, textColor=VIOLET,
        spaceAfter=2, alignment=TA_LEFT, leading=14,
    )
    styles["contact"] = ParagraphStyle(
        "contact", fontName="Helvetica", fontSize=8, textColor=MUTED,
        spaceAfter=10, alignment=TA_LEFT, leading=11,
    )
    styles["section"] = ParagraphStyle(
        "section", fontName="Helvetica-Bold", fontSize=9, textColor=VIOLET,
        spaceBefore=10, spaceAfter=4, alignment=TA_LEFT,
        leading=11, textTransform="uppercase", letterSpacing=0.8,
    )
    styles["body"] = ParagraphStyle(
        "body", fontName="Helvetica", fontSize=9, textColor=INK_2,
        spaceAfter=3, alignment=TA_LEFT, leading=13,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet", fontName="Helvetica", fontSize=9, textColor=INK_2,
        spaceAfter=2, leftIndent=12, bulletIndent=0, leading=13,
        bulletText="•",
    )
    styles["job_title"] = ParagraphStyle(
        "job_title", fontName="Helvetica-Bold", fontSize=9.5, textColor=INK,
        spaceAfter=1, leading=13,
    )
    styles["job_meta"] = ParagraphStyle(
        "job_meta", fontName="Helvetica-Oblique", fontSize=8.5, textColor=MUTED,
        spaceAfter=3, leading=12,
    )
    styles["skills_line"] = ParagraphStyle(
        "skills_line", fontName="Helvetica", fontSize=9, textColor=INK_2,
        spaceAfter=2, leading=13,
    )
    return styles


def divider(color=colors.HexColor("#e2e8f0")):
    return HRFlowable(width="100%", thickness=0.5, color=color, spaceAfter=6, spaceBefore=0)


def parse_txt(path: Path) -> list:
    """Parse .txt resume into structured sections."""
    lines = path.read_text(encoding="utf-8").splitlines()
    sections = []
    current_section = None
    current_lines = []

    SECTION_HEADERS = {
        "PROFILE", "SUMMARY", "CORE SKILLS", "SKILLS", "EXPERIENCE",
        "EDUCATION", "PROJECTS", "CERTIFICATIONS",
    }

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        upper = stripped.upper()
        # Check if it's a known section header
        if upper in SECTION_HEADERS:
            if current_section is not None:
                sections.append((current_section, current_lines))
            current_section = upper
            current_lines = []
        elif current_section is None:
            # Header block: name / title / contact
            sections.append(("_HEADER", [stripped]))
        else:
            current_lines.append(stripped)

    if current_section is not None:
        sections.append((current_section, current_lines))

    return sections


def build_pdf(txt_path: Path):
    pdf_path = txt_path.with_suffix(".pdf")
    styles = make_styles()
    story = []

    sections = parse_txt(txt_path)

    # ── Header block ──
    header_lines = [l for sec, lines in sections if sec == "_HEADER" for l in lines]
    if header_lines:
        story.append(Paragraph(header_lines[0], styles["name"]))
        if len(header_lines) > 1:
            story.append(Paragraph(header_lines[1], styles["title"]))
        if len(header_lines) > 2:
            story.append(Paragraph(" · ".join(header_lines[2:]), styles["contact"]))
        story.append(divider(VIOLET))

    # ── Content sections ──
    for sec, lines in sections:
        if sec == "_HEADER":
            continue

        # Skip the fictional disclaimer line
        if any("fictional sample" in l.lower() for l in lines):
            lines = [l for l in lines if "fictional sample" not in l.lower()]
        if not lines:
            continue

        story.append(Paragraph(sec.title(), styles["section"]))
        story.append(divider())

        if sec in ("PROFILE", "SUMMARY"):
            for line in lines:
                story.append(Paragraph(line, styles["body"]))

        elif sec in ("CORE SKILLS", "SKILLS"):
            for line in lines:
                # Split "Category: items, items" lines
                if ":" in line:
                    cat, rest = line.split(":", 1)
                    story.append(Paragraph(
                        f"<b>{cat.strip()}:</b> {rest.strip()}",
                        styles["skills_line"]
                    ))
                else:
                    story.append(Paragraph(line, styles["skills_line"]))

        elif sec == "EXPERIENCE":
            for line in lines:
                if line.startswith("-"):
                    story.append(Paragraph(line[1:].strip(), styles["bullet"]))
                elif "|" in line or ("—" in line and any(c.isdigit() for c in line)):
                    # Job title line
                    story.append(Spacer(1, 3))
                    # Format: "Title | Company | Dates" or "Title — Company (dates)"
                    story.append(Paragraph(line.replace("|", "·"), styles["job_title"]))
                else:
                    story.append(Paragraph(line, styles["body"]))

        elif sec == "EDUCATION":
            for line in lines:
                story.append(Paragraph(line, styles["body"]))

        elif sec == "PROJECTS":
            for line in lines:
                if line.startswith("-"):
                    story.append(Paragraph(line[1:].strip(), styles["bullet"]))
                else:
                    story.append(Paragraph(line, styles["body"]))

        else:
            for line in lines:
                if line.startswith("-"):
                    story.append(Paragraph(line[1:].strip(), styles["bullet"]))
                else:
                    story.append(Paragraph(line, styles["body"]))

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm,
        title=txt_path.stem,
    )
    doc.build(story)
    print(f"  ✓  {pdf_path.name}")
    return pdf_path


if __name__ == "__main__":
    txt_files = sorted(RESUMES_DIR.glob("*.txt"))
    if not txt_files:
        print("No .txt files found in data/resumes/")
    else:
        print(f"Generating {len(txt_files)} PDF resumes…")
        for txt in txt_files:
            build_pdf(txt)
        print("Done.")
