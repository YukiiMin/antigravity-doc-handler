# WORKFLOW.md — Quy Trình Tác Nghiệp Mô-đun Hóa Bộ Công Cụ AI-Native

> **Dự án**: `doctools` / `pdf_to_docx_converter`  
> **Phiên bản**: 2.0 (Master Baseline Toàn Diện) — Chuẩn hóa đồng bộ cả 3 mô-đun: **Module DOCX**, **Module XLSX**, và **Module DIAGRAM** theo Kế hoạch Kiến trúc Phiên bản 6.  
> **Đối tượng sử dụng**: AI Agent (Antigravity), CI/CD Automation Runner, và Kỹ sư phần mềm.

---

## 1. Kiến Trúc Điều Phối Tổng Thể (Master Workflow Architecture)

Bộ công cụ vận hành theo mô hình **AI-Native Plumbing (5 tầng chuẩn hóa)**:
- **Tầng 5: Client (AI Agent)**: Bộ não điều phối nghiệp vụ, phân tích yêu cầu, khảo sát file, phát sinh đặc tả cấu trúc JSON thuần (`DocSpec`, `MutationSpec`, `XlsxSpec`, `DiagramSpec`), phân tích báo cáo chẩn đoán (`diagnostics`) và kích hoạt phỏng vấn `/grill-me` khi có cảnh báo lệch mẫu (`W-DEV-*`).
- **Tầng 4: Registry & Protocol (MCP Server)**: Định tuyến yêu cầu tất định 100%, bảo đảm cô lập tenant, quản lý namespace công cụ với tiền tố tường minh: `docx.*`, `xlsx.*`, `diagram.*`.
- **Tầng 3: Engine Logic**: Biên dịch đặc tả, áp dụng rào chắn bảo vệ (OOXML Guards, AST Shift Manager, Cache Writer `lxml`, Topology Planner, Orthogonal Router).
- **Tầng 2: Data & File System**: Quản lý gói file ECMA-376 (ZIP) và pure native mxGraphModel XML.
- **Tầng 1: Infrastructure**: Môi trường thực thi an toàn (FileStore mờ, Sandbox cô lập, Headless Browser/LibreOffice Pool, Audit Logging).

### Cơ Chế Trao Đổi Bằng Hợp Đồng Chuẩn
Tuyệt đối không truyền payload binary lớn qua chat stream. Giao tiếp 100% qua đối tượng `FileRef` mờ `{ uri, sha256, size, mime, expires_at }` và phong bì kết quả thống nhất:
```json
{
  "success": true,
  "file_ref": { 
    "uri": "resource://<engine>/files/output_uuid", 
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 
    "size": 102400, 
    "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
    "expires_at": "2026-10-07T20:30:00Z" 
  },
  "diagnostics": {
    "engine": "docx",
    "errors": [],
    "warnings": [],
    "info": []
  },
  "guarantees_applied": ["cantSplit_enforced", "tblHeader_enforced", "tag_order_verified"],
  "stats": { "render_time_ms": 142, "elements_processed": 58 }
}
```

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              ANTIGRAVITY AI (MCP CLIENT)                               │
│  - Phân tích yêu cầu -> Khảo sát cấu trúc -> Phát sinh JSON Spec (Docx / Xlsx / Dgm)   │
│  - Đọc Diagnostics -> Triage (Tự sửa / Bàn giao / Grill-Before-Deviate)                 │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ MCP Tool Calls (JSON Spec + FileRef)
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                    REGISTRY TẬP TRUNG (doctools/registry.py)                            │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│    MODULE DOCX (Word)    │    MODULE XLSX (Excel)      │    MODULE DIAGRAM (Draw.io)   │
│  - docx.lint_template    │  - xlsx.preflight           │  - diagram.parse              │
│  - docx.normalize_tpl    │  - xlsx.inspect             │  - diagram.plan_layout        │
│  - docx.register_tpl     │  - xlsx.mutate              │  - diagram.build              │
│  - docx.render_template  │  - xlsx.build               │  - diagram.render_raster      │
│  - docx.get_manifest     │  - xlsx.validate            │  - diagram.render_svg         │
│  - docx.list_templates   │  - xlsx.diff                │  - diagram.inspect_visual     │
│  - docx.build_from_spec  │  - xlsx.recalc              │  - diagram.repair_layout      │
│  - docx.inspect_struct   │  - xlsx.lint_template       │  - diagram.diff_layout        │
│  - docx.validate         │  - xlsx.register_template   │  - diagram.export_pages       │
│  - docx.patch            │  - xlsx.list_templates      │                               │
│  - docx.merge            │  - xlsx.get_manifest        │                               │
│  (6 OOXML & Sec Gates)   │  (13 Universal & PG Gates)  │  (DG-00..08 + 21 MX_INV Gates)│
├──────────────────────────┴─────────────────────────────┴───────────────────────────────┤
│            HẠ TẦNG DÙNG CHUNG (FileStore, Sandbox Runner, Headless Pool, Audit)        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Workflows Cho Module DOCX (Word Document Engine)

