"""
mxgraph_engine.py — Next-Generation mxGraph & Draw.io Diagram Engine (v2.0).

Replaces legacy diagram renderers (mermaid_renderer, spec_diagram_engine, plantuml_renderer)
with a unified Dual-Core architecture:
1. Single Source of Truth: Pure native mxGraphModel XML conforming to MX_INV_01..06.
2. AI / Heuristic Auto-Layout: Topological layering, AABB collision-free spacing, Manhattan orthogonal routing.
3. Dual Delivery: Simultaneously exports editable .drawio/.xml files and publication-grade Full HD PNG.
4. 100% Offline Canvas Runner: Headless Edge/Chromium execution of local mxClient library.
5. Direct integration with docx_writer.py for seamless technical document embedding.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageChops

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_RUNNER_DIR = os.path.join(_CURRENT_DIR, "diagram_assets", "runner")
_RUNNER_HTML = os.path.join(_RUNNER_DIR, "mxgraph_runner.html")

# ==============================================================================
# DRAW.IO XML STYLE CONSTANTS (MX_INV_01..06)
# ==============================================================================

TABLE_STYLE = (
    "shape=table;startSize=43;container=1;collapsible=0;childLayout=tableLayout;"
    "fixedRows=1;rowLines=1;fontSize=15;fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;"
    "strokeWidth=1.5;strokeColor=#1E293B;fillColor=#F8FAFC;align=center;resizeLast=1;html=1;"
)

ROW_STYLE = (
    "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=1;"
    "strokeWidth=1;strokeColor=#E2E8F0;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];"
    "portConstraint=eastwest;top=0;left=0;right=0;bottom=0;"
)

CELL_STYLE_TYPE = (
    "shape=partialRectangle;connectable=0;strokeWidth=1;strokeColor=#E2E8F0;"
    "fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;top=1;left=1;bottom=1;right=1;"
    "align=left;spacingLeft=8;overflow=hidden;fontSize=13;fontColor=#64748B;fontStyle=2;"
)

CELL_STYLE_NAME = (
    "shape=partialRectangle;connectable=0;strokeWidth=1;strokeColor=#E2E8F0;"
    "fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;top=1;left=1;bottom=1;right=1;"
    "align=left;spacingLeft=8;overflow=hidden;fontSize=14;fontColor=#0F172A;"
)

CELL_STYLE_KEY = (
    "shape=partialRectangle;connectable=0;strokeWidth=1;strokeColor=#E2E8F0;"
    "fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;top=1;left=1;bottom=1;right=1;"
    "align=center;overflow=hidden;fontSize=12;fontColor=#D97706;fontStyle=1;"
)

EDGE_BASE_STYLE = (
    "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
    "strokeColor=#475569;strokeWidth=1.6;"
)


# ==============================================================================
# DATA STRUCTURES
# ==============================================================================

@dataclass
class ColumnInfo:
    name: str
    type: str = "string"
    key: str = ""  # "PK", "FK", or ""


@dataclass
class EntityInfo:
    name: str
    columns: List[ColumnInfo] = field(default_factory=list)
    x: float = 0.0
    y: float = 0.0
    width: float = 278.0
    height: float = 43.0


@dataclass
class RelationshipInfo:
    source: str
    target: str
    cardinality_source: str = ""
    cardinality_target: str = ""
    label: str = ""
    style: str = ""


# ==============================================================================
# CARDINALITY MAPPING TO DRAW.IO ARROWS
# ==============================================================================

def map_cardinality_to_arrows(card_src: str, card_tgt: str) -> Tuple[str, str]:
    """Map Mermaid/standard ERD cardinality notations to Draw.io native markers."""
    mapping = {
        "||": "ERmandOne",
        "1": "ERmandOne",
        "|o": "ERzeroToOne",
        "o|": "ERzeroToOne",
        "0..1": "ERzeroToOne",
        "}|": "ERoneToMany",
        "|{": "ERoneToMany",
        "1..*": "ERoneToMany",
        "}o": "ERzeroToMany",
        "o{": "ERzeroToMany",
        "0..*": "ERzeroToMany",
        "*": "ERzeroToMany",
    }
    start_arrow = mapping.get(card_src.strip(), "none")
    end_arrow = mapping.get(card_tgt.strip(), "ERzeroToMany")
    return start_arrow, end_arrow


def _find_chromium_executable() -> Optional[str]:
    """Locate Microsoft Edge or Google Chrome executable on Windows/system."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("msedge"),
        shutil.which("chrome"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


# ==============================================================================
# MERMAID ERD PARSER
# ==============================================================================

def parse_mermaid_erd(mermaid_text: str) -> Tuple[Dict[str, EntityInfo], List[RelationshipInfo]]:
    """
    Parses Mermaid erDiagram syntax into EntityInfo and RelationshipInfo models.
    Supports multi-field entities, PK/FK flags, and relationship arrows.
    """
    entities: Dict[str, EntityInfo] = {}
    relationships: List[RelationshipInfo] = []

    clean_text = re.sub(r"%%.*", "", mermaid_text)  # Strip comments

    # 1. Match entity definition blocks: EntityName { type name [PK|FK] ... }
    entity_blocks = re.findall(r"(\b[A-Za-z0-9_]+)\s*\{([^}]*)\}", clean_text)
    for ent_name, fields_body in entity_blocks:
        cols: List[ColumnInfo] = []
        for line in fields_body.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = re.split(r"\s+", line)
            col_type = parts[0] if len(parts) > 0 else "string"
            col_name = parts[1] if len(parts) > 1 else ""
            key_marker = parts[2].upper() if len(parts) > 2 and parts[2].upper() in ("PK", "FK") else ""
            if col_name:
                cols.append(ColumnInfo(name=col_name, type=col_type, key=key_marker))

        h = 43.0 * (len(cols) + 1)
        entities[ent_name] = EntityInfo(name=ent_name, columns=cols, height=h)

    # 2. Match relationships: ENTITY_A ||--o{ ENTITY_B : "label"
    rel_pattern = re.compile(
        r"(\b[A-Za-z0-9_]+)\s*([|o}{]{1,2})\s*--\s*([|o}{]{1,2})\s*(\b[A-Za-z0-9_]+)(?:\s*:\s*\"?([^\"]*)\"?)?"
    )
    for m in rel_pattern.finditer(clean_text):
        src_name = m.group(1).strip()
        card_src = m.group(2).strip()
        card_tgt = m.group(3).strip()
        tgt_name = m.group(4).strip()
        label = m.group(5).strip() if m.group(5) else ""

        # Ensure entity exists in registry even if without body
        if src_name not in entities:
            entities[src_name] = EntityInfo(name=src_name, height=43.0)
        if tgt_name not in entities:
            entities[tgt_name] = EntityInfo(name=tgt_name, height=43.0)

        start_ar, end_ar = map_cardinality_to_arrows(card_src, card_tgt)
        edge_style = f"{EDGE_BASE_STYLE}startArrow={start_ar};endArrow={end_ar};"

        relationships.append(
            RelationshipInfo(
                source=src_name,
                target=tgt_name,
                cardinality_source=card_src,
                cardinality_target=card_tgt,
                label=label,
                style=edge_style,
            )
        )

    return entities, relationships


# ==============================================================================
# AI & HEURISTIC AUTO-LAYOUT ENGINE
# ==============================================================================

def calculate_auto_layout(
    entities: Dict[str, EntityInfo],
    relationships: List[RelationshipInfo],
    col_gap: float = 100.0,
    row_gap: float = 70.0,
    start_x: float = 80.0,
    start_y: float = 80.0,
) -> None:
    """
    Computes collision-free AABB grid and topological layer coordinates for entities.
    Arranges nodes in balanced columns with adequate wire corridors (>= 60px).
    """
    if not entities:
        return

    # In-degree / out-degree calculation for topological ordering
    in_degree: Dict[str, int] = {name: 0 for name in entities}
    adj: Dict[str, List[str]] = {name: [] for name in entities}

    for rel in relationships:
        if rel.source in adj and rel.target in in_degree:
            adj[rel.source].append(rel.target)
            in_degree[rel.target] += 1

    # Layer assignment (Sugiyama-inspired rank heuristic)
    layers: Dict[int, List[str]] = {}
    visited = set()
    layer_map: Dict[str, int] = {}

    current_layer = 0
    current_nodes = [name for name, deg in in_degree.items() if deg == 0]
    if not current_nodes:
        current_nodes = list(entities.keys())[:2]

    while current_nodes:
        layers[current_layer] = current_nodes
        next_nodes = []
        for n in current_nodes:
            visited.add(n)
            layer_map[n] = current_layer
            for neighbor in adj.get(n, []):
                if neighbor not in visited and neighbor not in next_nodes:
                    next_nodes.append(neighbor)
        current_layer += 1
        current_nodes = next_nodes

    # Place unassigned orphan entities in final layer
    unassigned = [n for n in entities if n not in visited]
    if unassigned:
        layers[current_layer] = unassigned
        for n in unassigned:
            layer_map[n] = current_layer

    # Assign X, Y coordinates
    cur_x = start_x
    for l_idx in sorted(layers.keys()):
        cur_y = start_y
        col_nodes = layers[l_idx]
        max_w = 278.0

        for n_name in col_nodes:
            ent = entities[n_name]
            ent.x = cur_x
            ent.y = cur_y
            cur_y += ent.height + row_gap
            max_w = max(max_w, ent.width)

        cur_x += max_w + col_gap


# ==============================================================================
# MXGRAPH XML GENERATOR
# ==============================================================================

def build_mxgraph_model_xml(
    entities: Dict[str, EntityInfo],
    relationships: List[RelationshipInfo],
    canvas_w: int = 2400,
    canvas_h: int = 1600,
) -> str:
    """
    Generates pure native Draw.io XML adhering 100% to MX_INV_01..06.
    """
    out_root = ET.Element(
        "mxGraphModel",
        {
            "dx": "2060",
            "dy": "1124",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": str(canvas_w),
            "pageHeight": str(canvas_h),
            "math": "0",
            "shadow": "0",
        },
    )

    root_tag = ET.SubElement(out_root, "root")
    ET.SubElement(root_tag, "mxCell", {"id": "0"})
    ET.SubElement(root_tag, "mxCell", {"id": "1", "parent": "0"})

    # 1. Build Entity Tables
    for ent_name, ent in entities.items():
        row_count = len(ent.columns)
        total_h = 43.0 * (row_count + 1)
        ent.height = total_h
        tid = f"table_{ent_name}"

        tcell = ET.SubElement(
            root_tag,
            "mxCell",
            {
                "id": tid,
                "value": ent_name,
                "style": TABLE_STYLE,
                "vertex": "1",
                "parent": "1",
            },
        )
        ET.SubElement(
            tcell,
            "mxGeometry",
            {
                "x": str(round(ent.x, 1)),
                "y": str(round(ent.y, 1)),
                "width": str(round(ent.width, 1)),
                "height": str(round(total_h, 1)),
                "as": "geometry",
            },
        )

        # Build Field Rows
        for i, col in enumerate(ent.columns, 1):
            rid = f"row_{ent_name}_{i}"
            rcell = ET.SubElement(
                root_tag,
                "mxCell",
                {
                    "id": rid,
                    "style": ROW_STYLE,
                    "vertex": "1",
                    "parent": tid,
                },
            )
            ET.SubElement(
                rcell,
                "mxGeometry",
                {
                    "y": str(43 * i),
                    "width": str(round(ent.width, 1)),
                    "height": "43",
                    "as": "geometry",
                },
            )

            # Col 1: Type (82px)
            c1 = ET.SubElement(
                root_tag,
                "mxCell",
                {
                    "id": f"{rid}_c1",
                    "value": col.type,
                    "style": CELL_STYLE_TYPE,
                    "vertex": "1",
                    "parent": rid,
                },
            )
            ET.SubElement(c1, "mxGeometry", {"width": "82", "height": "43", "as": "geometry"})

            # Col 2: Name (153px)
            c2 = ET.SubElement(
                root_tag,
                "mxCell",
                {
                    "id": f"{rid}_c2",
                    "value": col.name,
                    "style": CELL_STYLE_NAME,
                    "vertex": "1",
                    "parent": rid,
                },
            )
            ET.SubElement(c2, "mxGeometry", {"x": "82", "width": "153", "height": "43", "as": "geometry"})

            # Col 3: Key (43px)
            c3 = ET.SubElement(
                root_tag,
                "mxCell",
                {
                    "id": f"{rid}_c3",
                    "value": col.key,
                    "style": CELL_STYLE_KEY,
                    "vertex": "1",
                    "parent": rid,
                },
            )
            ET.SubElement(c3, "mxGeometry", {"x": "235", "width": "43", "height": "43", "as": "geometry"})

    # 2. Build Edges (Container-level Docking MX_INV_03)
    for idx, rel in enumerate(relationships, 1):
        eid = f"edge_{idx}"
        src_table = f"table_{rel.source}"
        tgt_table = f"table_{rel.target}"

        # Determine best perimeter exit/entry based on relative coordinates
        src_ent = entities.get(rel.source)
        tgt_ent = entities.get(rel.target)

        edge_style = rel.style or EDGE_BASE_STYLE
        if src_ent and tgt_ent:
            if tgt_ent.x > src_ent.x + src_ent.width:
                # Target is to the right
                edge_style += "exitX=1;exitY=0.5;entryX=0;entryY=0.5;"
            elif tgt_ent.x + tgt_ent.width < src_ent.x:
                # Target is to the left
                edge_style += "exitX=0;exitY=0.5;entryX=1;entryY=0.5;"
            elif tgt_ent.y > src_ent.y:
                # Target is below
                edge_style += "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"
            else:
                # Target is above
                edge_style += "exitX=0.5;exitY=0;entryX=0.5;entryY=1;"

        ecell = ET.SubElement(
            root_tag,
            "mxCell",
            {
                "id": eid,
                "value": rel.label,
                "edge": "1",
                "parent": "1",
                "source": src_table,
                "target": tgt_table,
                "style": edge_style,
            },
        )
        ET.SubElement(ecell, "mxGeometry", {"relative": "1", "as": "geometry"})

    ET.indent(out_root, space="  ")
    return ET.tostring(out_root, encoding="utf-8").decode("utf-8")


def extract_xml_diagram_bounds(xml_content: str) -> Tuple[int, int]:
    """Calculates max X and max Y extent from mxGraphModel geometry elements."""
    try:
        tree = ET.fromstring(xml_content)
        max_x, max_y = 0.0, 0.0
        for geo in tree.findall(".//mxGeometry"):
            x = float(geo.attrib.get("x", 0) or 0)
            y = float(geo.attrib.get("y", 0) or 0)
            w = float(geo.attrib.get("width", 0) or 0)
            h = float(geo.attrib.get("height", 0) or 0)
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)
        for pt in tree.findall(".//mxPoint"):
            x = float(pt.attrib.get("x", 0) or 0)
            y = float(pt.attrib.get("y", 0) or 0)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        w = max(1800, int(max_x + 160))
        h = max(1200, int(max_y + 160))
        return w, h
    except Exception:
        return 4000, 2500


