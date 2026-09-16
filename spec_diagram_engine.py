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
NodeType = Literal["primary", "standard", "modal", "toast", "table"]


@dataclass
class ColumnDef:
    name: str
    type: str = "string"
    is_pk: bool = False
    is_fk: bool = False
    is_nullable: bool = False


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
    columns: list[ColumnDef] | None = None
    header_bg: str = "#F1F5F9"

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
class ClusterDef:
    id: str
    title: str
    x: float
    y: float
    width: float
    height: float
    bg_color: str = "#F8FAFC"
    border_color: str = "#E2E8F0"
    title_color: str = "#475569"


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
    cardinality_source: str | None = None
    cardinality_target: str | None = None
    cardinality_style: Literal["crow_foot", "arrow_text"] = "crow_foot"
    corner_radius: float = 8.0



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


def _points_to_rounded_path(pts: list[tuple[float, float]], radius: float = 8.0) -> str:
    """Generate SVG path d attribute with smooth quadratic bezier rounded corners."""
    if len(pts) < 2:
        return ""
    if len(pts) == 2 or radius <= 0:
        return f"M {pts[0][0]:.1f} {pts[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts[1:])

    cmds = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(1, len(pts) - 1):
        p_prev = pts[i - 1]
        p_curr = pts[i]
        p_next = pts[i + 1]

        v1_x = p_curr[0] - p_prev[0]
        v1_y = p_curr[1] - p_prev[1]
        l1 = (v1_x * v1_x + v1_y * v1_y) ** 0.5

        v2_x = p_next[0] - p_curr[0]
        v2_y = p_next[1] - p_curr[1]
        l2 = (v2_x * v2_x + v2_y * v2_y) ** 0.5

        if l1 == 0 or l2 == 0:
            cmds.append(f"L {p_curr[0]:.1f} {p_curr[1]:.1f}")
            continue

        r = min(radius, l1 / 2.0, l2 / 2.0)
        c1_x = p_curr[0] - (v1_x / l1) * r
        c1_y = p_curr[1] - (v1_y / l1) * r
        c2_x = p_curr[0] + (v2_x / l2) * r
        c2_y = p_curr[1] + (v2_y / l2) * r

        cmds.append(f"L {c1_x:.1f} {c1_y:.1f}")
        cmds.append(f"Q {p_curr[0]:.1f} {p_curr[1]:.1f} {c2_x:.1f} {c2_y:.1f}")

    cmds.append(f"L {pts[-1][0]:.1f} {pts[-1][1]:.1f}")
    return " ".join(cmds)


