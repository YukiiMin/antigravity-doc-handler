---
name: excel-handler
description: Master operations guide, mental model, and decision tree for XLSX Engine and universal spreadsheet processing (Excel .xlsx, .xls). Built on Foundation Plan v1.1, Tokenizer Shift Manager, lxml Cache Writer, two-tier UG/PG validation, and strict template preservation invariants.
---

# Antigravity Skill: XLSX Engine & Universal Spreadsheet Handler (`excel-handler`)

Sử dụng skill này bất cứ khi nào bạn cần tạo, đọc, sửa đổi, kiểm tra, kiểm định, tính toán hoặc đối chiếu bảng tính Excel (`.xlsx`, `.xls`) từ template doanh nghiệp hoặc phát sinh từ đặc tả `XlsxSpec`.

> **Quy chuẩn bắt buộc**: Xem [rule_xlsx_engine_standards.md](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/tool/pdf_to_docx_converter/.agents/rules/rule_xlsx_engine_standards.md) để tuân thủ các bất biến E1–E14, ERR_XLSX_001..007, Shift invariants và giao thức Grill-Before-Deviate.

---

## 🧠 Core Philosophy & Mental Model

### 1. Engine Tất Định, AI Quyết Định (Deterministic Engine, Decisive AI)
- **Engine là MCP Server tất định**: Tuyệt đối không tự ý gọi AI để tóm tắt số liệu, không chứa prompt ẩn, không tự động co giãn kiểu dáng nếu không có khai báo trong spec hoặc manifest.
- **AI (Client) đóng vai trò bộ não điều phối**: Đọc hiểu yêu cầu người dùng, khảo sát cấu trúc workbook qua `inspect_xlsx`, phát sinh `MutationSpec` JSON chuẩn xác, phân loại chẩn đoán (`diagnostics`) và xin ý kiến con người khi có cảnh báo lệch template (`W-DEV-*`).

### 2. Template Là Chân Lý & Bất Biến File Gốc (Template is Ground Truth)
- **Không hardcode kiểu dáng**: Mọi token định dạng (font, fill rgb/theme/indexed, border, alignment, `wrap_text`, number format `@`) phải được clone trực tiếp từ **Prototype Row** hoặc trích xuất từ **Reference Sheet** (`Example`, `Template`, `Sample`, `Pattern`).
- **Original Immutability (NFR-08)**: Mọi thao tác sửa đổi (`mutate_xlsx`, `recalc_xlsx`) đều thực thi trên bản sao tạm thời. File gốc được bảo toàn 100% hash `sha256`. File giao trả về qua `FileRef` URI mờ.

### 3. Hai Đường Dựng Bảng Tính (Dual-Path Builder Architecture)
- **Đường A — Mutate Template (Path A: openpyxl + Atomic Clone & Shift)**:
  - Dành cho tài liệu có template mẫu (báo cáo kiểm thử Report5, bảng chấm công, báo cáo tài chính).
  - Nhận `MutationSpec` JSON khai báo: `cell_updates`, `table_expansions` (kèm anchor, `prototype_row`, `id_columns`), `freeze_panes`, `calc_policy`.
- **Đường B — XlsxSpec Path (Path B: XlsxWriter + Design Tokens)**:
  - Dành cho workbook phát sinh mới từ đầu khi không có template.
  - Sử dụng Design Tokens chuẩn (`Theme.PRIMARY`, `Border.accounting_double`) và conditional formatting dạng công thức (ví dụ `=MOD(ROW(),2)=0` cho zebra).