# ==============================================================================
# HEADLESS CANVAS HD RENDERER
# ==============================================================================

def render_mxgraph_to_png(
    xml_content: str,
    output_png_path: str,
    scale: int = 2,
    padding: int = 25,
    timeout_sec: int = 60,
) -> Dict[str, Any]:
    """
    Renders mxGraphModel XML into high-resolution PNG using local HTML5 runner + headless Edge.
    Auto-crops bounding box margins and saves publication-grade PNG.
    """
    output_png_path = os.path.abspath(output_png_path)
    out_dir = os.path.dirname(output_png_path)
    os.makedirs(out_dir, exist_ok=True)

    chromium_exe = _find_chromium_executable()
    if not chromium_exe:
        raise EnvironmentError(
            "No Chromium browser (msedge.exe or chrome.exe) found on system for canvas rendering."
        )

    # 1. Create self-contained rendering HTML from template
    if not os.path.isfile(_RUNNER_HTML):
        raise FileNotFoundError(f"Offline mxGraph runner HTML template not found: {_RUNNER_HTML}")

    with open(_RUNNER_HTML, "r", encoding="utf-8") as f:
        template = f.read()

    calc_w, calc_h = extract_xml_diagram_bounds(xml_content)

    # Inject XML into window.renderDiagramXml invocation
    xml_encoded = json.dumps(xml_content)
    inject_script = f"""
    <script>
      window.addEventListener('DOMContentLoaded', function() {{
        window.renderDiagramXml({xml_encoded}, {calc_w}, {calc_h});
      }});
    </script>
    """
    html_page = template.replace("</body>", f"{inject_script}</body>")

    temp_html_path = os.path.join(_RUNNER_DIR, f"__tmp_runner_{int(time.time()*1000)}.html")
    temp_raw_png = os.path.join(_RUNNER_DIR, f"__tmp_raw_{int(time.time()*1000)}.png")

    try:
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_page)

        # 2. Launch headless browser
        cmd = [
            chromium_exe,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--virtual-time-budget=6000",
            "--run-all-compositor-stages-before-draw",
            f"--force-device-scale-factor={scale}",
            f"--window-size={calc_w},{calc_h}",
            f"--screenshot={temp_raw_png}",
            temp_html_path,
        ]

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        if res.returncode != 0:
            raise RuntimeError(f"Browser headless render failed ({res.returncode}): {res.stderr}")

        if not os.path.isfile(temp_raw_png):
            raise FileNotFoundError(f"Headless browser failed to capture image at {temp_raw_png}")

        # 3. Post-process: Auto-crop diagram canvas bounds with white padding
        im = Image.open(temp_raw_png)
        bg = Image.new(im.mode, im.size, (255, 255, 255))
        diff = ImageChops.difference(im, bg)
        bbox = diff.getbbox()

        if bbox:
            # Apply padding
            w, h = im.size
            pad_x = padding * scale
            pad_y = padding * scale
            crop_box = (
                max(0, bbox[0] - pad_x),
                max(0, bbox[1] - pad_y),
                min(w, bbox[2] + pad_x),
                min(h, bbox[3] + pad_y),
            )
            cropped_im = im.crop(crop_box)
            im.close()
            if os.path.exists(output_png_path):
                try:
                    os.remove(output_png_path)
                except Exception:
                    pass
            cropped_im.save(output_png_path)
            final_w, final_h = cropped_im.size
        else:
            if os.path.exists(output_png_path):
                try:
                    os.remove(output_png_path)
                except Exception:
                    pass
            im.save(output_png_path)
            final_w, final_h = im.size
            im.close()

        file_size = os.path.getsize(output_png_path)
        return {
            "png_path": output_png_path,
            "dimensions_px": (final_w, final_h),
            "file_size_bytes": file_size,
            "scale": scale,
        }

    finally:
        # Cleanup temporary files
        for tmp_f in (temp_html_path, temp_raw_png):
            if os.path.isfile(tmp_f):
                try:
                    os.remove(tmp_f)
                except OSError:
                    pass


