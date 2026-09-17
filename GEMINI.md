# Antigravity Document & Diagram Studio — Critical Rules Quickref

> **Auto-loaded every session when operating inside `antigravity-doc-handler` (`tool/pdf_to_docx_converter`).**
> Full rules: `.agents/rules/` | Skills: `.agents/skills/` | Architecture: `README.md`

---

## 🎯 Scope & Core Mission

This repository is a **standalone, high-fidelity Document & Diagram Automation Suite**. It is strictly decoupled from enterprise backend stacks (zero SAP/ABAP dependencies) and focuses 100% on:
1. **Universal Office Document Processing**: High-fidelity bidirectional conversion between PDF, DOCX, and Markdown with OpenXML table preservation.
2. **Spreadsheet Template Fidelity & Automation**: In-place OpenPyXL mutation, dynamic real-time cross-sheet formulas, unified matrix typography, and legacy binary XLS dual-delivery.
3. **Multi-Engine Technical Diagram Studio**: Declarative JSON-driven vector rendering across Canvas, PlantUML (v1.2026+), and Mermaid.
4. **Automated Quality Gates**: Zero placeholders, image preservation, and formula integrity.

---

## ⚡ KEYWORD TRIGGER PROTOCOL

When starting any task in the domains below, **YOU MUST review the corresponding rule BEFORE writing code**:

| When you are touching... | Mandatory Rule to Read First |
|---|---|
| Excel Template, openpyxl, Spreadsheet Data Injection, Matrix UX | `rule_excel_template_preservation_and_ux.md` |
| Technical diagram, ERD, Flowchart, PlantUML, Mermaid, Canvas | `rule_technical_diagram_standards.md` + `rule_database_erd_standards.md` |
| Document converter, PDF export, DOCX OpenXML, Table Formatting | `rule_decoupled_document_converter.md` |
| Quality Gate, Verification, Placeholder checks, XLS/PDF export | `rule_quality_gate_and_verification.md` |
| `/learn` invoked, writing new Rule, writing new Skill | `rule_learning_and_skill_authoring.md` |

---

## 📐 Spreadsheet & Excel Critical Invariants

| # | Rule | Common Violation & Corrective Action |
|---|---|---|
| **E1** | **Live Dynamic Cross-Sheet Formulas** | Hardcoding summary numbers (`Passed: 3, 5, 5`). MUST use live formulas: `='Function 1'!A7`, `=COUNTIF(F40:T40, "P")`, `=SUM(C12:C14)`, `=IF(I17=0, 0, (C17+D17)/I17*100)`. |
| **E2** | **Unified Matrix Typography** | Divergent fonts/sizes for `'O'` marks across cells. MUST enforce **`Tahoma 12pt Bold`**, center-aligned across ALL sibling sheets. |
| **E3** | **Sacred Design Signature Preservation** | Flattening or recoloring distinctive template headers. MUST preserve `#000080` navy backgrounds, 90° vertically rotated text (`textRotation=180`) in Row 9, and merged Column A titles (`Condition`, `Confirm`, `Result`). |
| **E4** | **Chronological & Domain-Relevant Mocking** | Retaining 20-year-old template dummy dates (`2000, 2007, 2009`). MUST inject modern **2026** domain parameters and execution dates (`2026-09-15`). |
| **E5** | **Sibling Structural Symmetry** | Sibling detail tabs (`Function 1`, `Function 2`, `Function 3`) MUST have 100% matched column widths, row heights, freeze panes (`F10`), and formatting. |

---

## 📄 Word & DOCX Critical Invariants

| # | Rule | Implementation Standard |
|---|---|---|
| **W1** | **`<w:cantSplit/>` Table Invariant** | Prohibits table rows from breaking across page splits. Enforced via `smart_post_processor.py`. |
| **W2** | **`<w:tblHeader/>` Table Header Invariant** | Repeats table headers at the top of every subsequent page automatically. |
| **W3** | **`<w:vAlign w:val="center"/>` Cell Invariant** | Vertically centers all text inside table cells. |
| **W4** | **Decoupled Markdown + Style YAML** | Keep `.md` free of inline style pollution; store page margins, colors, and typography tokens in `.style.yaml`. |
| **W5** | **TOC Dot-Leader Tab Stops** | Native right-aligned dot-leader tabs for Table of Contents entries. |

---

## 📊 Technical Diagram Invariants

| # | Rule | Requirement |
|---|---|---|
| **D1** | **Declarative JSON Spec Supremacy** | Author deterministic `.json` specs for screen flows and architectures. Avoid uncontrolled auto-layout drift. |
| **D2** | **Standardized English Node Box Titles** | 100% English inside screen boxes (`Login Screen`, `Home Dashboard`, `Cart Screen`). Never put Vietnamese inside node boxes. |
| **D3** | **Codebase-Truth Actions with `\n` Wrapping** | Action verbs in English (`Click "Đăng nhập"`, `Tap Recommendation Card`). Split labels $> 18-22$ chars with `\n`. |
| **D4** | **Golden Aspect Ratio (1.6:1 - 1.85:1)** | Fit standard portrait A4 margins ($14.0\text{cm}$ width) without font shrinkage. Render at `--scale 3` for 300+ DPI. |
| **D5** | **PlantUML Windows JVM Flags** | Always pass `-charset UTF-8` and `-DPLANTUML_LIMIT_SIZE=16384`. Use bundled local `<C4/C4_Context>` library. |

---

## 🛡 Quality Gate Invariants

| # | Rule | Verification Standard |
|---|---|---|
| **Q1** | **Zero Unreplaced Placeholders** | Zero `<Developer Name>`, `<TODO>`, `{{...}}` artifacts. Automated regex scan required before handoff. |
| **Q2** | **DrawingML Logo Fidelity** | Templates with embedded images/logos must preserve `len(ws._images) > 0` after mutation. |
| **Q3** | **Dual-Format Delivery** | Always generate modern `.xlsx` alongside legacy binary `.xls` (via headless LibreOffice export). |

---

## 💻 CLI Quick Reference

```bash
# 1. Diagram Rendering
python ai_tools_cli.py diagram-render specs/master_erd_smart_mart.json -o diagram_assets/master_erd.png
python spec_diagram_engine.py --spec specs/flow_smart_mart.json --out diagram_assets/flow_smart_mart.png --scale 3

# 2. Document Conversion & Repair
python -m ai_tools_cli convert input.pdf -o output.docx
python -m ai_tools_cli convert document.docx -t md
python -m ai_tools_cli convert document.md -t docx --style document.style.yaml

# 3. Excel Enhanced Generation & Quality Validation
python tools/generate_enhanced_ux_excel.py
soffice --headless --convert-to xls dataset1/output/Report5_Unit Test_Enhanced_UX.xlsx --outdir dataset1/output/
```