### WF-DOCX-01: Nhập Kho & Chuẩn Hóa Template (Template Ingestion)
Quy trình đưa một template Word mẫu của doanh nghiệp vào kho lưu trữ có kiểm soát.

```
[Template .docx]
       │
       ▼
1. docx.lint_template(template_ref) 
       │ ──► Phát hiện lỗi Run Splitting (thẻ {{ ... }} bị băm nhỏ trong XML)?
       ▼
2. docx.normalize_template(template_ref)
       │ ──► Gộp các run chứa thẻ Jinja (giữ nguyên noProof, lang, xml:space)
       │ ──► Xuất bản template chuẩn hóa + bản diff kiểm tra
       ▼
3. Nạp Manifest YAML
       │ ──► Khai báo danh mục biến, kiểu dữ liệu, các khối lặp và trường bất biến
       ▼
4. docx.register_template(template_ref, manifest) ──► Lưu phiên bản, hash sha256 vào Template Store
```

### WF-DOCX-02: Dựng Tài Liệu Từ Template (Path A: Template-Driven Rendering)
Quy trình sinh tài liệu chuẩn từ template và tập dữ liệu nghiệp vụ (hợp đồng, báo cáo định kỳ).

1. **Khảo sát Schema**: AI đọc manifest bằng `docx.get_template_manifest(template_id)` để nắm rõ cấu trúc dữ liệu yêu cầu.
2. **Xác thực Đầu vào (Input Validation)**: Kiểm tra `context_data` theo Pydantic model động; kiểm tra hash các trường bất biến (`immutability.py`); chuẩn hóa Unicode NFC và lọc ký tự điều khiển XML 1.0.
3. **Render Cách Ly (Sandboxed Render)**: Chạy tiến trình render qua `docxtpl` trong môi trường sandbox (`SandboxedEnvironment`, `autoescape=True`, allow-list tags/filters).
4. **Cưỡng chế Semantic Guards**:
   - Khóa `<w:cantSplit/>` cho mọi hàng trong bảng.
   - Bổ sung `<w:tblHeader/>` cho hàng tiêu đề của bảng nhiều trang.
   - Đặt `<w:keepNext/>` cho các tiêu đề heading (chống mồ côi cuối trang).
   - Đặt `<w:vAlign w:val="center"/>` căn giữa ô bảng.
5. **Kiểm định OOXML Gates**:
   - `xsd_gate`: Kiểm tra tính hợp lệ ECMA-376.
   - `element_order_gate`: Kiểm tra thứ tự thẻ con theo Tag Order Registry.
   - `static_layout_gate`: Kiểm tra ô kết thúc bằng thẻ `<w:p>` và kích thước ảnh $\le 15.92\text{ cm}$.
6. **Bàn giao**: Cấp `file_ref` kết quả kèm báo cáo `diagnostics`.

### WF-DOCX-03: Dựng Tài Liệu Tự Do Từ Đặc Tả (Path B: DocSpec Builder)
Quy trình tạo tài liệu kỹ thuật, báo cáo giải pháp mới từ đầu mà không cần template có sẵn.

1. **Lập Đặc tả DocSpec JSON**: AI thiết kế dàn ý tài liệu gồm các khối phân tầng: `heading`, `paragraph`, `list_block`, `table_block`, `image_block`, `callout`.
2. **Biên dịch Khối (Block Compilation)**: `docx.build_from_spec` duyệt cây DocSpec và gọi các module tương ứng trong `blocks/`.
3. **Cưỡng chế Schema Helper**: Mọi thao tác ghi XML buộc phải đi qua `oxml_factory` và `schema_helper` để chèn đúng thứ tự thẻ con, loại bỏ nguy cơ corrupt XML.
4. **Áp dụng Base Theme**: Sử dụng named styles từ `base_templates/tpl_report_vi.docx` (màu sắc, typography, lề in).
5. **Kiểm định & Xuất Bản**: Đi qua bộ 6 OOXML Gates và trả về `file_ref`.

### WF-DOCX-04: Soi Cấu Trúc, Kiểm Định & Vá Lỗi (Inspect & Patch)
Quy trình kiểm tra tài liệu có sẵn, phát hiện lỗi cấu trúc và sửa chữa từng phần.

