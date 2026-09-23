import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

sys.stdout.reconfigure(encoding='utf-8')

DOC_PATH = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\src\Report3_Software Requirement Specification.docx'
SCREENSHOT_DIR = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot'

from patch_report3_section32 import create_full_sec32_data

def patch_document():
    print(f"Loading document: {DOC_PATH}")
    doc = docx.Document(DOC_PATH)
    body = doc._body._element

    # =========================================================================
    # PART 1: Fix Paragraph 70, 71 (Screen Flow Diagrams in 3.1)
    # =========================================================================
    print("--- Fixing Section 3.1 Screen Flow Diagrams (p70, p71) ---")
    p70 = doc.paragraphs[70] # 3.1.2 Android User Screen Flow (Heading 4)
    p71 = doc.paragraphs[71] # normal text with 3.1.3 and two diagrams
    
    # p71 runs: run 0 is image92.png, run 1 is text, run 2 is image20.png
    # Let's extract image92 and image20 from p71
    # Check if run 0 and run 2 have graphics
    if len(p71.runs) >= 3 and 'graphic' in p71.runs[0]._element.xml and 'graphic' in p71.runs[2]._element.xml:
        user_diagram_elem = p71.runs[0]._element
        staff_diagram_elem = p71.runs[2]._element
        
        # Create paragraph for User Screen Flow diagram right before p71
        p_user_img = p71.insert_paragraph_before(style='normal')
        p_user_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_user_img._p.append(user_diagram_elem)
        
        # Sơ đồ User Screen Flow caption
        p_user_cap = p71.insert_paragraph_before(style='normal')
        p_user_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_ucap = p_user_cap.add_run("Sơ đồ 3.1.2: Luồng màn hình Ứng dụng Khách hàng (Android User Screen Flow)")
        r_ucap.font.italic = True
        r_ucap.font.size = Pt(9.5)
        r_ucap.font.color.rgb = RGBColor(100, 116, 139)
        
        # Turn p71 into clean Heading 4: 3.1.3 Android Staff Screen Flow
        p71.text = "3.1.3 Android Staff Screen Flow"
        p71.style = doc.styles['Heading 4']
        
        # Create paragraph for Staff Screen Flow diagram after p71 (before p72)
        p72 = doc.paragraphs[72]
        p_staff_img = p72.insert_paragraph_before(style='normal')
        p_staff_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_staff_img._p.append(staff_diagram_elem)
        
        p_staff_cap = p72.insert_paragraph_before(style='normal')
        p_staff_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_scap = p_staff_cap.add_run("Sơ đồ 3.1.3: Luồng màn hình Ứng dụng Nhân viên (Android Staff Screen Flow)")
        r_scap.font.italic = True
        r_scap.font.size = Pt(9.5)
        r_scap.font.color.rgb = RGBColor(100, 116, 139)
        print("Successfully decoupled User Screen Flow and Staff Screen Flow into proper sections.")

    # =========================================================================
    # PART 2: Update Table 3 (Robot Screen Descriptions) in Section 3.1
    # =========================================================================
    print("--- Updating Table 3 (Robot Screen Descriptions) ---")
    t3 = doc.tables[3]
    # Check if AdMultiProductSelectScreen is already in Table 3
    has_screen_19 = any("AdMultiProductSelectScreen" in r.cells[2].text for r in t3.rows)
    if not has_screen_19:
        new_row = t3.add_row()
        new_row.cells[0].text = "19"
        new_row.cells[1].text = "Overlays & Dynamic Displays"
        new_row.cells[2].text = "Ad Multi-Product Select Screen"
        new_row.cells[3].text = "Màn hình cho phép khách hàng thành viên lựa chọn nhiều sản phẩm từ phiên phát quảng cáo để robot dẫn đường theo lộ trình tối ưu (TSP)."
        print("Added row 19 (Ad Multi-Product Select Screen) to Table 3.")

    # =========================================================================
    # PART 3: Fix Section 3.5 Heading Level (p3705 -> Heading 2)
    # =========================================================================
    print("--- Fixing Section 3.5 Heading Level ---")
    for p in doc.paragraphs:
        if "3.5 Staff Mobile Experience" in p.text:
            p.style = doc.styles['Heading 2']
            print(f"Updated '{p.text}' to Heading 2.")
            break

    # =========================================================================
    # PART 4: Replace Section 3.2 App for Robot with Full Vietnamese Content
    # =========================================================================
    print("--- Rebuilding Section 3.2 App for Robot ---")
    
    # Locate p95 ("3.2 App for Robot") and p306 ("3.3 Android Customer App")
    p95_idx = None
    p306_idx = None
    for idx, p in enumerate(doc.paragraphs):
        if p.text.strip().startswith("3.2 App for Robot"):
            p95_idx = idx
        elif p.text.strip().startswith("3.3 Android Customer App"):
            p306_idx = idx
            break

    if p95_idx is None or p306_idx is None:
        raise ValueError(f"Could not locate 3.2 or 3.3 in document! (p95={p95_idx}, p306={p306_idx})")

    print(f"Found Section 3.2 from paragraph {p95_idx} to {p306_idx}")
    
    p95 = doc.paragraphs[p95_idx]
    p306 = doc.paragraphs[p306_idx]
    
    # Collect all XML elements from p95._element up to p306._element (exclusive)
    p95_elem = p95._element
    p306_elem = p306._element
    
    body_p95_idx = body.index(p95_elem)
    body_p306_idx = body.index(p306_elem)
    
    print(f"Body XML indices: start={body_p95_idx}, end={body_p306_idx}. Removing {body_p306_idx - body_p95_idx} elements...")
    
    # Delete old elements
    elements_to_delete = [body[i] for i in range(body_p95_idx, body_p306_idx)]
    for elem in elements_to_delete:
        body.remove(elem)
        
    print("Old Section 3.2 elements removed cleanly.")

    # Now insert the new Section 3.2 sequentially right before p306
    # 1. Main Heading 3: 3.2 App for Robot
    p_main = p306.insert_paragraph_before("3.2 App for Robot", style='Heading 3')
    
    # 2. Add overview description
    p_intro = p306.insert_paragraph_before(style='normal')
    p_intro.add_run(
        "Phân hệ ứng dụng Android Robot (SmartMarketBot App) vận hành trực tiếp trên máy tính bảng gắn trên đầu robot tự hành, "
        "đóng vai trò là giao diện tương tác Kiosk thông minh giữa robot và người tiêu dùng tại siêu thị. Hệ thống tích hợp khả năng "
        "nhận diện khuôn mặt sinh trắc học (Face ID), tìm kiếm thông minh bằng giọng nói AI tiếng Việt, bản đồ số 2D dẫn đường tự hành "
        "theo bài toán người đưa thư (TSP), và quy trình phát quảng cáo tự hành đa phương tiện linh hoạt với cơ chế tự động khôi phục "
        "hành trình tuần tra sau khi hoàn tất hỗ trợ khách hàng."
    )
    
    sec32_subsections = create_full_sec32_data()
    
    for sub in sec32_subsections:
        print(f"  -> Generating subsection {sub['id']}: {sub['title'][:50]}...")
        
        # Subheading 3: 3.2.X
        p_sub = p306.insert_paragraph_before(sub['title'], style='Heading 3')
        
        # Screenshots Paragraph (Centered)
        p_img = p306.insert_paragraph_before(style='normal')
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for img_name, width_in in sub['images']:
            img_path = os.path.join(SCREENSHOT_DIR, img_name)
            if os.path.exists(img_path):
                r_img = p_img.add_run()
                r_img.add_picture(img_path, width=Inches(width_in))
                p_img.add_run("   ")
            else:
                print(f"    [WARN] Image not found: {img_path}")
                
        # Caption Paragraph (Centered, Italic, Slate color)
        p_cap = p306.insert_paragraph_before(sub['caption'], style='normal')
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if len(p_cap.runs) > 0:
            p_cap.runs[0].font.italic = True
            p_cap.runs[0].font.size = Pt(9.5)
            p_cap.runs[0].font.color.rgb = RGBColor(100, 116, 139)
            
        # Empty separator
        p306.insert_paragraph_before("", style='normal')

        # Heading 4: Function Trigger
        p306.insert_paragraph_before("Điều kiện kích hoạt (Function Trigger)", style='Heading 4')
        for label, desc in sub['triggers']:
            p_item = p306.insert_paragraph_before(style='normal')
            r_bold = p_item.add_run(label + " ")
            r_bold.bold = True
            p_item.add_run(desc)

        # Heading 4: Timing / Frequency
        p306.insert_paragraph_before("Thời gian / Tần suất thực hiện (Timing / Frequency)", style='Heading 4')
        for label, desc in sub['timing']:
            p_item = p306.insert_paragraph_before(style='normal')
            r_bold = p_item.add_run(label + " ")
            r_bold.bold = True
            p_item.add_run(desc)

        # Heading 4: Function Description
        p306.insert_paragraph_before("Mô tả chức năng (Function Description)", style='Heading 4')
        for label, desc in sub['description']:
            p_item = p306.insert_paragraph_before(style='normal')
            r_bold = p_item.add_run(label + " ")
            r_bold.bold = True
            p_item.add_run(desc)

        # Heading 4: Normal Flow
        p306.insert_paragraph_before("Luồng hoạt động chuẩn (Normal Flow)", style='Heading 4')
        for flow_step in sub['normal_flow']:
            p_item = p306.insert_paragraph_before(style='normal')
            # Check if there is bold header in flow step (e.g. "Bước 1: ...")
            if flow_step.startswith("Bước ") and ":" in flow_step:
                b_part, rest = flow_step.split(":", 1)
                r_b = p_item.add_run(b_part + ":")
                r_b.bold = True
                p_item.add_run(rest)
            else:
                p_item.add_run(flow_step)

        # Heading 4: Abnormal Cases
        p306.insert_paragraph_before("Các trường hợp bất thường (Abnormal Cases)", style='Heading 4')
        for label, desc in sub['abnormal_cases']:
            p_item = p306.insert_paragraph_before(style='normal')
            r_bold = p_item.add_run(label + " ")
            r_bold.bold = True
            p_item.add_run(desc)

        # Heading 4: Data Processing
        p306.insert_paragraph_before("Xử lý dữ liệu (Data Processing)", style='Heading 4')
        for label, desc in sub['data_processing']:
            p_item = p306.insert_paragraph_before(style='normal')
            r_bold = p_item.add_run(label + " ")
            r_bold.bold = True
            p_item.add_run(desc)

        # Heading 4: Business Rules
        p306.insert_paragraph_before("Quy tắc nghiệp vụ (Business Rules)", style='Heading 4')
        for label, desc in sub['business_rules']:
            p_item = p306.insert_paragraph_before(style='normal')
            r_bold = p_item.add_run(label + " ")
            r_bold.bold = True
            p_item.add_run(desc)
            
        p306.insert_paragraph_before("", style='normal')

    print("All 8 subsections generated and inserted successfully!")

    # Save modified document
    print(f"Saving patched document to {DOC_PATH}...")
    doc.save(DOC_PATH)
    print("SUCCESS: Document patched successfully!")

if __name__ == '__main__':
    patch_document()
