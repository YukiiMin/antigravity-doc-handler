---
trigger: glob
globs: doctools/**/diagram/**, tests/test_diagram/**, **/*.drawio*
description: Technical diagram standards for Draw.io mxGraphModel, 21 invariants MX_INV_01..21, orthogonal routing, and headless rendering. Tiêu chuẩn sơ đồ Draw.io, vẽ kiến trúc, ERD, Sequence, routing dây trực giao, kiểm định thị giác.
---

# Rule: DIAGRAM Engine & Technical Diagram Standards

> **Module**: DIAGRAM (Technical Diagram & Architecture Visualization)  
> **Basis**: Diagram Foundation Plan v1.0, Master Architecture Plan v6, 21 invariants `MX_INV_01..21`.  
> **Scope**: Mandatory for all generation, validation, patching, import, and rendering tasks of technical diagrams (`.drawio`, PNG/SVG) in `doctools` / `pdf_to_docx_converter`.

---

## 1. Core Design Philosophy

1. **Deterministic Engine, Decisive AI**:
   - The engine is a 100% deterministic MCP server; it never invokes AI internally.
   - The AI client is responsible for domain content, producing a `DiagramSpec` JSON with `layout_hints` (orientation, grouping, rank, importance).
   - **AI MUST NEVER write raw XML or hand-craft coordinates ($X, Y$)**. Font advance measurement, layout topology, orthogonal routing, and XML serialization are exclusively handled by the engine.
2. **Semantic-First Validation (DGM-D-09)**:
   - **Semantic Gate DG-00** runs directly on the spec before layout computation (fail-closed).
   - Semantic violations (foreign keys referencing missing tables, inheritance cycles, reverse chronological sequences) immediately halt the pipeline.
3. **Phase 1 and Phase 2 Decoupling (DGM-D-03)**:
   - **Phase 1 (`diagram.build`)**: Generates deterministic pure `mxGraphModel` XML via `lxml` without headless browsers ($< 1$s for 50 nodes).
   - **Phase 2 (`diagram.render`)**: Renders raster/vector PNG/SVG via headless runner or Draw.io CLI; only triggered when export is explicitly required.
4. **Explicit Waypoints & Container Docking (DGM-D-06, DGM-D-07)**:
   - Orthogonal bends MUST carry explicit point arrays in `<Array as="points">`.
   - Edges attach `source`/`target` strictly to parent node/table IDs (`MX_INV_03`), never to child cells. Field-level FK alignment is controlled via fractional anchors (`entryDy`/`exitDy`).
5. **Advance Length Measurement via Pinned Fonts (DGM-D-08)**:
   - Measure label lengths using Pillow `font.getlength(text)` with bundled pinned fonts (Liberation Sans, Be Vietnam Pro) under Unicode NFC normalization.
   - **Heuristic fudge factor `K_adj = 0.78` and crude $N_{\text{chars}} \times 6.1$ formulas are permanently deprecated**.
6. **External Boundaries**:
   - The Diagram engine **never writes OOXML**; technical diagrams are embedded into Word/Excel via image `FileRef` + `render_info`. Schematic diagrams are scheduled for **Phase 3b (P2)** under Diagram Spec v1.1.

---

## 2. The 21 Draw.io & mxGraphModel Technical Invariants (`MX_INV_01..21`)

