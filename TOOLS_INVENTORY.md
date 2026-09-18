# Danh mục & Bảng Tổng hợp Công cụ (Python Tools Inventory)

> **Vị trí**: `tool/pdf_to_docx_converter/` & `tool/pdf_to_docx_converter/tools/`  
> **Phiên bản**: 2.0 (Cập nhật sau chuẩn hóa Invariants E1–E14)  
> **Tổng số file .py**: 37 files (16 files ở thư mục gốc, 21 files trong `tools/`)

---

## 1. Bản đồ Phân tầng Kiến trúc (Architectural Layers)

Hệ thống mã nguồn Python trong bộ công cụ được tổ chức thành 6 tầng chức năng:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Core Conversion Engine & Pipelines                                   │
│    converter_engine.py, markdown_converter.py, smart_post_processor.py │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Document & Spreadsheet Serializers / Deserializers                   │
│    docx_reader.py, docx_writer.py, xlsx_reader.py, xlsx_writer.py      │
├────────────────────────────────────────────────────────────────────────┤
│ 3. CLI, Desktop Studio & Editing Tools                                 │
│    main.py, cli.py, gui.py, ai_tools_cli.py, diagram_editor.py         │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Diagram & Visual Rendering Engines                                  │
│    spec_diagram_engine.py, mermaid_renderer.py, plantuml_renderer.py,  │
│    gen_canvas_erd.py, gen_master_erd.py, gen_hub_spoke_flow.py, ...    │
├────────────────────────────────────────────────────────────────────────┤
│ 5. Excel Generation & Format Assurance Engines (Invariants E1–E14)     │
│    build_final_workbook.py, format_diff_excel.py                        │
├────────────────────────────────────────────────────────────────────────┤
│ 6. DOCX Document Patchers & Precision Injectors                        │
│    patch_docx_report3.py, patch_docx_staff_flow.py, ...                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Chi tiết Thư mục Gốc (`tool/pdf_to_docx_converter/`) [16 Files]

| # | Tên File | Tầng Chức năng | Trạng thái | Tác dụng & Trách nhiệm Kỹ thuật |
|---|---|---|---|---|
| 1 | `__init__.py` | Package Core | Active | Định nghĩa package Universal Document Studio, phiên bản và các module export chính. |
| 2 | `main.py` | Entrypoint | Active | Điểm khởi chạy CLI cấp cao nhất của bộ công cụ chuyển đổi. |
| 3 | `cli.py` | CLI Interface | Active | Giao diện dòng lệnh chuẩn hỗ trợ chuyển đổi đa chiều giữa PDF, DOCX và Markdown. |
| 4 | `ai_tools_cli.py` | AI Tooling CLI | Active | Bộ công cụ CLI chuyên dụng cho AI thực hiện snapshot, diff và áp dụng chỉnh sửa tài liệu chính xác. |
| 5 | `gui.py` | Desktop UI | Active | Ứng dụng Desktop giao diện đồ họa hiện đại (CustomTkinter) cho Universal Document Studio. |
| 6 | `converter_engine.py` | Core Converter | Active | Engine điều phối chuyển đổi 6 chiều giữa PDF, DOCX, Markdown (.md) tích hợp LibreOffice và Poppler. |
| 7 | `markdown_converter.py` | Core Converter | Active | Parser và Generator chuyển đổi 2 chiều giữa Markdown chuẩn và tài liệu văn phòng DOCX / PDF. |
| 8 | `smart_post_processor.py`| Post-Processor | Active | Engine hậu xử lý tài liệu Word (v3.0): làm đẹp typography, căn chỉnh lề, fix border bảng biểu và ngắt trang. |
| 9 | `docx_reader.py` | Serializer | Active | Đọc cấu trúc file Word (.docx) và bóc tách thành cây JSON Snapshot cho AI phân tích. |
| 10 | `docx_writer.py` | Serializer | Active | Lắp ráp và tái tạo file Word (.docx) từ JSON Snapshot với khả năng bảo toàn định dạng 100%. |
| 11 | `xlsx_reader.py` | Serializer | Active | Đọc và bóc tách cấu trúc bảng tính Excel (.xlsx) thành dữ liệu Snapshot JSON. |
| 12 | `xlsx_writer.py` | Serializer | Active | Ghi và tuần tự hóa dữ liệu JSON vào Excel theo mẫu định dạng sẵn. |
| 13 | `spec_diagram_engine.py` | Diagram Engine | Active | Core engine vẽ sơ đồ kỹ thuật độ phân giải cao bằng code (Canvas declarative API, xuất SVG/PNG). |
| 14 | `diagram_editor.py` | Visual Editor | Active | Trình biên tập trực quan tương tác dạng Canvas cho các sơ đồ JSON Spec Diagrams. |
| 15 | `mermaid_renderer.py` | Diagram Engine | Active | Engine render sơ đồ Mermaid sang hình ảnh thông qua Puppeteer hoặc Mermaid CLI. |
| 16 | `plantuml_renderer.py` | Diagram Engine | Active | Engine render sơ đồ PlantUML sang PNG/SVG sử dụng `plantuml.jar` nội bộ hoặc server. |