### 4. Shift Manager Duy Nhất Qua AST Tokenizer (D-03, D-04, FR-07)
- **Cấm tiệt Regex toàn chuỗi (P-01, P-02)**: Dùng `openpyxl.formula.Tokenizer` để phân rã token. **Chỉ dịch toán hạng ô/dải trỏ vào sheet đích**. Bảo toàn 100% tên hàm (`LOG10`, `DAYS360`), chuỗi ký tự (`"TC001"`), và tên định danh (`FY2024`).
- **Dịch đồng thời trong 1 chu trình**: Công thức toàn workbook, merged cells, `sqref` của CF/DV, `ref` của bảng Excel (ListObject) và AutoFilter, Defined Names, Print Area, Chart series & anchor, chiều cao dòng.
- **Range Policy**: `table_aware` mở rộng dải tổng hợp khi chèn tại biên; `excel_native` giữ nguyên dải khi chèn thô.
- **Chặn tham chiếu mồ côi**: Khi xóa dòng/cột làm mất ô tham chiếu $\rightarrow$ Báo `E-SHIFT-ORPHAN` và dừng, tuyệt đối không âm thầm sinh `#REF!`.

### 5. Recalc Backend & Cache Writer (`write_cached` bằng `lxml`, EV-13)
- **Giải quyết lỗi mù số liệu (P-05)**: openpyxl lưu file không có thẻ `<v>`, khiến pandas, openpyxl `data_only=True`, Explorer Preview thấy ô trống.
- **Quy trình chuẩn**:
  1. Gửi bản sao sang Recalc Backend (LibreOffice headless trong sandbox) để tính lại và quét lỗi (`#REF!`, `#DIV/0!`).
  2. Dùng `lxml` can thiệp vào `xl/worksheets/sheetN.xml` của file giao: tiêm thẻ `<v>` và thuộc tính `t` (`n`/`str`/`b`/`e`) cho các node `<c>` có `<f>`.
  3. Bảo toàn 100% thẻ `<f>` (công thức còn sống khi mở bằng Excel thật).
  4. Tự kiểm tra lại bằng Gate `UG-13`: đọc lại bằng `data_only=True` phải khớp chính xác `values_summary`.

### 6. Kiểm Định Hai Tầng & Structural Diff (D-07, D-08)
- **Tầng UG (13 Universal Gates)**: Áp dụng chung cho mọi workbook (hợp lệ package OOXML, inventory parity, toàn vẹn công thức, không lỗi tính toán, clone style prototype row, safe merge, an toàn an ninh, cache nhất quán).
- **Tầng PG (Profile Gates)**: Khai báo theo profile template (ví dụ profile `unit_test_matrix` kế thừa trọn vẹn 12 Quality Gates của Report5).
- **Structural Diff (`xlsx.diff`)**: So sánh Package Inventory trước và sau, phát hiện mất mát thành phần không khai báo (`undeclared`).

---

## 🌲 Decision Tree & Use Cases

```
                                  [Spreadsheet Task]
                                          │
         ┌────────────────────────────────┼────────────────────────────────┐
         ▼                                ▼                                ▼
  [Nhập Kho Template]             [Mutate Template]               [Kiểm Định & Diff]
         │                                │                                │
  ┌──────┴──────┐                  ┌──────┴──────┐                  ┌──────┴──────┐
  ▼             ▼                  ▼             ▼                  ▼             ▼
xlsx.preflight  xlsx.lint_template xlsx.inspect  xlsx.mutate        xlsx.validate  xlsx.diff
(Inventory)     (Anchor/Zones)     (Anchors/Val) (Shift+Style)      (UG + PG)      (Declared?)
         │                                │                                │
         ▼                                ▼                                ▼
 xlsx.register_template            xlsx.recalc (Cache)             xlsx.repair (P1)
 (YAML Manifest)                   -> FileRef Hoàn Chỉnh          (Fix Engine Issues)
```

### Case 1: Nhập kho Template mới (Template Onboarding)
1. Gọi `xlsx.preflight(file_ref)` để kiểm tra Package Inventory và xác định Fidelity Tier (T1/T2/T3).
2. Gọi `xlsx.lint_template(template_ref)` để kiểm tra các anchor, dòng mẫu Prototype Row, vùng khóa và placeholder sót lại.
3. Soạn thảo file manifest YAML (`anchors`, `prototype_rows`, `locked_zones`, `id_columns`, `calc_policy`, `gates_profile`).
4. Gọi `xlsx.register_template(template_ref, manifest)` để lưu phiên bản và hash `sha256`.

