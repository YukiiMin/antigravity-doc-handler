---
name: mxgraph-diagram-engineering
description: AI-Native Diagram Engineering Skill for Draw.io (mxGraphModel). Professional generation, topology layout, orthogonal routing, headless rendering, visual inspection, and layout auto-repair without manual coordinate guesswork. Vẽ sơ đồ Draw.io, mô hình mxGraphModel, ERD Crow's Foot, sơ đồ khối kiến trúc, routing dây trực giao, render không cắt cụt.
---

# Skill: mxGraphModel & Draw.io Diagram Engineering (AI-Native Engine)

> **Goal**: Standardize the design, generation, validation, and layout optimization of professional engineering diagrams on Draw.io (`mxGraphModel`).  
> **Mandatory Invariants**: Adhere 100% to [`.agents/rules/rule_diagram_engine_standards.md`](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/tool/pdf_to_docx_converter/.agents/rules/rule_diagram_engine_standards.md) and the Delivery Cadence in `doctools-delivery`.

---

## 1. AI-Native Operational Mental Model

1. **AI NEVER Writes Raw Draw.io XML**: The AI client never writes thousands of lines of raw XML by hand. The risk of malformed tags, corrupt hierarchies, or Draw.io parse rejections is extremely high.
2. **AI NEVER Guesses Pixel Coordinates**: Geometric coordinates $(x, y)$, dimensions, and orthogonal routing waypoints are calculated by deterministic layout planners (`Sugiyama`, `Force-Directed`, `Radial`).
3. **Structured JSON Communication (`DiagramSpec`)**: The AI focuses exclusively on system architecture (entities, relations, groups, topology, theme), delegating layout to the engine via MCP tools.
4. **Visual Closed-Loop Inspection**: Generated drawings are rendered headless to PNG/SVG and automatically verified via `diagram.inspect_visual` before delivery.

---

## 2. The 21 Core Invariants Reference (`MX_INV_01–21`)