| Code | Name | Mandatory Invariant Rule | Gate / Test |
|---|---|---|---|
| `MX_INV_01` | **Pure Native Hierarchy** | Strictly forbid `<UserObject mermaidData/plantUmlData>`. Nodes and edges are `<mxCell>` children under `<root><mxCell id="1" parent="0"/>`. | `DG-01` / `DGM-TC-19` |
| `MX_INV_02` | **Minimalist & Clean XML** | Strip junk metadata (`mermaidBaseStyle`, `alternateBounds`). File size $< 300\text{KB}$, 100% well-formed. | `DG-01` / `DGM-TC-19` |
| `MX_INV_03` | **Container-Level Docking** | Edges attach only to parent container IDs (`table_<NAME>`), never to child row cells (`tableRow`). | `DG-04` / `DGM-TC-17` |
| `MX_INV_04` | **Orthogonal Perimeter Routing** | 90° orthogonal edges: `edgeStyle=orthogonalEdgeStyle;`. Standard perimeter anchor ports: Top `(0.5, 0.0)`, Bottom `(0.5, 1.0)`, Left `(0.0, 0.5)`, Right `(1.0, 0.5)`. | `DG-07` / `DGM-TC-15` |
| `MX_INV_05` | **Dynamic Geometry Scaling** | Dynamic table height: $H = 43 \times (N_{\text{fields}} + 1)$. Safety corridor $\ge 60\text{px}$ between tables. | `DG-03` / `DGM-TC-12` |
| `MX_INV_06` | **Dual Delivery** | Deliver both source vector `.drawio` and high-DPI raster/vector render (PNG/SVG). | Render / `DGM-TC-22` |
| `MX_INV_07` | **Monochrome Line-Art** | Academic technical style: white fill `#ffffff`, black stroke `#000000`, dashed `#888888` for optional links. | `DG-01` / `DGM-TC-28` |
| `MX_INV_08` | **Collision-Free Masks** | Edge labels require `labelBackgroundColor=#ffffff;` to prevent overlapping lines; wire corridor $\ge 40\text{px}$. | `DG-05` / `DGM-TC-09` |
| `MX_INV_09` | **Multi-Page Single-File** | Bundle related architecture views into a single `.drawio` file with multiple `<diagram name="...">` tabs. | `DG-01` / `DGM-TC-24` |
| `MX_INV_10` | **Schematic Direct Taps** | [Phase 3b] Color-coded power rails (+12V Red, +5V Orange, +3V3 Blue, GND Black) connect directly to IC/MCU. | `PG-SCH-01` / `DGM-TC-SCH-01` |
| `MX_INV_11` | **Fractional Port Anchoring** | Dynamic fractional exit: `exitY = clamp((y - y_top) / H, 0.05, 0.95)` with `entryDy` offset for flat arrows. | `DG-07` / `DGM-TC-15` |
| `MX_INV_12` | **Discrete Highway Corridors** | Parallel buses route along discrete axes spaced $\ge 30\text{px}$–$50\text{px}$. Auto-wrapping for long labels. | `DG-07` / `DGM-TC-18` |
| `MX_INV_13` | **Schematic Strip Layout** | [Phase 3b] Horizontal 1-row layout (L-to-R), top power rails, vertical bottom GND ties. | `PG-SCH-02` / `DGM-TC-SCH-02` |
| `MX_INV_14` | **DFD 5-Column Flow** | [Phase 3b] DFD enforces 5 columns: $C_1$ External $\rightarrow$ $C_2$ Ingest $\rightarrow$ $C_3$ Process/Store $\rightarrow$ $C_4$ Comm $\rightarrow$ $C_5$ Cloud. | `PG-DFD-01` / `DGM-TC-06` |
| `MX_INV_15` | **Dynamic Edge Label Width** | Forbid literal `\n`, `<br>` in edge labels. Use `labelWidth=<W>;html=1;whiteSpace=wrap;` for native wrap. | `DG-05` / `DGM-TC-09` |
| `MX_INV_16` | **4-Tier Stroke Depth** | Tier 1 (Frames/Rails: 2.5–3.0px) > Tier 2 (MCU/IC: 1.8–2.0px) > Tier 3 (Peripherals: 1.2px) > Tier 4 (Wires: 1.0px). | `PG-ARC-01` / `DGM-TC-13` |
| `MX_INV_17` | **Rail Header Legend** | [Phase 3b] Rail name placed in header column ($x < x_{\text{first\_ic}}$); rail body has `value=""` to avoid overlap. | `PG-SCH-02` / `DGM-TC-SCH-03` |
| `MX_INV_18` | **MCU Egress Waterfall** | MCU buses route through dedicated vertical corridors ($\ge 80\text{px}$) rather than cutting across peripheral blocks. | `DG-07` / `DGM-TC-18` |
| `MX_INV_19` | **4-Sided Data Store** | [Phase 3b] DFD data stores (D1, D2) must retain all 4 borders (`top=1;bottom=1;left=1;right=1;`). | `PG-DFD-01` / `DGM-TC-06` |
| `MX_INV_20` | **Snug Mask Bounding** | Forbid hardcoded large `labelWidth`. Calculate dynamic bounding snugly around measured text. | `DG-05` / `DGM-TC-09` |
| `MX_INV_21` | **Zero-Clipping Viewport** | Dynamic bounding scan $(\max_X, \max_Y)$. Viewport $\ge \max + 160\text{px}$, PIL auto-crop with 25px uniform padding. | `DG-06` / `DGM-TC-21` |

