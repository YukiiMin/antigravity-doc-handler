# Sổ Cái Quản Lý Tool & Tri Thức Kỹ Thuật (TOOLS_INVENTORY)

> **Vị trí**: `tool/pdf_to_docx_converter/TOOLS_INVENTORY.md`  
> **Phiên bản**: 3.0 (Schema-First Enterprise Standard)  
> **Kiến trúc**: Hỗ trợ xuất và nạp trực tiếp vào SQLite / PostgreSQL / Vector DB (ETL Ready).  
> **Lưu trữ phiên bản cũ**: Đã di chuyển 11 script thử nghiệm/cũ vào `tools/archive/` kèm `tools/archive/MANIFEST.json`.

---

# PHẦN A — TOOL CATALOG REGISTRY

| Tool File | Vai trò / Trách nhiệm | Input Specs | Output Artifacts | Status |
|---|---|---|---|---|
| `tools/unified_qa_diagnostic.py` | Kiểm tra, chẩn đoán toàn diện lỗi format Docx/Excel/Diagrams/Conversion & Tự động sửa an toàn | `.docx`, `.xlsx`, asset dirs | Terminal Report / JSON / SARIF | **Active Production** |
| `tools/build_final_workbook.py` | Engine sinh workbook hoàn chỉnh 25 sheets (Report 5) chuẩn 100% Invariants E1–E14 | `Report5_Unit Test.xlsx` + Template | `Report5_Unit Test-Final.xlsx` | **Active Production** |
| `tools/format_diff_excel.py` | Diff Engine 12 cổng chất lượng kiểm định cell-by-cell với reference sheet | `.xlsx` (Target sheet + Ref sheet) | Format diff report (Exit 0/1) | **Active Production** |
| `converter_engine.py` | Engine điều phối chuyển đổi 6 chiều giữa PDF, DOCX, Markdown (.md) | `.pdf`, `.docx`, `.md` | Target format document | **Active Production** |
| `markdown_converter.py` | Parser & Generator chuyển đổi 2 chiều giữa Markdown và Office DOCX/PDF | `.md`, `.docx`, `.pdf` | Converted document | **Active Production** |
| `smart_post_processor.py` | Hậu xử lý định dạng Word v3.0 (căn lề, table border, font, page split) | `.docx` | Cleaned `.docx` | **Active Production** |
| `docx_reader.py` | Đọc và bóc tách cây OpenXML của file Word thành JSON Snapshot | `.docx` | JSON Snapshot AST | **Active Production** |
| `docx_writer.py` | Tái tạo file Word từ JSON Snapshot bảo toàn 100% style template | JSON Snapshot AST | `.docx` | **Active Production** |
| `xlsx_reader.py` | Bóc tách cấu trúc workbook và cell ranges thành JSON Snapshot | `.xlsx` | JSON Snapshot AST | **Active Production** |
| `xlsx_writer.py` | Ghi dữ liệu JSON Snapshot vào Excel theo mẫu định dạng sẵn | JSON Snapshot AST | `.xlsx` | **Active Production** |
| `spec_diagram_engine.py` | Core engine vẽ sơ đồ kỹ thuật độ nét cao dạng Canvas Declarative | `specs/*.json` / Python API | `.svg`, `.png` Retina | **Active Production** |
| `diagram_editor.py` | Giao diện đồ họa Desktop chỉnh sửa trực quan sơ đồ Canvas Spec | `specs/*.json` | Rendered Diagram JSON/PNG | **Active Production** |
| `mermaid_renderer.py` | Biên dịch sơ đồ Mermaid sang PNG/SVG qua Puppeteer / mmdc | Mermaid syntax `.mmd` | `.png`, `.svg` | **Active Production** |
| `plantuml_renderer.py` | Biên dịch sơ đồ PlantUML sang PNG/SVG qua `plantuml.jar` nội bộ | PlantUML syntax `.puml` | `.png`, `.svg` | **Active Production** |
| `tools/gen_canvas_erd.py` | Sinh sơ đồ cơ sở dữ liệu Master ERD chất lượng xuất bản | Schema specification | `.png`, `.svg` | **Active Production** |
| `tools/gen_master_erd.py` | Sinh sơ đồ quan hệ thực thể Physical ERD 19 bảng Smart Mart | Schema specification | `.png`, `.svg` | **Active Production** |
| `tools/gen_hub_spoke_flow.py` | Sinh biểu đồ luồng kiến trúc Hub-and-Spoke hệ thống | System flow specification | `.png`, `.svg` | **Active Production** |
| `tools/gen_usecase_diagram.py` | Sinh sơ đồ phân nhóm tác nhân Use Case Diagram | Use case specification | `.png`, `.svg` | **Active Production** |
| `tools/patch_docx_report3.py` | Chắp vá và nhúng sơ đồ/bảng vào tài liệu Word Report 3 SRS | `Report3_SRS.docx` + Images | Patched `Report3_SRS.docx` | **Active Production** |
| `tools/patch_docx_staff_flow.py` | Nhúng sơ đồ quy trình nhân viên vào đúng cell bảng trong Word | `Report3_SRS.docx` + Staff Flow | Patched `Report3_SRS.docx` | **Active Production** |
| `tools/patch_docx_table_diagram.py` | Nhúng sơ đồ cấu trúc bảng dữ liệu vào tài liệu đặc tả | `Report3_SRS.docx` + DB Schema | Patched `Report3_SRS.docx` | **Active Production** |
| `tools/consolidate_and_clean_output.py` | Dọn dẹp tệp tin tạm và đồng bộ file output xuất xưởng | Target workspaces | Cleaned workspace directory | **Active Production** |
| `tools/archive/` (11 Files) | Thư mục lưu trữ các script thử nghiệm / inspect / verify cũ có MANIFEST | N/A | Lịch sử đối soát dự án | **Archived (Ignored)** |