| Code | Name | Mandatory Technical Rule |
|---|---|---|
| `MX_INV_01` | **Pure Native Hierarchy** | Forbid `<UserObject mermaidData/plantUmlData>`. All nodes and edges must be native `<mxCell>` children under `parent="1"`. |
| `MX_INV_02` | **Minimalist & Well-Formed XML** | Strip metadata bloat (`mermaidBaseStyle`, `alternateBounds`). 100% well-formed, compact XML. |
| `MX_INV_03` | **Container-Level Docking** | ERD edges dock exclusively to parent container tables (`table_X`), never to child row cells (`tableRow`). |
| `MX_INV_04` | **Orthogonal Perimeter Routing** | `edgeStyle=orthogonalEdgeStyle;` with standard perimeter anchor ports (`exitX, exitY, entryX, entryY` at `0.0`, `0.5`, `1.0`). |
| `MX_INV_05` | **Dynamic Geometry Scaling** | Table height: $H = 43 \times (N_{\text{fields}} + 1)$; routing corridor between boxes $\ge 60$px. |
| `MX_INV_06` | **Dual Delivery** | Deliver both native `.drawio` source and high-DPI raster/vector rendering (PNG/SVG). |
| `MX_INV_07` | **Academic Line-Art First** | Monochrome line-art preferred: `#ffffff` fill, `#000000` text/stroke, dashed `#888888` for optional links. |
| `MX_INV_08` | **Collision-Free Labels & Masks** | Wire labels require `labelBackgroundColor=#ffffff;` to prevent line overlap; routing corridor $\ge 40$px. |
| `MX_INV_09` | **Multi-Page Single-File** | Bundle related views into a single `.drawio` file with multiple `<diagram name="...">` tabs. |
| `MX_INV_10` | **Schematic Direct Taps** | Color-coded power rails (+12V Red, +5V Orange, +3V3 Blue, GND Black) route directly to ICs without redundant text nodes. |
| `MX_INV_11` | **Fractional Port Anchoring** | Hub-to-satellite links use fractional coordinates (`exitY = 0.05..1.0`) aligned to target $y_{\text{center}}$ for zero-zigzag flat horizontal lines. |
| `MX_INV_12` | **Discrete Highway Corridors** | Parallel buses route along discrete axes spaced $\ge 30$–$50$px. HTML wrapping prevents label spill. |
| `MX_INV_13` | **Schematic Horizontal Strip** | Main ICs arranged horizontally (L-to-R), top power rails, vertical bottom GND ties. |
| `MX_INV_14` | **DFD 5-Column Flow** | 5-column flow ($C_1$ External $\rightarrow$ $C_2$ Ingestion $\rightarrow$ $C_3$ Processing $\rightarrow$ $C_4$ Comm $\rightarrow$ $C_5$ Cloud). White mask offsets on labels. |
| `MX_INV_15` | **Dynamic Edge Label Width** | Forbid literal `\n`, `<br>` in edge labels; use `labelWidth=<W>;html=1;whiteSpace=wrap;labelBackgroundColor=#FFFFFF;` for native wrap. |
| `MX_INV_16` | **4-Tier Stroke Hierarchy** | Tier 1 (Frames/Rails: 2.5–3.0px) > Tier 2 (MCU/IC: 1.8–2.0px) > Tier 3 (Peripherals: 1.2px) > Tier 4 (Wires: 1.0px). |
| `MX_INV_17` | **Dedicated Rail Header Legend** | Dedicated header column for rail labels ($x < x_{\text{first\_ic}}$); rail body sets `value=""` to avoid line clutter. |
| `MX_INV_18` | **MCU Egress Waterfall** | MCU GPIO buses exit right (`exitX=1.0`), route via dedicated vertical corridors ($\ge 80\text{px}$), then cascade down to the main bus. |
| `MX_INV_19` | **4-Sided Data Store Enclosure** | DFD data stores (D1, D2) must retain all 4 borders (`top=1;bottom=1;left=1;right=1;`). |
| `MX_INV_20` | **Snug Mask Bounding** | Calculate dynamic label bounds snugly matching text width so white background masks do not obscure adjacent wires. |
| `MX_INV_21` | **Dynamic Viewport Bounds** | Headless render scans $(\max_X, \max_Y)$. Viewport $\ge \max + 160\text{px}$, PIL auto-crop with 25px uniform padding prevents clipping. |

---

## 3. Core MCP Tool Catalog (`diagram.*`)

| Tool Name | Tier | Primary Function |
|---|---|---|
| `diagram.parse` | MVP | Parses Mermaid, PlantUML, SQL DDL into normalized `DiagramSpec`, stripping metadata bloat. |
| `diagram.plan_layout` | MVP | Computes deterministic layout (Sugiyama, Force, Radial), layering, and collision avoidance, returning `LayoutPlan`. |
| `diagram.build` | MVP | Compiles `DiagramSpec` + `LayoutPlan` into pure native `mxGraphModel` XML (`.drawio`). |
| `diagram.render_raster`| MVP | Headless render to high-resolution PNG (300 DPI) via Playwright sidecar or Draw.io CLI. |
| `diagram.render_svg` | MVP | Exports crisp vector SVG with transparent background for publication. |
| `diagram.inspect_visual`| MVP | Visual closed-loop check: flags label-wire collisions, text clipping, and pierced component boxes. |
| `diagram.repair_layout`| P1 | Automatically adjusts bus corridors, docking ports, and spacing upon detecting collisions. |
| `diagram.diff_layout` | P1 | Compares structural and visual differences between two diagram versions. |
| `diagram.export_pages` | P1 | Splits and exports individual pages from multi-page `.drawio` files. |

---

## 4. Standard 5-Step Operational Workflow

