# AGENTS.md — Guidance for Antigravity AI Agents

Welcome, AI Agent! This file is your operational manual for `antigravity-doc-handler`.

## 📦 What is this Repository?

`antigravity-doc-handler` is a specialized Python toolkit designed for:
1. **High-Fidelity Document Processing**: Bidirectional conversion between PDF, DOCX, and Markdown with zero data loss, OpenXML table repair, and decoupled styling.
2. **Precision Technical Diagram Engine**: Programmatic and declarative generation of publication-grade Hub & Spoke architecture and mobile screen flow diagrams (300+ DPI, vector SVG + headless Chromium PNG).

---

## 🛠 Available Skills & Rules

The workspace includes preconfigured Antigravity customizations:
- **Skill 1**: [doc-handler](.agents/skills/doc-handler/SKILL.md) — PDF/Word/Markdown conversion, OpenXML table repair, document inspection, and JSON supremacy mental model.
- **Skill 2**: [technical-diagrams](.agents/skills/technical-diagrams/SKILL.md) — Declarative diagram rendering (`spec-render`), orthogonal Manhattan routing, multi-line wrapping, and collision prevention.
- **Rule 1**: [rule_technical_diagram_standards.md](.agents/rules/rule_technical_diagram_standards.md) — Mandatory standards for English screen names, codebase-truth action labels, multi-line wrapping (`\n`), and automated AABB collision detection.
- **Rule 2**: [rule_decoupled_document_converter.md](.agents/rules/rule_decoupled_document_converter.md) — Mandatory standards for table OpenXML invariants (`cantSplit`, `tblHeader`, `vAlign="center"`) and decoupled styling.

---

## 💻 CLI Commands Cheat Sheet

When user requests you to perform document tasks or draw diagrams, run these commands:

| Task | Command Line |
|---|---|
| **Render Diagram from JSON Spec** | `python -m ai_tools_cli spec-render <spec.json> -o <out.png> -s 3` |
| **Direct Diagram Engine CLI** | `python spec_diagram_engine.py --spec <spec.json> --out <out.png> --scale 3` |
| **Interactive Canvas Diagram Editor** | `python diagram_editor.py --spec <spec.json>` |
| **Render Mermaid Diagram** | `python -m ai_tools_cli render-diagram <file.mmd> -o <out.png> -s 3` |
| **Convert PDF to DOCX** | `python -m ai_tools_cli convert <input.pdf> -o <output.docx>` |
| **Convert DOCX to Decoupled MD** | `python -m ai_tools_cli convert <document.docx> -t md` |
| **Convert MD to Styled DOCX** | `python -m ai_tools_cli convert <document.md> -t docx --style <doc.style.yaml>` |
| **Inspect DOCX Headings & Tables** | `python -m ai_tools_cli inspect-doc <document.docx>` |
| **Insert Image into DOCX** | `python -m ai_tools_cli insert-diagram <doc.docx> <img.png> -s "Heading" -c "Caption"` |
| **Launch Desktop GUI** | `python main.py` |

---

## ⚡ Core Engine Architecture

```
antigravity-doc-handler/
├── spec_diagram_engine.py      # Precision Diagram Engine (SVG + Headless Edge/Chrome PNG)
├── diagram_editor.py           # Interactive Canvas Editor (Drag & Drop, 2-Way JSON Sync)
├── test_diagram_editor.py      # Automated Test Suite for Diagram Editor & Tkinter Traps
├── ai_tools_cli.py              # Unified CLI for AI Agents & Terminal Users
├── smart_post_processor.py      # OpenXML Post-Processor (TOC tab stops, table invariants)
├── converter_engine.py          # Unified Multi-Format Conversion Engine
├── markdown_converter.py        # Decoupled Markdown + Style YAML Parser/Serializer
├── docx_reader.py / docx_writer.py # Low-level Word OpenXML Handlers
├── android_user_flow_v2_spec.json  # Reference 19-Node User Flow Spec (Zero Collision)
├── android_staff_flow_spec.json    # Reference 10-Node Staff Flow Spec (Zero Collision)
└── .agents/
    ├── skills/                  # Native Antigravity IDE Skills (doc-handler, technical-diagrams)
    └── rules/                   # Core Document & Diagram Invariants
```

---

## 🎯 Important Invariants to Follow

1. **Table Invariants**: Whenever modifying Word `.docx` tables, ensure `<w:cantSplit/>`, `<w:tblHeader/>`, and `<w:vAlign w:val="center"/>` are present.
2. **Diagram Aspect Ratio**: Keep technical diagrams within the $1.6:1 - 1.85:1$ aspect ratio (e.g. $1400 \times 770\text{px}$ or $1360 \times 720\text{px}$) to perfectly fit standard portrait A4 margins ($14\text{cm}$ print width) without font shrinkage.
3. **JSON Spec Supremacy**: Always author declarative `.json` specs for diagrams. Do not rely on uncontrolled auto-layout.
4. **Standardized English Screen Names**: All node box titles must be 100% technical English (`Login Screen`, `Home Dashboard`, `Cart Screen`). Never put Vietnamese inside node boxes.
5. **Codebase-Truth Action Phrasing**: Use English verbs (`Click`, `Tap`, `Select`) + quoted original button labels (`Click "Đăng nhập"`). Default to 100% English for multi-language projects.
6. **Multi-line Wrapping & Collision Avoidance**: Always break action labels across multiple lines with `\n` when length $> 18-22$ characters. Pre-validate using engine AABB collision detection (`[WARN] Label collision detected`).
