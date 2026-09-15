"""
spec_diagram_engine.py — Precision Technical & Architecture Diagram Engine.

Designed for DEV/BA technical documentation, system architectures, and mobile screen flows.
Produces pixel-perfect, publication-grade Hub & Spoke and Grid diagrams with:
1. Precise coordinate and port-based placement (top, bottom, left, right).
2. Manhattan orthogonal L-shaped and multi-segment routing with arrowheads.
3. Label masking (pill-shaped white badges) preventing line/text collisions.
4. Visual hierarchy: Primary screens (thick 2.5px), Standard (1.5px), Modals/Toasts (dashed 1.5px).
5. Native SVG generation and headless Chromium/Edge 300+ DPI PNG rendering.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Any, Literal
from PIL import Image

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

PortType = Literal["top", "bottom", "left", "right"]
NodeType = Literal["primary", "standard", "modal", "toast"]


@dataclass
class Node:
    id: str
    label: str
    x: float
    y: float
    width: float
    height: float
    type: NodeType = "standard"
    sublabel: str | None = None

    def get_port(self, port: PortType, offset: float = 0.0) -> tuple[float, float]:
        """Calculate exact coordinate of anchor port on node perimeter."""
        cx = self.x + self.width / 2.0
        cy = self.y + self.height / 2.0
        if port == "top":
            return (cx + offset, self.y)
        elif port == "bottom":
            return (cx + offset, self.y + self.height)
        elif port == "left":
            return (self.x, cy + offset)
        elif port == "right":
            return (self.x + self.width, cy + offset)
        return (cx, cy)


@dataclass
class Edge:
    source_id: str
    target_id: str
    source_port: PortType = "right"
    target_port: PortType = "left"
    source_offset: float = 0.0
    target_offset: float = 0.0
    label: str | None = None
    line_style: Literal["solid", "dashed"] = "solid"
    waypoints: list[tuple[float, float]] = field(default_factory=list)
    label_pos: float = 0.5  # 0.0 to 1.0 along the path
    label_offset_y: float = 0.0
    label_offset_x: float = 0.0


def _find_chromium_executable() -> str | None:
    """Locate Microsoft Edge, Google Chrome, or Puppeteer Chromium for headless rendering."""
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


class PrecisionDiagram:
    """High-precision SVG diagram builder and renderer."""

    def __init__(
        self,
        width: float = 1000,
        height: float = 700,
        font_family: str = "Segoe UI, -apple-system, BlinkMacSystemFont, Arial, sans-serif",
        font_size: float = 12.0,
        bg_color: str = "#ffffff",
    ):
        self.width = width
        self.height = height
        self.font_family = font_family
        self.font_size = font_size
        self.bg_color = bg_color
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []

    def add_node(
        self,
        id: str,
        label: str,
        x: float,
        y: float,
        width: float = 140,
        height: float = 42,
        type: NodeType = "standard",
        sublabel: str | None = None,
    ) -> Node:
        node = Node(id=id, label=label, x=x, y=y, width=width, height=height, type=type, sublabel=sublabel)
        self.nodes[id] = node
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        source_port: PortType = "right",
        target_port: PortType = "left",
        source_offset: float = 0.0,
        target_offset: float = 0.0,
        label: str | None = None,
        line_style: Literal["solid", "dashed"] = "solid",
        waypoints: list[tuple[float, float]] | None = None,
        label_pos: float = 0.5,
        label_offset_y: float = 0.0,
        label_offset_x: float = 0.0,
    ) -> Edge:
        edge = Edge(
            source_id=source_id,
            target_id=target_id,
            source_port=source_port,
            target_port=target_port,
            source_offset=source_offset,
            target_offset=target_offset,
            label=label,
            line_style=line_style,
            waypoints=waypoints or [],
            label_pos=label_pos,
            label_offset_y=label_offset_y,
            label_offset_x=label_offset_x,
        )
        self.edges.append(edge)
        return edge

    def _calculate_manhattan_route(self, edge: Edge) -> list[tuple[float, float]]:
        """Calculate orthogonal path points from source port to target port."""
        s_node = self.nodes[edge.source_id]
        t_node = self.nodes[edge.target_id]

        p_start = s_node.get_port(edge.source_port, edge.source_offset)
        p_end = t_node.get_port(edge.target_port, edge.target_offset)

        if edge.waypoints:
            return [p_start] + edge.waypoints + [p_end]

        sx, sy = p_start
        tx, ty = p_end

        # Automatic orthogonal L-shape or Z-shape routing based on port orientations
        if edge.source_port == "right" and edge.target_port == "left":
            if tx > sx:
                mid_x = (sx + tx) / 2.0
                return [p_start, (mid_x, sy), (mid_x, ty), p_end]
            else:
                # Target is to the left of source -> loop around
                stub_x = sx + 25
                mid_y = max(sy, ty) + 35
                return [p_start, (stub_x, sy), (stub_x, mid_y), (tx - 25, mid_y), (tx - 25, ty), p_end]

        elif edge.source_port == "left" and edge.target_port == "left":
            min_x = min(sx, tx) - 25
            return [p_start, (min_x, sy), (min_x, ty), p_end]

        elif edge.source_port == "right" and edge.target_port == "right":
            max_x = max(sx, tx) + 25
            return [p_start, (max_x, sy), (max_x, ty), p_end]

        elif edge.source_port == "bottom" and edge.target_port == "top":
            mid_y = (sy + ty) / 2.0
            return [p_start, (sx, mid_y), (tx, mid_y), p_end]

        elif edge.source_port == "top" and edge.target_port == "bottom":
            mid_y = (sy + ty) / 2.0
            return [p_start, (sx, mid_y), (tx, mid_y), p_end]

        elif edge.source_port in ("top", "bottom") and edge.target_port in ("left", "right"):
            # L-shape: vertical then horizontal
            return [p_start, (sx, ty), p_end]

        elif edge.source_port in ("left", "right") and edge.target_port in ("top", "bottom"):
            # L-shape: horizontal then vertical
            return [p_start, (tx, sy), p_end]

        return [p_start, (tx, sy), p_end]

    def _get_edge_label_coords(self, edge: Edge, pts: list[tuple[float, float]]) -> tuple[float, float]:
        """Calculate Cartesian coordinates for an edge label along polyline points."""
        total_len = 0.0
        segs: list[tuple[tuple[float, float], tuple[float, float], float]] = []
        for i in range(len(pts) - 1):
            dx = pts[i + 1][0] - pts[i][0]
            dy = pts[i + 1][1] - pts[i][1]
            seg_len = (dx * dx + dy * dy) ** 0.5
            segs.append((pts[i], pts[i + 1], seg_len))
            total_len += seg_len

        target_dist = total_len * edge.label_pos
        accum = 0.0
        lbl_x, lbl_y = pts[0]
        for p1, p2, slen in segs:
            if slen == 0:
                continue
            if accum + slen >= target_dist:
                ratio = (target_dist - accum) / slen
                lbl_x = p1[0] + (p2[0] - p1[0]) * ratio
                lbl_y = p1[1] + (p2[1] - p1[1]) * ratio
                break
            accum += slen

        lbl_x += edge.label_offset_x
        lbl_y += edge.label_offset_y
        return lbl_x, lbl_y

    def check_label_node_collisions(self) -> list[str]:
        """Detect potential bounding-box overlaps between edge labels and node boxes."""
        warnings: list[str] = []
        for edge in self.edges:
            if not edge.label:
                continue
            pts = self._calculate_manhattan_route(edge)
            lbl_x, lbl_y = self._get_edge_label_coords(edge, pts)
            lines = edge.label.replace("<br/>", "\n").split("\n")
            max_chars = max(len(l) for l in lines)
            lbl_w = max_chars * 5.6 + 6.0
            lbl_h = len(lines) * 11.5 + 4.0
            l_min_x = lbl_x - lbl_w / 2.0
            l_max_x = lbl_x + lbl_w / 2.0
            l_min_y = lbl_y - lbl_h / 2.0
            l_max_y = lbl_y + lbl_h / 2.0

            for node in self.nodes.values():
                overlap_x = not (l_max_x <= node.x or node.x + node.width <= l_min_x)
                overlap_y = not (l_max_y <= node.y or node.y + node.height <= l_min_y)
                if overlap_x and overlap_y:
                    warn = (
                        f"[WARN] Label collision detected: edge '{edge.source_id} -> {edge.target_id}' "
                        f"(label={repr(edge.label)}) overlaps node '{node.id}' "
                        f"[Label: X={l_min_x:.1f}..{l_max_x:.1f}, Y={l_min_y:.1f}..{l_max_y:.1f} vs "
                        f"Node: X={node.x:.1f}..{node.x+node.width:.1f}, Y={node.y:.1f}..{node.y+node.height:.1f}]"
                    )
                    warnings.append(warn)
        return warnings

    def to_svg(self) -> str:
        """Generate clean, publication-quality SVG string."""
        svg: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}" style="background-color: {self.bg_color};">'
        ]

        # Defs: Markers for solid and dashed arrowheads
        svg.append("""  <defs>
    <marker id="arrow-solid" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#000000"/>
    </marker>
    <marker id="arrow-dashed" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#333333"/>
    </marker>
    <filter id="badge-shadow" x="-5%" y="-10%" width="110%" height="120%">
      <feDropShadow dx="0" dy="1" stdDeviation="1" flood-color="#000000" flood-opacity="0.08"/>
    </filter>
  </defs>""")

        # 1. Render Edges (lines and arrowheads)
        edge_label_elements: list[str] = []
        svg.append("  <!-- Edges -->")
        for edge in self.edges:
            pts = self._calculate_manhattan_route(edge)
            if len(pts) < 2:
                continue

            path_d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} " + " ".join(
                f"L {p[0]:.1f} {p[1]:.1f}" for p in pts[1:]
            )
            is_dashed = edge.line_style == "dashed"
            dash_attr = ' stroke-dasharray="4,4"' if is_dashed else ""
            marker = 'url(#arrow-dashed)' if is_dashed else 'url(#arrow-solid)'
            stroke_color = "#333333" if is_dashed else "#111111"
            stroke_width = "1.2" if is_dashed else "1.3"

            svg.append(f'  <path d="{path_d}" fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}"{dash_attr} marker-end="{marker}"/>')

            # Calculate edge label position
            if edge.label:
                lbl_x, lbl_y = self._get_edge_label_coords(edge, pts)

                lines = edge.label.replace("<br/>", "\n").split("\n")
                line_height = 11.5
                if len(lines) == 1:
                    escaped_label = html.escape(lines[0], quote=True)
                    edge_label_elements.append(
                        f'    <text x="{lbl_x:.1f}" y="{lbl_y + 3.0:.1f}" font-family="{self.font_family}" '
                        f'font-size="9px" font-weight="500" fill="#222222" text-anchor="middle" '
                        f'stroke="#ffffff" stroke-width="4px" stroke-linejoin="round" paint-order="stroke fill">{escaped_label}</text>'
                    )
                else:
                    start_ly = lbl_y - ((len(lines) - 1) * line_height) / 2.0 + 3.0
                    for l_idx, line in enumerate(lines):
                        ly = start_ly + l_idx * line_height
                        escaped_label = html.escape(line, quote=True)
                        edge_label_elements.append(
                            f'    <text x="{lbl_x:.1f}" y="{ly:.1f}" font-family="{self.font_family}" '
                            f'font-size="9px" font-weight="500" fill="#222222" text-anchor="middle" '
                            f'stroke="#ffffff" stroke-width="4px" stroke-linejoin="round" paint-order="stroke fill">{escaped_label}</text>'
                        )

        # 2. Render Nodes (Render nodes BEFORE edge labels so labels stay on top)
        svg.append("  <!-- Nodes -->")
        for node in self.nodes.values():
            if node.type == "primary":
                stroke_w = "2.5"
                dash_attr = ""
                font_w = "bold"
                fill_color = "#ffffff"
                stroke_color = "#000000"
            elif node.type in ("modal", "toast"):
                stroke_w = "1.5"
                dash_attr = ' stroke-dasharray="4,4"'
                font_w = "normal"
                fill_color = "#ffffff"
                stroke_color = "#222222"
            else:  # standard
                stroke_w = "1.5"
                dash_attr = ""
                font_w = "normal"
                fill_color = "#ffffff"
                stroke_color = "#000000"

            svg.append(
                f'  <g id="node-{node.id}">\n'
                f'    <rect x="{node.x:.1f}" y="{node.y:.1f}" width="{node.width:.1f}" height="{node.height:.1f}" '
                f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="{stroke_w}"{dash_attr} rx="3" filter="url(#badge-shadow)"/>'
            )

            cx = node.x + node.width / 2.0
            cy = node.y + node.height / 2.0

            # Split label lines if contains <br/> or \n
            lines = node.label.replace("<br/>", "\n").split("\n")
            if len(lines) == 1:
                esc_text = html.escape(lines[0], quote=True)
                svg.append(
                    f'    <text x="{cx:.1f}" y="{cy + 4:.1f}" font-family="{self.font_family}" '
                    f'font-size="{self.font_size}px" font-weight="{font_w}" fill="#000000" text-anchor="middle">{esc_text}</text>'
                )
            else:
                line_height = self.font_size * 1.25
                start_y = cy - ((len(lines) - 1) * line_height) / 2.0 + 3.5
                for idx, line in enumerate(lines):
                    ly = start_y + idx * line_height
                    esc_text = html.escape(line, quote=True)
                    svg.append(
                        f'    <text x="{cx:.1f}" y="{ly:.1f}" font-family="{self.font_family}" '
                        f'font-size="{self.font_size}px" font-weight="{font_w}" fill="#000000" text-anchor="middle">{esc_text}</text>'
                    )

            svg.append("  </g>")

        # 3. Render Edge Labels (on top of nodes and edges)
        svg.append("  <!-- Edge Labels -->")
        for el in edge_label_elements:
            svg.append(el)

        svg.append("</svg>")
        return "\n".join(svg)

    @classmethod
    def from_spec(cls, spec: dict[str, Any]) -> PrecisionDiagram:
        """Construct PrecisionDiagram from declarative specification dictionary."""
        diag = cls(
            width=spec.get("width", 1000),
            height=spec.get("height", 700),
            font_family=spec.get("font_family", "Segoe UI, -apple-system, BlinkMacSystemFont, Arial, sans-serif"),
            font_size=spec.get("font_size", 11.5),
            bg_color=spec.get("bg_color", "#ffffff"),
        )
        for n in spec.get("nodes", []):
            diag.add_node(
                id=n["id"],
                label=n["label"],
                x=n["x"],
                y=n["y"],
                width=n.get("width", 140),
                height=n.get("height", 42),
                type=n.get("type", "standard"),
                sublabel=n.get("sublabel"),
            )
        for e in spec.get("edges", []):
            waypoints = [tuple(w) for w in e.get("waypoints", [])]
            diag.add_edge(
                source_id=e["source"],
                target_id=e["target"],
                source_port=e.get("source_port", "right"),
                target_port=e.get("target_port", "left"),
                source_offset=e.get("source_offset", 0.0),
                target_offset=e.get("target_offset", 0.0),
                label=e.get("label"),
                line_style=e.get("line_style", "solid"),
                waypoints=waypoints,
                label_pos=e.get("label_pos", 0.5),
                label_offset_y=e.get("label_offset_y", 0.0),
                label_offset_x=e.get("label_offset_x", 0.0),
            )
        return diag

    def to_spec(self) -> dict[str, Any]:
        """Serialize diagram to dictionary specification."""
        return {
            "width": self.width,
            "height": self.height,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "bg_color": self.bg_color,
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "x": n.x,
                    "y": n.y,
                    "width": n.width,
                    "height": n.height,
                    "type": n.type,
                    "sublabel": n.sublabel,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "source_port": e.source_port,
                    "target_port": e.target_port,
                    "source_offset": e.source_offset,
                    "target_offset": e.target_offset,
                    "label": e.label,
                    "line_style": e.line_style,
                    "waypoints": [list(w) for w in e.waypoints],
                    "label_pos": e.label_pos,
                    "label_offset_y": e.label_offset_y,
                    "label_offset_x": e.label_offset_x,
                }
                for e in self.edges
            ],
        }

    def render_to_png(self, output_png_path: str, scale: int = 3) -> dict[str, Any]:
        """
        Render the diagram to high-resolution PNG using native Chromium/Edge headless.
        Returns execution metadata dictionary.
        """
        output_png_path = os.path.abspath(output_png_path)
        out_dir = os.path.dirname(output_png_path)
        os.makedirs(out_dir, exist_ok=True)

        # Write SVG
        svg_content = self.to_svg()
        svg_path = os.path.splitext(output_png_path)[0] + ".svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        chromium_exe = _find_chromium_executable()
        if not chromium_exe:
            raise EnvironmentError("No Chromium browser (msedge.exe or chrome.exe) found on system.")

        cmd = [
            chromium_exe,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--force-device-scale-factor={scale}",
            f"--window-size={int(self.width)},{int(self.height)}",
            f"--screenshot={output_png_path}",
            svg_path,
        ]

        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode != 0:
            raise RuntimeError(f"Chromium headless rendering failed with code {res.returncode}: {res.stderr}")

        if not os.path.isfile(output_png_path):
            raise FileNotFoundError(f"Rendered PNG was not generated at {output_png_path}")

        # Measure dimensions
        with Image.open(output_png_path) as img:
            w_px, h_px = img.size

        file_size = os.path.getsize(output_png_path)

        return {
            "success": True,
            "svg_path": svg_path,
            "png_path": output_png_path,
            "dimensions_px": (w_px, h_px),
            "file_size_bytes": file_size,
            "aspect_ratio": round(w_px / h_px, 2),
            "scale": scale,
        }

    @classmethod
    def from_json_spec(cls, spec_path: str) -> PrecisionDiagram:
        """
        Load a diagram definition from a declarative JSON specification file.
        Validates node existence for all edges and checks for AABB collisions.
        """
        if not os.path.isfile(spec_path):
            raise FileNotFoundError(f"Spec file not found: {spec_path}")

        with open(spec_path, "r", encoding="utf-8") as f:
            spec = json.load(f)

        diag = cls(
            width=spec.get("width", 1200),
            height=spec.get("height", 700),
            font_family=spec.get("font_family", "Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif"),
            font_size=spec.get("font_size", 11.0),
            bg_color=spec.get("bg_color", "#ffffff"),
        )

        for n in spec.get("nodes", []):
            diag.add_node(
                id=n["id"],
                label=n["label"],
                x=float(n["x"]),
                y=float(n["y"]),
                width=float(n.get("width", 140)),
                height=float(n.get("height", 42)),
                type=n.get("type", "standard"),
                sublabel=n.get("sublabel"),
            )

        # Collision detection (AABB overlap warning)
        nodes_list = list(diag.nodes.values())
        for i in range(len(nodes_list)):
            n1 = nodes_list[i]
            for j in range(i + 1, len(nodes_list)):
                n2 = nodes_list[j]
                overlap_x = not (n1.x + n1.width <= n2.x or n2.x + n2.width <= n1.x)
                overlap_y = not (n1.y + n1.height <= n2.y or n2.y + n2.height <= n1.y)
                if overlap_x and overlap_y:
                    print(
                        f"[WARN] AABB collision detected between node '{n1.id}' (x={n1.x}, y={n1.y}, w={n1.width}, h={n1.height}) "
                        f"and node '{n2.id}' (x={n2.x}, y={n2.y}, w={n2.width}, h={n2.height})"
                    )

        for e in spec.get("edges", []):
            src = e["source"]
            tgt = e["target"]
            if src not in diag.nodes:
                raise ValueError(f"Edge source '{src}' does not exist in diagram nodes.")
            if tgt not in diag.nodes:
                raise ValueError(f"Edge target '{tgt}' does not exist in diagram nodes.")

            raw_waypoints = e.get("waypoints", [])
            waypoints = [(float(pt[0]), float(pt[1])) for pt in raw_waypoints]

            diag.add_edge(
                source_id=src,
                target_id=tgt,
                source_port=e.get("source_port", "right"),
                target_port=e.get("target_port", "left"),
                source_offset=float(e.get("source_offset", 0.0)),
                target_offset=float(e.get("target_offset", 0.0)),
                label=e.get("label"),
                line_style=e.get("line_style", "solid"),
                waypoints=waypoints,
                label_pos=float(e.get("label_pos", 0.5)),
                label_offset_y=float(e.get("label_offset_y", 0.0)),
                label_offset_x=float(e.get("label_offset_x", 0.0)),
            )

        # Label-to-Node Collision Detection
        label_warnings = diag.check_label_node_collisions()
        for warn in label_warnings:
            print(warn)

        return diag


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Precision Technical Diagram Engine CLI")
    parser.add_argument("--spec", type=str, required=True, help="Path to diagram JSON spec file")
    parser.add_argument("--out", type=str, required=True, help="Path to output rendered PNG file")
    parser.add_argument("--scale", type=int, default=3, help="Render scale factor (default: 3 for 300+ DPI)")

    args = parser.parse_args()

    print(f"Loading diagram specification from: {args.spec}")
    diagram = PrecisionDiagram.from_json_spec(args.spec)
    print(f"Loaded {len(diagram.nodes)} nodes and {len(diagram.edges)} edges.")
    print(f"Rendering to PNG at scale={args.scale}...")
    result = diagram.render_to_png(args.out, scale=args.scale)
    print(f"Render complete: {result['png_path']} ({result['dimensions_px'][0]}x{result['dimensions_px'][1]}px, {result['file_size_bytes']} bytes)")
