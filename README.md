# 📄 antigravity-doc-handler

**Universal Office Document Studio & Precision Technical Diagram Engine for Antigravity AI and Developers**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Antigravity IDE Ready](https://img.shields.io/badge/Antigravity_AI-Compatible-orange.svg)](AGENTS.md)
[![Resolution: 300+ DPI](https://img.shields.io/badge/DPI-300%2B_Vector_Grade-purple.svg)](spec_diagram_engine.py)

---

## 🌟 Overview

`antigravity-doc-handler` is a specialized Python toolkit designed for software engineers, business analysts, technical writers, and autonomous AI agents (especially within **Google Antigravity IDE**). 

It bridges the gap between raw document conversion, OpenXML Word standard compliance, and publication-quality technical diagram generation.

### Why does this tool exist?
1. **Office Document Engines Lose Formatting**: Standard PDF-to-Word tools mangle Table of Contents (TOC) tab stops, split table rows awkwardly across page breaks, and fail to vertically center text.
2. **Diagram Engines Struggle with Aspect Ratios**: Traditional Mermaid Dagre layouts squeeze complex Hub & Spoke architectures into wide, unreadable horizontal strips (4:1 ratio) that turn into tiny unreadable specks when pasted into Word A4 pages.
3. **Decoupled Architecture**: Separate content (`.md`) from visual presentation (`.style.yaml`), allowing identical documents to be restyled effortlessly without modifying raw data.

---

## 🚀 Dual Core Engines

### 1. 📑 Universal Office Document Studio (`smart_post_processor.py`, `converter_engine.py`)
- **100% Fidelity PDF ↔ DOCX**: Converts PDF to editable Word while applying **Smart Post-Processor v6** to enforce strict OpenXML table invariants.
- **Word Table OpenXML Invariants**:
  - `<w:cantSplit/>`: Prohibits table rows from splitting across page breaks.
  - `<w:tblHeader/>`: Automatically repeats header rows across multiple pages.
  - `<w:vAlign w:val="center"/>`: Vertically centers text inside table cells.
  - `<w:shd w:fill="FFE8E0"/>`: Applies elegant Peach shading to table header rows.
- **TOC Dot-Leader Normalization**: Native right-aligned tab stops with leader dots (`.......`).
- **Decoupled Markdown + Style YAML**: Exports clean Markdown without inline CSS or YAML frontmatter clutter, pairing it with a standalone `.style.yaml` stylesheet.

### 2. 📐 Precision Technical Diagram Engine (`spec_diagram_engine.py`)
- **Hub & Spoke & Mobile Screen Flows**: Explicit coordinate control and perimeter port anchors (`top`, `bottom`, `left`, `right`).
- **Golden Aspect Ratio ($1.6:1 - 1.85:1$)**: Specially tuned for standard portrait A4 margins ($14\text{cm}$ width).
- **Manhattan Orthogonal Routing**: Clean 90-degree L-shaped and Z-shaped lines with custom waypoints.
- **SVG Text Halo Technology**: Employs `paint-order="stroke fill"` with a `4px` white outline (`#ffffff`) around text, eliminating badge collision boxes that obscure adjacent nodes.
- **Headless Chromium/Edge 300+ DPI Rasterization**: Generates ultra-sharp PNG images at 3x scale.

---

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Microsoft Edge or Google Chrome (for headless diagram rasterization)

### Setup
```bash
# Clone repository
git clone https://github.com/YukiiMin/antigravity-doc-handler.git
cd antigravity-doc-handler

# Install dependencies
pip install -r requirements.txt

# (Optional) Install in editable mode for global CLI commands:
pip install -e .
```

---

## 💻 CLI Usage Guide

`antigravity-doc-handler` provides a unified command line interface via `ai_tools_cli.py`:

### 1. Precision Technical Diagram Rendering
Render publication-grade diagrams from a declarative JSON specification:
```bash
python -m ai_tools_cli spec-render android_screen_flow_hub_spoke_spec.json -o screen_flow.png -s 3
```

### 2. Mermaid Diagram Rendering
Render `.mmd` diagrams using Mermaid CLI with standardized tree fan-out styling:
```bash
python -m ai_tools_cli render-diagram architecture.mmd -o architecture.png -s 3
```

### 3. Document Conversion Matrix
```bash
# Convert PDF to DOCX (with Smart Post-Processor v6)
python -m ai_tools_cli convert input.pdf -o output.docx

# Convert DOCX to Decoupled Markdown + Style YAML
python -m ai_tools_cli convert document.docx -t md

# Convert Markdown to DOCX using style tokens
python -m ai_tools_cli convert document.md -t docx --style document.style.yaml

# Convert DOCX to PDF (Word COM Automation)
python -m ai_tools_cli convert document.docx -t pdf
```

### 4. Document Inspection & Diagram Insertion
```bash
# Inspect Word document headings, tables, and OpenXML properties
python -m ai_tools_cli inspect-doc document.docx

# Insert diagram image directly beneath a specific heading
python -m ai_tools_cli insert-diagram document.docx screen_flow.png \
  -s "3.1.2 Android User Screen Flow" \
  -c "Figure 3.1: Android User Screen Flow" \
  -w 14.0
```

### 5. Desktop Drag-and-Drop GUI
For non-technical users, launch the native drag-and-drop desktop application:
```bash
python main.py
# Or double-click run_gui.bat on Windows
```

---

## 🤖 Antigravity AI Agent Integration

This repository is built natively for AI Agents operating in **Google Antigravity IDE**, Cursor, or Claude Code.

### Included Customizations:
- `.agents/skills/doc-handler/SKILL.md`: Instructs AI agents on converting documents, fixing table splits, and formatting headings.
- `.agents/skills/technical-diagrams/SKILL.md`: Instructs AI agents on composing declarative JSON specs, calculating zero-overlap layouts, and routing lines.
- `.agents/rules/rule_decoupled_document_converter.md`: System invariants for document fidelity and diagram styling.
- `AGENTS.md`: Full AI agent operational guide.

### Sample AI Prompt:
> *"Using the technical-diagrams skill in antigravity-doc-handler, create a declarative JSON spec for our Authentication and Payment flow, then run spec-render to generate a 300 DPI PNG at 1.8:1 aspect ratio."*

---

## 📐 Declarative Diagram Spec Format

Below is a minimal sample of the JSON schema used by `spec_diagram_engine.py`:

```json
{
  "width": 1320,
  "height": 720,
  "font_family": "Segoe UI, -apple-system, Roboto, sans-serif",
  "font_size": 10.5,
  "bg_color": "#ffffff",
  "scale": 3,
  "nodes": [
    {
      "id": "home",
      "label": "Member Home Screen",
      "x": 360,
      "y": 265,
      "width": 150,
      "height": 44,
      "type": "primary"
    },
    {
      "id": "profile",
      "label": "Profile Screen",
      "x": 550,
      "y": 460,
      "width": 115,
      "height": 42,
      "type": "standard"
    }
  ],
  "edges": [
    {
      "source": "home",
      "target": "profile",
      "source_port": "bottom",
      "target_port": "left",
      "source_offset": 30,
      "label": "Bottom Nav",
      "line_style": "solid",
      "waypoints": [[520, 309], [520, 481]],
      "label_pos": 0.45,
      "label_offset_x": -16
    }
  ]
}
```

---

## 📁 Repository Structure

```
antigravity-doc-handler/
├── .agents/
│   ├── rules/
│   │   └── rule_decoupled_document_converter.md # Core OpenXML & Diagram Rules
│   └── skills/
│       ├── doc-handler/SKILL.md                 # Document Processing Skill
│       └── technical-diagrams/SKILL.md          # Technical Diagramming Skill
├── ai_tools_cli.py                              # Unified CLI for Terminal & AI
├── spec_diagram_engine.py                       # Precision SVG + Chromium Engine
├── smart_post_processor.py                      # OpenXML Word Table & TOC Repair
├── converter_engine.py                          # Multi-Format Pipeline Coordinator
├── markdown_converter.py                        # Decoupled MD + Style YAML Engine
├── docx_reader.py / docx_writer.py              # Low-Level OpenXML Word Handlers
├── xlsx_reader.py / xlsx_writer.py              # Excel Worksheet Utilities
├── mermaid_renderer.py                          # Mermaid CLI Wrapper & Themes
├── generate_perfect_hub_spoke.py                # Reference Script: 25-Node Hub & Spoke
├── android_screen_flow_hub_spoke_spec.json     # Reference JSON Spec
├── gui.py / main.py                             # Desktop GUI Application
├── requirements.txt                             # Python Dependencies
├── pyproject.toml                               # Packaging Configuration
├── LICENSE                                      # MIT License
├── AGENTS.md                                    # Operational Guide for AI Agents
└── README.md                                    # Documentation
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
Feel free to use, modify, distribute, and integrate into your own workflows.