def render_cardinality_symbol(
    p: tuple[float, float],
    direction: tuple[float, float],
    card_type: str,
    style: str = "crow_foot",
    font_family: str = "Segoe UI, sans-serif",
) -> str:
    """
    Render exact ERD standard cardinality symbols (Crow's Foot notation) at endpoint p.
    direction: (ux, uy) unit vector pointing AWAY from node into the line.
    """
    px, py = p
    ux, uy = direction
    nx, ny = -uy, ux  # perpendicular normal

    norm = (ux * ux + uy * uy) ** 0.5
    if norm > 0:
        ux, uy = ux / norm, uy / norm
        nx, ny = -uy, ux

    if style == "arrow_text":
        bx = px + ux * 16.0
        by = py + uy * 16.0
        text = str(card_type)
        return (
            f'    <rect x="{bx - 12.0:.1f}" y="{by - 8.0:.1f}" width="24" height="16" rx="3" '
            f'fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.2"/>\n'
            f'    <text x="{bx:.1f}" y="{by + 4.0:.1f}" font-family="{font_family}" font-size="9px" '
            f'font-weight="bold" fill="#0F172A" text-anchor="middle">{html.escape(text)}</text>'
        )

    svg: list[str] = []
    w = 7.0
    stroke_c = "#1E293B"
    stroke_w = "2.0"
    c_type = str(card_type).strip().lower()

    # 1. One: Single vertical tick perpendicular to line near entity
    if c_type in ("one", "1", "+"):
        d = 10.0
        cx, cy = px + ux * d, py + uy * d
        svg.append(f'    <line x1="{cx + nx*w:.1f}" y1="{cy + ny*w:.1f}" x2="{cx - nx*w:.1f}" y2="{cy - ny*w:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')

    # 2. Many: Crow's foot with 3 branches flaring out towards entity
    elif c_type in ("many", "*", "}", ">"):
        d_apex = 15.0
        d_end = 2.0
        ax, ay = px + ux * d_apex, py + uy * d_apex
        e1x, e1y = px + ux * d_end + nx * w, py + uy * d_end + ny * w
        e2x, e2y = px + ux * d_end - nx * w, py + uy * d_end - ny * w
        svg.append(f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e1x:.1f}" y2="{e1y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        svg.append(f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e2x:.1f}" y2="{e2y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')

    # 3. One (and only one): Two parallel ticks perpendicular to line (||)
    elif c_type in ("one_and_only_one", "exact_one", "1..1", "||"):
        for d in (7.0, 15.0):
            cx, cy = px + ux * d, py + uy * d
            svg.append(f'    <line x1="{cx + nx*w:.1f}" y1="{cy + ny*w:.1f}" x2="{cx - nx*w:.1f}" y2="{cy - ny*w:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')

    # 4. Zero or one: Circle followed by vertical tick closer to entity (O|)
    elif c_type in ("zero_or_one", "0..1", "o|", "0|"):
        cx, cy = px + ux * 8.0, py + uy * 8.0
        svg.append(f'    <line x1="{cx + nx*w:.1f}" y1="{cy + ny*w:.1f}" x2="{cx - nx*w:.1f}" y2="{cy - ny*w:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        ox, oy = px + ux * 18.0, py + uy * 18.0
        svg.append(f'    <circle cx="{ox:.1f}" cy="{oy:.1f}" r="4.8" fill="#FFFFFF" stroke="{stroke_c}" stroke-width="{stroke_w}"/>')

    # 5. One or many: Vertical tick followed by crow's foot flaring to entity (|{ or >|)
    elif c_type in ("one_or_many", "1..*", "}|", ">|", "|<", "|{"):
        d_apex = 13.0
        d_end = 2.0
        ax, ay = px + ux * d_apex, py + uy * d_apex
        e1x, e1y = px + ux * d_end + nx * w, py + uy * d_end + ny * w
        e2x, e2y = px + ux * d_end - nx * w, py + uy * d_end - ny * w
        svg.append(f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e1x:.1f}" y2="{e1y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        svg.append(f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e2x:.1f}" y2="{e2y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        cx, cy = px + ux * 20.0, py + uy * 20.0
        svg.append(f'    <line x1="{cx + nx*w:.1f}" y1="{cy + ny*w:.1f}" x2="{cx - nx*w:.1f}" y2="{cy - ny*w:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')

    # 6. Zero or many: Circle followed by crow's foot flaring to entity (O{)
    elif c_type in ("zero_or_many", "0..*", "o{", "0{", "o}", "0}", "{"):
        d_apex = 13.0
        d_end = 2.0
        ax, ay = px + ux * d_apex, py + uy * d_apex
        e1x, e1y = px + ux * d_end + nx * w, py + uy * d_end + ny * w
        e2x, e2y = px + ux * d_end - nx * w, py + uy * d_end - ny * w
        svg.append(f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e1x:.1f}" y2="{e1y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        svg.append(f'    <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{e2x:.1f}" y2="{e2y:.1f}" stroke="{stroke_c}" stroke-width="{stroke_w}" stroke-linecap="round"/>')
        ox, oy = px + ux * 21.0, py + uy * 21.0
        svg.append(f'    <circle cx="{ox:.1f}" cy="{oy:.1f}" r="4.8" fill="#FFFFFF" stroke="{stroke_c}" stroke-width="{stroke_w}"/>')

    return "\n".join(svg)


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
        self.clusters: list[ClusterDef] = []

    def add_cluster(
        self,
        id: str,
        title: str,
        x: float,
        y: float,
        width: float,
        height: float,
        bg_color: str = "#F8FAFC",
        border_color: str = "#E2E8F0",
        title_color: str = "#475569",
    ) -> ClusterDef:
        c = ClusterDef(
            id=id,
            title=title,
            x=x,
            y=y,
            width=width,
            height=height,
            bg_color=bg_color,
            border_color=border_color,
            title_color=title_color,
        )
        self.clusters.append(c)
        return c

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
        columns: list[ColumnDef] | None = None,
        header_bg: str = "#F1F5F9",
    ) -> Node:
        # If ERD table with columns, ensure sufficient height if not overridden
        if columns and height <= 42:
            height = 36.0 + len(columns) * 24.0 + 10.0
        node = Node(
            id=id,
            label=label,
            x=x,
            y=y,
            width=width,
            height=height,
            type=type,
            sublabel=sublabel,
            columns=columns,
            header_bg=header_bg,
        )
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
        cardinality_source: str | None = None,
        cardinality_target: str | None = None,
        cardinality_style: Literal["crow_foot", "arrow_text"] = "crow_foot",
        corner_radius: float = 8.0,
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
            cardinality_source=cardinality_source,
            cardinality_target=cardinality_target,
            cardinality_style=cardinality_style,
            corner_radius=corner_radius,
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

        # 0. Render Cluster Panels (background boundary pillows with category titles)
        if self.clusters:
            svg.append("  <!-- Cluster Panels -->")
            for c in self.clusters:
                svg.append(f'  <g id="cluster-{c.id}">')
                svg.append(
                    f'    <rect x="{c.x:.1f}" y="{c.y:.1f}" width="{c.width:.1f}" height="{c.height:.1f}" '
                    f'fill="{c.bg_color}" stroke="{c.border_color}" stroke-width="1.8" stroke-dasharray="6,4" rx="12"/>'
                )
                esc_title = html.escape(c.title, quote=True)
                pill_w = len(c.title) * 8.0 + 26.0
                svg.append(
                    f'    <rect x="{c.x + 18.0:.1f}" y="{c.y - 13.0:.1f}" width="{pill_w:.1f}" height="24" '
                    f'rx="5" fill="{c.border_color}" stroke="{c.bg_color}" stroke-width="1"/>'
                )
                svg.append(
                    f'    <text x="{c.x + 31.0:.1f}" y="{c.y + 3.5:.1f}" font-family="{self.font_family}" '
                    f'font-size="11.5px" font-weight="bold" fill="{c.title_color}">{esc_title}</text>'
                )
                svg.append('  </g>')

        # 1. Render Edges (lines and arrowheads)
        edge_label_elements: list[str] = []
        cardinality_elements: list[str] = []
        svg.append("  <!-- Edges -->")
        for edge in self.edges:
            pts = self._calculate_manhattan_route(edge)
            if len(pts) < 2:
                continue

            path_d = _points_to_rounded_path(pts, radius=edge.corner_radius)
            is_dashed = edge.line_style == "dashed"
            dash_attr = ' stroke-dasharray="4,4"' if is_dashed else ""

            has_card_end = bool(edge.cardinality_target)
            has_card_start = bool(edge.cardinality_source)

            if has_card_end and edge.cardinality_style == "crow_foot":
                marker_attr = ""
            else:
                marker = 'url(#arrow-dashed)' if is_dashed else 'url(#arrow-solid)'
                marker_attr = f' marker-end="{marker}"'

            stroke_color = "#333333" if is_dashed else "#1E293B"
            stroke_width = "1.2" if is_dashed else "1.8"

            svg.append(f'  <path d="{path_d}" fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}"{dash_attr}{marker_attr} stroke-linejoin="round"/>')

            # Render cardinalities at endpoints
            if has_card_start:
                dx0 = pts[1][0] - pts[0][0]
                dy0 = pts[1][1] - pts[0][1]
                l0 = (dx0 * dx0 + dy0 * dy0) ** 0.5
                u0 = (dx0 / l0, dy0 / l0) if l0 > 0 else (1.0, 0.0)
                card_svg = render_cardinality_symbol(
                    pts[0], u0, edge.cardinality_source, edge.cardinality_style, self.font_family
                )
                cardinality_elements.append(card_svg)

            if has_card_end:
                dx1 = pts[-1][0] - pts[-2][0]
                dy1 = pts[-1][1] - pts[-2][1]
                l1 = (dx1 * dx1 + dy1 * dy1) ** 0.5
                u1 = (-dx1 / l1, -dy1 / l1) if l1 > 0 else (-1.0, 0.0)
                card_svg = render_cardinality_symbol(
                    pts[-1], u1, edge.cardinality_target, edge.cardinality_style, self.font_family
                )
                cardinality_elements.append(card_svg)

            # Calculate edge label position (with solid white pill badge)
            if edge.label:
                lbl_x, lbl_y = self._get_edge_label_coords(edge, pts)

                lines = edge.label.replace("<br/>", "\n").split("\n")
                line_height = 12.0
                max_chars = max(len(l) for l in lines)
                badge_w = max_chars * 6.5 + 16.0
                badge_h = len(lines) * line_height + 8.0
                badge_x = lbl_x - badge_w / 2.0
                badge_y = lbl_y - badge_h / 2.0

                edge_label_elements.append(
                    f'    <rect x="{badge_x:.1f}" y="{badge_y:.1f}" width="{badge_w:.1f}" height="{badge_h:.1f}" '
                    f'rx="4" ry="4" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.2" filter="url(#badge-shadow)"/>'
                )

                if len(lines) == 1:
                    escaped_label = html.escape(lines[0], quote=True)
                    edge_label_elements.append(
                        f'    <text x="{lbl_x:.1f}" y="{lbl_y + 3.8:.1f}" font-family="{self.font_family}" '
                        f'font-size="9.5px" font-weight="600" fill="#1E293B" text-anchor="middle">{escaped_label}</text>'
                    )
                else:
                    start_ly = lbl_y - ((len(lines) - 1) * line_height) / 2.0 + 3.8
                    for l_idx, line in enumerate(lines):
                        ly = start_ly + l_idx * line_height
                        escaped_label = html.escape(line, quote=True)
                        edge_label_elements.append(
                            f'    <text x="{lbl_x:.1f}" y="{ly:.1f}" font-family="{self.font_family}" '
                            f'font-size="9.5px" font-weight="600" fill="#1E293B" text-anchor="middle">{escaped_label}</text>'
                        )

        # 2. Render Nodes
        svg.append("  <!-- Nodes -->")
        for node in self.nodes.values():
            if node.columns:
                # Professional ERD Table Entity Rendering
                header_h = 36.0
                row_h = 24.0
                total_h = max(node.height, header_h + len(node.columns) * row_h + 10.0)
                header_bg = node.header_bg or "#F1F5F9"
                esc_title = html.escape(node.label, quote=True)

                svg.append(f'  <g id="node-{node.id}">')
                # Outer table box
                svg.append(
                    f'    <rect x="{node.x:.1f}" y="{node.y:.1f}" width="{node.width:.1f}" height="{total_h:.1f}" '
                    f'fill="#FFFFFF" stroke="#1E293B" stroke-width="1.8" rx="5" filter="url(#badge-shadow)"/>'
                )
                # Header with rounded top corners
                svg.append(
                    f'    <path d="M {node.x:.1f} {node.y+5.0:.1f} A 5 5 0 0 1 {node.x+5.0:.1f} {node.y:.1f} '
                    f'L {node.x+node.width-5.0:.1f} {node.y:.1f} A 5 5 0 0 1 {node.x+node.width:.1f} {node.y+5.0:.1f} '
                    f'L {node.x+node.width:.1f} {node.y+header_h:.1f} L {node.x:.1f} {node.y+header_h:.1f} Z" fill="{header_bg}"/>'
                )
                # Header divider line
                svg.append(
                    f'    <line x1="{node.x:.1f}" y1="{node.y+header_h:.1f}" x2="{node.x+node.width:.1f}" y2="{node.y+header_h:.1f}" '
                    f'stroke="#1E293B" stroke-width="1.5"/>'
                )
                # Header table name
                svg.append(
                    f'    <text x="{node.x + node.width/2.0:.1f}" y="{node.y + 23.0:.1f}" font-family="{self.font_family}" '
                    f'font-size="13px" font-weight="bold" fill="#0F172A" text-anchor="middle">{esc_title}</text>'
                )

                # Column rows
                for col_idx, col in enumerate(node.columns):
                    ry = node.y + header_h + 8.0 + col_idx * row_h

                    # Nullability bullet
                    if not col.is_nullable:
                        svg.append(f'    <circle cx="{node.x + 14.0:.1f}" cy="{ry + 5.5:.1f}" r="3.5" fill="#0F172A"/>')
                    else:
                        svg.append(f'    <circle cx="{node.x + 14.0:.1f}" cy="{ry + 5.5:.1f}" r="3.5" fill="none" stroke="#94A3B8" stroke-width="1.5"/>')

                    # Key / FK indicator
                    key_offset = 26.0
                    if col.is_pk:
                        # Golden vector key
                        svg.append(
                            f'    <g transform="translate({node.x + key_offset:.1f}, {ry - 1.0:.1f}) scale(0.75)">'
                            f'<path d="M 7 1 C 4.8 1 3 2.8 3 5 C 3 6.1 3.5 7.1 4.2 7.8 L 0 12 L 0 15 L 3 15 L 3 13 L 5 13 L 5 11 L 6.2 11 C 6.5 11 6.7 10.9 6.8 10.8 L 7.8 9.8 C 8.5 10.5 9.5 11 10.6 11 C 12.8 11 14.6 9.2 14.6 7 C 14.6 4.8 12.8 3 10.6 3 Z" fill="#D97706"/>'
                            f'</g>'
                        )
                        name_x = node.x + key_offset + 18.0
                    elif col.is_fk:
                        svg.append(
                            f'    <text x="{node.x + key_offset:.1f}" y="{ry + 10.0:.1f}" font-family="{self.font_family}" '
                            f'font-size="9px" font-weight="bold" fill="#2563EB">FK</text>'
                        )
                        name_x = node.x + key_offset + 18.0
                    else:
                        name_x = node.x + key_offset

                    # Column Name
                    font_w = "bold" if col.is_pk else "normal"
                    esc_name = html.escape(col.name, quote=True)
                    svg.append(
                        f'    <text x="{name_x:.1f}" y="{ry + 10.0:.1f}" font-family="{self.font_family}" '
                        f'font-size="11.5px" font-weight="{font_w}" fill="#0F172A">{esc_name}</text>'
                    )

                    # Column Type (right-aligned)
                    esc_type = html.escape(col.type, quote=True)
                    svg.append(
                        f'    <text x="{node.x + node.width - 12.0:.1f}" y="{ry + 10.0:.1f}" font-family="{self.font_family}" '
                        f'font-size="10.5px" font-style="italic" fill="#64748B" text-anchor="end">{esc_type}</text>'
                    )

                svg.append("  </g>")

            else:
                # Standard Screen Flow / Node Rendering
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

        # 3. Render Cardinality Markers
        if cardinality_elements:
            svg.append("  <!-- Cardinality Markers -->")
            for cm in cardinality_elements:
                svg.append(cm)

        # 4. Render Edge Labels (on top of nodes and edges)
        if edge_label_elements:
            svg.append("  <!-- Edge Labels -->")
            for el in edge_label_elements:
                svg.append(el)

        svg.append("</svg>")
        return "\n".join(svg)

    @classmethod
    def from_spec(cls, spec: dict[str, Any], base_dir: str | None = None) -> PrecisionDiagram:
        """Construct PrecisionDiagram from declarative specification dictionary."""
        diag = cls(
            width=spec.get("width", 1000),
            height=spec.get("height", 700),
            font_family=spec.get("font_family", "Segoe UI, -apple-system, BlinkMacSystemFont, Arial, sans-serif"),
            font_size=spec.get("font_size", 11.5),
            bg_color=spec.get("bg_color", "#ffffff"),
        )

        for c in spec.get("clusters", []):
            diag.add_cluster(
                id=c["id"],
                title=c["title"],
                x=float(c["x"]),
                y=float(c["y"]),
                width=float(c["width"]),
                height=float(c["height"]),
                bg_color=c.get("bg_color", "#F8FAFC"),
                border_color=c.get("border_color", "#E2E8F0"),
                title_color=c.get("title_color", "#475569"),
            )

        for n in spec.get("nodes", []):
            columns = None
            if "columns" in n and n["columns"]:
                columns = [
                    ColumnDef(
                        name=c["name"],
                        type=c.get("type", "string"),
                        is_pk=c.get("is_pk", False),
                        is_fk=c.get("is_fk", False),
                        is_nullable=c.get("is_nullable", False),
                    )
                    for c in n["columns"]
                ]
            def_w = 260.0 if columns else 140.0
            def_h = (36.0 + len(columns) * 24.0 + 10.0) if columns else 42.0
            diag.add_node(
                id=n["id"],
                label=n["label"],
                x=float(n["x"]),
                y=float(n["y"]),
                width=float(n.get("width", def_w)),
                height=float(n.get("height", def_h)),
                type=n.get("type", "table" if columns else "standard"),
                sublabel=n.get("sublabel"),
                columns=columns,
                header_bg=n.get("header_bg", "#F1F5F9"),
            )

        edges_list = spec.get("edges") or spec.get("connections", [])
        conn_ref = spec.get("connections_file") or (edges_list if isinstance(edges_list, str) else None)
        if conn_ref:
            conn_path = conn_ref
            candidates = [
                conn_path,
                os.path.join(base_dir, conn_path) if base_dir else "",
                os.path.join(base_dir, os.path.basename(conn_path)) if base_dir else "",
            ]
            found = False
            for cand in candidates:
                if cand and os.path.isfile(cand):
                    with open(cand, "r", encoding="utf-8") as f:
                        cdata = json.load(f)
                        edges_list = cdata.get("connections") or cdata.get("edges") or (cdata if isinstance(cdata, list) else [])
                    found = True
                    break
            if not found:
                print(f"[WARN] connections_file '{conn_ref}' could not be resolved from base_dir='{base_dir}'.")

        for e in edges_list:
            waypoints = [(float(w[0]), float(w[1])) for w in e.get("waypoints", [])]
            diag.add_edge(
                source_id=e["source"],
                target_id=e["target"],
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
                cardinality_source=e.get("cardinality_source"),
                cardinality_target=e.get("cardinality_target"),
                cardinality_style=e.get("cardinality_style", "crow_foot"),
                corner_radius=float(e.get("corner_radius", 8.0)),
            )
        return diag

    def to_spec(self) -> dict[str, Any]:
        """Serialize diagram to dictionary specification."""
        nodes_data = []
        for n in self.nodes.values():
            item = {
                "id": n.id,
                "label": n.label,
                "x": n.x,
                "y": n.y,
                "width": n.width,
                "height": n.height,
                "type": n.type,
                "sublabel": n.sublabel,
            }
            if n.columns:
                item["columns"] = [
                    {
                        "name": c.name,
                        "type": c.type,
                        "is_pk": c.is_pk,
                        "is_fk": c.is_fk,
                        "is_nullable": c.is_nullable,
                    }
                    for c in n.columns
                ]
                item["header_bg"] = n.header_bg
            nodes_data.append(item)

        edges_data = []
        for e in self.edges:
            edge_dict = {
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
            if e.cardinality_source:
                edge_dict["cardinality_source"] = e.cardinality_source
            if e.cardinality_target:
                edge_dict["cardinality_target"] = e.cardinality_target
            if e.cardinality_style != "crow_foot":
                edge_dict["cardinality_style"] = e.cardinality_style
            edges_data.append(edge_dict)

        return {
            "width": self.width,
            "height": self.height,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "bg_color": self.bg_color,
            "nodes": nodes_data,
            "edges": edges_data,
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

        diag = cls.from_spec(spec, base_dir=os.path.dirname(os.path.abspath(spec_path)))

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
