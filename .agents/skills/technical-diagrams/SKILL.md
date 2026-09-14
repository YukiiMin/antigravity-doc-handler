---
name: technical-diagrams
description: Precision system architecture, Hub & Spoke, and mobile screen flow diagrams with 300+ DPI vector rendering, Manhattan orthogonal routing, and collision avoidance.
---

# Antigravity Skill: Technical Diagram Engine (`technical-diagrams`)

Use this skill when you need to design, generate, or render technical architecture diagrams, mobile app screen flows, or state diagrams for DEV/BA documentation and Word/PDF reports.

---

## 🌟 Capabilities

1. **Precision Spec Diagram Engine (`spec_diagram_engine.py`)**:
   - Explicit Cartesian coordinate control ($X, Y, W, H$) and port perimeter anchors (`top`, `bottom`, `left`, `right`).
   - Manhattan orthogonal L-shaped and Z-shaped routing with custom waypoints.
   - **SVG Text Halo (`paint-order="stroke fill"` with `stroke="#ffffff"`)**: Deletes collision lines behind text without clipping or covering neighboring node borders.
   - Built-in headless Microsoft Edge / Chromium 300+ DPI rasterizer (`scale: 3x`).
2. **Mermaid Diagram Suite (`mermaid_renderer.py`)**:
   - Compiles `.mmd` files to high-resolution PNG using Mermaid CLI (`mmdc`).
   - Standardized `flowchart LR` tree fan-out style with `curve: 'stepAfter'`.

---

## 🚀 Quick CLI Reference

```bash
# 1. Render precision declarative diagram from JSON spec:
python -m ai_tools_cli spec-render diagram_spec.json -o output.png -s 3

# 2. Render Mermaid code file to 300 DPI PNG:
python -m ai_tools_cli render-diagram flow.mmd -o flow.png -s 3

# 3. Export SVG directly from Python:
python generate_perfect_hub_spoke.py
```

---

## 📐 Declarative JSON Spec Schema (`diagram_spec.json`)

```json
{
  "width": 1320,
  "height": 720,
  "font_family": "Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, sans-serif",
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
    },
    {
      "id": "error_toast",
      "label": "Error Toast",
      "x": 35,
      "y": 385,
      "width": 85,
      "height": 30,
      "type": "modal"
    }
  ],
  "edges": [
    {
      "source": "home",
      "target": "profile",
      "source_port": "bottom",
      "target_port": "left",
      "source_offset": 30,
      "target_offset": 0,
      "label": "Bottom Nav",
      "line_style": "solid",
      "waypoints": [[520, 309], [520, 481]],
      "label_pos": 0.45,
      "label_offset_x": -16
    }
  ]
}
```

### Node Types:
- `primary`: 2.5px solid black border, bold font (for Core / Hub screens).
- `standard`: 1.5px solid black border, regular font (for Standard screens).
- `modal` / `toast`: 1.5px dashed border (`stroke-dasharray="4,4"`), regular font (for Dialogs, Popups, Errors).

### Collision Prevention Rules:
1. **Minimum Horizontal Gap**: Keep $\ge 55\text{px}$ between adjacent nodes on the same horizontal line to give edge labels breathing room.
2. **Dedicated Port Anchors**: Use different perimeter ports (`top`, `right`, `bottom`, `left`) when branching out multiple lines from a single node to prevent line congestion.
3. **Corridor Checks**: Check that waypoint coordinates do not intersect any node rectangle.
