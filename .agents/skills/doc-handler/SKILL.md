---
name: doc-handler
description: Master operations guide, mental model, and decision tree for universal office document processing (PDF <-> DOCX <-> Markdown), OpenXML table enforcement, and precision JSON-driven technical diagram generation.
---

# Antigravity Master Skill: Universal Office Document & Diagram Studio (`doc-handler`)

Use this skill whenever you need to process, convert, inspect, format, repair, or generate publication-grade office documents (PDF, Word `.docx`, Excel `.xlsx`, Markdown `.md`) and system/software architecture diagrams.

---

## 🧠 Core Philosophy & Mental Model

### 1. The Supremacy of Declarative JSON Specification (`.json`)
Why does this tool reject ad-hoc diagram coding, freehand drawing, or uncontrolled auto-layout (like Mermaid Dagre)?
- **Deterministic & 100% Reproducible**: Auto-layout algorithms rearrange nodes unpredictably on every change. A Declarative JSON Spec guarantees that every node, port anchor, bend waypoint, and label position remains pixel-perfect forever across 10,000 renders.
- **Single Source of Truth**: The `.json` file contains pure topological data and state transitions, strictly decoupled from rendering code.
- **AABB Math Collision Engine**: The diagram engine performs automated rectangle collision math (Axis-Aligned Bounding Box) before rendering. It mathematically detects if an action label overlaps any screen box and warns you immediately, eliminating visual bugs before rasterization.
- **Version Control & Clean Git Diffs**: You can track changes to a complex 20-screen mobile flow with crystal-clear 1-line git diffs in JSON, rather than untrackable binary images.

### 2. Decoupled Presentation Architecture (`.md` + `.style.yaml`)
Following the HTML/CSS design paradigm:
- **Data Layer (`.md`)**: Pure, clean Markdown. No inline styles, no `<font>` or `<style>` tags, no frontmatter pollution. Perfect for git repositories, developer wikis, and LLM context.
- **Style Layer (`.style.yaml`)**: Stores page geometry (A4 margins), typography, heading palettes, table shading, and border properties. You can re-skin an entire 100-page document instantly by swapping the `.style.yaml` file without touching a single word of content.

### 3. Strict OpenXML Invariant Compliance
Standard tools (pandoc, basic python-docx) create fragile Word documents. This tool strictly enforces OpenXML invariants via `smart_post_processor.py`:
- `<w:cantSplit/>`: Prohibits any table row from splitting across page breaks.
- `<w:tblHeader/>`: Repeats table header rows automatically at the top of every subsequent page.
- `<w:vAlign w:val="center"/>`: Vertically centers text inside every table cell.
- `<w:shd w:fill="FFE8E0"/>`: Applies standard peach header shading to every table.
- **TOC Dot-Leader Tabs**: Formats Table of Contents entries with native right-aligned dot-leader tab stops.

---

## 🌲 Decision Tree & Use Cases

```
                                [Document / Diagram Task]
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
   [Convert / Repair]             [Decouple & Author]             [Technical Diagrams]
         │                                 │                                 │
  ┌──────┴──────┐                   ┌──────┴──────┐                   ┌──────┴──────┐
  ▼             ▼                   ▼             ▼                   ▼             ▼
PDF -> DOCX   DOCX Repair      DOCX -> MD    MD -> DOCX         Screen Flows   Arch / Hub
(Smart v6)   (OpenXML fix)    (+Style YAML)  (Style Apply)      (JSON Spec)   (JSON Spec)
```

### Case 1: Convert PDF to Editable DOCX with 100% Format Fidelity
- **Scenario**: You have an SRS specification, thesis, or client document in PDF and need to convert it to Word without losing dot-leader TOC tabs, table borders, or bullet hierarchies.
- **Command**:
  ```bash
  python -m ai_tools_cli convert input.pdf -o output.docx
  ```

### Case 2: Extract Content into Clean Markdown + Standalone Style YAML
- **Scenario**: You want to ingest a corporate Word document into an LLM or Git knowledge base while archiving its styling tokens.
- **Command**:
  ```bash
  python -m ai_tools_cli convert document.docx -t md
  # Generates document.md (clean GFM) and document.style.yaml (design tokens)
  ```