1. **Soi Cấu Trúc**: Gọi `docx.inspect_structure(file_ref)` để nhận cây DOM tóm tắt (các heading, bảng, đoạn văn) cùng các `anchor` định danh ổn định.
2. **Kiểm Định**: Gọi `docx.validate(file_ref)` để lấy danh sách vi phạm OpenXML (`ERR_DOCX_001..005`).
3. **Vá Lỗi (Patching)**:
   - AI lập danh sách thao tác nguyên tử: `replace_text`, `insert_paragraph`, `update_cell`.
   - Gọi `docx.patch(file_ref, operations=[...])` để áp dụng bản vá tại chỗ trên bản sao.
   - Kiểm định lại tính hợp lệ trước khi cấp `file_ref` mới.

### WF-DOCX-05: Ghép Nối Tài Liệu (Document Merge)
Quy trình nối nhiều tài liệu con (báo cáo chính + phụ lục).

1. Chuẩn bị file gốc `base_ref` và mảng phụ lục `parts[]`.
2. Chọn chính sách xử lý xung đột style (`style_conflict_policy`):
   - `master_wins` (mặc định): File chính áp đảo style của toàn bộ phụ lục.
   - `isolate_styles`: Tự động đổi tên style phụ lục để giữ nguyên giao diện độc lập.
3. Ghép part qua `merger.py` (dùng `docxcompose`), kiểm tra lại tính liên tục của numbering và header/footer giữa các section.

---

## 3. Workflows Cho Module XLSX (Spreadsheet Engine)

### WF-XLSX-01: Khảo Sát & Nhập Kho Template Excel (Preflight & Ingestion)
Quy trình thẩm định và nạp template bảng tính Excel vào hệ thống.

```
[Template .xlsx]
       │
       ▼
1. xlsx.preflight(file_ref)
       │ ──► Lập Package Inventory: hình ảnh, chart, pivot, CF, DV, bảng, macro, links
       │ ──► Xác định Fidelity Tier: T1 (an toàn), T2 (cần vá lxml), T3 (có nguy cơ mất dữ liệu)
       ▼
2. xlsx.lint_template(template_ref)
       │ ──► Quét Semantic Anchors (header, data_start, summary)
       │ ──► Kiểm tra Prototype Row và vùng khóa locked_zones
       │ ──► Phát hiện placeholder sót {{...}}
       ▼
3. Soạn thảo Template Profile YAML
       │ ──► Khai báo: reference_sheet, sibling_sheets, anchors, locked_zones, calc_policy
       ▼
4. xlsx.register_template(template_ref, manifest) ──► Lưu phiên bản và hash sha256 vào kho
```

### WF-XLSX-02: Đột Biến Bảng Tính Theo Dữ Liệu (Path A: In-Place Mutation)
Quy trình chuẩn cho mọi tác vụ điền dữ liệu, mở rộng dòng/cột trên template có sẵn.

```
[Yêu cầu & Dữ liệu]
       │
       ▼
1. xlsx.inspect(template_ref) ──► Lấy snapshot cấu trúc, anchors, và values_status
       │
       ▼
2. Lập MutationSpec JSON
       │ ──► cell_updates: Ghi ô dữ liệu đơn lẻ (tôn trọng locked_zones)
       │ ──► table_expansions: Khai báo anchor, prototype_row, rows[], id_columns (format '@')
       │ ──► calc_policy: { recalc: "oracle_verify", cache: "write", calc_on_open: "auto" }
       │ ──► approved_deviations: Danh sách mã W-DEV đã được người dùng duyệt qua /grill-me
       ▼
3. Gọi xlsx.mutate(template_id, mutation_spec)
       │
       ├─► [Engine Step 3.1] Tạo bản sao làm việc (Bảo toàn hash file gốc 100%)
       ├─► [Engine Step 3.2] Preflight lại bản sao, xác thực MutationSpec (chống chuỗi '=', NFC)
       ├─► [Engine Step 3.3] Phân giải Semantic Anchor (kind, scope, khớp cột theo header)
       ├─► [Engine Step 3.4] Shift Manager (AST Tokenizer):
       │                     - Dịch toán hạng ô/dải trỏ vào sheet đích trên TOÀN workbook
       │                     - Bảo toàn 100% tên hàm (LOG10, DAYS360), chuỗi, tên định danh
       │                     - Dịch đồng thời: merge, CF, DV, bảng, AutoFilter, defined names, charts
       ├─► [Engine Step 3.5] Style & Layout: Clone 100% Prototype Row, đồng bộ viền merged, freeze panes
       ├─► [Engine Step 3.6] Lưu file giao tạm thời qua openpyxl
       ├─► [Engine Step 3.7] Recalc Backend: Gửi bản sao sang LibreOffice headless tính lại và quét lỗi
       ├─► [Engine Step 3.8] Cache Writer (lxml):
       │                     - Tiêm thẻ <v> và thuộc tính t (n/str/b/e) vào sheetN.xml
       │                     - Bảo toàn 100% thẻ <f> (công thức còn sống)
       │                     - Tự kiểm bằng UG-13: đọc data_only khớp values_summary
       └─► [Engine Step 3.9] Kiểm định 13 Universal Gates + Profile Gates + Structural Diff
       ▼
4. Nhận FileRef và Diagnostics
       │ ──► Triage kết quả: Nếu có lỗi -> Tự sửa; Nếu có W-DEV -> Hỏi user; Nếu sạch -> Bàn giao
```

