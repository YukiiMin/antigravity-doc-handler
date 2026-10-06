# DOCX Core Module — Local Context

> **Scope**: `doctools/core/docx/` (OpenXML schema, tag order, package IO, template parsing & normalizer).
> **Spec**: `docs/update-spec/docx-engine-mcp-plan.md` | **Skill**: `docx-handler`

---

## Cấu Trúc Phân Hệ
- `schema/`: `tag_order_registry.py` (cưỡng chế thứ tự ECMA-376), `schema_helper.py` (rào chắn OpenXML, Last Paragraph Rule).
- `package_io/`: `package_reader.py` (chống zip bomb, XXE safe), `package_writer.py` (atomic write).
- `template/`: `template_linter.py` (read-only AST linter), `jinja_normalizer.py` (Mục 4.14: hàn gắn run Jinja, dọn `proofErr`).

## Invariants Cục Bộ
1. **The Last Paragraph Rule (`ERR_DOCX_001`)**: Mọi ô bảng (`<w:tc>`) luôn kết thúc bằng thẻ `<w:p>`.
2. **Deterministic Schema Order (`DOCX-D-06`)**: Mọi phần tử XML chèn qua `TagOrderRegistry`, không `append()` tùy tiện.
3. **Non-Destructive Template Normalization (`DOCX-D-09`)**: Normalizer xuất bản mới, không ghi đè bản gốc; bảo toàn `w:noProof`, `w:lang`, và `rsid*`.
