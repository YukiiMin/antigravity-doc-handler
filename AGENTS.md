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
| **Unified Multi-Engine Diagram Render** | `python ai_tools_cli.py diagram-render <spec.json> -o <out.png>` |
| **Render PlantUML Diagram** | `python ai_tools_cli.py plantuml-render <spec.json> -o <out.png> --dpi 300` |
| **Render Mermaid Diagram** | `python ai_tools_cli.py mermaid-render <spec.json> -o <out.png>` |
| **Render SVG Canvas Precision Diagram** | `python ai_tools_cli.py spec-render <spec.json> -o <out.png> --scale 3` |
| **Direct Diagram Engine CLI** | `python spec_diagram_engine.py --spec <spec.json> --out <out.png> --scale 3` |
| **Interactive Canvas Diagram Editor** | `python diagram_editor.py --spec <spec.json>` |
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
├── spec_diagram_engine.py      # SVG Canvas Engine (Pixel-perfect Screen Flow)
├── diagram_editor.py           # Interactive Canvas Editor (Drag & Drop, 2-Way JSON Sync)
├── plantuml_renderer.py        # PlantUML Engine (ERD, Class, C4, Swimlane, Use Case, Mindmap)
├── mermaid_renderer.py         # Mermaid Engine (Sequence, Flowchart, State)
├── specs/                      # Declarative Diagram Specs (flow_*.json, master_erd_*.json)
├── tools/                      # Generator & Patcher Scripts + plantuml.jar
│   ├── gen_canvas_erd.py       # Master 4K ERD Generator
│   ├── gen_hub_spoke_flow.py   # Hub & Spoke Flow Generator
│   ├── patch_docx_*.py         # Document Patcher Scripts
│   └── plantuml.jar            # Local PlantUML JAR (v1.2026+, bundled C4 standard library)
├── tests/                      # Test Suites (tests/test_*.py)
├── diagram_assets/             # High-Res Rendered PNG / SVG Artifacts
├── ai_tools_cli.py              # Unified CLI Dispatcher for AI Agents & Terminal Users
├── smart_post_processor.py      # OpenXML Post-Processor (TOC tab stops, table invariants)
├── converter_engine.py          # Unified Multi-Format Conversion Engine
├── markdown_converter.py        # Decoupled Markdown + Style YAML Parser/Serializer
├── docx_reader.py / docx_writer.py # Low-level Word OpenXML Handlers & Auto-Inject Pipeline
└── skills/
    └── technical-diagrams/     # Skill: Multi-Engine Technical Diagrams & Classification
```

---

## 🎯 Important Invariants & Diagram Selection Rules

### Diagram Engine Selection Rules (MANDATORY):
1. **Always Read `"engine"` Field First**: Dispatch to `"canvas"`, `"mermaid"`, or `"plantuml"`.
2. **Tuân Thủ Chuẩn Phân Loại 12 Loại Sơ Đồ Kỹ Thuật**:
   - **`canvas` Engine** (1):
     - Screen Flow (Interactive) — Tọa độ pixel-perfect, kéo thả trên `diagram_editor.py`.
   - **`mermaid` Engine** (5):
     - ERD (Database Schema) — Nền phẳng pastel hiện đại, gọn gàng cho phân hệ 3–15 bảng.
     - Sequence Diagram — Chuỗi gọi API thanh thoát, đánh số tự động `autonumber`.
     - Flowchart / Process — Bẻ nhánh if/else tự do, đổi màu khối nhanh bằng CSS/style.
     - State Diagram — Trạng thái bo góc tròn, màu sắc hiện đại.
     - Mind Map — Phân rã tính năng nhanh, màu pastel chia nhánh trực quan.
   - **`plantuml` Engine** (6):
     - Use Case Diagram — Actor người que, quan hệ `<<include>>`, `<<extend>>` chuẩn UML.
     - C4 Architecture — Thư viện C4 chuẩn quốc tế (`<C4/C4_Context>`), không vỡ dây container.
     - Component / Deployment — Đúng hình khối 3D `node`, `database`, `component`.
     - Activity Swimlane — Phân làn cột (`|Partition|`) thẳng đứng tuyệt đối, không đè dây.
     - Class Diagram — Hỗ trợ trọn vẹn OOP (`+`, `-`, `#`, generics `<T>`, composition).
     - Package Diagram — Hỗ trợ stereotype `<<Folder>>` trực quan cho cấu trúc thư mục.
3. **Tuân thủ 4 Bẫy Kỹ Thuật Windows Cho PlantUML**:
   - C4: Luôn dùng `!include <C4/C4_Context>` Standard Library nội bộ, tuyệt đối KHÔNG dùng URL Raw GitHub.
   - Font: Ghi file UTF-8 và truyền cờ JVM `-charset UTF-8` để tiếng Việt không bị vỡ.
   - Limit: Luôn truyền `-DPLANTUML_LIMIT_SIZE=16384` để ảnh kiến trúc/sơ đồ lớn không bị mờ hoặc cắt cụt.
   - Auto-Inject: Luôn kiểm tra `inject_into` để tự động nhúng vào DOCX sau khi render PNG.
4. **Table Invariants**: Whenever modifying Word `.docx` tables, ensure `<w:cantSplit/>`, `<w:tblHeader/>`, and `<w:vAlign w:val="center"/>` are present.
5. **Diagram Aspect Ratio**: Keep technical diagrams within the $1.6:1 - 1.85:1$ aspect ratio (e.g. $1400 \times 770\text{px}$ or $1360 \times 720\text{px}$) to perfectly fit standard portrait A4 margins ($14\text{cm}$ print width) without font shrinkage.
6. **JSON Spec Supremacy**: Always author declarative `.json` specs for diagrams. Do not rely on uncontrolled auto-layout.
7. **Standardized English Screen Names**: All node box titles must be 100% technical English (`Login Screen`, `Home Dashboard`, `Cart Screen`). Never put Vietnamese inside node boxes.
8. **Codebase-Truth Action Phrasing**: Use English verbs (`Click`, `Tap`, `Select`) + quoted original button labels (`Click "Đăng nhập"`). Default to 100% English for multi-language projects.
9. **Multi-line Wrapping & Collision Avoidance**: Always break action labels across multiple lines with `\n` when length $> 18-22$ characters. Pre-validate using engine AABB collision detection (`[WARN] Label collision detected`).