### WF-XLSX-03: Tạo Workbook Mới Từ Đầu (Path B: XlsxSpec Builder)
Dành cho trường hợp tạo file Excel hoàn toàn mới khi không có template mẫu.

1. **Lập Đặc tả XlsxSpec JSON**: AI soạn thảo sheets, bảng biểu, danh sách cột, dữ liệu.
2. **Khai báo Design Tokens**: Chọn theme và đường viền chuẩn (`theme: "corporate_blue"`, `border: "thin_grid"`). Tuyệt đối cấm đưa mã màu tùy ý.
3. **Biên dịch XlsxWriter**: Engine dựng workbook, tự động gán conditional formatting dạng công thức cho các hàng zebra.
4. **Tính toán & Tiêm Cache**: Chạy qua Recalc Backend và tiêm cache để file mở ở đâu cũng có sẵn số liệu.
5. **Kiểm định Universal Gates**: Chạy qua bộ cổng chung `UG-01..13` và xuất `file_ref`.

### WF-XLSX-04: Kiểm Định & Đối Chiếu Cấu Trúc Độc Lập (Validation & QA)
Dành cho kiểm thử chất lượng, CI/CD runner và nghiệm thu kỹ thuật.

1. **Kiểm định Cổng**: Gọi `xlsx.validate(file_ref, profile="unit_test_matrix")`.
   - Kiểm tra toàn bộ 13 Universal Gates (`UG-01..13`).
   - Kiểm tra các gate nghiệp vụ theo profile (PG-UT-01..12).
2. **Structural Diff**: Gọi `xlsx.diff(file_ref_before, file_ref_after)`.
   - Phân loại khác biệt thành: `declared` (hợp lệ theo spec) và `undeclared` (lỗi mất thành phần ngoài ý muốn).
   - Nếu có `undeclared` $\rightarrow$ Gate UG-02 thất bại, dừng phát hành.

### WF-XLSX-05: Đọc Cấu Trúc & Kiểm Soát Trạng Thái Giá Trị
Dành cho AI khi cần khảo sát số liệu bảng tính trước khi ra quyết định.

1. Gọi `xlsx.inspect(file_ref)`.
2. Kiểm tra cờ `values_status`:
   - `cached` (kèm `origin: "source_file"` hoặc `"engine_injected:libreoffice"`): File đã có số liệu cache sẵn, AI đọc an toàn.
   - `missing`: File chưa có cache $\rightarrow$ AI kích hoạt `xlsx.recalc(file_ref)` để backend tính và bổ sung cache trước khi đọc.
   - `recalculated`: Giá trị vừa được tính lại tươi mới.

---

## 4. Workflows Cho Module DIAGRAM (Diagram & Visual Architecture Engine)

### WF-DIAG-01: Dựng Sơ đồ Kiến trúc & ERD từ Đặc tả (Path B: Spec-Driven Generation)
Quy trình chuẩn mực để AI tạo sơ đồ khối kỹ thuật, ERD, DFD, hoặc kiến trúc hệ thống đạt chuẩn xuất bản.

