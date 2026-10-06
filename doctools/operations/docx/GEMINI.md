# DOCX Operations Module — Local Context

> **Scope**: `doctools/operations/docx/` (MCP tool handlers, request triage, FileStore & Audit integration).
> **Registry**: `doctools/registry.py` | **Skill**: `docx-handler`

---

## Cấu Trúc Nghiệp Vụ
- `template_ops.py`: Triển khai `docx.lint_template` và `docx.normalize_template`.
- `build_ops.py` (Phase 1.1.3/1.1.4): `docx.build_document` (Path A Jinja / Path B DocSpec).
- `inspect_ops.py` (Phase 1.1.5): `docx.inspect_structure`, `docx.validate`.

## Invariants Cục Bộ
1. **ResultEnvelope & Diagnostics**: 100% MCP handlers trả về `ResultEnvelope`. Không trả raw exception.
2. **Handle thay vì Byte (`DOCX-D-10`)**: Giao tiếp qua `FileRef` mờ (`resource://docx/files/...`), lưu trữ qua `FileStore`.
3. **Audit Tracing**: Mọi hành động được tự động ghi vết qua `AuditLogger` và `request_id`.
