# Master Workflow: Điều Phối Bộ Công Cụ AI-Native (`doctools`)

> **Dự án**: `doctools` / `pdf_to_docx_converter`  
> **Phiên bản**: 2.0 (Master Baseline) — Điều phối 3 mô-đun: **DOCX**, **XLSX**, và **DIAGRAM**.  
> **Đối tượng sử dụng**: AI Agent (Antigravity), CI/CD Automation Runner, và Kỹ sư phần mềm.

---

## 1. Kiến Trúc Điều Phối Tổng Thể (Master Architecture)

Bộ công cụ vận hành theo mô hình **AI-Native Plumbing (5 tầng chuẩn hóa)**:
- **Tầng 5: Client (AI Agent)**: Phân tích yêu cầu, phát sinh JSON Spec (`DocSpec`, `MutationSpec`, `DiagramSpec`), đọc `diagnostics` và xử lý cảnh báo `W-DEV-*`.
- **Tầng 4: Registry & Protocol (MCP Server)**: Định tuyến yêu cầu tất định 100%, bảo đảm cô lập tenant, quản lý namespace: `docx.*`, `xlsx.*`, `diagram.*`.
- **Tầng 3: Engine Logic**: Biên dịch đặc tả, áp dụng rào chắn bảo vệ (OOXML Guards, AST Shift Manager, Cache Writer `lxml`, Topology Planner, Orthogonal Router).
- **Tầng 2: Data & File System**: Quản lý gói file ECMA-376 (ZIP) và pure native mxGraphModel XML.
- **Tầng 1: Infrastructure**: Môi trường an toàn (`FileStore` mờ, `Sandbox` cô lập, Headless Pool, Audit Log).

### Hợp Đồng Giao Tiếp Chuẩn (`FileRef`)
Giao tiếp 100% qua đối tượng `FileRef` mờ `{ uri, sha256, size, mime, expires_at }` và phong bì kết quả `{ success, file_ref, diagnostics, guarantees_applied, stats }`. Tuyệt đối không truyền payload binary lớn qua chat stream.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              ANTIGRAVITY AI (MCP CLIENT)                               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ MCP Tool Calls (JSON Spec + FileRef)
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│                    REGISTRY TẬP TRUNG (doctools/registry.py)                            │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│    MODULE DOCX (Word)    │    MODULE XLSX (Excel)      │    MODULE DIAGRAM (Draw.io)   │
│ (Xem .agents/workflows/  │ (Xem .agents/workflows/     │ (Xem .agents/workflows/       │
│      workflow_docx.md)   │      workflow_xlsx.md)      │      workflow_diagram.md)     │
├──────────────────────────┴─────────────────────────────┴───────────────────────────────┤
│            HẠ TẦNG DÙNG CHUNG (FileStore, Sandbox Runner, Headless Pool, Audit)        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Danh Mục Workflows Chuyên Trách Từng Mô-Đun

Chi tiết từng bước tác nghiệp được tách thành các tài liệu module hóa trong `.agents/workflows/`:
1. **[Quy Trình Module DOCX (Word)](.agents/workflows/workflow_docx.md)**:
   - `WF-DOCX-01`: Nhập kho & Chuẩn hóa Template (`docx.lint_template`, `docx.normalize_template`).
   - `WF-DOCX-02`: Dựng tài liệu từ Template Path A (`docxtpl` + Jinja2 + Semantic Guards).
   - `WF-DOCX-03`: Dựng tài liệu tự do từ DocSpec Path B (`docx.build_from_spec`).
   - `WF-DOCX-04`: Soi cấu trúc, kiểm định & vá lỗi nguyên tử (`docx.inspect_structure`, `docx.patch`).
   - `WF-DOCX-05`: Ghép nối nhiều tài liệu con (`docx.merge`).
