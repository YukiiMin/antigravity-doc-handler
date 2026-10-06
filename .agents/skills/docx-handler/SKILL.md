---
name: doc-handler
description: Master operations guide, mental model, and decision tree for DOCX Engine and universal document processing (Word .docx, Markdown, PDF conversion). Built on Foundation Plan v1.1 and strict OpenXML OOXML invariants.
---

# Antigravity Skill: DOCX Engine & Universal Document Handler (`doc-handler`)

Use this skill whenever you need to create, modify, inspect, repair, or convert Word documents (`.docx`), Markdown documentation (`.md`), and format-accurate PDF documents.

> **Lưu ý**: Đối với các tác vụ thiết kế và render sơ đồ kỹ thuật (Draw.io, ERD, Sequence, Architecture), kích hoạt skill chuyên trách: `mxgraph-diagram-engineering`.
> **Quy trình Phân phối & Git**: Tuân thủ quy chuẩn Micro-Commit Cadence (X.Y.Z) và Git Workflow tại skill `doctools-delivery`.

---

## 🧠 Core Philosophy & Mental Model

### 1. Engine Tất Định, AI Quyết Định (Deterministic Engine, Decisive AI)
- Engine là **MCP Server tất định**: tuyệt đối không tự ý gọi AI để tóm tắt/cắt gọn nội dung, không chứa prompt bên trong lõi, không đo layout bằng render trong core.
- AI (Client) chịu trách nhiệm: quyết định cấu trúc nội dung, điều phối luồng gọi công cụ, xử lý các cảnh báo chẩn đoán (`issues`) và lựa chọn chiến lược layout.

### 2. Hai Đường Dựng Tài Liệu (Dual-Path Builder Architecture)
- **Đường A — Template Path (`docxtpl` + Jinja2 + Manifest)**:
  - Dành cho tài liệu có mẫu chuẩn (hợp đồng, hóa đơn, báo cáo định kỳ).
  - Bắt buộc kiểm tra `normalize_template` trước khi nạp dữ liệu để triệt tiêu lỗi **Run Splitting** do Word băm nhỏ thẻ `{{ ... }}`.
  - Manifest JSON là nguồn sự thật duy nhất (Single Source of Truth) quy định danh mục biến, kiểu dữ liệu và trường bất biến.
- **Đường B — DocSpec JSON Path (python-docx + Schema Helper)**:
  - Dành cho tài liệu tự do phát sinh từ đầu (tài liệu giải pháp, báo cáo phân tích, đặc tả kỹ thuật).
  - AI sinh bản đặc tả khai báo `DocSpec` JSON; Engine tự động biên dịch thành file DOCX có phân tầng Header, Block, Table, Callout.

### 3. Phòng Ngừa Bằng Rào Chắn OOXML (Preventive OOXML Guards)
Thay vì render ra PDF rồi đo pixel phỏng đoán, engine cưỡng chế hành vi ngắt trang/dòng trực tiếp qua thuộc tính OOXML native:
- `<w:cantSplit/>`: Ngăn chặn hàng trong bảng bị xé đôi qua 2 trang giấy.
- `<w:tblHeader/>`: Tự động lặp lại hàng tiêu đề của bảng ở đầu mọi trang tiếp theo.
- `<w:keepNext/>`: Khóa heading luôn đi liền với đoạn văn bản hoặc bảng tiếp theo (chống tiêu đề mồ côi cuối trang).
- `<w:vAlign w:val="center"/>`: Căn giữa văn bản theo chiều dọc cho 100% ô bảng.
- **Tag Order Registry**: Mọi thao tác ghi XML bắt buộc đi qua Schema Helper để đảm bảo thứ tự thẻ con nghiêm ngặt trong `pPr`, `rPr`, `tblPr`, `tcPr` theo chuẩn ECMA-376.

### 4. Kiến Trúc Phân Tách Giao Diện (`.md` + `.style.yaml`)
- **Data Layer (`.md`)**: Markdown GFM thuần khiết, sạch sẽ, không chứa HTML `<font>` hay inline styles, tối ưu cho LLM Context và Git Version Control.
- **Style Layer (`.style.yaml`)**: Lưu trữ design tokens: lề trang, bảng màu heading (`#C00000`), shading bảng (`#FFE8E0`), kiểu font, khoảng cách dòng. Có thể thay đổi giao diện toàn bộ tài liệu bằng cách đổi file style.

---

## 🌲 Decision Tree & Use Cases

