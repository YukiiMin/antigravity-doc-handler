---
name: technical-diagrams
description: Precision system architecture, Hub & Spoke, and mobile screen flow diagrams with 300+ DPI vector rendering, Manhattan orthogonal routing, and collision avoidance.
---

# Antigravity Skill: Technical Diagram Engine (`technical-diagrams`)

Use this skill when designing, generating, or rendering publication-grade technical architecture diagrams, mobile application screen flows, or state machines for DEV/BA documentation, SRS reports, and Word/PDF deliverables.

---

## 🌟 Capabilities & Core Principles

1. **Declarative JSON-First Architecture**:
   - Separate diagram data (screens, buttons, routing) from rendering logic.
   - Author simple `.json` spec files rather than complex drawing code.
2. **Pixel-Perfect Coordinate & Port-Based Placement**:
   - Explicit Cartesian grid ($X, Y, W, H$).
   - Perimeter port anchors (`top`, `bottom`, `left`, `right`) with sub-pixel offsets.
3. **Manhattan Orthogonal L-Shaped Routing**:
   - Clean 90-degree bend routing with custom waypoints (`[[x, y], ...]`).
   - Prevents chaotic diagonal overlaps and messy line tangling.
4. **Visual Hierarchy & Typography**:
   - `primary`: 2.5px solid border, bold font (Hub / Core Dashboard screens).
   - `standard`: 1.5px solid border, regular font (Normal sub-screens).
   - `modal` / `toast`: 1.5px dashed border (`stroke-dasharray="4,4"`), regular font (Overlays, dialogs, ephemeral toasts).
   - White pill text halos (`paint-order="stroke fill"` with `stroke="#ffffff"`) ensure zero collision with background grid lines.
5. **Native Headless Chromium/Edge 300+ DPI Rasterization**:
   - Generates pure SVG then rasterizes via Microsoft Edge or Chromium with `--force-device-scale-factor=3` to guarantee crystal clarity in Word documents without blurriness.

---

## 📐 Declarative JSON Spec Schema

```json
{
  "width": 1400,
  "height": 770,
  "font_family": "Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif",
  "font_size": 10.5,
  "bg_color": "#ffffff",
  "nodes": [
    {
      "id": "login",
      "label": "Login Screen",
      "x": 80,
      "y": 320,
      "width": 150,
      "height": 54,
      "type": "primary"
    },
    {
      "id": "home",
      "label": "Home Dashboard",
      "x": 480,
      "y": 340,
      "width": 160,
      "height": 60,
      "type": "primary"
    },
    {
      "id": "modal_otp",
      "label": "OTP Verification Modal",
      "x": 480,
      "y": 180,
      "width": 160,
      "height": 48,
      "type": "modal"
    }
  ],
  "edges": [
    {
      "source": "login",
      "target": "home",
      "source_port": "right",
      "target_port": "left",
      "source_offset": 0,
      "target_offset": 0,
      "label": "Click \"Đăng nhập\"",
      "line_style": "solid",
      "waypoints": [],
      "label_pos": 0.5,
      "label_offset_y": -8,
      "label_offset_x": 0
    },
    {
      "source": "home",
      "target": "login",
      "source_port": "left",
      "target_port": "right",
      "source_offset": 10,
      "target_offset": 10,
      "line_style": "dashed",
      "waypoints": [[450, 420], [250, 420]],
      "label": "Click \"Đăng xuất\"",
      "label_pos": 0.5,
      "label_offset_y": -8
    }
  ]
}
```

### Field Reference:

