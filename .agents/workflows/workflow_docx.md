# Workflow: Module DOCX (Word Document Engine)

> **Mô-đun**: DOCX Engine (`docx.*`)  
> **Căn cứ**: Docx Foundation Plan v1.1, [rule_docx_engine_standards.md](../rules/rule_docx_engine_standards.md).  
> **Phạm vi**: 5 quy trình tác nghiệp chuẩn từ template, đặc tả JSON, vá lỗi và trộn tài liệu.

---

## 1. Danh Mục Workflows Cho Module DOCX

```
                                  [Tác Vụ DOCX]
                                        │
      ┌──────────────────┬──────────────┴──────────────┬──────────────────┐
      ▼                  ▼                             ▼                  ▼
[WF-DOCX-01: Nhập Mẫu] [WF-DOCX-02: Template Path]   [WF-DOCX-03: Spec] [WF-DOCX-04/05]
lint & normalize       manifest & sandboxed render   DocSpec builder    patch & merge
```

---

## 2. Chi Tiết Từng Quy Trình Tác Nghiệp

### WF-DOCX-01: Nhập Kho & Chuẩn Hóa Template (Template Ingestion)
Quy trình đưa một template Word mẫu của doanh nghiệp vào kho lưu trữ có kiểm soát.

1. **Kiểm tra cú pháp**: Gọi `docx.lint_template(template_ref)` để quét thẻ Jinja vỡ, unclosed tags, và run splitting.
2. **Gộp run**: Gọi `docx.normalize_template(template_ref)` để gộp các run chứa thẻ `{{ ... }}` bị Word băm nhỏ (giữ nguyên noProof, lang, xml:space).
3. **Nạp manifest**: Soạn thảo manifest YAML (biến, kiểu dữ liệu, trường bất biến).
4. **Đăng ký kho**: Gọi `docx.register_template(template_ref, manifest)` lưu phiên bản và hash sha256.

---

### WF-DOCX-02: Dựng Tài Liệu Từ Template (Path A: Template-Driven Rendering)
Quy trình sinh tài liệu chuẩn từ template và tập dữ liệu nghiệp vụ (hợp đồng, báo cáo định kỳ).

1. **Khảo sát Schema**: Đọc manifest bằng `docx.get_template_manifest(template_id)`.
2. **Xác thực dữ liệu**: Kiểm tra `context_data` theo Pydantic schema; kiểm tra hash các trường bất biến (`immutability.py`); chuẩn hóa Unicode NFC và loại bỏ ký tự điều khiển XML 1.0.
3. **Render cách ly**: Chạy render qua `docxtpl` trong sandbox (`SandboxedEnvironment`, `autoescape=True`, allow-list tags/filters).
4. **Cưỡng chế Semantic Guards**:
   - Khóa `<w:cantSplit/>` cho mọi hàng trong bảng.
   - Bổ sung `<w:tblHeader/>` cho hàng tiêu đề của bảng nhiều trang.
   - Đặt `<w:keepNext/>` cho các tiêu đề heading (chống mồ côi cuối trang).
   - Đặt `<w:vAlign w:val="center"/>` căn giữa ô bảng.
5. **Kiểm định OOXML Gates**: Kiểm tra XSD ECMA-376, Tag Order Registry, và giới hạn ảnh $\le 15.92\text{ cm}$.
6. **Bàn giao**: Cấp `file_ref` kết quả kèm báo cáo `diagnostics`.

---

### WF-DOCX-03: Dựng Tài Liệu Tự Do Từ Đặc Tả (Path B: DocSpec Builder)
Quy trình tạo tài liệu kỹ thuật, báo cáo giải pháp mới từ đầu mà không cần template có sẵn.

1. **Lập Đặc tả DocSpec JSON**: AI thiết kế dàn ý gồm các khối: `heading`, `paragraph`, `list_block`, `table_block`, `image_block`, `callout`.
2. **Biên dịch Khối**: `docx.build_from_spec` duyệt cây DocSpec và gọi các builder tương ứng trong `blocks/`.
3. **Cưỡng chế Schema Helper**: Mọi thao tác ghi XML đi qua `oxml_factory` và `schema_helper` để chèn đúng thứ tự thẻ con theo Tag Order Registry.
4. **Áp dụng Base Theme**: Sử dụng named styles từ `base_templates/tpl_report_vi.docx`.
5. **Kiểm định & Xuất Bản**: Vượt qua 6 OOXML Gates và trả về `file_ref`.

---

### WF-DOCX-04: Soi Cấu Trúc, Kiểm Định & Vá Lỗi (Inspect & Patch)
Quy trình kiểm tra tài liệu có sẵn, phát hiện lỗi cấu trúc và sửa chữa từng phần.

1. **Soi cấu trúc**: Gọi `docx.inspect_structure(file_ref)` nhận cây DOM tóm tắt kèm các anchor ổn định.
2. **Kiểm định**: Gọi `docx.validate(file_ref)` nhận danh sách vi phạm OpenXML (`ERR_DOCX_001..005`).
3. **Vá lỗi nguyên tử**: Gửi danh sách thao tác (`replace_text`, `insert_paragraph`, `update_cell`) qua `docx.patch(file_ref, operations=[...])` trên bản sao.

---

### WF-DOCX-05: Ghép Nối Tài Liệu (Document Merge)
Quy trình nối nhiều tài liệu con (báo cáo chính + phụ lục).

1. Chuẩn bị file gốc `base_ref` và mảng phụ lục `parts[]`.
2. Chọn `style_conflict_policy`: `master_wins` (mặc định) hoặc `isolate_styles` (giữ giao diện phụ lục).
3. Ghép part qua `docx.merge`, kiểm tra tính liên tục của numbering và header/footer giữa các section.