---

## 3. Physical ERD & Crow's Foot Standards

1. **3-Column Table Block**: Col 1 Data Type, Col 2 Field Name, Col 3 Key Indicator (`PK`, `FK`, `UK`). Standard row height 43px.
2. **No Verb Labels on Relations**: In physical ERDs, NEVER render verb phrases (`authenticates`, `creates`). Relationship semantics are conveyed via `<<FK>>` fields and Crow's Foot markers.
3. **Crow's Foot Markers**:
   - `Mandatory 1` ($||$): `startArrow=ERmandOne; endArrow=ERmandOne;`
   - `Zero or 1` ($o|$): `startArrow=ERzeroToOne; endArrow=ERzeroToOne;`
   - `Zero or Many` ($o\{$): `startArrow=ERzeroToMany; endArrow=ERzeroToMany;`
   - `One or Many` ($|\{$): `startArrow=ERoneToMany; endArrow=ERoneToMany;`
4. Edges anchor into the specific FK field row via fractional `entryDy` (`PG-ERD-02`).

---

## 4. Verification Gate Pipeline `DG-00..DG-08` & PG Profiles

- `DG-00` (**Semantic Validity**): 100% of `SEM-*` error rules pass on DiagramSpec JSON prior to geometry computation.
- `DG-01` (**XML Well-Formedness**): Valid XML closing with `</root></mxGraphModel>`, zero forbidden UserObject nodes.
- `DG-02` (**Unique IDs & Hierarchy**): 100% unique IDs; all `mxCell` elements have valid parent nodes in the DOM tree.
- `DG-03` (**AABB Collision & Spacing**): 0 overlapping nodes verified by R-tree; `min_node_gap >= 60px`.
- `DG-04` (**Container Docking**): 100% edges dock to parent containers; child-cell docking is rejected.
- `DG-05` (**Snug Label & Bounds**): `labelWidth` matches measured advance length; label masks do not obscure adjacent edges.
- `DG-06` (**Zero-Clipping Viewport**): Viewport $\ge \max + 160\text{px}$; raster export cropped with 25px uniform padding.
- `DG-07` (**Edge Routing Integrity**): 100% orthogonal routing; no edge cuts across unrelated nodes; edge crossings logged.
- `DG-08` (**Render Oracle Gate**): `.drawio` opens cleanly in Draw.io Desktop/CLI without repair prompts.

---

## 5. MCP Tool Catalog `diagram.*` & Error Codes

1. `diagram.get_schema`: Returns JSON Schema and examples by `diagram_type`.
2. `diagram.validate_spec`: Validates schema and runs Semantic Gate DG-00 (fail-closed, read-only).
3. `diagram.build`: Compiles `DiagramSpec` $\rightarrow$ `.drawio` XML (Phase 1: font metrics, layout planning, router, serializer).
4. `diagram.validate_drawio`: Executes DG-01..DG-07 and PG profiles on `.drawio` files.
5. `diagram.inspect`: Inspects diagram hierarchy: pages, nodes, edges, stable anchors.
6. `diagram.render`: Phase 2: Renders PNG/SVG from `.drawio` via headless browser or Draw.io CLI.
7. `diagram.patch` [P1]: Applies declarative mutations and incremental layout updates.
8. `diagram.import_source` [P1]: Parses SQL DDL, DBML into deterministic DiagramSpec.
9. `diagram.list_style_registry` [P1]: Lists valid style tokens and cloud icon sets.

### Error Code Reference:
`E-DGM-SPEC-*` (schema violations); `E-DGM-SEM-*` (semantic rules ERD/ARC/SEQ); `E-DGM-STYLE-*` (unregistered tokens); `E-DGM-LAYOUT-*` (sidecar/overlap); `E-DGM-ROUTE-*` (non-orthogonal/piercing); `E-DGM-XML-*` (XML parsing/docking issues); `E-DGM-RENDER-*` (timeout/crash); `E-DGM-SEC-*` (label script injection, XXE); `W-DGM-*` (layout density, crossings, estimated font metrics).
