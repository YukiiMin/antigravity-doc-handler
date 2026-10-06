# AGENTS.md — Antigravity Agent Operations & Architecture Manual

> **Project Directory**: `tool/pdf_to_docx_converter`  
> **Architecture Version**: 2.0 (AI-Native Modular Architecture)  
> **Core Toolkit**: `doctools` (DOCX, XLSX, DIAGRAM)  
> **Dual-Run Baseline**: `legacy_engines/` (Preserved baseline)

---

## 🚀 Quick Reference: MCP Namespaces & Tool Catalog

All tools in the `doctools` suite are dispatched via a centralized Registry with explicit namespace prefixes:

| Module | Prefix | Core Tools | Standards & Guardrails |
|---|---|---|---|
| **DOCX** | `docx.*` | `lint_template`, `normalize_template`, `register_template`, `render_template`, `build_from_spec`, `inspect_structure`, `patch`, `merge`, `validate` | OpenXML Guards, `cantSplit`, `tblHeader`, Zero-Mutation Raw Cells |
| **XLSX** | `xlsx.*` | `preflight`, `inspect`, `mutate`, `build`, `validate`, `diff`, `recalc`, `lint_template`, `register_template` | 14 Invariants E1–E14, 13 Universal Gates UG-01..13, AST Formula Shift |
| **DIAGRAM** | `diagram.*` | `parse`, `plan_layout`, `build`, `render_raster`, `render_svg`, `inspect_visual`, `repair_layout`, `diff_layout`, `export_pages` | 21 Invariants `MX_INV_01..21`, Pure mxGraphModel, Orthogonal Routing |

---

## ⚡ Project Source Layout

```
pdf_to_docx_converter/
├── doctools/                     # Next-gen AI-Native toolkit (Phase-based development)
│   ├── contract/                 # Pydantic Schemas (FileRef, Envelope, Issue, BaseSpec)
│   ├── infra/                    # Opaque FileStore, Sandbox Runner, Headless Pool, Audit Log
│   ├── core/                     # Domain engines (docx, xlsx, diagram)
│   ├── gates/                    # Quality gates & verification (UG/PG, diff)
│   ├── operations/               # MCP tool handlers & pipelines
│   └── registry.py               # Centralized MCP Tool Dispatcher
├── legacy_engines/               # Preserved v1.0 source archive (Dual-Run Baseline)
│   ├── gui.py / run_gui.bat      # Desktop Tkinter GUI v1.0
│   ├── converter_engine.py       # Conversion dispatcher: PDF <-> DOCX <-> Markdown
│   ├── docx_reader.py / docx_writer.py
│   ├── xlsx_reader.py / xlsx_writer.py
│   ├── spec_diagram_engine.py / diagram_editor.py
│   ├── tools/                    # Legacy diagnostic and utility scripts
│   ├── tests/                    # Test suite for legacy engines
│   └── TOOLS_INVENTORY.md        # Tool catalog and v1.0 lessons learned
├── tests/                        # Standardized test suite for doctools
├── docs/                         # Architecture plans (Master Plan v6) & updated specs
├── .agents/                      # Antigravity IDE Customization configuration
│   ├── rules/                    # Invariant rules (Glob-triggered & semantic model_decision)
│   └── skills/                   # Interactive skills (docx-handler, excel-handler, mxgraph-diagram-engineering, doctools-delivery)
```

---

## 🎯 Important Invariants & Engine Rules

### 1. DOCX Module (Word Processing)
- **The Last Paragraph Rule (`ERR_DOCX_001`)**: Every table cell (`<w:tc>`) MUST terminate with at least one paragraph (`<w:p>`).
- **Run Text Overwrite (`ERR_DOCX_002`)**: Mutate text strictly through `cell.paragraphs[0].runs`; NEVER assign `cell.text = "..."` directly, which strips run styling.
- **Table Integrity (`ERR_DOCX_003`)**: Multi-page tables MUST have `<w:cantSplit/>` on every row and `<w:tblHeader/>` on header rows.
- **Image Bounds (`ERR_DOCX_005`)**: Image width must not exceed printable margins ($\le 15.92\text{ cm}$ for standard A4 portrait margins).

### 2. XLSX Module (Spreadsheet Engineering)
- **Template-Driven Token Extraction (E1)**: 100% of formatting tokens must be extracted from the reference sheet; never guess.
- **Live KPI Formulas (E3)**: All summary and KPI cells MUST use dynamic formulas (`=COUNTIF`, `=SUM`); never hardcode static numbers.
- **Safe Merged-Cell Handling (`ERR_XLSX_004`)**: Assign values strictly to the Top-Left cell; synchronize borders across the entire merged range to prevent border clipping.
- **DrawingML Preservation (`ERR_XLSX_006`)**: Always load existing template workbooks directly (`data_only=False`); never create a blank `Workbook()`, which strips Cover sheet logos and shapes.
- **13 Universal Gates (UG-01..13)**: Every mutate or build operation MUST pass validation gates before delivery.

### 3. DIAGRAM Module (Draw.io mxGraphModel)
- **Pure Native Hierarchy (`MX_INV_01`)**: Strictly forbid `<UserObject mermaidData/plantUmlData>`. All nodes and edges must be native `<mxCell>` children under `parent="1"`.
- **Orthogonal Perimeter Routing (`MX_INV_04`)**: Use `edgeStyle=orthogonalEdgeStyle;` with standard perimeter anchor ports (`exitX, exitY, entryX, entryY` at `0.0`, `0.5`, `1.0`).
- **Dynamic Geometry Scaling (`MX_INV_05`)**: Entity table height $H = 43 \times (N_{\text{fields}} + 1)$; traffic clearance corridor $\ge 60\text{px}$.
- **Monochrome Academic Line-Art (`MX_INV_07`)**: Default to academic black-and-white styling (#ffffff fill, #000000 stroke).
- **Playwright Headless Sidecar (`MX_INV_21`)**: Precise font advance length measurement and high-DPI rendering via sidecar; PIL uniform padding 25px prevents graphical clipping.

### 4. Git & Workflow Protocol
- **Dual-Run Baseline**: Throughout development, legacy engines and scripts in `legacy_engines/` remain independently executable.
- **Verifiable Sub-Step Gate**: Only commit when a sub-step has 100% passing tests and an approved commit message.
- **Scope Boundary**: Only commit to the sub-repo (`antigravity-doc-handler`); NEVER touch the main SAP repository unless explicitly commanded.