```
[Mô tả Kỹ thuật / Thiết kế Hệ thống]
       │
       ▼
1. Lập DiagramSpec JSON thuần
       │ ──► topology: "erd" | "flowchart" | "c4_container" | "layered_arch" | "dfd"
       │ ──► nodes: id, label, kind, fields[] (cho ERD), group_id
       │ ──► edges: id, source, target, relationship (1:1, 1:N, N:M), label
       │ ──► theme: "academic_monochrome" | "slate_contrast" | "corporate_blue"
       ▼
2. diagram.plan_layout(diagram_spec)
       │ ──► Sugiyama Hierarchical / Force / Radial Layout tính toán tự động
       │ ──► Trả về LayoutPlan (tọa độ x, y, width, height, waypoints cho edge)
       │ ──► Cấm AI tự đoán tọa độ pixel bằng tay!
       ▼
3. diagram.build(diagram_spec, layout_plan)
       │ ──► Biên dịch ra pure native mxGraphModel XML (.drawio)
       │ ──► Cưỡng chế MX_INV_01 (không UserObject), MX_INV_03 (docking vỏ bảng)
       │ ──► Cưỡng chế MX_INV_04 (cổng viền orthogonal 0.0, 0.5, 1.0)
       │ ──► Cưỡng chế MX_INV_16 (phân cấp 4 tầng nét vẽ: 2.5px > 1.8px > 1.2px > 1.0px)
       │ ──► Cưỡng chế MX_INV_20 (mặt nạ che nhãn snug mask, không che dây)
       ▼
4. diagram.render_raster(file_ref, format="png")
       │ ──► Render headless qua Draw.io Desktop CLI hoặc Playwright sidecar
       │ ──► Áp dụng MX_INV_21: viewport động max + 160px, PIL auto-crop 25px uniform padding
       ▼
5. diagram.inspect_visual(file_ref_png)
       │ ──► Kiểm tra thị giác khép kín: va chạm nhãn, dây cắt thân, nhãn tràn
       │ ──► Nếu sạch 100% ──► Bàn giao file_ref (.drawio và .png)
       │ ──► Nếu phát hiện lỗi ──► Chuyển sang WF-DIAG-03 (Auto-Repair Loop)
```

### WF-DIAG-02: Chuyển đổi Từ Cú pháp Văn bản (Path A: Text DSL Ingestion)
Quy trình tiếp nhận sơ đồ từ cú pháp phổ biến (Mermaid, PlantUML, SQL DDL) sang Draw.io native chất lượng cao.

```
[Mermaid / PlantUML / SQL DDL]
       │
       ▼
1. diagram.parse(text_content, format="mermaid"|"plantuml"|"ddl")
       │ ──► Trích xuất cấu trúc thành DiagramSpec chuẩn hóa
       │ ──► Tuyệt đối LOẠI BỎ thuộc tính rác: mermaidData, plantUmlData, alternateBounds
       ▼
2. Kế thừa tiếp WF-DIAG-01 (Step 2: plan_layout ──► Step 3: build ──► Step 4: render ──► Step 5: inspect)
```

### WF-DIAG-03: Kiểm định Cổng & Chẩn đoán Thị giác Khép kín (Visual Inspection & Auto-Repair Loop)
Quy trình đảm bảo sơ đồ không bị lỗi kỹ thuật hình thức, chống từ chối Apply và chống méo mó.

```
[Bản vẽ .drawio vừa sinh]
       │
       ▼
1. Kiểm định Cú pháp & Cổng Cấu trúc (DG-00..08 + 21 MX_INV Gates)
       │ ──► DG-00: Well-formed XML, no orphan edges, no cycle parents
       │ ──► DG-01: Pure Native Hierarchy (không UserObject)
       │ ──► DG-02: Orthogonal Port Snapping
       │ ──► DG-03: Container Docking Check
       │ ──► DG-04: Label Masking & No-Clipped Text
       │ ──► DG-05: Dynamic Height Matching (H = 43 * (N + 1))
       ▼
2. Headless Render & Phân tích Thị giác: diagram.inspect_visual(png_ref)
       │ ──► Quét bounding boxes: phát hiện va chạm nhãn-dây (Collision Detection)
       │ ──► Phát hiện dây đâm xuyên hộp linh kiện (Component Piercing)
       ▼
3. Đánh giá Kết quả:
       ├─► KHÔNG CÓ LỖI: Bàn giao file_ref cho người dùng.
       └─► CÓ LỖI HÌNH HỌC (Fixable by Engine):
             │
             ▼
       Gọi diagram.repair_layout(file_ref, diagnostics)
             │ ──► Engine tự điều chỉnh khoảng cách trục bus (≥ 30-50px)
             │ ──► Engine nắn lại cổng viền khớp trục Y
             │ ──► Re-render và inspect lần 2
             ▼
       (Quy tắc Fail-Fast: Sau 1 lần sửa nếu không đạt -> DỪNG, báo cáo bằng chứng)
```

### WF-DIAG-04: Đóng gói Đa Trang Độc Lập (Multi-Page Packaging & Export)
Quy trình đóng gói bộ tài liệu kiến trúc nhiều góc nhìn (Context, Container, Component, Data Model) vào một file duy nhất.

