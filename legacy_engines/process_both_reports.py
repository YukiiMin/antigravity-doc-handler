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
    set_tab_stop
)

BLACK_COLOR = RGBColor(0, 0, 0)
NAVY_ACCENT = RGBColor(31, 73, 125)

# ==========================================
# REPORT 6 PROCESSOR
# ==========================================

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
    (3, "3.2 AI Smart Meal Planning & Recipe Discovery", "12"),
    (3, "3.3 Smart Shopping Cart & Barcode Scanning", "14"),
    (3, "3.4 In-Store Supermarket Navigation & Waypoint Guidance", "16"),
    (3, "3.5 Autonomous Service Robot Escort Mode", "19"),
    (3, "3.6 Guest Banner Ad Interaction & Multi-Product Flow", "21"),
]

def process_report6(doc_path: str, output_path: str = None) -> str:
    if output_path is None:
        output_path = doc_path

    bak_path = doc_path + ".bak"
    if not os.path.exists(bak_path):
        shutil.copy2(doc_path, bak_path)

    doc = docx.Document(bak_path)

    # 1. Locate TOC anchor and Record of Changes
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
            apply_font_to_run(r, font_name="Calibri", size_pt=16.0, bold=True, color_rgb=BLACK_COLOR)

        # Clear any empty paragraphs between toc_idx and record_idx
        for k in range(toc_idx + 1, record_idx):
            doc.paragraphs[k].text = ""
            doc.paragraphs[k].style = doc.styles['Normal']

        # Insert TOC entries before p_record (All TOC lines in BLACK)
        for level, title, page_str in REPORT6_TOC:
            new_p = doc.add_paragraph()
            p_record._p.addprevious(new_p._p)
            new_p.style = doc.styles['Normal']
            
            if level == 1:
                indent = Inches(0.0)
                is_bold = True
                size_pt = 11.0
                sb, sa = 6.0, 2.0
            elif level == 2:
                indent = Inches(0.18)
                is_bold = True
                size_pt = 11.0
                sb, sa = 3.0, 2.0
            elif level == 3:
                indent = Inches(0.36)
                is_bold = False
                size_pt = 10.5
                sb, sa = 1.5, 1.5
            else: # level 4
                indent = Inches(0.54)
                is_bold = False
                size_pt = 10.0
                sb, sa = 1.0, 1.0

            new_p.paragraph_format.left_indent = indent
            new_p.paragraph_format.space_before = Pt(sb)
            new_p.paragraph_format.space_after = Pt(sa)
            new_p.paragraph_format.line_spacing = 1.15
            
            set_tab_stop(new_p, pos_twips=9050, align_val='right', leader_val='dot')
            
            r_title = new_p.add_run(title)
            apply_font_to_run(r_title, font_name="Calibri", size_pt=size_pt, bold=is_bold, color_rgb=BLACK_COLOR)
            
            r_tab = new_p.add_run('\t')
            apply_font_to_run(r_tab, font_name="Calibri", size_pt=size_pt, bold=False, color_rgb=BLACK_COLOR)
            
            r_page = new_p.add_run(page_str)
            apply_font_to_run(r_page, font_name="Calibri", size_pt=size_pt, bold=is_bold, color_rgb=BLACK_COLOR)

    # 2. Iterate paragraphs to normalize fonts, headings, and spacings
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            p.style = doc.styles['Normal']
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            continue

        # Skip TOC lines
        if '\t' in p.text and any(t.endswith(str(num)) for num in range(1, 100)):
            p.style = doc.styles['Normal']
            continue

        # Cover page styling
        # EXCEPTION 1: CAPSTONE PROJECT REPORT
        if t == "CAPSTONE PROJECT REPORT":
            p.style = doc.styles['Normal']
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12.0)
            p.paragraph_format.space_after = Pt(6.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=20.0, bold=True, color_rgb=NAVY_ACCENT)
            continue
        # EXCEPTION 2: Report 6 – Software User Guides
        elif t == "Report 6 – Software User Guides":
            p.style = doc.styles['Normal']
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0.0)
            p.paragraph_format.space_after = Pt(18.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=16.0, bold=True, color_rgb=NAVY_ACCENT)
            continue
        elif "Ho Chi Minh City" in t and ("2026" in t or "•" in t or "–" in t):
            p.style = doc.styles['Normal']
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6.0)
            p.paragraph_format.space_after = Pt(12.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=12.0, italic=True, color_rgb=BLACK_COLOR)
            continue

        # Heading 1
        # EXCEPTION 3 & 4: I. Record of Changes, II. Release Package & User Guides
        if t in ["I. Record of Changes", "II. Release Package & User Guides"]:
            p.style = doc.styles['Heading 1'] if 'Heading 1' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(14.0)
            p.paragraph_format.space_after = Pt(6.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=16.0, bold=True, color_rgb=NAVY_ACCENT)
            continue

        # Heading 2 -> BLACK
        if t in ["1. Deliverable Package", "2. Installation Guides", "3. User Manual"]:
            p.style = doc.styles['Heading 2'] if 'Heading 2' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(12.0)
            p.paragraph_format.space_after = Pt(4.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=14.0, bold=True, color_rgb=BLACK_COLOR)
            continue

        # Heading 3 -> BLACK
        if re.match(r'^3\.\d+\s+', t) or t in [
            "2.1 System Requirements", "2.2 Installation Instructions",
            "3.1 Customer Registration & Face Biometric Check-in",
            "3.2 AI Smart Meal Planning & Recipe Discovery",
            "3.3 Smart Shopping Cart & Barcode Scanning",
            "3.4 In-Store Supermarket Navigation & Waypoint Guidance",
            "3.5 Autonomous Service Robot Escort Mode",
            "3.6 Guest Banner Ad Interaction & Multi-Product Flow"
        ]:
            p.style = doc.styles['Heading 3'] if 'Heading 3' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(10.0)
            p.paragraph_format.space_after = Pt(3.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=12.0, bold=True, color_rgb=BLACK_COLOR)
            continue

        # Heading 4 -> BLACK
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
            if t.startswith("2.1.1 Hardware Specifications") and not t.endswith(")"):
                t = t + ")"
                p.text = t

            p.style = doc.styles['Heading 4'] if 'Heading 4' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(8.0)
            p.paragraph_format.space_after = Pt(2.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=11.0, bold=True, color_rgb=BLACK_COLOR)
            continue

        # Figure / Table Captions -> BLACK
        if t.startswith("Figure ") or t.startswith("Table "):
            t = re.sub(r'^(Figure\s+\d+(\.\d+)*)\s*[:\-–—]\s*', r'\1 – ', t, flags=re.IGNORECASE)
            t = re.sub(r'^(Table\s+\d+(\.\d+)*)\s*[:\-–—]\s*', r'\1 – ', t, flags=re.IGNORECASE)
            p.text = t
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4.0)
            p.paragraph_format.space_after = Pt(12.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=10.0, bold=True, color_rgb=BLACK_COLOR)
            continue

        # General body paragraphs -> BLACK
        p.style = doc.styles['Normal']
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(0.0)
        p.paragraph_format.space_after = Pt(6.0)
        
        if t.startswith("•") or t.startswith("-") or t.startswith("*"):
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_after = Pt(3.0)

        for r in p.runs:
            apply_font_to_run(r, font_name="Calibri", size_pt=11.0, color_rgb=BLACK_COLOR)

    # 3. Format all tables (Header white on Navy, data cells black)
    format_all_tables(doc)

    # 4. Header and dynamic page numbering
    set_header_text(doc, header_text="SmartMarketBot – Report 6: Software User Guides", font_name="Calibri", font_size_pt=9.5)
    inject_dynamic_page_numbers(doc, font_name="Calibri", font_size_pt=10.0)

    # 5. Save
    try:
        doc.save(output_path)
        print(f"[SUCCESS] Report 6 processed and saved to: {output_path}")
    except PermissionError:
        fallback = output_path.replace(".docx", "_updated.docx")
        doc.save(fallback)
        print(f"[WARN] File locked. Saved to: {fallback}")