```
                                  [Document Operation]
                                            │
          ┌─────────────────────────────────┼─────────────────────────────────┐
          ▼                                 ▼                                 ▼
   [Sinh Mới DOCX]                  [Sửa / Ghép / Vá]                 [Chuyển Đổi / Xuất Bản]
          │                                 │                                 │
   ┌──────┴──────┐                   ┌──────┴──────┐                   ┌──────┴──────┐
   ▼             ▼                   ▼             ▼                   ▼             ▼
Template Path  DocSpec JSON        Patch / Repair   Merge Files      PDF -> DOCX    DOCX -> MD
(Jinja+Manifest) (From Scratch)     (Inspect & Fix)  (Conflict Policy) (Fidelity)    (+Style YAML)
```

### Case 1: Sinh tài liệu từ Template có sẵn (Template-Driven)
1. Kiểm tra template qua `docx.lint_template(template_ref)`.
2. Nếu phát hiện run bị băm nhỏ $\rightarrow$ chạy `docx.normalize_template(template_ref)` để sinh template sạch.
3. Chuẩn bị `context_data` JSON khớp với schema trong manifest (đọc qua `docx.get_template_manifest`).
4. Gọi `docx.render_template(template_id="...", context_data={...})`.

### Case 2: Tạo tài liệu tự do từ đầu (DocSpec JSON)
1. AI lập dàn ý và phát sinh cấu trúc `DocSpec` JSON (sections, paragraphs, tables, callouts).
2. Gọi `docx.build_from_spec(docspec={...}, layout_policy={...})`.
3. Nhận `FileRef` kết quả kèm báo cáo `diagnostics`.

### Case 3: Kiểm tra, soi cấu trúc và vá lỗi (Inspect & Patch)
1. Gọi `docx.inspect_structure(file_ref)` để lấy cây cấu trúc tóm tắt kèm các `anchor` định danh.
2. Gọi `docx.validate(file_ref)` để kiểm tra các vi phạm OpenXML (`ERR_DOCX_001..010`).
3. Gửi mảng thao tác khai báo qua `docx.patch(file_ref, operations=[...])` để vá lỗi có chủ đích.

### Case 4: Ghép nhiều tài liệu (Document Merge)
1. Chuẩn bị file gốc `base_ref` và danh sách phụ lục `parts[]`.
2. Xác định rõ `style_conflict_policy`:
   - `master_wins` (mặc định): File chính quyết định style của toàn bộ tài liệu.
   - `isolate_styles`: Tự đổi tên style của phụ lục để không bị biến dạng giao diện.
3. Gọi `docx.merge(base_ref, parts, style_conflict_policy="master_wins")`.

### Case 5: Bóc tách Markdown hoặc Chuyển đổi PDF
- Bóc tách: DOCX $\rightarrow$ `[name].md` (nội dung) + `[name].style.yaml` (tokens).
- Chuyển đổi PDF $\rightarrow$ DOCX: Bảo toàn bảng biểu OpenXML (`cantSplit`, `tblHeader`), bullet hierarchies và dot-leader tab stops cho mục lục.

---

## 📋 Bảng Mã Lỗi Chẩn Đoán & Hướng Xử Lý

Mọi kết quả trả về từ Engine đều bọc trong phong bì chuẩn: `{ success, file_ref, diagnostics: { errors, warnings, info } }`.

| Mã Lỗi | Nguyên Nhân | Hướng Tự Sửa Của AI (`suggested_action`) |
|---|---|---|
| `E-DOCX-TAG-ORDER` | Thẻ con XML đặt sai thứ tự trong `pPr`/`tblPr` | Sử dụng Schema Helper để chèn phần tử thay vì tự ghép chuỗi XML |
| `E-DOCX-LAST-P` | Ô bảng `<w:tc>` không kết thúc bằng `<w:p>` | Tự động thêm `<w:p/>` rỗng vào cuối ô trước khi đóng thẻ |
| `E-DOCX-RUN-SPLIT` | Thẻ Jinja bị băm nát giữa các `<w:r>` | Chạy `normalize_template` trước khi render dữ liệu |
| `E-DOCX-IMMUTABLE` | Nội dung điều khoản pháp lý/số liệu bị lệch hash | Khôi phục nguyên trạng đoạn văn bản từ manifest, không được tóm tắt |
| `E-DOCX-OVERFLOW` | Chiều rộng ảnh hoặc bảng vượt quá lề in | Giảm kích thước ảnh về $\le 15.92\text{ cm}$ (đối với A4 lề 2.54cm) |
| `W-FIELD-UPDATE` | Tài liệu có mục lục TOC hoặc số trang động | Thông báo cho người dùng biết Word sẽ tự cập nhật khi mở (`update_on_open`) |