1. **Soạn Thảo Bộ DiagramSpec**: Mỗi góc nhìn kiến trúc tương ứng với một trang `<diagram name="...">` (`MX_INV_09`).
2. **Build Multi-Page**: Gọi `diagram.build` với danh sách specs để nhúng chung vào một container XML duy nhất.
3. **Xuất Bản Đa Định Dạng**: Gọi `diagram.export_pages(file_ref, format="png"|"svg"|"pdf")` để xuất đồng thời:
   - File tổng `.drawio` để kỹ sư mở và kéo thả chỉnh sửa trực tiếp trên Draw.io desktop.
   - Thư mục ảnh từng trang `.png` (2x DPI) để nhúng vào báo cáo DOCX hoặc thuyết trình.

### WF-DIAG-05: So sánh Khác biệt Sơ đồ (Visual & Structural Diff)
Dành cho CI/CD hoặc quy trình Review Kiến trúc khi cập nhật phiên bản sơ đồ.

1. **Structural Diff**: Gọi `diagram.diff_layout(file_ref_before, file_ref_after)`.
   - Đối chiếu danh sách Node thêm mới / xóa bỏ / sửa đổi thuộc tính.
   - Đối chiếu danh sách Edge và đường đi waypoints.
2. **Visual Diff**: So sánh hình ảnh raster trước và sau, đánh dấu vùng biến đổi (Bounding Box Highlight) để kỹ sư nhận biết trực quan thay đổi kiến trúc.

---

## 5. Diagnostics Triage — Hướng Dẫn Xử Lý Chẩn Đoán Toàn Diện Cho AI

Cả 3 Module đều dùng chung cấu trúc `Issue` chuẩn:
```json
{
  "code": "E-...",
  "severity": "error | warning | info",
  "engine": "docx | xlsx | diagram",
  "location": { "sheet": "...", "cell": "...", "part": "...", "node_id": "...", "edge_id": "..." },
  "message": "Mô tả nguyên nhân kỹ thuật",
  "evidence": { "before": "...", "after": "..." },
  "fixable_by": "engine | ai | human",
  "suggested_action": "Tên hành động khắc phục đề xuất"
}
```

### Bảng Tra Cứu Mã Lỗi Phổ Biến Theo Module

| Mã Lỗi | Mô-đun | Ý Nghĩa Kỹ Thuật | Hành Động Xử Lý Chuẩn |
|---|---|---|---|
| `E-DOCX-SPEC-INVALID` | DOCX | DocSpec sai cấu trúc schema Pydantic | AI tự sửa JSON Spec theo path báo lỗi |
| `E-DOCX-SEC-INJECTION`| DOCX | Thẻ Jinja chứa mã nguy hiểm hoặc biểu thức cấm | Dừng, xóa biểu thức cấm khỏi template |
| `E-DOCX-OPENXML-TC-P` | DOCX | Ô bảng `<w:tc>` thiếu thẻ kết thúc `<w:p>` | Engine tự động chèn `<w:p/>` trước khi đóng |
| `E-XLSX-SPEC-SCHEMA`  | XLSX | MutationSpec sai cấu trúc JSON | AI tự sửa MutationSpec theo path |
| `E-XLSX-LOCK-VIOLATION`| XLSX| Cố tình ghi đè vào vùng khóa `locked_zones` | Dừng, hỏi ý kiến người dùng qua `/grill-me` |
| `E-XLSX-SHIFT-FORMULA`| XLSX | Công thức bị lệch dải ô sau khi chèn dòng | Kích hoạt Shift Manager dịch lại AST toán hạng |
| `E-XLSX-CACHE-MISMATCH`| XLSX| Giá trị cache tính lại không khớp ô công thức | Chạy lại Recalc Backend và tiêm lại cache |
| `E-DGM-SPEC-SCHEMA`   | DIAGRAM| DiagramSpec thiếu trường hoặc sai kiểu | AI tự sửa JSON Spec |
| `E-DGM-TOPOLOGY-PORT` | DIAGRAM| Cổng viền docking bị lệch khỏi 0.0, 0.5, 1.0 | Kích hoạt Auto-Repair nắn lại cổng viền chuẩn |
| `E-DGM-XML-USEROBJECT`| DIAGRAM| Xuất hiện thẻ cấm `<UserObject>` | Loại bỏ thẻ rác, chuyển về `<mxCell>` native |
| `E-DGM-FONT-METRICS`  | DIAGRAM| Thiếu font file, đo text width không chính xác | Kích hoạt fallback Pillow font metrics chuẩn |
| `E-DGM-ROUTING-PIERCE`| DIAGRAM| Tuyến dây đâm xuyên qua thân linh kiện | Nắn lại hành lang Waterfall ($x \ge 80\text{px}$) |
| `W-DEV-*`             | CHUNG  | Độ lệch giao diện có chủ đích so với mẫu gốc | Bắt buộc dừng lại, hỏi người dùng qua `/grill-me` |
| `W-LAYOUT-*`          | CHUNG  | Cảnh báo bố cục ước lượng (chiều cao, ngắt trang)| Kiểm tra trực quan và điều chỉnh nếu cần |

