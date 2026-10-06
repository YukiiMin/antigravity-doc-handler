# Rule: DOCX Engine Standards & OOXML Invariants

> **Module**: DOCX (Word Processing & Decoupled Conversion)
> **Companion Spec**: `docs/update-spec/docx-engine-mcp-plan.md` (Foundation Plan v1.1)
> **Scope**: Bắt buộc áp dụng cho mọi tác vụ tạo, sửa, chuyển đổi, kiểm định và ghép tài liệu Word (.docx).

---

## 1. Triết lý Cốt lõi & Ranh giới Cam kết

1. **Engine tất định, AI quyết định**: Engine là MCP Server tất định, không chứa prompt, không gọi ngược AI, không đo layout bằng render trong core. AI là client chịu trách nhiệm nội dung và điều phối.
2. **Phòng ngừa bằng OOXML Guards thay vì đo đạc**: Áp dụng thuộc tính OOXML native (`keepNext`, `cantSplit`, `tblHeader`) để ép Word tự xử lý ngắt trang chính xác trên máy người dùng.
3. **Đường ghi XML duy nhất (Schema Helper)**: Mọi thao tác ghi/sửa XML bắt buộc đi qua Schema Helper tuân thủ Tag Order Registry. Nghiêm cấm `append()` XML tùy tiện.
4. **Cam kết tường minh**:
   - **Cam kết**: File hợp lệ 100% OOXML schema; không vỡ thẻ Jinja; bảo toàn nguyên vẹn nội dung bất biến; bảng không rách hàng; ảnh không tràn lề.
   - **KHÔNG cam kết**: Số trang cuối cùng trong Word (do font/môi trường render của máy khách quyết định); số trang TOC chỉ đúng sau khi Word update field (engine luôn gắn cảnh báo `W-FIELD-UPDATE-REQUIRED`).

---

## 2. Kiến trúc Hai Đường Dựng (Dual-Path Builder)

Mọi thao tác sinh tài liệu Word phải đi qua 1 trong 2 đường:
- **Đường A — Template Path (docxtpl + Jinja2 + Manifest)**: Dành cho biểu mẫu chuẩn, hợp đồng, báo cáo định kỳ.
  - Template phải đi kèm **Manifest JSON** quy định biến, kiểu dữ liệu, trường bất biến và layout policy.
  - Trước khi render, bắt buộc chạy `normalize_template` để hàn gắn Run Splitting.
- **Đường B — DocSpec JSON Path (python-docx + Schema Helper)**: Dành cho tài liệu tự do sinh từ đầu (báo cáo kỹ thuật, tài liệu giải pháp).
  - AI phát sinh bản đặc tả `DocSpec` JSON có schema nghiêm ngặt.
  - Engine dựng document theo cấu trúc phân cấp: Document $\rightarrow$ Sections $\rightarrow$ Blocks (Paragraph, Table, Callout, List).

---

## 3. Các Bất Biến OOXML Bắt Buộc (Core Invariants)

### 3.1. Tag Order Registry (D-06 — Thứ tự Thẻ Con Nghiêm Ngặt)
Word rất khắt khe về thứ tự thẻ con trong OOXML. Sai thứ tự sẽ dẫn đến lỗi *"Unreadable Content / File Corrupt"*. Mọi XML generator phải tuân thủ thứ tự sinh từ XSD:
- **Trong `w:pPr`**: `pStyle` $\rightarrow$ `keepNext` $\rightarrow$ `keepLines` $\rightarrow$ `pageBreakBefore` $\rightarrow$ `widowControl` $\rightarrow$ `numPr` $\rightarrow$ `suppressLineNumbers` $\rightarrow$ `pBdr` $\rightarrow$ `shd` $\rightarrow$ `tabs` $\rightarrow$ `spacing` $\rightarrow$ `ind` $\rightarrow$ `jc` $\rightarrow$ `outlineLvl` $\rightarrow$ `rPr` $\rightarrow$ `sectPr`.
- **Trong `w:rPr`**: `rStyle` $\rightarrow$ `rFonts` $\rightarrow$ `b` $\rightarrow$ `i` $\rightarrow$ `strike` $\rightarrow$ `color` $\rightarrow$ `spacing` $\rightarrow$ `w` $\rightarrow$ `sz` $\rightarrow$ `highlight` $\rightarrow$ `u` $\rightarrow$ `vertAlign`.
- **Trong `w:tblPr`**: `tblStyle` $\rightarrow$ `tblpPr` $\rightarrow$ `tblOverlap` $\rightarrow$ `tblW` $\rightarrow$ `jc` $\rightarrow$ `tblCellSpacing` $\rightarrow$ `tblInd` $\rightarrow$ `tblBorders` $\rightarrow$ `shd` $\rightarrow$ `tblLayout` $\rightarrow$ `tblCellMar`.
- **Trong `w:tcPr`**: `tcW` $\rightarrow$ `gridSpan` $\rightarrow$ `hMerge` $\rightarrow$ `vMerge` $\rightarrow$ `tcBorders` $\rightarrow$ `shd` $\rightarrow$ `noWrap` $\rightarrow$ `tcMar` $\rightarrow$ `vAlign`.