### Case 2: Cập nhật dữ liệu vào Template có sẵn (Path A Mutation)
1. Gọi `xlsx.inspect(file_ref)` để lấy snapshot cấu trúc, các anchor hiện có và trạng thái giá trị `values_status`.
2. Lập bản đặc tả `MutationSpec` JSON:
   - Khai báo `table_expansions` với anchor (header text), `prototype_row`, danh sách dữ liệu `rows[]`, `id_columns` (cột mã định danh mang format `@`).
   - Cấu hình `calc_policy: { recalc: "oracle_verify", cache: "write", calc_on_open: "auto" }`.
   - Nếu có cải tiến UX lệch template: Đã xin duyệt qua `/grill-me` và điền mã vào `approved_deviations[]`.
3. Gọi `xlsx.mutate(template_id, mutation_spec)` $\rightarrow$ Engine tự động thực thi Shift Manager, clone kiểu dáng, tính toán và tiêm cache.
4. Đọc kết quả trong phong bì trả về: nhận `file_ref` và kiểm tra mảng `diagnostics`.

### Case 3: Tạo Workbook mới từ đầu (Path B XlsxSpec)
1. AI soạn thảo đặc tả `XlsxSpec` JSON (sheets, tables, columns, rows, cell types).
2. Chỉ định Design Tokens theo tên (`theme: "corporate_blue"`, `border: "thin_grid"`). Tuyệt đối không sinh mã màu hex hay style tùy tiện.
3. Gọi `xlsx.build(xlsx_spec)` $\rightarrow$ Engine biên dịch bằng XlsxWriter, tính toán và xuất file.

### Case 4: Kiểm tra chất lượng và đối chiếu cấu trúc (Validation & QA)
1. Gọi `xlsx.validate(file_ref, profile="unit_test_matrix")` để kiểm tra toàn diện 13 UG Gates và Profile Gates.
2. Gọi `xlsx.diff(file_ref_a, file_ref_b)` để đối chiếu giữa bản gốc và bản sau khi sửa.
3. Nếu phát hiện lỗi `fixable_by="engine"`: Gọi `xlsx.repair(file_ref, issues=[...])` (P1) để sửa chữa tất định.

---

## 💻 Danh Mục 11 Công Cụ MCP XLSX Core

Mọi công cụ đều giao tiếp qua `FileRef` `{ uri, sha256, size, mime, expires_at }` và trả kết quả phong bì chuẩn `{ success, file_ref, diagnostics, guarantees_applied, stats }`.

| Tên Công Cụ | Phân Loại | Đầu Vào Chính | Đầu Ra Chính |
|---|---|---|---|
| `xlsx.preflight` | Chỉ đọc | `file_ref` | `inventory`, `fidelity_tier`, `issues` |
| `xlsx.inspect` | Chỉ đọc | `file_ref`, `sheet?`, `range?` | Cấu trúc cây, ô, công thức, `values_status` |
| `xlsx.lint_template` | Chỉ đọc | `template_ref` | `valid`, `anchors_found`, `issues` |
| `xlsx.register_template` | Quản trị | `template_ref`, `manifest` | `template_id`, `version`, `manifest` |
| `xlsx.list_templates` | Quản trị | — | Danh sách template đã đăng ký |
| `xlsx.get_template_manifest` | Quản trị | `template_id` | Chi tiết manifest YAML của template |
| `xlsx.mutate` | Thực thi | `template_id`/`file_ref`, `mutation_spec` | `file_ref` mới, `diagnostics`, `stats` |
| `xlsx.build` | Thực thi | `xlsx_spec` | `file_ref` mới, `diagnostics` |
| `xlsx.recalc` | Thực thi | `file_ref`, `calc_policy?` | `values_summary`, `errors`, `file_ref` (đã tiêm cache) |
| `xlsx.validate` | Kiểm định | `file_ref`, `profile?` | `issues`, `gates_passed`, `gates_failed` |
| `xlsx.diff` | Kiểm định | `file_ref_a`, `file_ref_b` | Khác biệt `inventory`, `styles` có anchor |

