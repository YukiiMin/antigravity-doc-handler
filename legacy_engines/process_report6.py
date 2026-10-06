import sys
import os
import re
import shutil
import copy
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

from format_reports_pipeline import (
    NAVY_COLOR, DARK_NAVY, DARK_SLATE, BODY_COLOR, MUTED_COLOR,
    apply_font_to_run, apply_font_to_paragraph,
    format_all_tables, inject_dynamic_page_numbers, set_header_text,
    set_tab_stop, format_figure_captions
)

REPORT6_TOC = [
    (1, "I. Record of Changes", "3"),
    (1, "II. Release Package & User Guides", "4"),
    (2, "1. Deliverable Package", "4"),
    (2, "2. Installation Guides", "5"),
    (3, "2.1 System Requirements", "5"),
    (4, "2.1.1 Hardware Specifications (Server, Mobile & Autonomous Mobile Robot)", "5"),
    (4, "2.1.2 Software Requirements", "6"),
    (3, "2.2 Installation Instructions", "7"),
    (4, "2.2.1 Setup Database", "7"),
    (4, "2.2.2 Setup Backend API", "7"),
    (4, "2.2.3 Setup AI Microservice", "8"),
    (4, "2.2.4 Setup Robot Embedded Firmware & ROS 2", "8"),
    (4, "2.2.5 Setup Mobile & Robot Smartphone Apps", "9"),
    (2, "3. User Manual", "10"),
    (3, "3.1 Customer Registration & Face Biometric Check-in", "10"),
    (3, "3.2 Facial Recognition Login & Face Vector AI Setup", "12"),
    (3, "3.3 Multi-Modal Product Search Flow", "14"),
    (3, "3.4 In-Store Supermarket Navigation & Waypoint Guidance", "16"),
    (3, "3.5 Autonomous Service Robot Escort Mode", "19"),
    (3, "3.6 Guest Banner Ad Interaction & Multi-Product Flow", "21"),
]

