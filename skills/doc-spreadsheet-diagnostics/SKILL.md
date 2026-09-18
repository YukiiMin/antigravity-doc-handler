---
name: doc-spreadsheet-diagnostics
description: Comprehensive QA and diagnostic workflow for Word (DOCX), Excel (XLSX), Diagrams, and File Conversions. Run static/semantic inspection and safe non-destructive repairs.
---

# Skill: Enterprise Document & Spreadsheet QA / Diagnostics

This skill provides a standardized workflow and CLI toolchain for inspecting, diagnosing, and repairing office documents (`.docx`, `.xlsx`), diagrams, and conversion artifacts.

> **Related Rules**:
> - [`.agents/rules/rule_enterprise_document_and_spreadsheet_qa.md`](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/.agents/rules/rule_enterprise_document_and_spreadsheet_qa.md)
> - [`.agents/rules/rule_excel_template_preservation_and_ux.md`](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/.agents/rules/rule_excel_template_preservation_and_ux.md)
> - [`tool/pdf_to_docx_converter/TOOLS_INVENTORY.md`](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/tool/pdf_to_docx_converter/TOOLS_INVENTORY.md)

---

## 1. When to Use This Skill

Activate this skill whenever:
- Generating or mutating any Excel workbook or Word document before delivery to user.
- Verifying whether a `.docx` file has corrupt XML structure (The Last Paragraph Rule, missing `<w:p>`).
- Checking whether an `.xlsx` file has broken formulas (`#REF!`), merged cell pollution, text clipping, or missing DrawingML shapes.
- Auditing high-resolution diagram outputs and ensuring they do not exceed page print margins.
- Detecting and cleaning up zombie lock files (`.~lock.*`, `~$*`) left by crashed headless processes.

---

## 2. CLI Execution Toolchain

The core engine is located at [`tools/unified_qa_diagnostic.py`](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py).

### A. Run Diagnostic (Read-Only Audit)
```bash
# Audit an Excel file
python tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py --xlsx "path/to/workbook.xlsx"

# Audit a Word document
python tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py --docx "path/to/document.docx"

# Audit an entire folder & export JSON log for CI/CD
python tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py --all "path/to/folder" --format json --output "qa_report.json"
```

### B. Run Safe Repair (Non-Destructive)
```bash
# Safe repair (creates path/to/workbook_repaired.xlsx)
python tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py --xlsx "path/to/workbook.xlsx" --mode audit-fix

# In-place repair (automatically creates a .bak backup first)
python tool/pdf_to_docx_converter/tools/unified_qa_diagnostic.py --docx "path/to/document.docx" --mode audit-fix --in-place
```

---

## 3. Exit Code Interpretations for Automation

| Exit Code | Status | Meaning | Next Action |
|---|---|---|---|
| `0` | **CLEAN** | 100% Quality Gates passed. No warnings, no errors. | Ready for final delivery or git commit. |
| `1` | **WARNING** | Minor aesthetic issue (e.g. text wrap recommendation, slight padding deviation). | Review warnings; fix if required or proceed if intentional. |
| `2` | **CRITICAL** | Severe issue (Corrupt XML, broken formula `#REF!`, missing images, data loss risk). | **STOP DELIVERY**. Must be repaired before proceeding. |

---

## 4. Key Invariant Quickref

- **Excel Merged Cells**: Always access top-left cell. Writing to non-top-left cells throws an exception.
- **Excel Formula Shifting**: Never hardcode formula strings; parse and expand ranges via regex when adding rows.
- **Excel Prototype Cloning**: Always copy format tokens (font, fill, border, alignment) from the template's representative data row.
- **Docx Last Paragraph**: Every `<w:tc>` must have at least one `<w:p>`. Never leave a cell with 0 paragraphs.
- **Docx Multi-page Tables**: Every table > 10 rows must include `<w:tblHeader/>` on row 0 and `<w:cantSplit/>` on all rows.
- **Lock Files**: Always remove `~$*` and `.~lock.*#` files before packaging deliverables.