### 3.2. Hàn Gắn Run Splitting & Token Interpolation (FR-02)
- Khi người dùng chỉnh sửa template trong Word, các thẻ `{{ variable }}` hoặc `{% for %}` bị Word tự động băm nát thành nhiều thẻ `<w:r>` xen kẽ `<w:proofErr>` (lỗi chính tả), `<w:noProof/>` hoặc `<w:rPr>` thừa.
- **Quy tắc**: Phải chuẩn hóa và gom cụm toàn bộ text trong cùng một paragraph, loại bỏ sạch các node trung gian gây nhiễu (`w:proofErr`, `w:lang`) trước khi chuyển giao cho Jinja compiler.

### 3.3. Quy Chuẩn Bảng Biểu Toàn Vẹn (Table Integrity Invariants)
- **`ERR_DOCX_001` (The Last Paragraph Rule)**: Mọi cell trong bảng (`<w:tc>`) BẮT BUỘC phải kết thúc bằng tối thiểu một thẻ `<w:p>`. Nghiêm cấm ô rỗng không có đoạn văn bản.
- **`ERR_DOCX_002` (Run Text Overwrite)**: Tuyệt đối không gán `cell.text = "..."`. Phải can thiệp qua `cell.paragraphs[0].runs` để giữ nguyên font chữ, cỡ chữ và màu sắc của template.
- **`ERR_DOCX_003` (Multi-Page Table Pagination)**:
  - 100% các hàng (`w:trPr`) phải có `<w:cantSplit/>` để chống bị chẻ đôi nội dung giữa 2 trang.
  - Hàng tiêu đề 0 (`w:trPr`) phải có `<w:tblHeader/>` để tự động lặp lại ở đầu mỗi trang tiếp theo.
- **`ERR_DOCX_004` (Căn lề dọc & Màu nền tiêu đề)**:
  - 100% ô bảng (`w:tcPr`) phải có `<w:vAlign w:val="center"/>`.
  - Hàng tiêu đề bảng mặc định đổ màu nền thống nhất (ví dụ: `#FFE8E0` hoặc theo palette template).
- **`ERR_DOCX_005` (Khóa Lề In & Tỷ Lệ Ảnh)**:
  - Mọi hình ảnh chèn vào Word phải khóa tỷ lệ và có kích thước:
    $$\text{Width} \le \text{Page Width} - \text{Left Margin} - \text{Right Margin}$$
  - Với trang A4 chuẩn (lề 2.54cm), chiều rộng tối đa của bảng và ảnh không vượt quá `15.92 cm` (`6.27 inches` / `5730 dxa`).

---

## 4. Bảo Vệ Nội Dung Bất Biến & Trường Động

### 4.1. Bất Biến Nội Dung Pháp Lý & Số Liệu (FR-13)
- Các điều khoản hợp đồng mẫu, định danh pháp lý hoặc số liệu tài chính được đánh dấu trong Manifest với mã băm SHA256.
- Engine kiểm tra hash trước và sau khi build; nếu phát hiện AI tự ý tóm tắt, cắt xén hoặc thay đổi, engine ném lỗi `E-DOCX-IMMUTABLE-VIOLATION` và từ chối xuất file.

### 4.2. Chính Sách Trường Động & Mục Lục (D-08, D-16)
- Engine tự phát hiện sự tồn tại của trường `TOC` hoặc `PAGEREF`.
- Khi tài liệu có TOC: Engine lưu nội dung cached của mục lục, gán thuộc tính `w:updateFields w:val="true"` trên `settings.xml` và luôn phát sinh cảnh báo `W-FIELD-UPDATE-REQUIRED` trong Diagnostics để người dùng/AI biết số trang sẽ được Word đồng bộ khi mở.

### 4.3. Chính Sách Xung Đột Style Khi Ghép File (D-15)
Khi ghép tài liệu phụ lục vào tài liệu chính (`merge_docx`):
- `master_wins` (mặc định): Style của file chính ghi đè style cùng tên của file con.
- `isolate_styles`: Tự động đổi tên style của file con (ví dụ: `Heading 1_part2`) để bảo toàn nguyên vẹn hình thức của phụ lục.

---

## 5. Quy Chuẩn Giao Tiếp & Envelope
- Mọi thao tác tệp vào/ra đều thông qua `FileRef` dạng `{ uri, sha256, size, mime }`.
- Chiều ra của server sử dụng URI mờ `resource://docx-engine/files/{opaque_id}`.
- Kết quả trả về bọc trong phong bì chuẩn: `{ success, file_ref, diagnostics: { errors, warnings, info }, guarantees_applied, stats }`.