| Field | Type | Description |
|-------|------|-------------|
| `width`, `height` | `number` | Canvas viewport size in pixels (keep ratio between 1.6:1 and 1.85:1). |
| `font_family` | `string` | System typography stack (default: `Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, sans-serif`). |
| `font_size` | `number` | Base font size (10.5 – 11.5pt recommended). |
| `nodes[].id` | `string` | Unique identifier referenced by edges. |
| `nodes[].label` | `string` | Display label (supports `\n` for multi-line title + subtitle). |
| `nodes[].type` | `string` | Visual style: `"primary"` (thick 2.5px), `"standard"` (1.5px), `"modal"` / `"toast"` (dashed). |
| `edges[].source`, `target` | `string` | Node IDs for source and target. |
| `edges[].source_port`, `target_port` | `string` | Port orientation: `"top"`, `"bottom"`, `"left"`, or `"right"`. |
| `edges[].waypoints` | `number[][]` | List of `[x, y]` intermediate bend points for Manhattan orthogonal routing. |
| `edges[].line_style` | `string` | `"solid"` for forward actions, `"dashed"` for return/cancel/auto-sync loops. |
| `edges[].label_pos` | `number` | Position along path from 0.0 (source) to 1.0 (target), default 0.5. |
| `edges[].label_offset_x`, `_y` | `number` | Fine-tuning offsets for label pill to prevent touching boxes or lines. |

---

## 📏 A4 Document Layout & Sizing Rules

When diagrams are destined for Word (`.docx`) or PDF documents on A4 Portrait:

1. **Aspect Ratio Constraint (1.6:1 – 1.85:1)**:
   - *Why*: A4 Portrait body width is limited to **14.0 cm** between standard 1-inch margins.
   - If a diagram is too wide (e.g. 4:1), Word will scale down the whole image to fit 14.0 cm width, collapsing font size to 3–4pt and rendering text unreadable.
   - An aspect ratio of **1.6:1 to 1.85:1** fills approximately 1/3 to 1/2 of an A4 page vertically, keeping effective rendered font size at **9.5 – 10.5pt** (100% crisp and readable without zooming).
2. **300+ DPI Rasterization (`scale: 3`)**:
   - Always render PNG at `scale=3`. A 1340x770 canvas becomes a **4020x2310** ultra-high-resolution image.
3. **Word Insertion Parameters**:
   - In Word OpenXML: set image width to exactly **14.0 cm** (`5040000 EMUs`).
   - Calculate height dynamically: $H_{\text{cm}} = W_{\text{cm}} \times \frac{H_{\text{px}}}{W_{\text{px}}}$.

---

## 🎯 Standardized Diagram Language & Action Formatting Rules

> **MANDATORY**: Technical diagrams must maintain international technical standards while faithfully representing the codebase implementation.

1. **Object / Screen Box Names & Metadata — 100% Standardized English**:
   - Every node box label MUST be in standardized technical English (e.g., `Login Screen`, `Register Screen`, `Home Dashboard`, `Cart Screen`, `Product Detail Screen`, `Navigation Map 2D`).
   - Applies to ALL diagram entities:
     - Group / Cluster titles (`Authentication Flow`, `Main Operations`, `Warehouse Staff Area`).
     - Container boxes, Subtitles, Badges & Role tags (`[Authorized Staff Only]`, `Route: /login`).
   - NEVER place Vietnamese titles or redundant bilingual strings (`Đăng nhập (Login Screen)`) inside node boxes.

2. **Automated i18n Codebase Detection (AI Heuristic)**:
   - Before drafting the spec, AI scans the target codebase for internationalization resources:
     - **Android**: `res/values-*/strings.xml` (presence of `values-en/` alongside `values-vi/` or default `values/`).
     - **Web/FE**: `locales/`, `messages/`, `i18n.ts/js`, or pairs like `en.json` and `vi.json`.
     - **Flutter/Cross-platform**: `l10n/` or `.arb` resource files.
   - **Multi-language (i18n) Mode** (>= 2 languages found): Default 100% of all diagram text, including action button labels, to English (`Tap "Login"`, `Click "View Cart"`, `Select "Settings"`).
   - **Single-language Native Mode** (only 1 native locale found, e.g. Vietnamese-only FE): Action verbs in English + Quoted native UI string directly from codebase.