---

# PHẦN B — LESSONS LEARNED & EDGE-CASES SCHEMA

Toàn bộ các bài học, bẫy lỗi và kỹ thuật xử lý được định dạng dưới dạng structured JSON blocks có schema chuẩn, sẵn sàng để ETL nạp vào Database/Vector DB.

```json
[
  {
    "id": "ERR_XLSX_001",
    "domain": "EXCEL",
    "title": "Prototype Row Style Cloning (Kế thừa dòng mẫu)",
    "symptom": "Dòng dữ liệu mới chèn vào bị lệch font (Arial 8.5pt), mất viền hoặc sai màu nền so với các dòng trên.",
    "root_cause": "Script tự khởi tạo Font, PatternFill, Border mới bằng code hoặc sao chép style từ file input thô thay vì clone từ dòng dữ liệu đại diện trong template.",
    "solution_pattern": "Xác định 1 dòng dữ liệu đại diện có sẵn ngay dưới Header. Khi chèn N dòng mới, sao chép 100% thuộc tính (font, fill, border, alignment, number_format) từ dòng prototype.",
    "target_tool": "tools/build_final_workbook.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_XLSX_002",
    "domain": "EXCEL",
    "title": "Dynamic Formula Range Expansion (Co giãn công thức theo AST/Regex)",
    "symptom": "Bảng tóm tắt hiển thị sai tổng số hoặc báo lỗi #REF!, #VALUE!, biểu đồ trỏ vào vùng ô rỗng.",
    "root_cause": "Hardcode chuỗi công thức như f'=COUNTIF(G10:G25,...)' hoặc gán giá trị số tĩnh khiến khi bảng dữ liệu phình to lên N dòng, dải tham chiếu không tự tịnh tiến.",
    "solution_pattern": "Quét công thức gốc có sẵn trong template, dùng Regex bóc tách dải ô tham chiếu (e.g. F10:F25) và tự động cập nhật dải thành F10:F{25 + Delta K}.",
    "target_tool": "tools/build_final_workbook.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_XLSX_003",
    "domain": "EXCEL",
    "title": "Semantic Anchor Discovery (Tự động dò tìm điểm neo)",
    "symptom": "Dữ liệu mới ghi đè lên hàng Subtotal hoặc hàng Header do số dòng template khác với dự tính.",
    "root_cause": "Hardcode vị trí dòng (row=10, col=4) thay vì quét ma trận bảng để nhận diện các điểm mốc ngữ nghĩa.",
    "solution_pattern": "Quét bảng nhận diện Header Sentinel ('No', 'ID', 'Test Case'), Data Start Anchor (ngay dưới Header), và Summary Sentinel ('Total', 'Summary', '=SUM'). Dữ liệu chỉ chèn vào giữa Data Start và Summary Sentinel.",
    "target_tool": "tools/build_final_workbook.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_XLSX_004",
    "domain": "EXCEL",
    "title": "Safe Merged-Cell Introspection (Bảo vệ ô gộp)",
    "symptom": "Ném ngoại lệ 'AttributeError: MergedCell is read-only' hoặc rách viền ô xung quanh vùng gộp.",
    "root_cause": "OpenXML chỉ cho phép lưu trữ giá trị tại ô Top-Left trong dải merged_cells; các ô phụ là đối tượng chỉ đọc.",
    "solution_pattern": "Sử dụng helper get_effective_cell(ws, coordinate). Giá trị chỉ ghi vào ô Top-Left; style và border phải đồng bộ cho toàn bộ các ô trong dải merged.",
    "target_tool": "tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_XLSX_005",
    "domain": "EXCEL",
    "title": "Adaptive 2D Freeze Panes & Column Padding",
    "symptom": "Cuộn trang bị mất tiêu đề hoặc cột dữ liệu bị che khuất văn bản.",
    "root_cause": "Không cấu hình Freeze Panes hoặc cố định vị trí Freeze Panes cứng nhắc không khớp với cấu trúc bảng.",
    "solution_pattern": "Xác định điểm neo Freeze Panes tự động tại giao điểm (Header Sentinel Row + 1, Cột dữ liệu đầu tiên). Điều chỉnh độ rộng cột bằng max(độ dài dữ liệu + 3, độ rộng template).",
    "target_tool": "tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_XLSX_006",
    "domain": "EXCEL",
    "title": "DrawingML & Package Integrity Preservation",
    "symptom": "Mất logo, hình ảnh hoặc các shape đồ họa ở Cover sheet sau khi xuất file.",
    "root_cause": "Khởi tạo lại đối tượng Workbook() rỗng thay vì load trực tiếp template gốc để chỉnh sửa (mutate in-place/clone).",
    "solution_pattern": "Tuyệt đối không dùng Workbook(). Luôn dùng load_workbook(template_path, data_only=False) để bảo tồn 100% DrawingML package parts.",
    "target_tool": "tools/build_final_workbook.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_XLSX_007",
    "domain": "EXCEL",
    "title": "Data Type Coercion & Leading-Zero Loss",
    "symptom": "Mã định danh '00123' hoặc mã TR '00001' bị mất số 0 đứng đầu, biến thành số nguyên 123.",
    "root_cause": "OpenPyXL tự động ép kiểu chuỗi số thành int/float khi không được chỉ định number_format rõ ràng.",
    "solution_pattern": "Đối với các cột định danh (ID, Code, Mã), bắt buộc gán cell.number_format = '@' và truyền giá trị dưới dạng kiểu chuỗi (str) tường minh.",
    "target_tool": "tools/build_final_workbook.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_DOCX_001",
    "domain": "WORD",
    "title": "The Last Paragraph Rule (Quy tắc đoạn văn cuối cell)",
    "symptom": "Microsoft Word báo lỗi 'The file is corrupt and cannot be opened' khi mở file .docx sau khi chỉnh sửa bằng code.",
    "root_cause": "Chuẩn OpenXML quy định mỗi ô bảng (<w:tc>) bắt buộc phải kết thúc bằng tối thiểu một đoạn văn (<w:p>). Code xóa sạch nội dung cell mà không để lại thẻ <w:p>.",
    "solution_pattern": "Kiểm tra len(tc.findall(qn('w:p'))) > 0. Nếu cell rỗng, bắt buộc chèn <w:p/> trước khi đóng thẻ cell.",
    "target_tool": "docx_writer.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_DOCX_002",
    "domain": "WORD",
    "title": "Cell Text Overwrite Stripping Formatting",
    "symptom": "Toàn bộ định dạng chữ, màu sắc và cỡ font trong cell của template bị biến mất sau khi gán nội dung mới.",
    "root_cause": "Gán trực tiếp cell.text = '...' sẽ xóa sạch toàn bộ paragraph và run con hiện có, đưa ô về style mặc định.",
    "solution_pattern": "Truy cập paragraph đầu tiên qua cell.paragraphs[0], xóa hoặc tái sử dụng các run hiện có, và chỉ gán text vào run: run.text = '...'.",
    "target_tool": "docx_writer.py, tools/patch_docx_report3.py"
  },
  {
    "id": "ERR_DOCX_003",
    "domain": "WORD",
    "title": "Multi-Page Table Pagination Rupture",
    "symptom": "Bảng biểu dài nhiều trang bị cắt đôi dòng ngang qua 2 trang hoặc trang thứ 2 không có hàng tiêu đề lặp lại.",
    "root_cause": "Thiếu các thuộc tính OpenXML điều khiển phân trang bảng: <w:cantSplit/> và <w:tblHeader/>.",
    "solution_pattern": "Thêm <w:cantSplit/> vào toàn bộ các dòng của bảng để chống cắt ngang dòng, và thêm <w:tblHeader/> vào dòng đầu tiên để tự động lặp lại header ở mọi trang.",
    "target_tool": "smart_post_processor.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_DOCX_004",
    "domain": "WORD",
    "title": "Table Cell Shading & Border XML Desync",
    "symptom": "Viền bảng bị đứt quãng hoặc màu nền của cell không hiển thị đúng như thiết kế.",
    "root_cause": "Xung đột giữa thuộc tính bảng tổng thể (<w:tblPr>) và thuộc tính riêng của từng cell (<w:tcPr>), hoặc thiếu namespace OpenXML khi chèn XML thô.",
    "solution_pattern": "Sử dụng parse_xml(f'<w:shd {nsdecls(\"w\")} w:fill=\"{color}\"/>') với namespace đầy đủ để gán shading và border đồng bộ.",
    "target_tool": "smart_post_processor.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_DOCX_005",
    "domain": "WORD",
    "title": "Inline Shapes Aspect Ratio & Margin Overflow",
    "symptom": "Hình ảnh sơ đồ bị tràn ra ngoài lề trang giấy in hoặc bị méo tỉ lệ ngang/dọc.",
    "root_cause": "Chèn hình ảnh với kích thước cố định lớn hơn chiều rộng vùng in khả dụng (page_width - left_margin - right_margin) hoặc chỉnh width mà không chỉnh height theo tỉ lệ gốc.",
    "solution_pattern": "Đọc kích thước vùng in của section: printable_w = page_width - left_margin - right_margin. Nếu ảnh lớn hơn printable_w, tự động co về printable_w và tính height = width / aspect_ratio.",
    "target_tool": "tools/patch_docx_report3.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_DOCX_006",
    "domain": "WORD",
    "title": "Template Style Inheritance vs Raw XML Injection",
    "symptom": "Tài liệu phình to dung lượng, khó chỉnh sửa đồng loạt từ Word và có nguy cơ sinh XML không hợp lệ.",
    "root_cause": "Inject hàng loạt thẻ XML thô cho từng cell thay vì kế thừa Table Style có sẵn trong styles.xml của template.",
    "solution_pattern": "Kiểm tra danh sách style có sẵn trong document.styles. Nếu có style chuẩn, gán table.style = '...' để tài liệu gọn nhẹ và bảo toàn phân cấp.",
    "target_tool": "docx_writer.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_DIAG_001",
    "domain": "DIAGRAM",
    "title": "Template-Driven Token Drift",
    "symptom": "Sơ đồ vẽ lại không khớp với phong cách thiết kế chung của bộ tài liệu mẫu.",
    "root_cause": "Tự suy diễn màu sắc, font chữ và bán kính bo góc thay vì trích xuất từ sơ đồ mẫu trong template.",
    "solution_pattern": "Khi có template, trích xuất 100% token kiểu dáng (font family, node width, corner radius, connection stroke, palette) làm nguồn chân lý duy nhất.",
    "target_tool": "spec_diagram_engine.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_DIAG_002",
    "domain": "DIAGRAM",
    "title": "Zero-Template Layout Collision (Nguyên tắc vẽ khi không có mẫu)",
    "symptom": "Các box đè lên nhau, đường nối cắt ngang chữ, màu sắc chói lóa gây khó đọc.",
    "root_cause": "Không có hệ thống lưới tọa độ declarative và thiếu quy tắc phối màu chuẩn khi tạo sơ đồ từ đầu.",
    "solution_pattern": "Áp dụng quy tắc phối màu 60-30-10 (60% nền trung tính, 30% cấu trúc thẻ trắng/slate, 10% màu nhấn ngữ nghĩa). Bố trí node trên Canvas Grid có khoảng cách tối thiểu 40px giữa các box và bo tròn góc 8px.",
    "target_tool": "spec_diagram_engine.py, tools/gen_canvas_erd.py"
  },
  {
    "id": "ERR_DIAG_003",
    "domain": "DIAGRAM",
    "title": "Chart Anchor Overlap (Đè biểu đồ lên dữ liệu)",
    "symptom": "Biểu đồ trong sheet tổng quan nằm đè lên các dòng chỉ số hoặc bảng số liệu.",
    "root_cause": "OpenPyXL không tự động dịch chuyển vị trí neo (anchor) của biểu đồ khi các bảng dữ liệu bên trên được mở rộng thêm dòng.",
    "solution_pattern": "Sau khi chèn dữ liệu, tính toán tọa độ dòng kết thúc cuối cùng của khối bảng (e.g. SUB_ROW + 8), gán chart.anchor._from.row = dòng này.",
    "target_tool": "tools/build_final_workbook.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_CONV_001",
    "domain": "CONVERSION",
    "title": "Headless Conversion Layout Drift",
    "symptom": "Chuyển PDF sang DOCX bị vỡ bảng thành các đoạn text rời rạc hoặc mất định dạng cột.",
    "root_cause": "Dùng công cụ OCR cấp thấp hoặc trình trích xuất text thuần túy thay vì engine phân tích layout cấu trúc.",
    "solution_pattern": "Sử dụng kiến trúc phân tầng của Stirling-PDF: dùng bộ lọc writer_pdf_import của LibreOffice headless làm engine lõi để bảo toàn 100% layout và bảng biểu.",
    "target_tool": "converter_engine.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_CONV_002",
    "domain": "CONVERSION",
    "title": "Font Embedding & Missing Glyphs",
    "symptom": "Chữ tiếng Việt có dấu bị biến thành ô vuông hoặc dấu chấm hỏi khi render sơ đồ sang PNG/PDF.",
    "root_cause": "Hệ thống render thiếu các font chữ tiêu chuẩn hỗ trợ đầy đủ bộ ký tự Unicode (Segoe UI, Arial, Tahoma).",
    "solution_pattern": "Chỉ định chuỗi font-family fallback đầy đủ: 'Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif' trong engine đồ họa.",
    "target_tool": "spec_diagram_engine.py, tools/unified_qa_diagnostic.py"
  },
  {
    "id": "ERR_CONV_003",
    "domain": "CONVERSION",
    "title": "Markdown-Office Roundtrip Semantic Loss",
    "symptom": "Mất định dạng gộp ô (merged cells) hoặc mất màu nền khi chuyển đổi qua lại giữa Markdown và Word/Excel.",
    "root_cause": "Markdown chuẩn không hỗ trợ thuộc tính colspan/rowspan hoặc cell shading.",
    "solution_pattern": "Bảo tồn ngữ nghĩa thông qua tầng trung gian JSON AST (docx_reader -> JSON Snapshot -> docx_writer) thay vì convert phẳng qua chuỗi Markdown.",
    "target_tool": "markdown_converter.py, docx_reader.py, docx_writer.py"
  },
  {
    "id": "ERR_CONV_004",
    "domain": "CONVERSION",
    "title": "Zombie Lock Files Cleanup",
    "symptom": "Lần chạy sau bị treo (freeze) hoặc báo lỗi 'Permission Denied: [WinError 32]' do file đang bị khóa.",
    "root_cause": "Tiến trình chạy nền của Office hoặc script bị crash giữa chừng để lại file khóa tạm (~$*.xlsx hoặc .~lock.*#).",
    "solution_pattern": "Bổ sung Context Manager tự động quét và thu gom sạch các file khóa tạm trước và sau khi thực thi tiến trình.",
    "target_tool": "tools/unified_qa_diagnostic.py"
  }
]
```
