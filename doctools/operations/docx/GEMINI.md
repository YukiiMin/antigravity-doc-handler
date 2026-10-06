# DOCX Operations Module — Local Context

> **Scope**: `doctools/operations/docx/` (MCP tool handlers, request triage, FileStore & Audit integration).
> **Registry**: `doctools/registry.py` | **Skill**: `doc-handler`

---

## Operations Structure
- `template_ops.py`: Implements `docx.lint_template` and `docx.normalize_template`.
- `build_ops.py` (Phase 1.1.3 / 1.1.4): `docx.build_document` (Path A Jinja / Path B DocSpec).
- `inspect_ops.py` (Phase 1.1.5): `docx.inspect_structure`, `docx.validate`.

## Local Invariants
1. **ResultEnvelope & Diagnostics**: 100% of MCP handlers return a structured `ResultEnvelope`. Never leak raw unhandled exceptions.
2. **Opaque Handles Over Raw Bytes (`DOCX-D-10`)**: Exchange data via opaque `FileRef` handles (`resource://docx/files/...`), persisted via `FileStore`.
3. **Audit Tracing**: Every operation is automatically traced with `request_id` via `AuditLogger`.