### Case 3: Compile Markdown to High-Fidelity Word DOCX
- **Scenario**: An AI agent or human author wrote documentation in Markdown and needs to compile it into a presentation-ready Word document conforming to corporate style.
- **Command**:
  ```bash
  python -m ai_tools_cli convert document.md -t docx --style document.style.yaml
  ```

### Case 4: Design & Render Precision Technical Diagrams (Screen Flows / Hub & Spoke)
- **Scenario**: Designing mobile screen flows, state machines, or system architectures destined for Word reports or PDF deliverables.
- **Command**:
  ```bash
  python spec_diagram_engine.py --spec flow_spec.json --out flow_diagram.png --scale 3
  ```

---

## 📐 Strict Standards for Diagram JSON Specifications (`.json`)

When drafting or updating any diagram `.json` specification, you MUST follow these 5 golden rules:

### Rule 1: International English for Object / Screen Names
- All text inside node boxes MUST be 100% standardized technical English (e.g., `Login Screen`, `Register Screen`, `Home Dashboard`, `Cart Screen`, `Navigation Map 2D`).
- **NEVER** put Vietnamese or redundant bilingual strings (`Đăng nhập (Login Screen)`) inside node boxes.

### Rule 2: Codebase-Truth Action Phrasing on Arrows
- **English Action Verb**: Always begin with an English verb (`Click`, `Tap`, `Select`).
- **Quoted Button Text**:
  - For **single-language projects without i18n** (e.g. Vietnamese): Quote the exact UI string from the codebase: `Click "Đăng nhập"`, `Click "Xem lộ trình\n& Chỉ đường"`, `Click "Đăng xuất"`, `Tap Recommendation Card`.
  - For **multi-language (i18n) projects**: Default 100% of the action string to English: `Click "Login"`, `Click "View Route & Directions"`.

### Rule 3: Multi-line Wrapping & Collision Prevention (`\n`)
- When any action label exceeds **18–22 characters**, you MUST split it with `\n` across 2 or 3 lines.
- The engine will render stacked text with a `4px` white halo (`paint-order="stroke fill"`).
- Always verify that the label's bounding box does not overlap adjacent node boxes. The engine's built-in AABB collision engine will print `[WARN]` if a collision is detected.

### Rule 4: Column-Based Cartesian Grid & Golden Aspect Ratio
- **Portrait A4 Page Constraint**: Word documents on A4 Portrait have **14.0 cm** of printable width between 1-inch margins.
- Maintain canvas aspect ratio between **1.6:1 and 1.85:1** (e.g. `1400x770` or `1360x720`).
- Arrange nodes in a logical 4-to-5 column flow (Auth $\to$ Onboarding $\to$ Hub $\to$ Features $\to$ Details) rather than a wide 1-row strip.
- Render at `--scale 3` for ultra-sharp 300+ DPI vector grade resolution.

### Rule 5: Manhattan Orthogonal Routing
- Keep lines strictly orthogonal (90-degree L-shaped or Z-shaped bends).
- Use `waypoints: [[x, y], ...]` to cleanly route return loops around intervening nodes without messy diagonal crossings.

---

## 💻 CLI Quick Reference

| Action | Command Line |
|---|---|
| **Render Spec Diagram** | `python spec_diagram_engine.py --spec <spec.json> --out <output.png> --scale 3` |
| **Convert PDF $\to$ DOCX** | `python -m ai_tools_cli convert <input.pdf> -o <output.docx>` |
| **Decouple DOCX $\to$ MD** | `python -m ai_tools_cli convert <doc.docx> -t md` |
| **Compile MD $\to$ DOCX** | `python -m ai_tools_cli convert <doc.md> -t docx --style <doc.style.yaml>` |
| **Inspect Document Structure** | `python -m ai_tools_cli inspect-doc <document.docx>` |
| **Insert Image into Section** | `python -m ai_tools_cli insert-diagram <doc.docx> <img.png> -s "<Heading>" -w 14.0` |