### Step 1 — Draft DiagramSpec JSON
Normalize requirements into a structured `DiagramSpec`:
```json
{
  "title": "Authentication Microservice Architecture",
  "topology": "layered_arch",
  "theme": "academic_monochrome",
  "nodes": [
    { "id": "client", "label": "Client App", "kind": "boundary", "group": "frontend" },
    { "id": "gateway", "label": "API Gateway", "kind": "service", "group": "backend" },
    { "id": "auth_svc", "label": "Auth Service", "kind": "service", "group": "backend" },
    { "id": "redis", "label": "Session Cache", "kind": "datastore", "group": "data" }
  ],
  "edges": [
    { "id": "e1", "source": "client", "target": "gateway", "label": "HTTPS POST /login" },
    { "id": "e2", "source": "gateway", "target": "auth_svc", "label": "gRPC VerifyToken" },
    { "id": "e3", "source": "auth_svc", "target": "redis", "label": "GetSession(Token)" }
  ]
}
```

### Step 2 — Deterministic Layout Planning (`diagram.plan_layout`)
Call `diagram.plan_layout(spec=diagram_spec)` to receive `LayoutPlan`:
- Coordinates $(x, y)$ and dimensions assigned to each node.
- Orthogonal routing waypoints calculated for each edge without overlaps.

### Step 3 — Compile Native XML (`diagram.build`)
Call `diagram.build(spec=diagram_spec, layout_plan=layout_plan)`:
- Generates clean `.drawio` XML adhering to `MX_INV_01..05`.
- Returns output `file_ref_drawio`.

### Step 4 — Headless Render & Visual Inspection
1. Call `diagram.render_raster(file_ref=file_ref_drawio, format="png")` $\rightarrow$ Receive `png_ref`.
2. Call `diagram.inspect_visual(file_ref=png_ref)` $\rightarrow$ Receive visual report:
   - Violations list: `collisions`, `pierced_boxes`, `clipped_labels`.

### Step 5 — Triage & Delivery
- If diagnostics report is 100% clean: Deliver both `.drawio` and `.png` files to the user.
- If geometric collisions occur: Invoke `diagram.repair_layout` or adjust spec parameters.

---

## 5. Troubleshooting & Auto-Repair Reference

### Error Codes (`E-DGM-*`)

| Error Code | Category | Technical Cause | Remediation |
|---|---|---|---|
| `E-DGM-SPEC-SCHEMA` | Schema | Missing required fields or invalid types | AI corrects JSON Spec following error path. |
| `E-DGM-SEC-INJECTION` | Security | Label contains script tags or XML injection | Strip malicious content, escape XML characters. |
| `E-DGM-TOPOLOGY-PORT` | Topology | Perimeter docking port outside 0.0–1.0 | Trigger Auto-Repair to clamp to perimeter anchors. |
| `E-DGM-XML-USEROBJECT` | XML | Detected forbidden `<UserObject mermaidData>` | Convert to pure `<mxCell>` hierarchy. |
| `E-DGM-XML-CORRUPT` | XML | Malformed XML or missing closing tags | Re-serialize via `xml_serializer.py`. |
| `E-DGM-FONT-METRICS` | Layout | Missing system font, unable to measure text | Activate Pillow bundled font metrics fallback. |
| `E-DGM-ROUTING-PIERCE` | Routing | Edge cuts through peripheral box (`MX_INV_18`)| Route edge through Waterfall corridor ($x \ge 80\text{px}$). |
| `E-DGM-RENDER-CRASH` | Render | Headless render timed out or crashed | Restart Chromium sidecar sandbox. |
| `W-LAYOUT-COLLISION` | Warning | Labels positioned too closely ($\Delta d < 20\text{px}$) | Expand bus axis spacing $\ge 30$–$50$px. |

### Infinite Loop Prevention (Fail-Fast Rule)
- Maximum **2 automated repair attempts** (`diagram.repair_layout`).
- If errors persist after attempt 1 without reduction: **HALT IMMEDIATELY**, present evidence and visual inspection output for user guidance.

---

## 6. Transitional Fallback Scripts

Prior to full deployment of MCP `diagram.*` runtime services, auxiliary utility scripts remain available under `.agents/skills/mxgraph-diagram-engineering/scripts/`:
- `build_drawio.py`: Deterministic pure XML generator for ERD tables.
- `validate_drawio.py`: Syntax and gate verification.
- All diagrams generated via auxiliary scripts MUST be manually validated against `MX_INV_01..21` prior to delivery.