### Cây Quyết Định Xử Lý Chẩn Đoán (Master Triage Decision Tree)

```
                              [Nhận Báo Cáo Diagnostics]
                                           │
                 ┌─────────────────────────┴─────────────────────────┐
                 ▼                                                   ▼
          [Có Khối ERRORS]                                    [Chỉ Có WARNINGS]
                 │                                                   │
   ┌─────────────┼──────────────────┐                 ┌──────────────┼──────────────────┐
   ▼             ▼                  ▼                 ▼              ▼                  ▼
[Hỏng Template/ [Vi phạm Bất biến [Sai Cấu Trúc     [Lệch Mẫu        [Rủi Ro Mất       [Bố Cục Ước
 Thư Viện]       Kỹ Thuật]         JSON Spec]        Template]        Thành Phần]       Lượng/Style]
E-PKG / E-TPL   E-LOCK / E-SHIFT   E-*-SPEC          W-DEV-*          W-PKG-UNSUPPORTED W-LAYOUT / W-STYLE
E-DGM-XML-CORRUPT E-CACHE / E-ROUTING               (Cần UX Mới)     (Slicer/3D/Macro) (Tự co giãn)
   │             │                  │                 │              │                  │
   ▼             ▼                  ▼                 ▼              ▼                  ▼
Dừng phát hành, Dừng phát hành,    AI tự sửa JSON    Dừng lại, hỏi   Bắt buộc hỏi user:  Chấp nhận kèm
báo lỗi ra      phân tích          Spec theo path,   user qua        chấp nhận mất hay  nhãn 'estimated'
màn hình        evidence chi tiết  thử lại (max 2)   /grill-me       đổi file mẫu khác   hoặc tinh chỉnh
```

### Nguyên Tắc Chặn Vòng Lặp Vô Tận (Anti-Infinite Loop)
- **Giới hạn số vòng gọi lại**: Tối đa **2 lần** đối với các lỗi `fixable_by="ai"` (lỗi schema spec, điều chỉnh tọa độ).
- **Quy tắc dừng ngay (Fail-Fast)**: Nếu sau 1 lần sửa mà số lượng lỗi không giảm hoặc sinh thêm lỗi mới $\rightarrow$ **DỪNG LẠI NGAY LẬP TỨC**, in toàn bộ evidence ra màn hình và chờ người dùng hướng dẫn.
- **Không tự ý quyết định thay con người**: Các lỗi `fixable_by="human"` (lệch template, ghi vào vùng khóa, mất thành phần) TUYỆT ĐỐI không được tự ý bypass.

---

## 6. Workflows Tích Hợp Liên Mô-Đun (Cross-Module Integration)

### WF-CROSS-01: Xuất Bản Báo Cáo Kèm Số Liệu Bảng Tính (Analytics to Document)
Quy trình liên kết giữa việc xử lý dữ liệu lớn trên Excel và trình bày báo cáo executive trên Word.

```
[Dữ Liệu Thô / Log Hệ Thống]
       │
       ▼
1. Module XLSX: Thực thi WF-XLSX-02 (Mutate Template)
       │ ──► Mở rộng bảng dữ liệu 5.000 dòng
       │ ──► Recalc Backend tính toán các chỉ số KPI, tỷ lệ thành công, tỷ lệ lỗi
       │ ──► Cache Writer tiêm số liệu, bảo toàn công thức sống
       │ ──► Xuất bản: file_ref_xlsx
       ▼
2. Module XLSX: Gọi xlsx.inspect(file_ref_xlsx)
       │ ──► AI trích xuất bảng tóm tắt KPI tổng hợp từ sheet Statistics
       ▼
3. Module DOCX: Thực thi WF-DOCX-03 (Build from DocSpec)
       │ ──► Tạo báo cáo giải pháp/nghiệm thu
       │ ──► Bơm bảng KPI vừa trích xuất vào khối table_block của Word
       │ ──► Áp dụng cantSplit, tblHeader, Tag Order Registry
       │ ──► Xuất bản: file_ref_docx
       ▼
4. Bàn giao bộ đôi sản phẩm hoàn chỉnh:
       ├─► Báo cáo chính: file_ref_docx (Word .docx)
       └─► Bảng dữ liệu gốc: file_ref_xlsx (Excel .xlsx với công thức sống 100%)
```

### WF-CROSS-02: Nhúng Sơ Đồ Kiến Trúc Vào Tài Liệu & Bảng Tính (Visual Diagram to Document)
Quy trình liên kết giữa việc dựng sơ đồ trực quan và nhúng tự động vào tài liệu báo cáo kỹ thuật.

