# AGENTS.md — Antigravity Agent Operations & Architecture Manual

> **Thư mục dự án**: `tool/pdf_to_docx_converter`  
> **Phiên bản**: 2.0 (AI-Native Modular Architecture)  
> **Bộ công cụ cốt lõi**: `doctools` (DOCX, XLSX, DIAGRAM)  
> **Kiến trúc song hành**: `legacy_engines/` (Bảo tồn Dual-Run Baseline)

---

## 🚀 Quick Reference: MCP Namespaces & Tool Catalog

Tất cả các công cụ của bộ công cụ `doctools` được điều phối qua Registry tập trung với tiền tố tường minh:

| Module | Tiền Tố | Các Công Cụ Chính | Tiêu Chuẩn & Rào Chắn |
|---|---|---|---|
| **DOCX** | `docx.*` | `lint_template`, `normalize_template`, `register_template`, `render_template`, `build_from_spec`, `inspect_structure`, `patch`, `merge`, `validate` | OpenXML Guards, `cantSplit`, `tblHeader`, Zero-Mutation Raw Cells |
| **XLSX** | `xlsx.*` | `preflight`, `inspect`, `mutate`, `build`, `validate`, `diff`, `recalc`, `lint_template`, `register_template` | 14 Bất biến E1–E14, 13 Universal Gates UG-01..13, AST Formula Shift |
| **DIAGRAM** | `diagram.*` | `parse`, `plan_layout`, `build`, `render_raster`, `render_svg`, `inspect_visual`, `repair_layout`, `diff_layout`, `export_pages` | 21 Bất biến `MX_INV_01..21`, Pure mxGraphModel, Orthogonal Routing |

---

## ⚡ Cấu Trúc Mã Nguồn Dự Án (Project Layout)

```
pdf_to_docx_converter/
├── doctools/                     # Bộ công cụ AI-Native thế hệ mới (Phát triển theo Phase)
│   ├── contract/                 # Pydantic Schemas (FileRef, Envelope, Issue, BaseSpec)
│   ├── infra/                    # FileStore mờ, Sandbox Runner, Headless Pool, Audit Log
│   ├── docx/                     # Module Word (Template Jinja Path A + DocSpec Path B)
│   ├── xlsx/                     # Module Excel (AST Formula Shifter + Cache Writer lxml)
│   ├── diagram/                  # Module Diagram (Draw.io pure XML + Topology Planner)
│   └── registry.py               # MCP Tool Dispatcher tập trung
├── legacy_engines/               # Kho lưu trữ bảo tồn mã nguồn v1.0 (Dual-Run Baseline)
│   ├── gui.py / run_gui.bat      # Giao diện Desktop Tkinter v1.0
│   ├── converter_engine.py       # Điều phối chuyển đổi PDF <-> DOCX <-> Markdown
│   ├── docx_reader.py / docx_writer.py
│   ├── xlsx_reader.py / xlsx_writer.py
│   ├── spec_diagram_engine.py / diagram_editor.py
│   ├── tools/                    # Script chẩn đoán và tiện ích cũ
│   ├── tests/                    # Bộ kiểm thử cho các engine cũ
│   └── TOOLS_INVENTORY.md        # Danh mục công cụ và bài học v1.0
├── tests/                        # Bộ kiểm thử chuẩn hóa cho doctools
├── docs/                         # Kế hoạch kiến trúc (Master Plan v6) & Specs cập nhật
├── .agents/                      # Cấu hình Customization của Antigravity IDE
│   ├── rules/                    # Bộ quy chuẩn bất biến (< 12,000 ký tự)
│   ├── workflows/                # Master WORKFLOW.md + 3 sub-workflows module hóa
│   └── skills/                   # Skills tương tác (docx-handler, excel-handler, mxgraph-diagram-engineering)
└── WORKFLOW.md                   # Master Workflow chính thống của repository
```

---

## 🎯 Important Invariants & Engine Rules

### 1. Module DOCX (Word Processing)
- **The Last Paragraph Rule (`ERR_DOCX_001`)**: Mọi cell bảng (`<w:tc>`) bắt buộc phải kết thúc bằng tối thiểu một thẻ `<w:p>`.
- **Run Text Overwrite (`ERR_DOCX_002`)**: Thao tác nội dung qua `cell.paragraphs[0].runs`, tuyệt đối không gán `cell.text = "..."` làm mất định dạng run.
- **Table Integrity (`ERR_DOCX_003`)**: Bảng nhiều trang bắt buộc có `<w:cantSplit/>` trên từng dòng và `<w:tblHeader/>` trên dòng tiêu đề.
- **Image Bounds (`ERR_DOCX_005`)**: Chiều rộng ảnh không vượt quá khổ in khả dụng ($\le 15.92\text{ cm}$ cho A4 portrait lề chuẩn).

### 2. Module XLSX (Spreadsheet Engineering)
- **Template-Driven Token Extraction (E1)**: 100% token định dạng trích xuất từ reference sheet, không đoán mò.
- **Live KPI Formulas (E3)**: Toàn bộ ô tóm tắt và KPI phải dùng công thức động (`=COUNTIF`, `=SUM`), không hardcode số tĩnh.
- **Safe Merged-Cell Handling (`ERR_XLSX_004`)**: Chỉ gán giá trị vào Top-Left cell; đồng bộ border toàn dải merged chống rách viền.
- **DrawingML Preservation (`ERR_XLSX_006`)**: Luôn load trực tiếp template gốc; không tạo `Workbook()` rỗng làm mất shapes/logo.
- **13 Universal Gates (UG-01..13)**: Mọi thao tác mutate/build bắt buộc vượt qua cổng kiểm định trước khi bàn giao.

### 3. Module DIAGRAM (Draw.io mxGraphModel)
- **Pure Native Hierarchy (`MX_INV_01`)**: Cấm tuyệt đối `<UserObject mermaidData/plantUmlData>`. Mọi node và edge là `<mxCell>` trực tiếp dưới `parent="1"`.
- **Orthogonal Perimeter Routing (`MX_INV_04`)**: Sử dụng `edgeStyle=orthogonalEdgeStyle;` kèm các cổng viền chuẩn (`exitX, exitY, entryX, entryY` là `0.0`, `0.5`, `1.0`).
- **Dynamic Geometry Scaling (`MX_INV_05`)**: Chiều cao bảng $H = 43 \times (N_{\text{fields}} + 1)$, hành lang giao thông an toàn $\ge 60\text{px}$.
- **Monochrome Academic Line-Art (`MX_INV_07`)**: Ưu tiên phong cách học thuật trắng đen (#ffffff fill, #000000 stroke).
- **Playwright Headless Sidecar (`MX_INV_21`)**: Đo kích thước chữ và render ảnh độ phân giải cao qua sidecar, PIL uniform padding 25px chống cắt xén.

### 4. Git & Workflow Protocol
- **Dual-Run Baseline**: Trong suốt quá trình phát triển, các engine và script trong `legacy_engines/` luôn được bảo đảm khả năng thực thi độc lập.
- **Verifiable Sub-Step Gate**: Chỉ commit khi hoàn thành một module con có test pass 100% và được người dùng phê duyệt commit message.
- **Scope Boundary**: Chỉ commit vào repo con (`antigravity-doc-handler`), tuyệt đối không đụng vào main repo SAP trừ khi được chỉ định.