2. **[Quy Trình Module XLSX (Spreadsheet)](.agents/workflows/workflow_xlsx.md)**:
   - `WF-XLSX-01`: Khảo sát & Nhập kho Template (`xlsx.preflight`, `xlsx.lint_template`).
   - `WF-XLSX-02`: Đột biến bảng tính in-place Path A (9 bước Shift AST Tokenizer + Cache Writer).
   - `WF-XLSX-03`: Dựng workbook mới từ XlsxSpec Path B (`xlsx.build`).
   - `WF-XLSX-04`: Kiểm định 13 Universal Gates & Structural Diff (`xlsx.validate`, `xlsx.diff`).
   - `WF-XLSX-05`: Đọc cấu trúc & Kiểm soát cache số liệu (`xlsx.inspect`, `xlsx.recalc`).
3. **[Quy Trình Module DIAGRAM (Visual)](.agents/workflows/workflow_diagram.md)**:
   - `WF-DIAG-01`: Dựng sơ đồ kiến trúc & ERD từ JSON Spec (`diagram.plan_layout`, `diagram.build`).
   - `WF-DIAG-02`: Chuyển đổi từ cú pháp text DSL Mermaid/PlantUML/DDL (`diagram.parse`).
   - `WF-DIAG-03`: Kiểm định cổng DG-00..08 & Tự sửa thị giác khép kín (`diagram.inspect_visual`).
   - `WF-DIAG-04`: Đóng gói đa trang độc lập (`diagram.export_pages`).
   - `WF-DIAG-05`: So sánh khác biệt cấu trúc và thị giác (`diagram.diff_layout`).

---

## 3. Master Diagnostics Triage Cho AI

Mọi kết quả trả về từ cả 3 module đều dùng chung cấu trúc `Issue`:
```json
{
  "code": "E-...",
  "severity": "error | warning | info",
  "engine": "docx | xlsx | diagram",
  "location": { "sheet": "...", "cell": "...", "part": "...", "node_id": "...", "edge_id": "..." },
  "message": "Mô tả nguyên nhân kỹ thuật",
  "fixable_by": "engine | ai | human",
  "suggested_action": "Tên hành động khắc phục"
}
```

### Bảng Mã Lỗi Phổ Biến
- **DOCX**: `E-DOCX-SPEC-INVALID` (sai schema), `E-DOCX-SEC-INJECTION` (mã Jinja nguy hiểm), `E-DOCX-OPENXML-TC-P` (thiếu thẻ `<w:p>`).
- **XLSX**: `E-XLSX-SPEC-SCHEMA` (sai spec), `E-XLSX-LOCK-VIOLATION` (ghi vào vùng khóa), `E-XLSX-SHIFT-FORMULA` (lệch dải ô), `E-XLSX-CACHE-MISMATCH` (cache sai).
- **DIAGRAM**: `E-DGM-SPEC-SCHEMA` (sai spec), `E-DGM-TOPOLOGY-PORT` (lệch cổng viền), `E-DGM-XML-USEROBJECT` (thẻ cấm UserObject), `E-DGM-ROUTING-PIERCE` (dây xuyên hộp).
- **Cảnh báo chung**: `W-DEV-*` (lệch template $\rightarrow$ hỏi người dùng qua `/grill-me`), `W-LAYOUT-*` (bố cục ước lượng).

### Cây Quyết Định Xử Lý Chẩn Đoán (Triage Decision Tree)
```
                              [Nhận Báo Cáo Diagnostics]
                                           │
                 ┌─────────────────────────┴─────────────────────────┐
                 ▼                                                   ▼
          [Có Khối ERRORS]                                    [Chỉ Có WARNINGS]
                 │                                                   │
   ┌─────────────┼──────────────────┐                 ┌──────────────┼──────────────────┐
   ▼             ▼                  ▼                 ▼              ▼                  ▼
[Hỏng Mẫu]      [Vi phạm Kỹ thuật] [Sai Schema Spec] [Lệch Mẫu]     [Mất Thành Phần]   [Bố Cục Ước Lượng]
E-PKG / E-TPL   E-LOCK / E-SHIFT   E-*-SPEC          W-DEV-*        W-PKG-UNSUPPORTED  W-LAYOUT / W-STYLE
Dừng phát hành, Dừng phát hành,    AI tự sửa JSON,   Dừng lại, hỏi  Bắt buộc hỏi user: Chấp nhận kèm
báo lỗi         phân tích evidence thử lại (max 2)   qua /grill-me  chấp nhận hay đổi  nhãn 'estimated'
```
*Nguyên tắc Fail-Fast*: Tối đa 2 lần thử sửa cho lỗi `fixable_by="ai"`. Nếu không đạt $\rightarrow$ Dừng lại ngay lập tức và in bằng chứng.