def format_report6(doc_path: str, output_path: str = None) -> str:
    if output_path is None:
        output_path = doc_path

    # Make backup
    bak_path = doc_path + ".bak"
    if not os.path.exists(bak_path):
        shutil.copy2(doc_path, bak_path)

    doc = docx.Document(doc_path)

    # 1. Locate TOC anchor
    toc_idx = None
    record_idx = None
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t == "Table of Contents":
            toc_idx = i
        elif t.startswith("I. Record of Changes"):
            record_idx = i
            break

    if toc_idx is not None and record_idx is not None:
        p_record = doc.paragraphs[record_idx]
        
        # Style Table of Contents title
        p_toc = doc.paragraphs[toc_idx]
        p_toc.text = "Table of Contents"
        p_toc.style = doc.styles['Heading 1'] if 'Heading 1' in doc.styles else doc.styles['Normal']
        p_toc.paragraph_format.space_before = Pt(18.0)
        p_toc.paragraph_format.space_after = Pt(12.0)
        for r in p_toc.runs:
            apply_font_to_run(r, font_name="Calibri", size_pt=16.0, bold=True, color_rgb=NAVY_COLOR)

        # Clear any empty paragraphs between toc_idx and record_idx
        for k in range(toc_idx + 1, record_idx):
            doc.paragraphs[k].text = ""

        # Insert TOC entries before p_record
        for level, title, page_str in REPORT6_TOC:
            new_p = doc.add_paragraph()
            p_record._p.addprevious(new_p._p)
            
            if level == 1:
                indent = Inches(0.0)
                is_bold = True
                size_pt = 11.0
                color_rgb = NAVY_COLOR
                sb, sa = 6.0, 2.0
            elif level == 2:
                indent = Inches(0.18)
                is_bold = True
                size_pt = 11.0
                color_rgb = DARK_NAVY
                sb, sa = 3.0, 2.0
            elif level == 3:
                indent = Inches(0.36)
                is_bold = False
                size_pt = 10.5
                color_rgb = BODY_COLOR
                sb, sa = 1.5, 1.5
            else: # level 4
                indent = Inches(0.54)
                is_bold = False
                size_pt = 10.0
                color_rgb = BODY_COLOR
                sb, sa = 1.0, 1.0

            new_p.paragraph_format.left_indent = indent
            new_p.paragraph_format.space_before = Pt(sb)
            new_p.paragraph_format.space_after = Pt(sa)
            new_p.paragraph_format.line_spacing = 1.15
            
            set_tab_stop(new_p, pos_twips=9050, align_val='right', leader_val='dot')
            
            r_title = new_p.add_run(title)
            apply_font_to_run(r_title, font_name="Calibri", size_pt=size_pt, bold=is_bold, color_rgb=color_rgb)
            
            r_tab = new_p.add_run('\t')
            apply_font_to_run(r_tab, font_name="Calibri", size_pt=size_pt, bold=False, color_rgb=MUTED_COLOR)
            
            r_page = new_p.add_run(page_str)
            apply_font_to_run(r_page, font_name="Calibri", size_pt=size_pt, bold=is_bold, color_rgb=color_rgb)

    # 2. Iterate all paragraphs to normalize fonts, headings, and spacings
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue

        # Cover page styling
        if t == "CAPSTONE PROJECT REPORT":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12.0)
            p.paragraph_format.space_after = Pt(6.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=20.0, bold=True, color_rgb=NAVY_COLOR)
            continue
        elif t == "Report 6 – Software User Guides":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0.0)
            p.paragraph_format.space_after = Pt(18.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=16.0, bold=True, color_rgb=NAVY_COLOR)
            continue
        elif "Ho Chi Minh City" in t and ("2026" in t or "•" in t or "–" in t):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6.0)
            p.paragraph_format.space_after = Pt(12.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=12.0, italic=True, color_rgb=MUTED_COLOR)
            continue

        # Heading 1
        if t in ["I. Record of Changes", "II. Release Package & User Guides"]:
            p.style = doc.styles['Heading 1'] if 'Heading 1' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(14.0)
            p.paragraph_format.space_after = Pt(6.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=16.0, bold=True, color_rgb=NAVY_COLOR)
            continue

        # Heading 2
        if t in ["1. Deliverable Package", "2. Installation Guides", "3. User Manual"]:
            p.style = doc.styles['Heading 2'] if 'Heading 2' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(12.0)
            p.paragraph_format.space_after = Pt(4.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=14.0, bold=True, color_rgb=NAVY_COLOR)
            continue

        # Heading 3
        if t in [
            "2.1 System Requirements", "2.2 Installation Instructions",
            "3.1 Customer Registration & Face Biometric Check-in",
            "3.2 Facial Recognition Login & Face Vector AI Setup",
            "3.3 Multi-Modal Product Search Flow",
            "3.4 In-Store Supermarket Navigation & Waypoint Guidance",
            "3.5 Autonomous Service Robot Escort Mode",
            "3.6 Guest Banner Ad Interaction & Multi-Product Flow"
        ]:
            p.style = doc.styles['Heading 3'] if 'Heading 3' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(10.0)
            p.paragraph_format.space_after = Pt(3.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=12.0, bold=True, color_rgb=DARK_NAVY)
            continue

        # Heading 4
        if (
            t.startswith("2.1.1 Hardware Specifications") or
            t == "2.1.1.2 Mobile Application" or
            t == "2.1.2 Software Requirements" or
            t.startswith("2.2.1 Setup Database") or
            t.startswith("2.2.2 Setup Backend API") or
            t.startswith("2.2.3 Setup AI Microservice") or
            t.startswith("2.2.4 Setup Robot Embedded") or
            t.startswith("2.2.5 Setup Mobile & Robot") or
            t == "Key UI Elements & Interactive Controls" or
            t == "Exceptions & Troubleshooting Handling"
        ):
            # Fix missing closing parenthesis if any
            if t.startswith("2.1.1 Hardware Specifications") and not t.endswith(")"):
                t = t + ")"
                p.text = t

            p.style = doc.styles['Heading 4'] if 'Heading 4' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(8.0)
            p.paragraph_format.space_after = Pt(2.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=11.0, bold=True, color_rgb=DARK_SLATE)
            continue

        # Figure / Table Captions
        if t.startswith("Figure ") or t.startswith("Table "):
            t = re.sub(r'^(Figure\s+\d+(\.\d+)*)\s*[:\-–—]\s*', r'\1 – ', t, flags=re.IGNORECASE)
            t = re.sub(r'^(Table\s+\d+(\.\d+)*)\s*[:\-–—]\s*', r'\1 – ', t, flags=re.IGNORECASE)
            p.text = t
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4.0)
            p.paragraph_format.space_after = Pt(12.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=10.0, bold=True, color_rgb=NAVY_COLOR)
            continue

        # General body paragraphs
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(0.0)
        p.paragraph_format.space_after = Pt(6.0)
        
        # Check if bullet list
        if t.startswith("•") or t.startswith("-") or t.startswith("*"):
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_after = Pt(3.0)

        for r in p.runs:
            apply_font_to_run(r, font_name="Calibri", size_pt=11.0)

    # 3. Format all tables
    format_all_tables(doc)

    # 4. Normalize figure captions
    format_figure_captions(doc)

    # 5. Header and dynamic page numbering
    set_header_text(doc, header_text="SmartMarketBot – Report 6: Software User Guides", font_name="Calibri", font_size_pt=9.5)
    inject_dynamic_page_numbers(doc, font_name="Calibri", font_size_pt=10.0)

    # 6. Save
    try:
        doc.save(output_path)
        print(f"[SUCCESS] Formatted Report 6 saved to: {output_path}")
        return output_path
    except PermissionError:
        fallback = output_path.replace(".docx", "_updated.docx")
        doc.save(fallback)
        print(f"[WARN] File locked. Saved to: {fallback}")
        return fallback

if __name__ == '__main__':
    r6_file = r'd:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\AI-Docx-Testing-Product\SuperMarketBot-Doc\Report6_Software_User_Guides.docx'
    format_report6(r6_file)
