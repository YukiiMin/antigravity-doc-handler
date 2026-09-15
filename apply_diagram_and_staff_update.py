import os
import shutil
import sys
import docx
from PIL import Image
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

DOCX_PATH = r"../AI-Docx-Testing-Product/Report3_Software Requirement Specification.docx"
BAK_PATH = r"../AI-Docx-Testing-Product/Report3_Software Requirement Specification.docx.bak_phase3"

USER_PNG_PATH = r"../AI-Docx-Testing-Product/android_user_screen_flow_v2.png"
STAFF_PNG_PATH = r"../AI-Docx-Testing-Product/android_staff_screen_flow.png"

def update_docx():
    print(f"1. Creating backup: {BAK_PATH}")
    shutil.copyfile(DOCX_PATH, BAK_PATH)
    print("   Backup created successfully.")

    print(f"2. Loading DOCX: {DOCX_PATH}")
    doc = docx.Document(DOCX_PATH)

    # ─────────────────────────────────────────────────────────────
    # Step A: Update User Screen Flow diagram in Paragraph 71
    # ─────────────────────────────────────────────────────────────
    p71 = doc.paragraphs[71]
    drawings = p71._element.xpath('.//w:drawing')
    if not drawings:
        raise ValueError("No drawing found in P71!")

    blips = p71._element.xpath('.//a:blip')
    if not blips:
        raise ValueError("No blip found in P71 drawing!")

    embed_rId = blips[0].attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
    print(f"   Found User diagram blip rId: {embed_rId}")

    with open(USER_PNG_PATH, "rb") as f:
        new_user_png_data = f.read()

    with Image.open(USER_PNG_PATH) as img:
        u_w_px, u_h_px = img.size

    w_cm = 14.0
    u_h_cm = round((u_h_px / u_w_px) * w_cm, 2)
    u_cx_emu = int(w_cm * 360000)
    u_cy_emu = int(u_h_cm * 360000)

    rel = doc.part.rels[embed_rId]
    rel.target_part._blob = new_user_png_data
    print(f"   Replaced User diagram blob for {rel.target_ref} ({len(new_user_png_data)} bytes)")
    print(f"   Dimensions: {u_w_px}x{u_h_px}px -> {w_cm}cm x {u_h_cm}cm ({u_cx_emu} x {u_cy_emu} EMUs)")

    for extent in p71._element.xpath('.//wp:extent'):
        extent.set('cx', str(u_cx_emu))
        extent.set('cy', str(u_cy_emu))

    for a_ext in p71._element.xpath('.//a:xfrm/a:ext'):
        a_ext.set('cx', str(u_cx_emu))
        a_ext.set('cy', str(u_cy_emu))

    # ─────────────────────────────────────────────────────────────
    # Step B: Insert Staff Screen Flow (Section 3.1.3 Diagram)
    # Vị trí: Ngay sau đoạn User Screen Flow P71 (trước P72/P73)
    # ─────────────────────────────────────────────────────────────
    print("3. Inserting Section 3.1.3 Android Staff Screen Flow diagram...")
    p71_element = p71._element

    # Measure Staff PNG
    with Image.open(STAFF_PNG_PATH) as img:
        s_w_px, s_h_px = img.size
    s_h_cm = round((s_h_px / s_w_px) * w_cm, 2)
    s_cx_emu = int(w_cm * 360000)
    s_cy_emu = int(s_h_cm * 360000)

    # Heading 3.1.3
    p_staff_heading = doc.add_paragraph()
    p_staff_heading.text = "3.1.3 Android Staff Screen Flow"
    p_staff_heading.style = doc.paragraphs[70].style # match 3.1.2 style
    p_staff_heading.paragraph_format.space_before = Pt(12)
    p_staff_heading.paragraph_format.space_after = Pt(6)
    p_staff_heading.paragraph_format.keep_with_next = True

    # Caption Figure 3.1f
    p_staff_fig = doc.add_paragraph()
    p_staff_fig.text = "Figure 3.1f: Android Staff App – Screen Navigation Flow"
    p_staff_fig.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_staff_fig.paragraph_format.space_before = Pt(4)
    p_staff_fig.paragraph_format.space_after = Pt(6)
    p_staff_fig.paragraph_format.keep_with_next = True
    for r in p_staff_fig.runs:
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.italic = True

    # Image paragraph
    p_staff_img = doc.add_paragraph()
    p_staff_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_staff_img.paragraph_format.space_before = Pt(0)
    p_staff_img.paragraph_format.space_after = Pt(12)
    run_staff_img = p_staff_img.add_run()
    run_staff_img.add_picture(STAFF_PNG_PATH, width=docx.shared.Cm(w_cm), height=docx.shared.Cm(s_h_cm))

    # Move elements to sit right after p71_element
    p71_element.addnext(p_staff_img._element)
    p71_element.addnext(p_staff_fig._element)
    p71_element.addnext(p_staff_heading._element)
    print("   Staff diagram elements placed after User diagram.")

    # ─────────────────────────────────────────────────────────────
    # Step C: Insert Table 3: Android Staff Screen Flow
    # Vị trí: Ngay sau Table 2 (doc.tables[4])
    # ─────────────────────────────────────────────────────────────
    print("4. Inserting Table 3: Android Staff Screen Flow...")
    t2 = doc.tables[4]
    t2_element = t2._element

    # Caption paragraph for Table 3
    p_t3_caption = doc.add_paragraph()
    p_t3_caption.text = "Table 3: Android Staff Screen Flow"
    p_t3_caption.paragraph_format.space_before = Pt(12)
    p_t3_caption.paragraph_format.space_after = Pt(6)
    p_t3_caption.paragraph_format.keep_with_next = True
    for r in p_t3_caption.runs:
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = True

    # Data for Table 3 (10 screens)
    staff_table_data = [
        ("1", "Authentication", "Đăng nhập (Staff Login Screen)", "Màn hình đăng nhập tài khoản nhân viên siêu thị với mã nhân viên và mật khẩu bảo mật."),
        ("2", "Main Dashboard", "Trang chủ (Staff Home Dashboard)", "Bảng điều khiển trung tâm hiển thị trạng thái tổng quan siêu thị, telemetry robot và các lối tắt chức năng."),
        ("3", "Alert & Inventory", "Cảnh báo & Kệ trống (Notifications Tab)", "Danh sách cảnh báo thời gian thực về các kệ hàng sắp hết hoặc đã hết hàng cần được bổ sung ngay."),
        ("4", "Task Management", "Chi tiết Cảnh báo & Châm hàng Screen", "Xem thông tin chi tiết vị trí kệ, mặt hàng cần châm, số lượng và xác nhận đã hoàn thành châm hàng."),
        ("5", "Shelf Density", "Theo dõi Mật độ 6 Kệ (Shelf Density)", "Biểu đồ trực quan mật độ hàng hóa trên từng dãy kệ (Kệ 1..6) hỗ trợ phát hiện sớm điểm nghẽn tồn kho."),
        ("6", "Quick Action", "Modal Xác nhận Fill Kệ (In-Place)", "Hộp thoại thao tác nhanh cho phép nhân viên xác nhận châm hàng ngay tại kệ hoặc chuyển sang bản đồ chỉ đường."),
        ("7", "Robot Telemetry", "Thẻ Telemetry Robot (RB0001 Status)", "Hiển thị mức pin, trạng thái hoạt động và vị trí hiện tại của Robot phục vụ trong khu vực siêu thị."),
        ("8", "Interactive Map", "Bản đồ Siêu thị 2D (Interactive Map Tab)", "Bản đồ số 2D định vị chính xác vị trí robot, các dãy kệ hàng và lối đi của nhân viên."),
        ("9", "Profile & Security", "Hồ sơ Cá nhân (Profile Tab)", "Quản lý thông tin tài khoản nhân viên, ca làm việc và thao tác đăng xuất an toàn khỏi ứng dụng."),
        ("10", "Real-time Sync", "Cập nhật Tồn kho 100% (SignalR Broadcast)", "Tự động đồng bộ trạng thái tồn kho lên máy chủ và phát broadcast SignalR tới toàn hệ thống."),
    ]

    t3 = doc.add_table(rows=len(staff_table_data) + 1, cols=4)
    t3.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER

    # Copy tblPr properties from Table 2
    t3_tblPr = t3._tbl.tblPr
    t3_tblPr.append(parse_xml(r'<w:tblW %s w:w="9210" w:type="dxa"/>' % nsdecls('w')))
    t3_tblPr.append(parse_xml(r'<w:tblLayout %s w:type="fixed"/>' % nsdecls('w')))

    # Header Row
    headers = ["#", "Feature", "Screen", "Description"]
    for j, h in enumerate(headers):
        cell = t3.cell(0, j)
        cell.text = h
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j == 0 else WD_ALIGN_PARAGRAPH.LEFT
        for r in p.runs:
            r.font.name = "Calibri"
            r.font.size = Pt(10)
            r.font.bold = True
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

        tcPr = cell._tc.get_or_add_tcPr()
        tcPr.append(parse_xml(r'''<w:tcBorders %s>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>
            <w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>
        </w:tcBorders>''' % nsdecls('w')))
        tcPr.append(parse_xml(r'<w:shd %s w:val="clear" w:color="auto" w:fill="FFE8E1"/>' % nsdecls('w')))

    # Header row tblHeader & cantSplit
    trPr0 = t3.rows[0]._tr.get_or_add_trPr()
    trPr0.append(parse_xml(r'<w:tblHeader %s/>' % nsdecls('w')))
    trPr0.append(parse_xml(r'<w:cantSplit %s/>' % nsdecls('w')))

    # Data Rows
    col_widths = [323850, 1028700, 1076325, 3419475]
    col_dxa = [510, 1620, 1695, 5385]

    for i, row_data in enumerate(staff_table_data):
        row = t3.rows[i + 1]
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(r'<w:cantSplit %s/>' % nsdecls('w')))

        for j, val in enumerate(row_data):
            cell = row.cells[j]
            cell.text = val
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j == 0 else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(10)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

            tcPr = cell._tc.get_or_add_tcPr()
            tcPr.append(parse_xml(r'''<w:tcBorders %s>
                <w:top w:val="nil"/>
                <w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>
                <w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>
            </w:tcBorders>''' % nsdecls('w')))

    # Set column widths across all rows
    for row in t3.rows:
        for j in range(4):
            row.cells[j].width = col_widths[j]
            tcPr = row.cells[j]._tc.get_or_add_tcPr()
            tcPr.append(parse_xml(r'<w:tcW %s w:w="%d" w:type="dxa"/>' % (nsdecls('w'), col_dxa[j])))

    # Place Table 3 caption and Table 3 right after Table 2 in body
    t2_element.addnext(t3._tbl)
    t2_element.addnext(p_t3_caption._element)
    print("   Table 3 elements placed after Table 2.")

    # ─────────────────────────────────────────────────────────────
    # Step D: Renumber subsequent sections:
    # 3.1.3 Screen Authorization -> 3.1.4 Screen Authorization
    # 3.1.4 Non-Screen Functions -> 3.1.5 Non-Screen Functions
    # ─────────────────────────────────────────────────────────────
    print("5. Renumbering subsequent sections...")
    for p in doc.paragraphs:
        if p.text.strip().startswith("3.1.3 Screen Authorization"):
            p.text = p.text.replace("3.1.3 Screen Authorization", "3.1.4 Screen Authorization")
            print("   Renumbered 3.1.3 -> 3.1.4 Screen Authorization")
        elif p.text.strip().startswith("3.1.4 Non-Screen Functions"):
            p.text = p.text.replace("3.1.4 Non-Screen Functions", "3.1.5 Non-Screen Functions")
            print("   Renumbered 3.1.4 -> 3.1.5 Non-Screen Functions")

    # ─────────────────────────────────────────────────────────────
    # Step E: Save DOCX safely
    # ─────────────────────────────────────────────────────────────
    print(f"6. Saving updated document to {DOCX_PATH}")
    doc.save(DOCX_PATH)
    print("   [SUCCESS] Document saved successfully!")

if __name__ == "__main__":
    update_docx()