# ==========================================
# REPORT 1 PROCESSOR
# ==========================================

REPORT1_TOC = [
    (1, "I. Project Introduction", "3"),
    (2, "1. Overview", "3"),
    (3, "1.1 Project Information", "3"),
    (3, "1.2 Project Team", "3"),
    (2, "2. Product Background", "4"),
    (2, "3. Existing Systems", "5"),
    (3, "3.1 Amazon Go", "5"),
    (3, "3.2 Pudu Robotics Service Robots", "6"),
    (3, "3.3 Walmart Intelligent Inventory System", "7"),
    (2, "4. Business Opportunity", "8"),
    (2, "5. Software Product Vision", "9"),
    (2, "6. Project Scope & Limitations", "10"),
    (3, "6.1 Major Features", "10"),
    (3, "6.2 Limitations & Exclusions", "12"),
]

def process_report1(doc_path: str, output_path: str = None) -> str:
    if output_path is None:
        output_path = doc_path

    bak_path = doc_path + ".bak"
    if not os.path.exists(bak_path):
        shutil.copy2(doc_path, bak_path)

    doc = docx.Document(bak_path)

    # 1. Locate Intro anchor where TOC should be inserted
    intro_idx = None
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t == "Introduction" or t.startswith("1. Overview"):
            intro_idx = i
            break

    if intro_idx is not None:
        p_intro = doc.paragraphs[intro_idx]
        
        # Insert Table of Contents Header -> BLACK
        p_toc = doc.add_paragraph()
        p_intro._p.addprevious(p_toc._p)
        p_toc.text = "Table of Contents"
        p_toc.style = doc.styles['Heading 1'] if 'Heading 1' in doc.styles else doc.styles['Normal']
        p_toc.paragraph_format.space_before = Pt(18.0)
        p_toc.paragraph_format.space_after = Pt(12.0)
        for r in p_toc.runs:
            apply_font_to_run(r, font_name="Calibri", size_pt=16.0, bold=True, color_rgb=BLACK_COLOR)

        # Insert TOC entries before p_intro (All in BLACK)
        for level, title, page_str in REPORT1_TOC:
            new_p = doc.add_paragraph()
            p_intro._p.addprevious(new_p._p)
            new_p.style = doc.styles['Normal']
            
            if level == 1:
                indent = Inches(0.0)
                is_bold = True
                size_pt = 11.0
                sb, sa = 6.0, 2.0
            elif level == 2:
                indent = Inches(0.18)
                is_bold = True
                size_pt = 11.0
                sb, sa = 3.0, 2.0
            elif level == 3:
                indent = Inches(0.36)
                is_bold = False
                size_pt = 10.5
                sb, sa = 1.5, 1.5
            else: # level 4
                indent = Inches(0.54)
                is_bold = False
                size_pt = 10.0
                sb, sa = 1.0, 1.0

            new_p.paragraph_format.left_indent = indent
            new_p.paragraph_format.space_before = Pt(sb)
            new_p.paragraph_format.space_after = Pt(sa)
            new_p.paragraph_format.line_spacing = 1.15
            
            set_tab_stop(new_p, pos_twips=9050, align_val='right', leader_val='dot')
            
            r_title = new_p.add_run(title)
            apply_font_to_run(r_title, font_name="Calibri", size_pt=size_pt, bold=is_bold, color_rgb=BLACK_COLOR)
            
            r_tab = new_p.add_run('\t')
            apply_font_to_run(r_tab, font_name="Calibri", size_pt=size_pt, bold=False, color_rgb=BLACK_COLOR)
            
            r_page = new_p.add_run(page_str)
            apply_font_to_run(r_page, font_name="Calibri", size_pt=size_pt, bold=is_bold, color_rgb=BLACK_COLOR)

    # 2. Iterate and re-style all paragraphs
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            p.style = doc.styles['Normal']
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            continue

        # Skip TOC lines
        if '\t' in p.text and any(t.endswith(str(num)) for num in range(1, 100)):
            p.style = doc.styles['Normal']
            continue

        # Cover page styling
        # EXCEPTION 1: CAPSTONE PROJECT REPORT
        if t == "CAPSTONE PROJECT REPORT":
            p.style = doc.styles['Normal']
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(12.0)
            p.paragraph_format.space_after = Pt(6.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=20.0, bold=True, color_rgb=NAVY_ACCENT)
            continue
        # EXCEPTION 2: Report 1 – Project Introduction
        elif t == "Report 1 – Project Introduction":
            p.style = doc.styles['Normal']
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0.0)
            p.paragraph_format.space_after = Pt(18.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=16.0, bold=True, color_rgb=NAVY_ACCENT)
            continue
        elif "HoChiMinh" in t or "Ho Chi Minh" in t:
            p.text = "• Ho Chi Minh City, September 2026 •"
            p.style = doc.styles['Normal']
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6.0)
            p.paragraph_format.space_after = Pt(12.0)
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=12.0, italic=True, color_rgb=BLACK_COLOR)
            continue

        # Heading 1: I. Project Introduction -> BLACK
        if t == "Introduction" or t == "I. Project Introduction":
            p.text = "I. Project Introduction"
            p.style = doc.styles['Heading 1'] if 'Heading 1' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(14.0)
            p.paragraph_format.space_after = Pt(6.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=16.0, bold=True, color_rgb=BLACK_COLOR)
            continue

        # Heading 2 -> BLACK
        if t in [
            "1. Overview", "2. Product Background", "3. Existing Systems",
            "4. Business Opportunity", "5. Software Product Vision",
            "6. Project Scope & Limitations"
        ]:
            p.style = doc.styles['Heading 2'] if 'Heading 2' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(12.0)
            p.paragraph_format.space_after = Pt(4.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=14.0, bold=True, color_rgb=BLACK_COLOR)
            continue

        # Heading 3 -> BLACK
        if t in [
            "1.1 Project Information", "1.2 Project Team",
            "3.1 Amazon Go", "3.2 Pudu Robotics Service Robots",
            "3.3 Walmart Intelligent Inventory System",
            "6.1 Major Features", "6.2 Limitations & Exclusions"
        ]:
            p.style = doc.styles['Heading 3'] if 'Heading 3' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(10.0)
            p.paragraph_format.space_after = Pt(3.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=12.0, bold=True, color_rgb=BLACK_COLOR)
            continue

        # Subheadings in Existing Systems (Brief Description, Features, Pros, Cons) -> BLACK
        if t in ["Brief Description", "Features", "Pros", "Cons"]:
            p.style = doc.styles['Heading 4'] if 'Heading 4' in doc.styles else doc.styles['Normal']
            p.paragraph_format.space_before = Pt(8.0)
            p.paragraph_format.space_after = Pt(2.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=11.0, bold=True, color_rgb=BLACK_COLOR)
            continue

        # Remove duplicate company name paragraphs under 3.X
        if t in ["Amazon", "Pudu Robotics", "Walmart"]:
            p.text = ""
            p.style = doc.styles['Normal']
            continue

        # Project Information Items (Group Code, Project Code, Project Title...) -> BLACK
        if any(t.startswith(prefix) for prefix in ["Group Code:", "Project Code:", "Project Title (English):", "Project Title (Vietnamese):"]):
            p.style = doc.styles['Normal']
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(0.0)
            p.paragraph_format.space_after = Pt(3.0)
            parts = t.split(":", 1)
            p.text = ""
            r1 = p.add_run(parts[0] + ":")
            apply_font_to_run(r1, font_name="Calibri", size_pt=11.0, bold=True, color_rgb=BLACK_COLOR)
            if len(parts) > 1:
                r2 = p.add_run(parts[1])
                apply_font_to_run(r2, font_name="Calibri", size_pt=11.0, bold=False, color_rgb=BLACK_COLOR)
            continue

        # Feature Items: FE-01..FE-13 -> BLACK
        if re.match(r'^FE-\d+:', t):
            p.style = doc.styles['Normal']
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(6.0)
            p.paragraph_format.space_after = Pt(2.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=11.0, bold=True, color_rgb=BLACK_COLOR)
            continue

        # Limitation Items: LI-01..LI-07 -> BLACK
        if re.match(r'^LI-\d+:', t):
            p.style = doc.styles['Normal']
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_before = Pt(6.0)
            p.paragraph_format.space_after = Pt(2.0)
            p.paragraph_format.keep_with_next = True
            for r in p.runs:
                apply_font_to_run(r, font_name="Calibri", size_pt=11.0, bold=True, color_rgb=BLACK_COLOR)
            continue

        # General body paragraphs -> BLACK
        p.style = doc.styles['Normal']
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(0.0)
        p.paragraph_format.space_after = Pt(6.0)
        
        # Check if bullet list
        if t.startswith("•") or t.startswith("-") or t.startswith("*") or (
            p.style and 'List' in p.style.name
        ):
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_after = Pt(3.0)

        for r in p.runs:
            apply_font_to_run(r, font_name="Calibri", size_pt=11.0, color_rgb=BLACK_COLOR)

    # 3. Format all tables (Header white on Navy, data cells black)
    format_all_tables(doc)

    # 4. Header and dynamic page numbering
    set_header_text(doc, header_text="SmartMarketBot – Report 1: Project Introduction", font_name="Calibri", font_size_pt=9.5)
    inject_dynamic_page_numbers(doc, font_name="Calibri", font_size_pt=10.0)

    # 5. Save
    try:
        doc.save(output_path)
        print(f"[SUCCESS] Report 1 processed and saved to: {output_path}")
    except PermissionError:
        fallback = output_path.replace(".docx", "_updated.docx")
        doc.save(fallback)
        print(f"[WARN] File locked. Saved to: {fallback}")

if __name__ == '__main__':
    r6_file = r'd:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\AI-Docx-Testing-Product\SuperMarketBot-Doc\Report6_Software_User_Guides.docx'
    r1_file = r'd:\Minh\For_myself\ZSCORT_GSU26_SAP05\tool\AI-Docx-Testing-Product\SuperMarketBot-Doc\Report1_Project_Introduction.docx'

    print("=== Processing Report 6 ===")
    process_report6(r6_file)

    print("\n=== Processing Report 1 ===")
    process_report1(r1_file)
