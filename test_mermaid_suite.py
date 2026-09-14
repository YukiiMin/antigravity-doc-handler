"""
test_mermaid_suite.py — Comprehensive end-to-end test suite for Mermaid Diagram Engine.

Tests:
1. Flowchart rendering with clean_modern theme.
2. Sequence Diagram rendering with clean_modern theme.
3. ER Diagram rendering with clean_modern theme.
4. Aspect ratio scaling verification (wide vs tall diagrams).
5. DOCX Placeholder injection (Patch 2 Run Fragmentation + Patch 3 keepNext chain).
6. DOCX Target Heading injection.
7. Atomic Protection on Mermaid syntax error.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from docx import Document
from docx.oxml.ns import qn
from PIL import Image

from tool.pdf_to_docx_converter.mermaid_renderer import (
    calculate_aspect_dimensions,
    render_mermaid_to_png,
)


def run_tests() -> bool:
    print("=" * 60)
    print("STARTING MERMAID DIAGRAM ENGINE END-TO-END TEST SUITE")
    print("=" * 60)

    test_dir = tempfile.mkdtemp(prefix="mermaid_test_")
    all_passed = True

    try:
        # -------------------------------------------------------------
        # Test 1: Flowchart rendering
        # -------------------------------------------------------------
        print("\n[TEST 1] Flowchart Rendering (clean_modern)...")
        spec_flow = {
            "diagram_name": "flowchart_sample",
            "mermaid_code": """flowchart TD
    A[Bắt đầu] --> B{Đăng nhập?}
    B -- Có --> C[Mở Dashboard]
    B -- Không --> D[Hiển thị Form Login]
    D --> E[Quét Face ID]
    E --> B""",
            "theme_preset": "clean_modern",
            "scale": 2,
            "output_path": os.path.join(test_dir, "flowchart.png"),
        }
        res_flow = render_mermaid_to_png(spec_flow)
        assert os.path.isfile(res_flow["png_path"]), "Flowchart PNG not created"
        assert res_flow["file_size_bytes"] > 1024, "Flowchart PNG too small"
        assert res_flow["width_cm"] <= 14.0, "Width exceeds 14.0cm"
        assert res_flow["height_cm"] <= 20.0, "Height exceeds 20.0cm"
        print(f"  --> PASS: {res_flow['png_path']} ({res_flow['dimensions_px']}) | Doc: {res_flow['width_cm']}x{res_flow['height_cm']}cm")

        # -------------------------------------------------------------
        # Test 2: Sequence Diagram rendering
        # -------------------------------------------------------------
        print("\n[TEST 2] Sequence Diagram Rendering (clean_modern)...")
        spec_seq = {
            "diagram_name": "sequence_sample",
            "mermaid_code": """sequenceDiagram
    autonumber
    actor Customer as Khách hàng
    participant App as Android App
    participant Gateway as API Gateway
    participant AI as AI Face Recognition
    participant DB as SAP Database

    Customer->>App: Bấm Login Face ID
    App->>AI: POST /api/v1/face/verify (Camera Frame)
    AI-->>Gateway: Result (Match 98.6%)
    Gateway->>DB: Query Customer Profile
    DB-->>Gateway: Profile Data & Roles
    Gateway-->>App: 200 OK + JWT Session Token
    App-->>Customer: Chuyển hướng Dashboard""",
            "theme_preset": "clean_modern",
            "scale": 2,
            "output_path": os.path.join(test_dir, "sequence.png"),
        }
        res_seq = render_mermaid_to_png(spec_seq)
        assert os.path.isfile(res_seq["png_path"]), "Sequence PNG not created"
        assert res_seq["file_size_bytes"] > 1024, "Sequence PNG too small"
        print(f"  --> PASS: {res_seq['png_path']} ({res_seq['dimensions_px']}) | Doc: {res_seq['width_cm']}x{res_seq['height_cm']}cm")

        # -------------------------------------------------------------
        # Test 3: ER Diagram rendering
        # -------------------------------------------------------------
        print("\n[TEST 3] ER Diagram Rendering (clean_modern)...")
        spec_er = {
            "diagram_name": "er_sample",
            "mermaid_code": """erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER {
        string customer_id PK
        string full_name
        string face_vector
        datetime created_at
    }
    ORDER ||--|{ ORDER_ITEM : contains
    ORDER {
        string order_id PK
        string customer_id FK
        decimal total_amount
        string status
    }
    ORDER_ITEM {
        string item_id PK
        string order_id FK
        string product_code
        int quantity
    }""",
            "theme_preset": "clean_modern",
            "scale": 2,
            "output_path": os.path.join(test_dir, "er.png"),
        }
        res_er = render_mermaid_to_png(spec_er)
        assert os.path.isfile(res_er["png_path"]), "ER PNG not created"
        assert res_er["file_size_bytes"] > 1024, "ER PNG too small"
        print(f"  --> PASS: {res_er['png_path']} ({res_er['dimensions_px']}) | Doc: {res_er['width_cm']}x{res_er['height_cm']}cm")

        # -------------------------------------------------------------
        # Test 4: Aspect Ratio Scaling Calculation
        # -------------------------------------------------------------
        print("\n[TEST 4] Aspect Ratio Scaling Validation...")
        # Wide image
        w, h = calculate_aspect_dimensions(2000, 800, max_w_cm=14.0, max_h_cm=20.0)
        assert w == 14.0 and h == 5.6, f"Expected (14.0, 5.6), got ({w}, {h})"
        # Extremely tall flowchart TD (aspect ratio 1:3)
        w2, h2 = calculate_aspect_dimensions(1000, 3000, max_w_cm=14.0, max_h_cm=20.0)
        assert h2 == 20.0 and w2 == 6.67, f"Expected (6.67, 20.0), got ({w2}, {h2})"
        print(f"  --> PASS: Wide -> ({w}cm, {h}cm) | Tall -> ({w2}cm, {h2}cm)")

        # -------------------------------------------------------------
        # Test 5: DOCX Injection with Placeholder (Run Fragmentation + keepNext chain)
        # -------------------------------------------------------------
        print("\n[TEST 5] DOCX Placeholder Injection & keepNext Chain...")
        test_docx_path = os.path.join(test_dir, "test_document.docx")
        doc = Document()
        doc.add_heading("1. Tổng quan hệ thống", level=1)
        p_pre = doc.add_paragraph("Đoạn văn mở đầu tài liệu.")
        # Simulate fragmented placeholder by creating multiple runs
        p_place = doc.add_paragraph()
        p_place.add_run("{{DIAGRAM_")
        p_place.add_run("AUTH_")
        p_place.add_run("FLOW}}")
        doc.add_paragraph("Đoạn văn kết thúc sau biểu đồ.")
        doc.save(test_docx_path)

        spec_inject_placeholder = {
            "mermaid_code": spec_seq["mermaid_code"],
            "diagram_name": "auth_flow",
            "inject_into": test_docx_path,
            "placeholder": "{{DIAGRAM_AUTH_FLOW}}",
            "caption_template": {
                "caption": "Hình 1.1: Luồng xác thực người dùng qua Face ID",
                "description": "Biểu đồ trình bày toàn bộ tiến trình xác thực sinh trắc học từ lúc ứng dụng khách gửi frame đến khi nhận session JWT.",
                "style": {
                    "caption_font_size": 10,
                    "caption_italic": True,
                    "caption_color": "#595959",
                },
            },
        }
        res_inj = render_mermaid_to_png(spec_inject_placeholder, base_dir=test_dir)
        assert res_inj["injected"] is True, "Injection failed"

        # Verify modified DOCX
        doc_mod = Document(test_docx_path)
        all_texts = [p.text for p in doc_mod.paragraphs]

        # 1. Verify placeholder is gone
        for t in all_texts:
            assert "{{DIAGRAM_AUTH_FLOW}}" not in t, f"Placeholder still present in: {t}"
            assert "{{DIAGRAM_" not in t, f"Fragmented run still present in: {t}"

        # 2. Verify caption and description present
        assert any("Hình 1.1: Luồng xác thực" in t for t in all_texts), "Caption not found in document"
        assert any("Biểu đồ trình bày toàn bộ tiến trình" in t for t in all_texts), "Description not found in document"

        # 3. Verify keepNext attributes
        img_p_found = False
        cap_p_found = False
        desc_p_found = False

        for p in doc_mod.paragraphs:
            drawings = p._element.findall(".//" + qn("w:drawing"))
            if drawings:
                img_p_found = True
                pPr = p._element.find(qn("w:pPr"))
                assert pPr is not None and pPr.find(qn("w:keepNext")) is not None, "Image paragraph missing keepNext"

            if "Hình 1.1:" in p.text:
                cap_p_found = True
                pPr = p._element.find(qn("w:pPr"))
                assert pPr is not None and pPr.find(qn("w:keepNext")) is not None, "Caption paragraph missing keepNext"

            if "Biểu đồ trình bày toàn bộ" in p.text:
                desc_p_found = True
                pPr = p._element.find(qn("w:pPr"))
                has_keep = (pPr is not None and pPr.find(qn("w:keepNext")) is not None)
                assert not has_keep, "Final description paragraph should NOT have keepNext"

        assert img_p_found, "Image paragraph not found in DOCX"
        assert cap_p_found, "Caption paragraph not found in DOCX"
        assert desc_p_found, "Description paragraph not found in DOCX"

        print("  --> PASS: Placeholder replaced cleanly, keepNext chain verified on [Image -> Caption -> Description]!")

        # -------------------------------------------------------------
        # Test 6: Atomic Protection on Mermaid syntax error
        # -------------------------------------------------------------
        print("\n[TEST 6] Atomic Protection on Syntax Error...")
        mod_time_before = os.path.getmtime(test_docx_path)
        spec_fail = {
            "mermaid_code": "invalid syntax that will crash mmdc\n  >>> ->>",
            "inject_into": test_docx_path,
            "target_heading": "1. Tổng quan hệ thống",
        }
        caught_error = False
        try:
            render_mermaid_to_png(spec_fail)
        except RuntimeError as exc:
            caught_error = True
            assert "DOCX was not modified" in str(exc), "Error message does not state DOCX protection"

        assert caught_error, "RuntimeError was not raised for invalid Mermaid syntax"
        mod_time_after = os.path.getmtime(test_docx_path)
        assert mod_time_before == mod_time_after, "DOCX file was modified despite rendering failure!"
        print("  --> PASS: Atomic Protection confirmed! DOCX was completely untouched.")

        print("\n" + "=" * 60)
        print("ALL 6 TEST CASES PASSED SUCCESSFULLY (100%)!")
        print("=" * 60)

    except Exception as exc:
        import traceback
        print(f"\n[FAILURE] Test suite error: {exc}")
        traceback.print_exc()
        all_passed = False
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    return all_passed


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