---

## 3. Chi tiết Thư mục Công cụ Chuyên biệt (`tool/pdf_to_docx_converter/tools/`) [21 Files]

### Nhóm A: Bộ Công cụ Production Active (Đang Sử dụng Trực tiếp)

| # | Tên File | Tầng Chức năng | Trọng tâm Nghiệp vụ | Mô tả Chi tiết Tác dụng |
|---|---|---|---|---|
| 17 | `build_final_workbook.py` | Excel Production | Report 5 Unit Test | **Bộ sinh bảng tính hoàn chỉnh cấp Enterprise**: Tự động sinh 20 sheet hàm từ input thô, cập nhật KPI hàng 7, tính toán overview (`Cover`, `Functions`, `Statistics`), relink biểu đồ Pie Chart và tích hợp UX Auto-scaling (Tuân thủ Invariants E1–E14). |
| 18 | `format_diff_excel.py` | QA / Audit | 12 Quality Gates | **Diff Engine 12 cổng chất lượng**: Đối chiếu cell-by-cell (Font, Size, Fill, Border, Align, Merge, Data Validation, Geometry) giữa sheet tạo ra và sheet mẫu `Example`. Bắt buộc chạy kiểm định trước khi bàn giao. |
| 19 | `gen_canvas_erd.py` | Diagram Engine | Master ERD | Sinh sơ đồ cơ sở dữ liệu quan hệ (ERD) chất lượng xuất bản dạng SVG và PNG độ nét cao bằng canvas declarative. |
| 20 | `gen_master_erd.py` | Diagram Engine | Physical ERD | Trình sinh đặc tả Physical ERD cho hệ thống Smart Mart với 19 bảng cơ sở dữ liệu, khóa chính, khóa ngoại. |
| 21 | `gen_hub_spoke_flow.py` | Diagram Engine | System Architecture| Sinh sơ đồ luồng kiến trúc Hub-and-Spoke kết nối các microservice thông qua `spec_diagram_engine`. |
| 22 | `gen_usecase_diagram.py`| Diagram Engine | Use Case Analysis | Sinh biểu đồ Use Case Diagram phân chia các nhóm tác nhân (Customer, Staff, Admin, Robot). |
| 23 | `patch_docx_report3.py` | DOCX Patching | Report 3 SRS | Chắp vá và nhúng tự động các hình ảnh sơ đồ kỹ thuật, bảng dữ liệu và style vào file Word `Report3_SRS.docx`. |
| 24 | `patch_docx_staff_flow.py` | DOCX Patching | Staff Workflow | Nhúng sơ đồ quy trình nghiệp vụ nhân viên vào tài liệu Word theo kích thước và vị trí bảng chính xác. |
| 25 | `patch_docx_table_diagram.py` | DOCX Patching | DB Specification | Định dạng bảng biểu cơ sở dữ liệu và nhúng sơ đồ quan hệ vào tài liệu đặc tả phần mềm. |
| 26 | `consolidate_and_clean_output.py` | Workspace Utility | Clean & Archive | Dọn dẹp các tệp tin tạm thời, chuẩn hóa cây thư mục xuất xưởng và đồng bộ các file output cuối cùng. |