```
[Yêu cầu Vẽ Sơ đồ Thiết kế Hệ thống]
       │
       ▼
1. Module DIAGRAM: Thực thi WF-DIAG-01 (Spec-Driven Diagram)
       │ ──► Sinh file kiến trúc .drawio chuẩn native
       │ ──► Chạy diagram.render_raster(file_ref_drawio, format="png") -> png_ref
       │ ──► Kiểm định thị giác qua diagram.inspect_visual đạt 100% CLEAN
       ▼
2. Tích hợp Đích Đến:
       ├─► ĐÍCH ĐẾN LÀ BÁO CÁO WORD (Module DOCX):
       │     - AI lập DocSpec chứa khối image_block trỏ tới png_ref
       │     - docx.build_from_spec tự động co giãn ảnh $\le 15.92\text{ cm}$ (khóa tỉ lệ lề in)
       │     - Xuất bản tài liệu Word có hình minh họa sắc nét
       │
       └─► ĐÍCH ĐẾN LÀ BẢNG TÍNH EXCEL (Module XLSX):
             - AI lập MutationSpec chèn hình ảnh minh họa vào sheet Cover/Architecture
             - xlsx.mutate neo hình ảnh chuẩn xác theo tọa độ hai ô (Two-Cell Anchor)
             - Xuất bản bảng tính có sơ đồ hệ thống tích hợp
```

### WF-CROSS-03: Quy Chuẩn Bảo Mật, Sandbox & Lưu Trữ Thống Nhất
Mọi luồng tác nghiệp trong cả 3 module đều tuân thủ các chuẩn hạ tầng tại `doctools/infra/`:
1. **Traceability**: Mọi lệnh gọi đều mang một `request_id` duy nhất xuyên suốt giữa các module để phục vụ Audit Log.
2. **File Store & TTL**: Mọi file tạm được quản lý qua `file_store.py` với thời gian hết hạn (`expires_at`), cô lập theo tenant, tự động dọn dẹp file khóa rác (`.~lock.*`, `~$*`).
3. **Sandbox Isolation**:
   - Jinja render (DOCX) chạy trong `jinja_sandbox.py` với `autoescape=True` và bộ lọc an toàn.
   - LibreOffice (XLSX) chạy trong `libreoffice_sandbox.py` với tiến trình headless riêng biệt.
   - Draw.io render (DIAGRAM) chạy trong `node_sidecar.py` và `browser_pool.py`.
   - Toàn bộ đều ngắt kết nối mạng, giới hạn RAM $\le 2\text{GB}$ và timeout tối đa 60 giây.

---

## 7. Quy Chuẩn Git Tracking & Commit Protocol Cho Solo Dev + AI Agent

Để đảm bảo khả năng tracking chính xác 100%, không mất dấu vết ngữ cảnh và bảo vệ nhánh `main` luôn tinh gọn:

### 7.1. Chiến Lược Phân Nhánh
1. **Nhánh `main` (Production Sạch)**: Chỉ lưu trữ code chuẩn, không chứa tài sản demo nặng hay file log tạm.
2. **Nhánh `archive/legacy-v1` (Bảo Tàng Lịch Sử)**: Tạo tại mốc chốt Phase 0.1 để đẩy toàn bộ engine cũ lên GitHub lưu trữ kinh nghiệm xương máu.
3. **Nhánh Phase (`feat/phase-X-...`)**: Mọi công việc từng Phase chạy trên nhánh riêng (`feat/phase-0-foundation`, `feat/phase-1-docx`...).

### 7.2. Điểm Dừng Kích Hoạt Commit (Verifiable Sub-Step Gate)
- **Tiêu chí**: Khi Agent hoàn thành 1 module con và chạy test pass 100% $\rightarrow$ Agent dừng lại, in bằng chứng pass test, đề xuất commit message.
- **Quyền commit**: Người dùng duyệt $\rightarrow$ Mới thực thi lệnh `git commit`. Agent tuyệt đối không commit ngầm.

### 7.3. Định Dạng Commit Message
Tuân thủ Conventional Commits kèm Scope và Mã Gate/TC:
```
<type>(<scope>): <mô tả> [<Mã Gate/TC>]
```
*Ví dụ*: `feat(infra): implement FileStore with TTL cleanup and quarantine isolation [UG-01, DGM-TC-01]`

### 7.4. Cơ Chế Xử Lý Lỗi (Keep Dirty State & Fail-Fast)
- Khi vi phạm luật Max 1 Fix Attempt: Giữ nguyên dirty state, in `git diff` tóm tắt, tuyệt đối không tự ý rollback ngầm, chờ Người dùng chỉ đạo.