# ==============================================================================
# HIGH-LEVEL API & PIPELINE INTEGRATION
# ==============================================================================

def render_diagram(
    spec: Dict[str, Any],
    base_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    High-level API for generating mxGraph diagrams, exporting .drawio, and rendering Full HD PNG.

    Args:
        spec: Dictionary containing:
            - mermaid_code: (optional) str Mermaid code
            - xml_content / xml_path: (optional) str raw Draw.io XML
            - spec: (optional) dict with nodes/edges JSON
            - output_path: (optional) str destination PNG path
            - drawio_path: (optional) str destination .drawio path
            - scale: (optional) int, default 2
            - inject_into: (optional) str path to target DOCX
            - caption / placeholder / heading: (optional) injection metadata
        base_dir: Optional root path for resolving relative paths.

    Returns:
        Dictionary containing png_path, drawio_path, dimensions_px, file_size_bytes.
    """
    t0 = time.time()
    scale = spec.get("scale", 2)

    # 1. Resolve output paths
    out_png = spec.get("output_path") or spec.get("out") or "diagram_assets/diagram.png"
    if not os.path.isabs(out_png) and base_dir:
        out_png = os.path.abspath(os.path.join(base_dir, out_png))
    else:
        out_png = os.path.abspath(out_png)

    base_no_ext = os.path.splitext(out_png)[0]
    out_drawio = spec.get("drawio_path") or f"{base_no_ext}.drawio"
    if not os.path.isabs(out_drawio) and base_dir:
        out_drawio = os.path.abspath(os.path.join(base_dir, out_drawio))
    else:
        out_drawio = os.path.abspath(out_drawio)

    # 2. Determine and generate XML
    xml_content = spec.get("xml_content")
    if not xml_content and spec.get("xml_path"):
        xml_f = spec["xml_path"]
        if not os.path.isabs(xml_f) and base_dir:
            xml_f = os.path.join(base_dir, xml_f)
        with open(xml_f, "r", encoding="utf-8") as f:
            xml_content = f.read()

    if not xml_content and spec.get("mermaid_code"):
        entities, relationships = parse_mermaid_erd(spec["mermaid_code"])
        calculate_auto_layout(entities, relationships)
        xml_content = build_mxgraph_model_xml(entities, relationships)

    if not xml_content and "nodes" in spec:
        # JSON Spec compatibility
        entities = {}
        for n in spec["nodes"]:
            cols = [
                ColumnInfo(
                    name=c.get("name", ""),
                    type=c.get("type", "string"),
                    key="PK" if c.get("is_pk") else ("FK" if c.get("is_fk") else ""),
                )
                for c in n.get("columns", [])
            ]
            entities[n["id"]] = EntityInfo(
                name=n.get("label", n["id"]),
                columns=cols,
                x=float(n.get("x", 0.0)),
                y=float(n.get("y", 0.0)),
                width=float(n.get("width", 278.0)),
                height=float(n.get("height", 43.0 * (len(cols) + 1))),
            )
        rels = []
        for e in spec.get("edges", []):
            rels.append(
                RelationshipInfo(
                    source=e["source"],
                    target=e["target"],
                    label=e.get("label", ""),
                )
            )
        if not any(ent.x > 0 or ent.y > 0 for ent in entities.values()):
            calculate_auto_layout(entities, rels)
        xml_content = build_mxgraph_model_xml(entities, rels)

    if not xml_content:
        raise ValueError("Specification must contain 'mermaid_code', 'xml_content', 'xml_path', or 'nodes'.")

    # 3. Dual Export 1: Save .drawio and .xml files
    os.makedirs(os.path.dirname(out_drawio), exist_ok=True)
    with open(out_drawio, "w", encoding="utf-8") as f:
        f.write(xml_content)
    out_xml = f"{os.path.splitext(out_drawio)[0]}.xml"
    with open(out_xml, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # 4. Dual Export 2: Render Full HD PNG via Headless Canvas Runner
    render_meta = render_mxgraph_to_png(xml_content, out_png, scale=scale)

    # 5. Optional DOCX Injection
    injected = False
    docx_target = spec.get("inject_into")
    if docx_target:
        if not os.path.isabs(docx_target) and base_dir:
            docx_target = os.path.abspath(os.path.join(base_dir, docx_target))
        if os.path.isfile(docx_target):
            try:
                from .docx_writer import inject_diagram_into_docx
            except (ImportError, ValueError):
                from docx_writer import inject_diagram_into_docx  # type: ignore
            inject_diagram_into_docx(
                docx_path=docx_target,
                png_path=render_meta["png_path"],
                heading=spec.get("heading") or spec.get("target_heading"),
                placeholder=spec.get("placeholder"),
                caption=spec.get("caption") or spec.get("caption_template"),
                width_cm=spec.get("width_cm", 14.0),
                max_height_cm=spec.get("max_height_cm", 20.0),
            )
            injected = True

    elapsed = time.time() - t0
    return {
        "png_path": render_meta["png_path"],
        "drawio_path": out_drawio,
        "xml_path": out_xml,
        "dimensions_px": render_meta["dimensions_px"],
        "file_size_bytes": render_meta["file_size_bytes"],
        "scale": scale,
        "elapsed_sec": round(elapsed, 2),
        "injected": injected,
    }


# ==============================================================================
# CLI ENTRYPOINT
# ==============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="mxGraph Engine v2.0 — Dual-Core Draw.io & Full HD Canvas Generator."
    )
    parser.add_argument("--input", "-i", required=True, help="Input file path (.mmd, .xml, .drawio, or .json)")
    parser.add_argument("--output", "-o", help="Output PNG path (defaults to same name with .png)")
    parser.add_argument("--drawio", "-d", help="Output .drawio path")
    parser.add_argument("--scale", "-s", type=int, default=2, help="Device scale factor (1=Standard, 2=Full HD, 3=4K)")
    parser.add_argument("--inject", help="Path to DOCX file to inject rendered image into")

    args = parser.parse_args()
    input_path = os.path.abspath(args.input)
    if not os.path.isfile(input_path):
        print(f"[ERROR] Input file not found: {input_path}", file=sys.stderr)
        return 1

    ext = os.path.splitext(input_path)[1].lower()
    spec: Dict[str, Any] = {
        "scale": args.scale,
        "output_path": os.path.abspath(args.output) if args.output else os.path.splitext(input_path)[0] + ".png",
        "drawio_path": os.path.abspath(args.drawio) if args.drawio else None,
        "inject_into": args.inject,
    }

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    if ext in (".mmd", ".mermaid"):
        spec["mermaid_code"] = content
    elif ext in (".xml", ".drawio"):
        spec["xml_content"] = content
    elif ext == ".json":
        json_spec = json.loads(content)
        json_spec.update(spec)
        spec = json_spec
    else:
        # Fallback detection
        if "<mxGraphModel" in content:
            spec["xml_content"] = content
        else:
            spec["mermaid_code"] = content

    try:
        res = render_diagram(spec, base_dir=os.path.dirname(input_path))
        print(f"[OK] mxGraph Engine v2.0 rendered successfully ({res['elapsed_sec']}s):")
        print(f"     Draw.io: {res['drawio_path']}")
        print(f"     PNG HD : {res['png_path']} ({res['dimensions_px'][0]}x{res['dimensions_px'][1]}px)")
        if res.get("injected"):
            print(f"     DOCX   : Injected into {args.inject}")
        return 0
    except Exception as exc:
        print(f"[ERROR] mxGraph render failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