---

## 4. Tích Hợp Liên Mô-Đun (Cross-Module Pipelines)

### WF-CROSS-01: Báo Cáo Phân Tích Kèm Bảng Tính (Analytics to Document)
1. Module XLSX thực thi `WF-XLSX-02` (Mutate Template) $\rightarrow$ tính KPI, tiêm cache $\rightarrow$ xuất `file_ref_xlsx`.
2. Module XLSX gọi `xlsx.inspect` trích xuất bảng tổng hợp số liệu.
3. Module DOCX thực thi `WF-DOCX-03` (Build from DocSpec) $\rightarrow$ bơm bảng KPI vào khối `table_block` của Word.
4. Bàn giao bộ đôi sản phẩm: Báo cáo Word (`.docx`) + Bảng dữ liệu gốc (`.xlsx` công thức sống 100%).

### WF-CROSS-02: Nhúng Sơ Đồ Kiến Trúc Vào Tài Liệu (Visual Diagram to Document)
1. Module DIAGRAM thực thi `WF-DIAG-01` $\rightarrow$ sinh `.drawio` $\rightarrow$ render `png_ref` qua `diagram.render_raster` $\rightarrow$ kiểm tra thị giác sạch 100%.
2. Tích hợp đích:
   - *Báo cáo Word*: Nhúng vào khối `image_block`, tự động co giãn $\le 15.92\text{ cm}$ theo lề in.
   - *Bảng tính Excel*: Nhúng vào sheet Cover theo Two-Cell Anchor.

### WF-CROSS-03: Bảo Mật, Sandbox & Lưu Trữ Thống Nhất
- **Traceability**: Mọi lệnh gọi mang một `request_id` xuyên suốt.
- **FileStore & TTL**: Quản lý file tạm qua `file_store.py` (TTL 24h, cô lập tenant, dọn zombie locks `.~lock.*`).
- **Sandbox Isolation**: Jinja render (DOCX), LibreOffice (XLSX), và Chromium sidecar (DIAGRAM) chạy trong sandbox cách ly, ngắt mạng, RAM $\le 2\text{GB}$, timeout $\le 60\text{s}$.

---

## 5. Quy Chuẩn Git Tracking Cho Solo Dev + AI Agent

- **Mô hình nhánh**: Nhánh `main` sạch 100%; Nhánh `archive/legacy-v1` lưu bảo tồn code cũ lên GitHub sau Phase 0.1; Nhánh phát triển theo Phase (`feat/phase-X-...`).
- **Quy chuẩn mã hóa Micro-Commit**: Mỗi Phase X được phân rã thành các mục lớn theo độ ưu tiên: `X.1` (MVP), `X.2` (P1), `X.3` (P2). Khi triển khai thực tế, Agent chia thành các tiểu bước kiểm chứng được: `X.Y.0`, `X.Y.1`, `X.Y.2`... Mỗi tiểu bước có unit test pass 100% $\rightarrow$ Agent đề xuất commit $\rightarrow$ User duyệt $\rightarrow$ Mới commit.
- **Điểm kích hoạt commit (Verifiable Sub-Step Gate)**: Hoàn thành 1 module con + pass 100% test $\rightarrow$ Agent dừng lại, in bằng chứng pass test, đề xuất commit message $\rightarrow$ Người dùng duyệt $\rightarrow$ Mới commit.
- **Format commit**: `type(scope): description [Gate/TC ref]` (vd: `feat(infra): implement FileStore with TTL cleanup [UG-01, DGM-TC-01]`).
- **Cơ chế phục hồi lỗi**: Keep Dirty State kèm `git diff` rõ ràng khi vi phạm luật Max 1 Fix Attempt.
