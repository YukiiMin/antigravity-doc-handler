# DOCX Core Module — Local Context

> **Scope**: `doctools/core/docx/` (OpenXML schema, tag order, package IO, template parsing & normalization).
> **Spec**: `docs/update-spec/docx-engine-mcp-plan.md` | **Skill**: `doc-handler`

---

## Subsystem Structure
- `schema/`: `tag_order_registry.py` (strict ECMA-376 child ordering), `schema_helper.py` (OpenXML guardrails, Last Paragraph Rule).
- `package_io/`: `package_reader.py` (zip bomb protection, XXE safe), `package_writer.py` (atomic write).
- `template/`: `template_linter.py` (read-only AST linter), `jinja_normalizer.py` (Section 4.14: Jinja run consolidation, `proofErr` cleanup).

## Local Invariants
1. **The Last Paragraph Rule (`ERR_DOCX_001`)**: Every table cell (`<w:tc>`) MUST terminate with at least one paragraph (`<w:p>`).
2. **Deterministic Schema Order (`DOCX-D-06`)**: All XML elements MUST be inserted via `TagOrderRegistry`; arbitrary `append()` is strictly prohibited.
3. **Non-Destructive Template Normalization (`DOCX-D-09`)**: Normalizer outputs a new package without overwriting the original file; preserves `w:noProof`, `w:lang`, and `rsid*` attributes.