---

## 🛡 Diagnostics Triage & Hướng Xử Lý Lỗi

Khi nhận kết quả từ công cụ, AI thực hiện triage theo cây quyết định nghiêm ngặt:

```
Nhận Diagnostics
  ├─ Có Errors?
  │     ├─ E-PKG-*   (OOXML hỏng)            ──► Dừng, báo người dùng / đổi template
  │     ├─ E-LOCK-*  (Ghi vào vùng khóa)     ──► Dừng ngay, KHÔNG tự ghi đè, hỏi người dùng
  │     ├─ E-SHIFT-* (Lỗi dịch/mồ côi)       ──► Dừng, không phát hành file, phân tích evidence
  │     ├─ E-CACHE-* (Cache sai kiểu/lỗi XML)──► Dừng, lỗi lõi engine, báo cáo chi tiết
  │     └─ E-SPEC-*  (Spec sai schema)       ──► AI tự sửa spec theo JSON path và gọi lại (tối đa 2 lần)
  │
  └─ Có Warnings?
        ├─ W-PKG-UNSUPPORTED-* (Shape/Slicer)──► BẮT BUỘC hỏi người dùng: chấp nhận mất hay đổi mẫu
        ├─ W-DEV-* (Lệch template)           ──► Dừng, trình bày trước/sau qua /grill-me để xin duyệt
        ├─ W-CALC-* (Hàm biến động/chưa tính)──► Bàn giao file kèm ghi chú nguồn số liệu (origin)
        └─ W-LAYOUT / W-STYLE (estimated)    ──► Điều chỉnh lại spec hoặc chấp nhận nếu hợp lý
```

### Bảng Mã Lỗi Tiêu Biểu & Hành Động Khắc Phục (`suggested_action`)

| Mã Lỗi | Ý Nghĩa Kỹ Thuật | Hành Động Tự Động Khắc Phục Của AI |
|---|---|---|
| `E-LOCK-001` | Ghi đè vào ô thuộc `locked_zones` trong manifest | Xóa bỏ cập nhật ô này khỏi `cell_updates`; kiểm tra lại anchor mở rộng bảng |
| `E-SHIFT-002` | Công thức cross-sheet không được dịch sau chèn dòng | Chạy lại Shift Manager với tham số `target_sheet` được chỉ định tường minh |
| `E-SHIFT-ORPHAN` | Xóa dòng/cột làm mất ô tham chiếu công thức | Hủy bỏ thao tác xóa hoặc cập nhật lại công thức tham chiếu trước khi xóa |
| `E-TPL-ANCHOR-AMBIGUOUS` | Tìm thấy >1 ô khớp với từ khóa anchor trong vùng quét | Thu hẹp `scan_rows` hoặc bổ sung thuộc tính `scope: "first_table"` |
| `E-CACHE-TYPE-MISMATCH` | Đọc lại cache qua data_only không khớp kiểu dữ liệu Recalc | Kiểm tra ánh xạ kiểu trong Cache Writer (`n`/`str`/`b`/`e`) |
| `W-DEV-LAYOUT:freeze_panes`| Đề xuất thêm Freeze Panes lệch so với template gốc | Hỏi người dùng qua `/grill-me`. Nếu duyệt, thêm mã vào `approved_deviations` |
| `W-PKG-UNSUPPORTED-SHAPE`| Template chứa Text Box / Shape có nguy cơ mất khi lưu | Báo người dùng xác nhận rủi ro trước khi thực hiện ghi |
| `W-CALC-NO-CACHE` | Hàm phức tạp không được Recalc Backend hỗ trợ tính | Bàn giao file kèm cờ `calc_on_open: "on"` để Excel tự tính khi người dùng mở |