---

### Nhóm B: Bộ Script Thử nghiệm / Phiên bản Tiền nhiệm / Kiểm định Riêng biệt

Các file này được sinh ra trong các bước phát triển trung gian, thử nghiệm mẫu hoặc phục vụ kiểm tra một lần:

| # | Tên File | Phân loại | Mục đích & Lịch sử Sử dụng |
|---|---|---|---|
| 27 | `create_example_test01.py` | Thử nghiệm / Test | Script sinh thử nghiệm một sheet đơn `example_test01` lấy dữ liệu từ sheet `NAV-SVC` trong giai đoạn kiểm chứng format. |
| 28 | `create_example_test_sheet.py` | Phiên bản cũ | Bản tiền nhiệm của bộ tạo sheet đơn trước khi tách thành generator hoàn chỉnh. |
| 29 | `generate_report5_deliverables.py` | Phiên bản cũ | Bộ sinh kép cho Report 5 ban đầu; hiện tại đã được nâng cấp và thay thế toàn diện bởi `build_final_workbook.py`. |
| 30 | `generate_enhanced_ux_excel.py` | Phiên bản cũ | Script thử nghiệm thêm tính năng UX nâng cao (màu sắc, freeze panes) trước khi áp dụng Invariant `E2` (Grill-Before-Deviate). |
| 31 | `generate_chohung_unit_test.py` | Deliverable riêng | Script tạo bảng tính test case cho nhánh yêu cầu riêng (`Report5_Unit Test_ChoHung.xlsx`). |
| 32 | `precision_template_injector.py` | Phiên bản cũ | Thử nghiệm inject dữ liệu trực tiếp đè lên template mà không qua bước clone cấu trúc. |
| 33 | `format_unit_test_files.py` | Phiên bản cũ | Script định dạng các file unit test ban đầu. |
| 34 | `inspect_example_tokens.py` | QA / Diagnostic | Script phân tích nhanh và in ra các style token từ ô `F9`, `F15`, `A10`, `B45..B48` trong sheet mẫu `Example`. |
| 35 | `inspect_full_example.py` | QA / Diagnostic | Script kiểm tra toàn diện cấu trúc tab, freeze panes, tab color của sheet `Example`. |
| 36 | `verify_chohung.py` | QA / Diagnostic | Script kiểm định số lượng sheet và dữ liệu của file output ChoHung. |
| 37 | `verify_semantic_fidelity.py` | QA / Diagnostic | Script audit tính toàn vẹn ngữ nghĩa và số lượng function sheet sau khi build. |

---

## 4. Hướng dẫn Lựa chọn Công cụ Nhanh (Cheat Sheet)

* **Cần tạo file Excel Test Report chuẩn 100% template**:  
  👉 Chạy `python tool/pdf_to_docx_converter/tools/build_final_workbook.py`
* **Cần kiểm định định dạng bảng tính với Template mẫu**:  
  👉 Chạy `python tool/pdf_to_docx_converter/tools/format_diff_excel.py <target_file> <target_sheet> <ref_sheet>`
* **Cần vẽ lại sơ đồ ERD hoặc Architecture dạng ảnh nét cao**:  
  👉 Dùng `spec_diagram_engine.py` hoặc chạy `gen_canvas_erd.py` / `gen_hub_spoke_flow.py`
* **Cần chắp vá tài liệu Word (DOCX) với ảnh sơ đồ kỹ thuật**:  
  👉 Dùng `patch_docx_report3.py` hoặc `smart_post_processor.py`
* **Cần chuyển đổi file 6 chiều (PDF, DOCX, Markdown)**:  
  👉 Dùng `converter_engine.py` qua lệnh CLI `python cli.py` hoặc mở giao diện `python gui.py`
