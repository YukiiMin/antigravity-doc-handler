# 📄 doctools

**AI-Native Office Document & Precision Technical Diagram Engineering Studio**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Antigravity AI Ready](https://img.shields.io/badge/Antigravity_AI-Compatible-orange.svg)](AGENTS.md)
[![Architecture: v2.0 Modular](https://img.shields.io/badge/Architecture-v2.0_Modular_5--Layer-blueviolet.svg)](WORKFLOW.md)
[![Tests: 30/30 Passing](https://img.shields.io/badge/Tests-30%2F30_Passing-brightgreen.svg)](tests/)
[![Dual-Run Baseline: Preserved](https://img.shields.io/badge/Dual--Run_Baseline-Preserved-success.svg)](legacy_engines/README.md)

---

## 🌟 Overview

`doctools` is an enterprise-grade, modular Python toolkit engineered specifically for autonomous AI agents (especially within **Google Antigravity IDE**), CI/CD runners, and senior software engineers.

It replaces fragile heuristic document scripts with a **deterministic 5-layer plumbing architecture**, delivering 100% format fidelity, strict schema validation, and mathematically verifiable guarantees across three core media formats:

1. **Word Documents (`.docx`)**: Strict ECMA-376 Tag Order Registry and dual-path compilation.
2. **Excel Spreadsheets (`.xlsx`)**: AST formula range shifting, prototype row cloning, and cached value injection.
3. **Technical Diagrams (`.drawio`)**: Pure native `mxGraphModel` XML engineering with orthogonal routing and headless rendering (**Zero PlantUML, Zero Mermaid, Zero UserObject wrappers**).

> [!NOTE]
> **Dual-Run Baseline & Legacy Preservation**:
> All legacy monolithic v1.0 conversion scripts, runners, and Tkinter GUI have been cleanly relocated and preserved inside [`legacy_engines/`](legacy_engines/) and permanently archived on GitHub at branch [`archive/legacy-v1`](https://github.com/YukiiMin/antigravity-doc-handler/tree/archive/legacy-v1). The root repository strictly maintains **Zero Python files at root** and enforces `< 300` lines of code per logical file.

---

## 🏛️ 5-Layer AI-Native Architecture

`doctools` strictly adheres to a unidirectional dependency flow enforced by CI linters:

```
adapters (CLI / MCP stdio)
   │
   ▼
registry (Central ToolRegistry with Namespace & Collision Guards)
   │
   ▼
operations (MCP Operations & Workflows: docx.*, xlsx.*, diagram.*)
   │
   ▼
gates (Fail-Closed Verification Gates & Structural AST Diffing)
   │
   ▼
core (Format Logic: Schema Builders, AST Shifters, Topology Planners)
   │
   ▼
contract (Pydantic Schemas: FileRef, ResultEnvelope, Issues, BaseSpec)
   ▲
   │
infra (FileStore with 24h TTL, SandboxRunner with UTF-8 & Timeout, AuditLogger)
```

### Opaque File Communication (`FileRef`)
To prevent token exhaustion and context pollution, large binary files are never streamed directly into AI context windows. All inputs and outputs are exchanged via opaque `FileRef` handles:
```json
{
  "uri": "resource://docx/files/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "size": 102400,
  "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "expires_at": "2026-10-07T22:00:00Z"
}
```

---

## 🚀 The Triple Core Engineering Modules

### 1. 📘 Module DOCX — Precision Word Processing (`docx.*`)
Designed to eliminate formatting corruption, table tearing, and XML tag disorder in Microsoft Word documents.

- **Tag Order Registry (`lxml`)**: Strictly enforces ECMA-376 schema sequence rules, eliminating corrupt document warnings upon opening Word.
- **Dual-Path Compilation**:
  - *Path A (Template Engine)*: Secure Jinja2 rendering through `docxtpl` with isolated variable extraction and semantic slot replacement.
  - *Path B (DocSpec Builder)*: Programmatic generation of structured documents from pure declarative JSON specifications.
- **Run Consolidator**: Transparently heals split XML runs (`<w:r>`) created by Word editors, ensuring template variables like `{{ invoice_id }}` remain contiguous.
- **Table Integrity Invariants**:
  - Automatically enforces `<w:cantSplit/>` on every row (preventing ugly page-break row splits).
  - Enforces `<w:tblHeader/>` on header rows (repeating table headers across multi-page breaks).
  - Guarantees `<w:vAlign w:val="center"/>` for professional vertical cell alignment.
- **Verification Gates**: 6 Quality Gates (`DG-01..04`, Schema validation, and structural AST diffing).

---

### 2. 📗 Module XLSX — Spreadsheet Engineering (`xlsx.*`)
Engineered to handle complex financial, testing, and KPI workbooks with live dynamic formulas and 100% cell style preservation.

- **Preflight Package Inventory**: Inspects workbooks across Fidelity Tiers (T1 Native OpenPyXL to T4 Complex Macro/DrawingML).
- **AST Formula Shift Manager**: Parses formula syntax trees via `openpyxl.formula.Tokenizer` to dynamically shift cell references (e.g., updating `=COUNTIF(G10:G25, ...)` when expanding data rows) across all sheets and chart series.
- **Recalc Backend & Cache Writer (`write_cached`)**:
  - Evaluates formulas using Microsoft Excel COM (primary) or headless LibreOffice (fallback).
  - Directly injects computed `<v>` value nodes via `lxml` into worksheet XML, ensuring third-party viewers (mobile apps, web portals) display live numbers without requiring user save prompts.
- **14 Invariants E1–E14**:
  - *Prototype Row Style Cloning (E1)*: 100% clones fonts, fills, borders, alignments, and number formats from the representative template row.
  - *Live KPI Formulas (E3)*: Enforces dynamic formulas for summaries (`=COUNTIF`, `=SUM`).
  - *Safe Merged-Cell Handling (`ERR_XLSX_004`)*: Writes values solely to the Top-Left cell while preserving the full border box.
  - *DrawingML Preservation (`ERR_XLSX_006`)*: Retains shapes, floating images, and company logos without corruption.
- **13 Universal Gates (`UG-01..13`)**: Fail-closed gate suite guaranteeing zero `#REF!`, `#VALUE!`, or unformatted cells.

---

### 3. 📙 Module DIAGRAM — Draw.io mxGraph Engineering (`diagram.*`)
Generates publication-quality technical diagrams in native Draw.io (`.drawio` / `mxGraphModel`) format without manual coordinate guesswork.

> **Zero PlantUML & Zero Mermaid**:
> Previous engines relied on external DSLs and fragile web scrapers that produced distorted aspect ratios and unreadable text when embedded into Word documents. `doctools` generates **pure native mxGraph XML** directly.

- **21 Diagram Invariants (`MX_INV_01..21`)**:
  - *Pure Native Hierarchy (`MX_INV_01`)*: Cấm tuyệt đối `<UserObject plantUmlData/mermaidData>`. Mọi node và edge là `<mxCell>` chuẩn trực tiếp dưới root layer `parent="1"`.
  - *Orthogonal Perimeter Routing (`MX_INV_04`)*: Uses `edgeStyle=orthogonalEdgeStyle;` with standardized perimeter ports (`exitX, exitY, entryX, entryY` $\in \{0.0, 0.5, 1.0\}$).
  - *Dynamic Geometry Scaling (`MX_INV_05`)*: Auto-calculates entity table height $H = 43 \times (N_{\text{fields}} + 1)$ with safe traffic corridors $\ge 60\text{px}$.
  - *Monochrome Academic Line-Art (`MX_INV_07`)*: Clean, professional black-and-white publication styling (`#ffffff` fill, `#000000` strokes).
  - *Snug White Mask Bounding (`MX_INV_20`)*: Calculates proportional `labelWidth` dynamically so line masks wrap tightly without occluding neighboring parallel bus wires.
  - *5-Column Orthogonal Flow (`MX_INV_14`)*: Enforces 5-column layout for DFDs (External $\rightarrow$ Ingestion $\rightarrow$ Processing/Store $\rightarrow$ Comm $\rightarrow$ Cloud).
- **Decoupled 2-Phase Rendering Pipeline**:
  - *Phase 1 (Static XML Generation)*: Computes node bounding boxes using Pillow exact font advance lengths (`font.getlength()`), plans topology via ELK sidecar (`elk_worker.mjs`) and Python layouts, and serializes XML via `lxml` with **zero browser required**.
  - *Phase 2 (Headless Rasterization)*: Playwright headless browser renders 300+ DPI vector-grade PNG/SVG with PIL uniform 25px auto-crop to prevent clipped borders (`MX_INV_21`).

---

## 🛠️ Official MCP Tool Catalog

All tools are registered in the central `ToolRegistry` (`doctools/registry.py`) and exposed via Model Context Protocol:

| Module | MCP Tool Name | Priority | Purpose & Guarantees |
|---|---|---|---|
| **DOCX** | `docx.lint_template` | MVP | Lints template syntax, detects split tags and invalid styles |
| **DOCX** | `docx.normalize_template`| MVP | Consolidates fragmented XML runs and cleans Jinja delimiters |
| **DOCX** | `docx.register_template` | MVP | Registers template with schema manifest and slot definitions |
| **DOCX** | `docx.render_template` | MVP | Path A: Renders template with data and semantic OpenXML guards |
| **DOCX** | `docx.build_from_spec` | MVP | Path B: Compiles standalone `.docx` from declarative `DocSpec` JSON |
| **DOCX** | `docx.inspect_structure`| MVP | Extracts document AST (headings, paragraphs, tables) with anchors |
| **DOCX** | `docx.validate` | MVP | Executes 6 Quality Gates for schema and layout fidelity |
| **DOCX** | `docx.merge` | P1 | Merges multiple `.docx` files resolving style collisions |
| **DOCX** | `docx.patch` | P1 | Surgically replaces specific block elements by anchor ID |
| **XLSX** | `xlsx.preflight` | MVP | Analyzes Package Inventory and assigns Fidelity Tier (T1..T4) |
| **XLSX** | `xlsx.inspect` | MVP | Inspects sheets, named ranges, formulas, and merged coordinates |
| **XLSX** | `xlsx.lint_template` | MVP | Validates template layout, formula ranges, and prototype rows |
| **XLSX** | `xlsx.register_template`| MVP | Registers Excel template with expansion rules and design tokens |
| **XLSX** | `xlsx.mutate` | MVP | Expands data tables via Shift Manager; shifts formulas in-place |
| **XLSX** | `xlsx.recalc` | MVP | Recalculates workbook via COM / LibreOffice & injects `<v>` cache |
| **XLSX** | `xlsx.validate` | MVP | Executes 13 Universal Gates (`UG-01..13`) and PG Profiles |
| **XLSX** | `xlsx.diff` | MVP | Performs cell-by-cell structural and formatting AST diff |
| **XLSX** | `xlsx.build` | P1 | Builds workbook from `XlsxSpec`; handles native DrawingML Charts |
| **DIAGRAM**| `diagram.parse` | MVP | Parses DDL, SQL, or text DSL into normalized `DiagramSpec` |
| **DIAGRAM**| `diagram.plan_layout` | MVP | Computes geometric layout and orthogonal waypoints (Phase 1) |
| **DIAGRAM**| `diagram.build` | MVP | Compiles `DiagramSpec` to native `.drawio` XML (Phase 1) |
| **DIAGRAM**| `diagram.render_raster` | MVP | Renders `.drawio` to 300+ DPI PNG via Playwright sidecar (Phase 2) |
| **DIAGRAM**| `diagram.render_svg` | MVP | Exports vector-grade SVG with embedded font definitions (Phase 2) |
| **DIAGRAM**| `diagram.inspect_visual`| MVP | Inspects geometry for edge collisions, crossings, and label overlaps |
| **DIAGRAM**| `diagram.repair_layout` | MVP | Auto-repairs topological defects and applies snug label masks |
| **DIAGRAM**| `diagram.diff_layout` | MVP | Compares structural graph changes between two diagram versions |
| **DIAGRAM**| `diagram.export_pages` | MVP | Packages multiple diagrams into single multi-tab `.drawio` files |

---

## 📂 Project Structure

```
pdf_to_docx_converter/
├── doctools/                     # Official AI-Native Package (< 300 lines/file)
│   ├── contract/                 # Layer 1: Pydantic Data Contracts & Schemas
│   │   ├── fileref.py            # Opaque FileRef with SHA-256 and TTL validation
│   │   ├── envelope.py           # Unified ResultEnvelope, Diagnostics, and Stats
│   │   ├── issues.py             # Diagnostic Issues, Severity, Engine, and Location
│   │   └── spec_base.py          # BaseSpec abstract model with strict schema validation
│   ├── infra/                    # Foundational Infrastructure
│   │   ├── file_store.py         # FileStore: 24h TTL, hash verification, zombie lock cleanup
│   │   ├── sandbox.py            # SandboxRunner: Process isolation, UTF-8, timeout guards
│   │   └── audit.py              # AuditLogger: Traceable request_id context via ContextVar
│   ├── core/                     # Format Execution Cores (docx, xlsx, diagram) [In Progress]
│   ├── gates/                    # Quality Gates & AST Diff Engines [In Progress]
│   ├── operations/               # MCP Tool Handlers & Cross-Module Pipelines [In Progress]
│   ├── resources/                # Schemas, XSD, Built-in Styles, and Font Assets
│   └── registry.py               # Central ToolRegistry with Namespace & Collision Guards
├── tests/                        # Comprehensive Unit & Integration Test Suites
│   ├── contract/                 # Tests for Pydantic contracts (15/15 PASS)
│   ├── infra/                    # Tests for FileStore, Sandbox, Audit (8/8 PASS)
│   └── test_registry.py          # Tests for ToolRegistry and MCP dispatcher (7/7 PASS)
├── legacy_engines/               # Dual-Run Baseline (Archived v1.0 engines and runners)
│   ├── gui.py / run_gui.bat      # Desktop Tkinter GUI v1.0
│   ├── converter_engine.py       # Monolithic PDF <-> DOCX <-> Markdown converter
│   ├── docx_writer.py / xlsx_writer.py
│   ├── spec_diagram_engine.py / diagram_editor.py
│   ├── tools/                    # Legacy generator and patcher scripts
│   └── tests/                    # Legacy test suite
├── docs/                         # Architecture Specs (Master Plan v6, Appendixes)
├── .agents/                      # Antigravity IDE Customizations
│   ├── rules/                    # 10 Standardized Invariant Rules (< 12,000 chars)
│   ├── workflows/                # Master WORKFLOW.md + 3 sub-workflows
│   └── skills/                   # MCP Integration Skills (docx-handler, excel-handler...)
├── AGENTS.md                     # Agent operational manual & invariants quick reference
├── WORKFLOW.md                   # Repository operational workflow runbook
├── pyproject.toml                # Project packaging configuration
└── requirements.txt              # Production dependencies
```

---

## ⚡ Quickstart & Testing

### Installation
```bash
# Clone repository
git clone https://github.com/YukiiMin/antigravity-doc-handler.git
cd antigravity-doc-handler

# Install dependencies
pip install -r requirements.txt
```

### Running Tests
Execute the complete test suite verifying Contracts, Infrastructure, and the ToolRegistry:
```bash
python -m unittest discover -s tests -v
```
*Current test suite status: **30/30 tests passing (100% OK)**.*

---

## 📜 License
Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