3. **Action Button Phrasing on Arrows**:
   - **Standardized English Action Verbs**:
     - `Tap`: For Mobile / Touchscreen interactions (`Tap "Đăng nhập"`).
     - `Click`: For Web / Desktop / Mouse interactions (`Click "Submit"`).
     - `Select`: For Tabs, Radio buttons, Dropdown menus, List items (`Select "Cài đặt"`).
     - `Scan`: For Camera, Barcode, QR scanning (`Scan "Mã vạch sản phẩm"`).
     - `Swipe`: For Gesture-based transitions (`Swipe Down to Refresh`).
     - `Auto`: For System-triggered redirects and timer expirations (`Auto Redirect (3s)`).
   - **Quoted Native Button UI String**:
     - When a real UI button exists in single-language mode: `Click "Đăng nhập"`, `Tap "Xem lộ trình\n& Chỉ đường"`, `Click "Đăng xuất"`.
   - **Interactions Without Explicit Buttons (Non-button / Gesture / System Events)**:
     - Use 100% technical English without quotes:
     - Card / Item selection: `Tap Item Card`, `Tap Recommendation Banner`.
     - System events: `Auto Redirect (3s)`, `Session Expired`.
     - Hardware & Scanners: `Press System Back`, `Scan Barcode Success`.

4. **Multi-line Wrapping & Collision Avoidance (`\n`)**:
   - When an action label exceeds 18–22 characters, break it across multiple lines using `\n` at natural whitespace breaks.
   - Never let button labels overflow horizontally into adjacent node boxes or lines.
   - The diagram engine calculates stacked line heights with white halo masking and automatically runs AABB collision detection to warn if any label collides with a node.


---

## 🚫 Anti-Patterns to Avoid

- ❌ **Wide 1-Row Layouts**: Do not lay out 10+ nodes horizontally in a single row. Use a 4-to-5 column grid with vertical stacking.
- ❌ **Overlong Single-Line Labels**: Never let a 30-character label stretch across a 100px gap, overlapping adjacent nodes. Always wrap with `\n`.
- ❌ **Vietnamese Inside Screen Boxes**: Keep screen titles in standardized English for international technical clarity.
- ❌ **Diagonal Lines Crossing Nodes**: Always route around intervening nodes using L-shaped or U-shaped waypoints.
- ❌ **Labels Clipped Off-Canvas**: Ensure `label_offset_x` does not push text past the canvas boundary ($x < 0$ or $x > \text{width}$).
- ❌ **Ambiguous Ports**: Never anchor multiple outgoing arrows to the exact same port without offsetting (`source_offset`).

---

## 💻 CLI Usage & Visual Editor

```bash
# 1. Render directly using the precision diagram engine (scale 3 for 300+ DPI):
python spec_diagram_engine.py --spec android_user_flow_v2_spec.json --out android_user_screen_flow_v2.png --scale 3

# 2. Launch Interactive Canvas Editor for visual Drag & Drop, port tuning, and 2-way JSON sync:
python diagram_editor.py --spec android_user_flow_v2_spec.json

# Or via unified CLI:
python -m ai_tools_cli diagram-editor android_user_flow_v2_spec.json
```

### 🎨 Visual Canvas Editor Capabilities:
- **Two-Way JSON Sync**: Edit visually on canvas, save directly to `.json` (Single Source of Truth).
- **Zero-Flicker Drag**: Smooth tag-based motion (`canvas.move`) recalculating only incident edges.
- **Node ID Rename Guard**: Duplicate ID protection ensuring references across all edges remain valid.
- **Edge Hit-Testing**: Seamless click-to-select on orthogonal polyline connections.
- **Deep Undo/Redo**: 30-step snapshot stack (`Ctrl+Z` / `Ctrl+Y`).
- **Direct 300+ DPI Export**: High-resolution PNG rasterization with one click.
