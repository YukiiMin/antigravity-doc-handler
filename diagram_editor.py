"""
diagram_editor.py — Standalone Interactive Canvas Editor for JSON Spec Diagrams.

Provides DEV/BA and engineers with a visual two-way canvas editor for technical flow diagrams:
- Single Source of Truth: JSON spec file.
- Real-time visual manipulation: Drag & Drop nodes, modify labels, connect ports, adjust routing.
- High-fidelity rendering: 100% consistent with spec_diagram_engine.py.
- Export to 300+ DPI publication-ready PNG (Chromium/Edge headless).
- Full Undo/Redo (30-step deep snapshot history).

Addresses Tkinter technical pitfalls:
1. Anti-flicker drag: Uses Tkinter canvas tags and moves only dragging items and incident edges.
2. Space pan focus guard: Only triggers pan when canvas widget has keyboard focus.
3. Edge hit-testing: Uses canvas.find_overlapping bounding box around cursor.
4. Node ID collision guard: Strict duplicate ID validation before updating references.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Literal, Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Attempt relative or absolute import of spec_diagram_engine
try:
    from .spec_diagram_engine import Edge, Node, NodeType, PortType, PrecisionDiagram
except (ImportError, ValueError):
    from spec_diagram_engine import Edge, Node, NodeType, PortType, PrecisionDiagram  # type: ignore


# ==============================================================================
# PHASE 1: DATA MODEL & DIAGRAM STATE
# ==============================================================================

class DiagramState:
    """
    Data model and state manager for the interactive diagram editor.
    Maintains nodes, edges, canvas metadata, undo/redo stack, and dirty tracking.
    """

    MAX_HISTORY = 30

    def __init__(self, spec_path: str | None = None) -> None:
        self.spec_path: str | None = spec_path
        self.width: float = 1200.0
        self.height: float = 750.0
        self.font_family: str = "Segoe UI, -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif"
        self.font_size: float = 11.5
        self.bg_color: str = "#ffffff"

        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []

        self.is_dirty: bool = False
        self._history: list[dict[str, Any]] = []
        self._future: list[dict[str, Any]] = []

        if spec_path and os.path.isfile(spec_path):
            self.load_from_json(spec_path)

    # --------------------------------------------------------------------------
    # Snapshot & Undo / Redo
    # --------------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize current state to spec dictionary conforming strictly to engine schema."""
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
                    "x": round(n.x, 1),
                    "y": round(n.y, 1),
                    "width": round(n.width, 1),
                    "height": round(n.height, 1),
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
                    "source_offset": round(e.source_offset, 1),
                    "target_offset": round(e.target_offset, 1),
                    "label": e.label,
                    "line_style": e.line_style,
                    "waypoints": [list(w) for w in e.waypoints],
                    "label_pos": round(e.label_pos, 2),
                    "label_offset_y": round(e.label_offset_y, 1),
                    "label_offset_x": round(e.label_offset_x, 1),
                }
                for e in self.edges
            ],
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        """Hydrate diagram state from dictionary."""
        self.width = float(data.get("width", 1200.0))
        self.height = float(data.get("height", 750.0))
        self.font_family = data.get("font_family", self.font_family)
        self.font_size = float(data.get("font_size", 11.5))
        self.bg_color = data.get("bg_color", "#ffffff")

        self.nodes.clear()
        for nd in data.get("nodes", []):
            node = Node(
                id=str(nd["id"]),
                label=str(nd["label"]),
                x=float(nd["x"]),
                y=float(nd["y"]),
                width=float(nd.get("width", 140.0)),
                height=float(nd.get("height", 42.0)),
                type=nd.get("type", "standard"),
                sublabel=nd.get("sublabel"),
            )
            self.nodes[node.id] = node

        self.edges.clear()
        for ed in data.get("edges", []):
            waypoints = [tuple(w) for w in ed.get("waypoints", [])]
            edge = Edge(
                source_id=str(ed["source"]),
                target_id=str(ed["target"]),
                source_port=ed.get("source_port", "right"),
                target_port=ed.get("target_port", "left"),
                source_offset=float(ed.get("source_offset", 0.0)),
                target_offset=float(ed.get("target_offset", 0.0)),
                label=ed.get("label"),
                line_style=ed.get("line_style", "solid"),
                waypoints=waypoints,
                label_pos=float(ed.get("label_pos", 0.5)),
                label_offset_y=float(ed.get("label_offset_y", 0.0)),
                label_offset_x=float(ed.get("label_offset_x", 0.0)),
            )
            self.edges.append(edge)

    def push_snapshot(self) -> None:
        """Capture deep snapshot for undo stack before making modifications."""
        snap = copy.deepcopy(self.to_dict())
        self._history.append(snap)
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop(0)
        self._future.clear()
        self.is_dirty = True

    def undo(self) -> bool:
        """Restore state to previous snapshot."""
        if not self._history:
            return False
        current_state = copy.deepcopy(self.to_dict())
        self._future.append(current_state)
        prev_state = self._history.pop()
        self.from_dict(prev_state)
        self.is_dirty = True
        return True

    def redo(self) -> bool:
        """Re-apply previously undone state."""
        if not self._future:
            return False
        current_state = copy.deepcopy(self.to_dict())
        self._history.append(current_state)
        next_state = self._future.pop()
        self.from_dict(next_state)
        self.is_dirty = True
        return True

    # --------------------------------------------------------------------------
    # Node Operations (with Safe ID Guard)
    # --------------------------------------------------------------------------

    def rename_node(self, old_id: str, new_id: str) -> tuple[bool, str]:
        """
        Safely rename a node ID with collision guard (Tkinter Trap #4).
        Updates all incident edge references atomically.
        """
        new_id = new_id.strip()
        if not new_id:
            return False, "Node ID không được để trống."
        if old_id not in self.nodes:
            return False, f"Không tìm thấy node nguồn '{old_id}'."
        if new_id == old_id:
            return True, "ID không đổi."
        if new_id in self.nodes:
            return False, f"Lỗi trùng lặp: Node ID '{new_id}' đã tồn tại!"

        self.push_snapshot()
        node = self.nodes.pop(old_id)
        node.id = new_id
        self.nodes[new_id] = node

        # Update all references in edges
        for edge in self.edges:
            if edge.source_id == old_id:
                edge.source_id = new_id
            if edge.target_id == old_id:
                edge.target_id = new_id

        self.is_dirty = True
        return True, "Đổi Node ID thành công."

    def add_node(
        self,
        node_id: str,
        label: str,
        x: float,
        y: float,
        width: float = 140.0,
        height: float = 42.0,
        node_type: NodeType = "standard",
    ) -> tuple[bool, str, Optional[Node]]:
        """Add a new node ensuring unique ID."""
        node_id = node_id.strip()
        if not node_id:
            return False, "ID không được để trống.", None
        if node_id in self.nodes:
            return False, f"Node ID '{node_id}' đã tồn tại.", None

        self.push_snapshot()
        new_node = Node(
            id=node_id,
            label=label,
            x=x,
            y=y,
            width=width,
            height=height,
            type=node_type,
        )
        self.nodes[node_id] = new_node
        self.is_dirty = True
        return True, "Thêm node thành công.", new_node

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all incident edges."""
        if node_id not in self.nodes:
            return False
        self.push_snapshot()
        del self.nodes[node_id]
        self.edges = [
            e for e in self.edges
            if e.source_id != node_id and e.target_id != node_id
        ]
        self.is_dirty = True
        return True

    # --------------------------------------------------------------------------
    # Edge Operations
    # --------------------------------------------------------------------------

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
        label_offset_x: float = 0.0,
        label_offset_y: float = 0.0,
    ) -> tuple[bool, str, Optional[Edge]]:
        """Add an edge between two valid nodes."""
        if source_id not in self.nodes:
            return False, f"Source node '{source_id}' không tồn tại.", None
        if target_id not in self.nodes:
            return False, f"Target node '{target_id}' không tồn tại.", None

        self.push_snapshot()
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
            label_offset_x=label_offset_x,
            label_offset_y=label_offset_y,
        )
        self.edges.append(edge)
        self.is_dirty = True
        return True, "Thêm edge thành công.", edge

    def remove_edge(self, edge_index: int) -> bool:
        """Remove edge by its index."""
        if 0 <= edge_index < len(self.edges):
            self.push_snapshot()
            self.edges.pop(edge_index)
            self.is_dirty = True
            return True
        return False

    # --------------------------------------------------------------------------
    # File I/O
    # --------------------------------------------------------------------------

    def load_from_json(self, path: str) -> None:
        """Load spec from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.from_dict(data)
        self.spec_path = os.path.abspath(path)
        self._history.clear()
        self._future.clear()
        self.is_dirty = False

    def save_to_json(self, path: str | None = None) -> str:
        """Save spec to JSON file."""
        target_path = path or self.spec_path
        if not target_path:
            raise ValueError("Không có đường dẫn lưu file.")
        target_path = os.path.abspath(target_path)
        data = self.to_dict()
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.spec_path = target_path
        self.is_dirty = False
        return target_path


# ==============================================================================
# PHASE 2 & 3: CANVAS RENDERER & INTERACTION HANDLER
# ==============================================================================

class DiagramCanvas(tk.Frame):
    """
    High-performance interactive diagram canvas.
    Handles coordinate transformations, zoom/pan, smooth anti-flicker dragging,
    precise edge hit-testing, and keyboard bindings.
    """

    GRID_SIZE: float = 10.0
    MIN_ZOOM: float = 0.25
    MAX_ZOOM: float = 3.5

    # Color tokens matching precision design standards
    COLOR_BG = "#f8fafc"
    COLOR_GRID = "#e2e8f0"
    COLOR_NODE_FILL = "#ffffff"
    COLOR_NODE_BORDER_STD = "#0f172a"
    COLOR_NODE_BORDER_PRI = "#1d4ed8"
    COLOR_NODE_BORDER_MODAL = "#475569"
    COLOR_NODE_SEL = "#f59e0b"
    COLOR_EDGE_SOLID = "#0f172a"
    COLOR_EDGE_DASHED = "#475569"
    COLOR_EDGE_SEL = "#d97706"
    COLOR_LABEL_BG = "#ffffff"
    COLOR_LABEL_TEXT = "#0f172a"

    def __init__(
        self,
        parent: tk.Widget,
        state: DiagramState,
        on_selection_changed: Optional[Callable[[], None]] = None,
        on_state_modified: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, bg=self.COLOR_BG)
        self.state = state
        self.on_selection_changed = on_selection_changed
        self.on_state_modified = on_state_modified

        # Viewport transformation
        self.zoom_level: float = 1.0
        self.pan_x: float = 40.0
        self.pan_y: float = 40.0
        self.show_grid: bool = True

        # Selection state: ("node", node_id) or ("edge", edge_index) or None
        self.selected_item: tuple[str, Any] | None = None

        # Drag tracking
        self._drag_mode: Literal["none", "node", "pan"] = "none"
        self._drag_start_mouse: tuple[float, float] = (0.0, 0.0)
        self._drag_start_node_pos: tuple[float, float] = (0.0, 0.0)
        self._drag_node_id: str | None = None
        self._space_pressed: bool = False

        # Build Canvas Widget
        self.canvas = tk.Canvas(
            self,
            bg=self.COLOR_BG,
            highlightthickness=0,
            borderwidth=0,
            cursor="arrow",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._bind_events()
        self.redraw_all()

    # --------------------------------------------------------------------------
    # Coordinate Transforms
    # --------------------------------------------------------------------------

    def world_to_screen(self, wx: float, wy: float) -> tuple[float, float]:
        """Convert diagram world coordinates to canvas pixel coordinates."""
        sx = (wx + self.pan_x) * self.zoom_level
        sy = (wy + self.pan_y) * self.zoom_level
        return sx, sy

    def screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        """Convert canvas pixel coordinates to diagram world coordinates."""
        wx = (sx / self.zoom_level) - self.pan_x
        wy = (sy / self.zoom_level) - self.pan_y
        return wx, wy

    # --------------------------------------------------------------------------
    # Event Bindings & Pitfall Protections
    # --------------------------------------------------------------------------

    def _bind_events(self) -> None:
        """Setup mouse and keyboard listeners with strict focus guards."""
        self.canvas.bind("<Configure>", lambda e: self.redraw_all())

        # Mouse Interactions
        self.canvas.bind("<ButtonPress-1>", self._on_left_down)
        self.canvas.bind("<B1-Motion>", self._on_left_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_up)

        # Middle & Right Click Pan
        self.canvas.bind("<ButtonPress-2>", self._start_pan)
        self.canvas.bind("<B2-Motion>", self._do_pan)
        self.canvas.bind("<ButtonRelease-2>", self._end_pan)
        self.canvas.bind("<ButtonPress-3>", self._start_pan)
        self.canvas.bind("<B3-Motion>", self._do_pan)
        self.canvas.bind("<ButtonRelease-3>", self._end_pan)

        # Zoom bindings
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self._zoom_at(e.x, e.y, 1.15))
        self.canvas.bind("<Button-5>", lambda e: self._zoom_at(e.x, e.y, 0.87))

        # Tkinter Trap #2: Space pan focus guard
        # Only activate space-pan when Canvas is the active focused widget!
        self.canvas.bind("<KeyPress-space>", self._on_space_down)
        self.canvas.bind("<KeyRelease-space>", self._on_space_up)

        # Global delete key for selected element
        self.canvas.bind("<Delete>", self._on_delete_key)
        self.canvas.bind("<BackSpace>", self._on_delete_key)

        # Allow canvas to receive focus when clicked
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set(), add="+")

    def _on_space_down(self, event: tk.Event) -> None:
        """Activate space-pan ONLY if the Canvas itself has focus (Trap #2)."""
        if event.widget == self.canvas:
            self._space_pressed = True
            self.canvas.configure(cursor="fleur")

    def _on_space_up(self, event: tk.Event) -> None:
        """Release space-pan."""
        self._space_pressed = False
        if self._drag_mode != "pan":
            self.canvas.configure(cursor="arrow")

    def _start_pan(self, event: tk.Event) -> None:
        self._drag_mode = "pan"
        self._drag_start_mouse = (float(event.x), float(event.y))
        self.canvas.configure(cursor="fleur")

    def _do_pan(self, event: tk.Event) -> None:
        if self._drag_mode == "pan":
            dx = float(event.x) - self._drag_start_mouse[0]
            dy = float(event.y) - self._drag_start_mouse[1]
            self.pan_x += dx / self.zoom_level
            self.pan_y += dy / self.zoom_level
            self._drag_start_mouse = (float(event.x), float(event.y))
            self.redraw_all()

    def _end_pan(self, event: tk.Event) -> None:
        if self._drag_mode == "pan":
            self._drag_mode = "none"
            cursor = "fleur" if self._space_pressed else "arrow"
            self.canvas.configure(cursor=cursor)

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Zoom centered at mouse location."""
        factor = 1.15 if event.delta > 0 else 0.87
        self._zoom_at(event.x, event.y, factor)

    def _zoom_at(self, sx: float, sy: float, factor: float) -> None:
        """Perform zoom centered at (sx, sy)."""
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.zoom_level * factor))
        if abs(new_zoom - self.zoom_level) < 0.001:
            return

        # Preserve the world coordinate under cursor
        wx, wy = self.screen_to_world(sx, sy)
        self.zoom_level = new_zoom
        # Adjust pan so that (wx, wy) stays under (sx, sy)
        self.pan_x = (sx / self.zoom_level) - wx
        self.pan_y = (sy / self.zoom_level) - wy
        self.redraw_all()

    # --------------------------------------------------------------------------
    # Click, Drag & Hit-Testing (Traps #1 & #3)
    # --------------------------------------------------------------------------

    def _on_left_down(self, event: tk.Event) -> None:
        """Handle left click: check space-pan, node selection, or edge hit-testing."""
        self.canvas.focus_set()

        # Check Space-pan mode
        if self._space_pressed:
            self._start_pan(event)
            return

        # Find clicked item using find_overlapping for robust hit-testing (Trap #3)
        sx, sy = float(event.x), float(event.y)
        hit_items = self.canvas.find_overlapping(sx - 4, sy - 4, sx + 4, sy + 4)

        # 1. Check if a Node was clicked
        clicked_node_id: str | None = None
        for item in reversed(hit_items):
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("node_") and not tag.startswith("node_sel_"):
                    potential_id = tag[len("node_"):]
                    if potential_id in self.state.nodes:
                        clicked_node_id = potential_id
                        break
            if clicked_node_id:
                break

        if clicked_node_id:
            # Select node and prepare drag
            self.select_node(clicked_node_id)
            node = self.state.nodes[clicked_node_id]
            self._drag_mode = "node"
            self._drag_node_id = clicked_node_id
            self._drag_start_mouse = (sx, sy)
            self._drag_start_node_pos = (node.x, node.y)
            # Push snapshot at drag start for undo
            self.state.push_snapshot()
            return

        # 2. Check if an Edge or Edge Label was clicked (Trap #3)
        clicked_edge_idx: int | None = None
        for item in reversed(hit_items):
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("edge_") and not tag.startswith("edge_sel_"):
                    raw_idx = tag[len("edge_"):]
                    if raw_idx.isdigit():
                        clicked_edge_idx = int(raw_idx)
                        break
                elif tag.startswith("edge_lbl_"):
                    raw_idx = tag[len("edge_lbl_"):]
                    if raw_idx.isdigit():
                        clicked_edge_idx = int(raw_idx)
                        break
            if clicked_edge_idx is not None:
                break

        if clicked_edge_idx is not None and 0 <= clicked_edge_idx < len(self.state.edges):
            self.select_edge(clicked_edge_idx)
            self._drag_mode = "none"
            return

        # 3. Clicked on empty canvas background -> clear selection
        self.clear_selection()
        self._drag_mode = "none"

    def _on_left_motion(self, event: tk.Event) -> None:
        """
        Anti-flicker Drag & Drop (Tkinter Trap #1):
        Uses canvas.move on the dragged node's tags, and only redraws incident edges.
        Never calls canvas.delete("all") during motion!
        """
        if self._drag_mode == "pan":
            self._do_pan(event)
            return

        if self._drag_mode != "node" or not self._drag_node_id:
            return

        node_id = self._drag_node_id
        node = self.state.nodes.get(node_id)
        if not node:
            return

        sx, sy = float(event.x), float(event.y)
        # Calculate delta from last mouse position
        dx_screen = sx - self._drag_start_mouse[0]
        dy_screen = sy - self._drag_start_mouse[1]
        self._drag_start_mouse = (sx, sy)

        dx_world = dx_screen / self.zoom_level
        dy_world = dy_screen / self.zoom_level

        # Update node logical coordinates
        node.x += dx_world
        node.y += dy_world

        # Fast tag-based move on canvas items (TRAP #1)
        self.canvas.move(f"node_group_{node_id}", dx_screen, dy_screen)
        self.canvas.move(f"node_sel_{node_id}", dx_screen, dy_screen)

        # Redraw ONLY incident edges connected to this node
        self._redraw_incident_edges(node_id)

    def _on_left_up(self, event: tk.Event) -> None:
        """Snap to 10px grid on release and sync properties."""
        if self._drag_mode == "pan":
            self._end_pan(event)
            return

        if self._drag_mode == "node" and self._drag_node_id:
            node = self.state.nodes.get(self._drag_node_id)
            if node:
                # Snap to grid
                node.x = round(node.x / self.GRID_SIZE) * self.GRID_SIZE
                node.y = round(node.y / self.GRID_SIZE) * self.GRID_SIZE
                # Full clean redraw to ensure perfect alignment
                self.redraw_all()
                if self.on_state_modified:
                    self.on_state_modified()

        self._drag_mode = "none"
        self._drag_node_id = None

    def _on_delete_key(self, event: tk.Event) -> None:
        """Handle Delete/Backspace key on selected item."""
        if not self.selected_item:
            return
        item_type, item_ref = self.selected_item
        if item_type == "node":
            self.state.remove_node(item_ref)
            self.clear_selection()
            self.redraw_all()
            if self.on_state_modified:
                self.on_state_modified()
        elif item_type == "edge":
            self.state.remove_edge(item_ref)
            self.clear_selection()
            self.redraw_all()
            if self.on_state_modified:
                self.on_state_modified()

    # --------------------------------------------------------------------------
    # Selection Management
    # --------------------------------------------------------------------------

    def select_node(self, node_id: str) -> None:
        self.selected_item = ("node", node_id)
        self.redraw_all()
        if self.on_selection_changed:
            self.on_selection_changed()

    def select_edge(self, edge_index: int) -> None:
        self.selected_item = ("edge", edge_index)
        self.redraw_all()
        if self.on_selection_changed:
            self.on_selection_changed()

    def clear_selection(self) -> None:
        self.selected_item = None
        self.redraw_all()
        if self.on_selection_changed:
            self.on_selection_changed()

    # --------------------------------------------------------------------------
    # Rendering Logic
    # --------------------------------------------------------------------------

    def redraw_all(self) -> None:
        """Full redraw of grid, edges, nodes, and selection highlights."""
        self.canvas.delete("all")

        # 1. Background Grid
        if self.show_grid:
            self._draw_grid()

        # 2. Canvas Boundary Box
        c_x1, c_y1 = self.world_to_screen(0, 0)
        c_x2, c_y2 = self.world_to_screen(self.state.width, self.state.height)
        self.canvas.create_rectangle(
            c_x1, c_y1, c_x2, c_y2,
            outline="#cbd5e1",
            dash=(3, 3),
            tags="canvas_border"
        )

        # 3. Edges (Lines and Arrowheads)
        for idx, edge in enumerate(self.state.edges):
            self._draw_edge(idx, edge)

        # 4. Nodes
        for node in self.state.nodes.values():
            self._draw_node(node)

        # 5. Edge Labels (on top of nodes)
        for idx, edge in enumerate(self.state.edges):
            if edge.label:
                self._draw_edge_label(idx, edge)

        # 6. Selection Highlight
        self._draw_selection_highlight()

    def _draw_grid(self) -> None:
        """Render faint dot grid aligned to world coordinates."""
        w_px = self.canvas.winfo_width()
        h_px = self.canvas.winfo_height()
        if w_px <= 1 or h_px <= 1:
            return

        w_start_x, w_start_y = self.screen_to_world(0, 0)
        w_end_x, w_end_y = self.screen_to_world(w_px, h_px)

        # Snap start to grid multiples
        gx0 = math.floor(w_start_x / (self.GRID_SIZE * 2)) * (self.GRID_SIZE * 2)
        gy0 = math.floor(w_start_y / (self.GRID_SIZE * 2)) * (self.GRID_SIZE * 2)

        # Limit maximum grid points to prevent rendering overload
        step = self.GRID_SIZE * 2
        if step * self.zoom_level < 8:
            step = self.GRID_SIZE * 4

        x = gx0
        while x <= w_end_x:
            y = gy0
            while y <= w_end_y:
                sx, sy = self.world_to_screen(x, y)
                self.canvas.create_rectangle(
                    sx, sy, sx + 1.2, sy + 1.2,
                    fill=self.COLOR_GRID,
                    outline="",
                    tags="grid"
                )
                y += step
            x += step

    def _draw_node(self, node: Node) -> None:
        """Render a single node with tags matching its id."""
        x1, y1 = self.world_to_screen(node.x, node.y)
        x2, y2 = self.world_to_screen(node.x + node.width, node.y + node.height)
        node_group_tag = f"node_group_{node.id}"
        node_tag = f"node_{node.id}"

        # Style resolution
        is_primary = node.type == "primary"
        is_modal = node.type in ("modal", "toast")

        border_color = (
            self.COLOR_NODE_BORDER_PRI if is_primary
            else self.COLOR_NODE_BORDER_MODAL if is_modal
            else self.COLOR_NODE_BORDER_STD
        )
        border_width = max(1, int((2.5 if is_primary else 1.5) * self.zoom_level))
        dash = (4, 4) if is_modal else ()

        # Node rectangle
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self.COLOR_NODE_FILL,
            outline=border_color,
            width=border_width,
            dash=dash,
            tags=("node", node_tag, node_group_tag)
        )

        # Center label text
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        font_size = max(7, int(self.state.font_size * self.zoom_level))
        weight = "bold" if is_primary else "normal"

        lines = node.label.replace("<br/>", "\n").split("\n")
        line_spacing = font_size * 1.3
        start_y = cy - ((len(lines) - 1) * line_spacing) / 2.0

        for idx, line in enumerate(lines):
            ly = start_y + idx * line_spacing
            self.canvas.create_text(
                cx, ly,
                text=line,
                font=(self.state.font_family.split(",")[0], font_size, weight),
                fill="#000000",
                justify=tk.CENTER,
                tags=("node", node_tag, node_group_tag)
            )

    def _calculate_manhattan_route(self, edge: Edge) -> list[tuple[float, float]]:
        """Calculate orthogonal path points using engine logic."""
        if edge.source_id not in self.state.nodes or edge.target_id not in self.state.nodes:
            return []

        s_node = self.state.nodes[edge.source_id]
        t_node = self.state.nodes[edge.target_id]

        p_start = s_node.get_port(edge.source_port, edge.source_offset)
        p_end = t_node.get_port(edge.target_port, edge.target_offset)

        if edge.waypoints:
            return [p_start] + edge.waypoints + [p_end]

        sx, sy = p_start
        tx, ty = p_end

        # Automatic orthogonal L-shape or Z-shape routing
        if edge.source_port == "right" and edge.target_port == "left":
            if tx > sx:
                mid_x = (sx + tx) / 2.0
                return [p_start, (mid_x, sy), (mid_x, ty), p_end]
            else:
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
            return [p_start, (sx, ty), p_end]

        elif edge.source_port in ("left", "right") and edge.target_port in ("top", "bottom"):
            return [p_start, (tx, sy), p_end]

        return [p_start, (tx, sy), p_end]

    def _draw_edge(self, idx: int, edge: Edge) -> None:
        """Render an edge polyline with arrow."""
        pts = self._calculate_manhattan_route(edge)
        if len(pts) < 2:
            return

        # Convert to screen coordinates
        screen_pts: list[float] = []
        for wx, wy in pts:
            sx, sy = self.world_to_screen(wx, wy)
            screen_pts.extend([sx, sy])

        is_dashed = edge.line_style == "dashed"
        color = self.COLOR_EDGE_DASHED if is_dashed else self.COLOR_EDGE_SOLID
        width = max(1, int((1.3 if not is_dashed else 1.2) * self.zoom_level))
        dash = (4, 4) if is_dashed else ()

        edge_tag = f"edge_{idx}"
        edge_line_tag = f"edge_line_{idx}"

        # Draw line with arrowhead at end
        self.canvas.create_line(
            *screen_pts,
            fill=color,
            width=width,
            dash=dash,
            arrow=tk.LAST,
            arrowshape=(int(8 * self.zoom_level), int(10 * self.zoom_level), int(3 * self.zoom_level)),
            tags=("edge", edge_tag, edge_line_tag)
        )

    def _get_edge_label_coords(self, edge: Edge, pts: list[tuple[float, float]]) -> tuple[float, float]:
        """Calculate Cartesian coordinates for an edge label along path."""
        total_len = 0.0
        segs: list[tuple[tuple[float, float], tuple[float, float], float]] = []
        for i in range(len(pts) - 1):
            dx = pts[i + 1][0] - pts[i][0]
            dy = pts[i + 1][1] - pts[i][1]
            seg_len = math.hypot(dx, dy)
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

    def _draw_edge_label(self, idx: int, edge: Edge) -> None:
        """Render masked pill label on edge."""
        if not edge.label:
            return
        pts = self._calculate_manhattan_route(edge)
        if len(pts) < 2:
            return

        lbl_wx, lbl_wy = self._get_edge_label_coords(edge, pts)
        sx, sy = self.world_to_screen(lbl_wx, lbl_wy)

        lines = edge.label.replace("<br/>", "\n").split("\n")
        font_size = max(7, int(8.5 * self.zoom_level))
        font = (self.state.font_family.split(",")[0], font_size, "bold")

        line_h = font_size * 1.35
        max_line_len = max(len(l) for l in lines)
        approx_w = max_line_len * (font_size * 0.62) + (14 * self.zoom_level)
        approx_h = len(lines) * line_h + (6 * self.zoom_level)

        edge_lbl_tag = f"edge_lbl_{idx}"

        # Pill background
        x1 = sx - approx_w / 2.0
        y1 = sy - approx_h / 2.0
        x2 = sx + approx_w / 2.0
        y2 = sy + approx_h / 2.0

        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=self.COLOR_LABEL_BG,
            outline="#94a3b8",
            width=1,
            tags=("edge_label", edge_lbl_tag)
        )

        start_y = sy - ((len(lines) - 1) * line_h) / 2.0
        for l_idx, line in enumerate(lines):
            ly = start_y + l_idx * line_h
            self.canvas.create_text(
                sx, ly,
                text=line,
                font=font,
                fill=self.COLOR_LABEL_TEXT,
                justify=tk.CENTER,
                tags=("edge_label", edge_lbl_tag)
            )

    def _redraw_incident_edges(self, node_id: str) -> None:
        """Anti-flicker helper: redraw only edges incident to node_id during drag."""
        for idx, edge in enumerate(self.state.edges):
            if edge.source_id == node_id or edge.target_id == node_id:
                # Delete specific edge and label items
                self.canvas.delete(f"edge_{idx}")
                self.canvas.delete(f"edge_lbl_{idx}")
                self._draw_edge(idx, edge)
                if edge.label:
                    self._draw_edge_label(idx, edge)

    def _draw_selection_highlight(self) -> None:
        """Render selection auras for currently active node or edge."""
        if not self.selected_item:
            return

        item_type, item_ref = self.selected_item
        if item_type == "node":
            node = self.state.nodes.get(item_ref)
            if not node:
                return
            x1, y1 = self.world_to_screen(node.x, node.y)
            x2, y2 = self.world_to_screen(node.x + node.width, node.y + node.height)
            pad = 3 * self.zoom_level
            self.canvas.create_rectangle(
                x1 - pad, y1 - pad, x2 + pad, y2 + pad,
                outline=self.COLOR_NODE_SEL,
                width=max(2, int(2.5 * self.zoom_level)),
                dash=(5, 3),
                tags=f"node_sel_{node.id}"
            )

        elif item_type == "edge":
            idx = int(item_ref)
            if 0 <= idx < len(self.state.edges):
                edge = self.state.edges[idx]
                pts = self._calculate_manhattan_route(edge)
                if len(pts) >= 2:
                    screen_pts: list[float] = []
                    for wx, wy in pts:
                        sx, sy = self.world_to_screen(wx, wy)
                        screen_pts.extend([sx, sy])
                    self.canvas.create_line(
                        *screen_pts,
                        fill=self.COLOR_EDGE_SEL,
                        width=max(3, int(3.5 * self.zoom_level)),
                        arrow=tk.LAST,
                        arrowshape=(int(10 * self.zoom_level), int(12 * self.zoom_level), int(4 * self.zoom_level)),
                        tags="edge_sel"
                    )

    # --------------------------------------------------------------------------
    # Auto-fit Viewport
    # --------------------------------------------------------------------------

    def fit_view(self) -> None:
        """Calculate bounding box of all nodes and fit viewport."""
        if not self.state.nodes:
            self.pan_x = 40.0
            self.pan_y = 40.0
            self.zoom_level = 1.0
            self.redraw_all()
            return

        min_x = min(n.x for n in self.state.nodes.values())
        min_y = min(n.y for n in self.state.nodes.values())
        max_x = max(n.x + n.width for n in self.state.nodes.values())
        max_y = max(n.y + n.height for n in self.state.nodes.values())

        margin = 60.0
        content_w = (max_x - min_x) + margin * 2
        content_h = (max_y - min_y) + margin * 2

        vw = max(100, self.canvas.winfo_width())
        vh = max(100, self.canvas.winfo_height())

        zoom_x = vw / content_w
        zoom_y = vh / content_h
        self.zoom_level = max(self.MIN_ZOOM, min(1.8, min(zoom_x, zoom_y)))

        # Center content
        center_wx = (min_x + max_x) / 2.0
        center_wy = (min_y + max_y) / 2.0
        self.pan_x = (vw / (2.0 * self.zoom_level)) - center_wx
        self.pan_y = (vh / (2.0 * self.zoom_level)) - center_wy

        self.redraw_all()


# ==============================================================================
# PHASE 4: PROPERTIES PANEL (SIDEBAR)
# ==============================================================================

class PropertiesPanel(ttk.Frame):
    """
    Two-way reactive sidebar property editor.
    Updates canvas in real-time, validates node rename uniqueness (Trap #4),
    and manages edges and connections.
    """

    def __init__(
        self,
        parent: tk.Widget,
        state: DiagramState,
        canvas_widget: DiagramCanvas,
    ) -> None:
        super().__init__(parent, padding=10, width=310)
        self.pack_propagate(False)
        self.state = state
        self.canvas_widget = canvas_widget

        self._updating: bool = False
        self._build_header()
        self._build_body()
        self.refresh()

    def _build_header(self) -> None:
        lbl = ttk.Label(self, text="⚙️ Thuộc tính (Properties)", font=("Segoe UI", 11, "bold"))
        lbl.pack(anchor=tk.W, pady=(0, 8))

    def _build_body(self) -> None:
        # Scrollable container for dynamic properties
        self.body_canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, bg="#f8fafc")
        self.body_sb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.body_canvas.yview)
        self.body_frame = ttk.Frame(self.body_canvas)

        self.body_frame.bind(
            "<Configure>",
            lambda e: self.body_canvas.configure(scrollregion=self.body_canvas.bbox("all"))
        )
        self.body_win = self.body_canvas.create_window((0, 0), window=self.body_frame, anchor="nw")
        self.body_canvas.configure(yscrollcommand=self.body_sb.set)

        self.body_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.body_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.body_canvas.bind(
            "<Configure>",
            lambda e: self.body_canvas.itemconfig(self.body_win, width=e.width)
        )

    def refresh(self) -> None:
        """Re-render properties form according to current selection."""
        if self._updating:
            return

        for w in self.body_frame.winfo_children():
            w.destroy()

        sel = self.canvas_widget.selected_item
        if not sel:
            self._render_canvas_properties()
        elif sel[0] == "node":
            self._render_node_properties(sel[1])
        elif sel[0] == "edge":
            self._render_edge_properties(sel[1])

    # --------------------------------------------------------------------------
    # Node Properties Form (Trap #4 ID Collision Guard)
    # --------------------------------------------------------------------------

    def _render_node_properties(self, node_id: str) -> None:
        node = self.state.nodes.get(node_id)
        if not node:
            self.canvas_widget.clear_selection()
            return

        f = self.body_frame

        # Title
        sec_lbl = ttk.Label(f, text=f"Màn hình / Node: {node.id}", font=("Segoe UI", 10, "bold"), foreground="#1e40af")
        sec_lbl.pack(anchor=tk.W, pady=(0, 6))

        # ID Field with rename guard (Trap #4)
        ttk.Label(f, text="Node ID:").pack(anchor=tk.W)
        id_var = tk.StringVar(value=node.id)
        id_entry = ttk.Entry(f, textvariable=id_var)
        id_entry.pack(fill=tk.X, pady=(2, 2))

        err_label = tk.Label(f, text="", font=("Segoe UI", 8), fg="#dc2626", bg="#f8fafc", anchor=tk.W)
        err_label.pack(fill=tk.X, pady=(0, 4))

        def commit_rename(*_) -> None:
            new_id = id_var.get().strip()
            if new_id == node.id:
                err_label.config(text="")
                return
            ok, msg = self.state.rename_node(node.id, new_id)
            if not ok:
                err_label.config(text=f"⚠️ {msg}")
                id_entry.config(foreground="#dc2626")
            else:
                err_label.config(text="")
                id_entry.config(foreground="#0f172a")
                self.canvas_widget.selected_item = ("node", new_id)
                self.canvas_widget.redraw_all()
                self.refresh()

        id_entry.bind("<Return>", commit_rename)
        id_entry.bind("<FocusOut>", commit_rename)

        # Label Field (Supports multi-line \n)
        ttk.Label(f, text="Tiêu đề / Label:").pack(anchor=tk.W)
        lbl_text = tk.Text(f, height=3, font=("Segoe UI", 9), wrap=tk.WORD)
        lbl_text.insert("1.0", node.label)
        lbl_text.pack(fill=tk.X, pady=(2, 6))

        def commit_label(*_) -> None:
            val = lbl_text.get("1.0", "end-1c").strip()
            if val != node.label:
                self.state.push_snapshot()
                node.label = val
                self.state.is_dirty = True
                self.canvas_widget.redraw_all()

        lbl_text.bind("<KeyRelease>", commit_label)

        # Node Type
        ttk.Label(f, text="Loại Node (Type):").pack(anchor=tk.W)
        type_var = tk.StringVar(value=node.type)
        type_combo = ttk.Combobox(
            f, textvariable=type_var,
            values=["standard", "primary", "modal", "toast"],
            state="readonly"
        )
        type_combo.pack(fill=tk.X, pady=(2, 6))

        def on_type_changed(e) -> None:
            self.state.push_snapshot()
            node.type = type_var.get()  # type: ignore
            self.state.is_dirty = True
            self.canvas_widget.redraw_all()

        type_combo.bind("<<ComboboxSelected>>", on_type_changed)

        # Geometry Row (X, Y, W, H)
        geo_box = ttk.LabelFrame(f, text="Tọa độ & Kích thước", padding=6)
        geo_box.pack(fill=tk.X, pady=(4, 8))

        g_grid = ttk.Frame(geo_box)
        g_grid.pack(fill=tk.X)

        # X
        ttk.Label(g_grid, text="X:").grid(row=0, column=0, sticky=tk.W, padx=2)
        x_var = tk.DoubleVar(value=round(node.x, 1))
        x_entry = ttk.Spinbox(g_grid, textvariable=x_var, from_=0, to=4000, increment=10, width=6)
        x_entry.grid(row=0, column=1, padx=2, pady=2)

        # Y
        ttk.Label(g_grid, text="Y:").grid(row=0, column=2, sticky=tk.W, padx=2)
        y_var = tk.DoubleVar(value=round(node.y, 1))
        y_entry = ttk.Spinbox(g_grid, textvariable=y_var, from_=0, to=4000, increment=10, width=6)
        y_entry.grid(row=0, column=3, padx=2, pady=2)

        # Width
        ttk.Label(g_grid, text="W:").grid(row=1, column=0, sticky=tk.W, padx=2)
        w_var = tk.DoubleVar(value=round(node.width, 1))
        w_entry = ttk.Spinbox(g_grid, textvariable=w_var, from_=20, to=800, increment=10, width=6)
        w_entry.grid(row=1, column=1, padx=2, pady=2)

        # Height
        ttk.Label(g_grid, text="H:").grid(row=1, column=2, sticky=tk.W, padx=2)
        h_var = tk.DoubleVar(value=round(node.height, 1))
        h_entry = ttk.Spinbox(g_grid, textvariable=h_var, from_=20, to=800, increment=10, width=6)
        h_entry.grid(row=1, column=3, padx=2, pady=2)

        def commit_geo(*_) -> None:
            try:
                node.x = float(x_var.get())
                node.y = float(y_var.get())
                node.width = float(w_var.get())
                node.height = float(h_var.get())
                self.state.is_dirty = True
                self.canvas_widget.redraw_all()
            except ValueError:
                pass

        for entry in (x_entry, y_entry, w_entry, h_entry):
            entry.bind("<Return>", commit_geo)
            entry.bind("<FocusOut>", commit_geo)

        # Connections Box
        conn_box = ttk.LabelFrame(f, text="Kết nối (Connections)", padding=6)
        conn_box.pack(fill=tk.X, pady=(4, 8))

        out_edges = [
            (idx, e) for idx, e in enumerate(self.state.edges)
            if e.source_id == node.id
        ]

        if not out_edges:
            ttk.Label(conn_box, text="Chưa có đường nối xuất phát.", font=("Segoe UI", 8), foreground="#64748b").pack(anchor=tk.W)
        else:
            for idx, e in out_edges:
                row = ttk.Frame(conn_box)
                row.pack(fill=tk.X, pady=1)
                lbl_t = f"➔ {e.target_id} ({e.label or 'không nhãn'})"
                ttk.Label(row, text=lbl_t, font=("Segoe UI", 8), width=24, anchor=tk.W).pack(side=tk.LEFT)
                btn_del = ttk.Button(
                    row, text="✕", width=2,
                    command=lambda i=idx: self._delete_edge_idx(i)
                )
                btn_del.pack(side=tk.RIGHT)

        # Add New Connection Sub-Panel
        add_conn_frame = ttk.Frame(conn_box)
        add_conn_frame.pack(fill=tk.X, pady=(6, 0))

        other_nodes = [nid for nid in self.state.nodes if nid != node.id]
        if other_nodes:
            ttk.Label(add_conn_frame, text="Nối đến:").grid(row=0, column=0, sticky=tk.W)
            target_var = tk.StringVar(value=other_nodes[0])
            combo_target = ttk.Combobox(add_conn_frame, textvariable=target_var, values=other_nodes, state="readonly", width=14)
            combo_target.grid(row=0, column=1, sticky=tk.EW, padx=2, pady=2)

            ttk.Label(add_conn_frame, text="Nhãn nút:").grid(row=1, column=0, sticky=tk.W)
            conn_lbl_var = tk.StringVar()
            entry_conn_lbl = ttk.Entry(add_conn_frame, textvariable=conn_lbl_var, width=14)
            entry_conn_lbl.grid(row=1, column=1, sticky=tk.EW, padx=2, pady=2)

            def do_add_conn() -> None:
                tgt = target_var.get()
                clbl = conn_lbl_var.get().strip() or None
                ok, _, _ = self.state.add_edge(
                    source_id=node.id,
                    target_id=tgt,
                    source_port="right",
                    target_port="left",
                    label=clbl,
                )
                if ok:
                    self.canvas_widget.redraw_all()
                    self.refresh()

            btn_add_c = ttk.Button(add_conn_frame, text="➕ Tạo kết nối", command=do_add_conn)
            btn_add_c.grid(row=2, column=0, columnspan=2, pady=(4, 0), sticky=tk.EW)

        # Delete Node Button
        ttk.Separator(f, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        btn_del_node = tk.Button(
            f, text="🗑️ Xóa Node này",
            command=lambda: self._delete_current_node(node.id),
            bg="#fee2e2", fg="#b91c1c", activebackground="#fca5a5",
            relief=tk.FLAT, font=("Segoe UI", 9, "bold"), pady=4
        )
        btn_del_node.pack(fill=tk.X)

    def _delete_current_node(self, node_id: str) -> None:
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa node '{node_id}' cùng toàn bộ kết nối liên quan?"):
            self.state.remove_node(node_id)
            self.canvas_widget.clear_selection()
            self.canvas_widget.redraw_all()

    def _delete_edge_idx(self, edge_idx: int) -> None:
        self.state.remove_edge(edge_idx)
        self.canvas_widget.redraw_all()
        self.refresh()

    # --------------------------------------------------------------------------
    # Edge Properties Form
    # --------------------------------------------------------------------------

    def _render_edge_properties(self, edge_idx: int) -> None:
        if not (0 <= edge_idx < len(self.state.edges)):
            self.canvas_widget.clear_selection()
            return

        edge = self.state.edges[edge_idx]
        f = self.body_frame

        # Title
        sec_lbl = ttk.Label(f, text=f"Đường nối: {edge.source_id} ➔ {edge.target_id}", font=("Segoe UI", 10, "bold"), foreground="#b45309")
        sec_lbl.pack(anchor=tk.W, pady=(0, 6))

        # Action Label
        ttk.Label(f, text="Nhãn Thao Tác (Action Label):").pack(anchor=tk.W)
        lbl_var = tk.StringVar(value=edge.label or "")
        lbl_entry = ttk.Entry(f, textvariable=lbl_var)
        lbl_entry.pack(fill=tk.X, pady=(2, 6))

        def commit_edge_label(*_) -> None:
            new_val = lbl_var.get().strip() or None
            if new_val != edge.label:
                self.state.push_snapshot()
                edge.label = new_val
                self.state.is_dirty = True
                self.canvas_widget.redraw_all()

        lbl_entry.bind("<KeyRelease>", commit_edge_label)

        # Source & Target Ports
        port_box = ttk.LabelFrame(f, text="Cổng kết nối (Ports)", padding=6)
        port_box.pack(fill=tk.X, pady=4)

        ttk.Label(port_box, text="Cổng Nguồn:").grid(row=0, column=0, sticky=tk.W)
        src_port_var = tk.StringVar(value=edge.source_port)
        combo_sp = ttk.Combobox(port_box, textvariable=src_port_var, values=["right", "left", "top", "bottom"], state="readonly", width=8)
        combo_sp.grid(row=0, column=1, padx=2, pady=2)

        ttk.Label(port_box, text="Cổng Đích:").grid(row=1, column=0, sticky=tk.W)
        tgt_port_var = tk.StringVar(value=edge.target_port)
        combo_tp = ttk.Combobox(port_box, textvariable=tgt_port_var, values=["left", "right", "top", "bottom"], state="readonly", width=8)
        combo_tp.grid(row=1, column=1, padx=2, pady=2)

        def on_ports_changed(e) -> None:
            self.state.push_snapshot()
            edge.source_port = src_port_var.get()  # type: ignore
            edge.target_port = tgt_port_var.get()  # type: ignore
            self.state.is_dirty = True
            self.canvas_widget.redraw_all()

        combo_sp.bind("<<ComboboxSelected>>", on_ports_changed)
        combo_tp.bind("<<ComboboxSelected>>", on_ports_changed)

        # Line Style
        ttk.Label(f, text="Kiểu đường (Line Style):").pack(anchor=tk.W, pady=(4, 0))
        style_var = tk.StringVar(value=edge.line_style)
        combo_style = ttk.Combobox(f, textvariable=style_var, values=["solid", "dashed"], state="readonly")
        combo_style.pack(fill=tk.X, pady=(2, 6))

        def on_style_changed(e) -> None:
            self.state.push_snapshot()
            edge.line_style = style_var.get()  # type: ignore
            self.state.is_dirty = True
            self.canvas_widget.redraw_all()

        combo_style.bind("<<ComboboxSelected>>", on_style_changed)

        # Label Position Slider (0.0 to 1.0)
        ttk.Label(f, text="Vị trí nhãn dọc đường nối (0.0 - 1.0):").pack(anchor=tk.W)
        pos_var = tk.DoubleVar(value=edge.label_pos)
        slider_pos = ttk.Scale(f, from_=0.1, to=0.9, variable=pos_var)
        slider_pos.pack(fill=tk.X, pady=(2, 6))

        def on_pos_changed(e) -> None:
            edge.label_pos = round(pos_var.get(), 2)
            self.state.is_dirty = True
            self.canvas_widget.redraw_all()

        slider_pos.bind("<B1-Motion>", on_pos_changed)
        slider_pos.bind("<ButtonRelease-1>", lambda e: self.state.push_snapshot())

        # Offsets
        off_box = ttk.Frame(f)
        off_box.pack(fill=tk.X, pady=2)

        ttk.Label(off_box, text="Offset X:").grid(row=0, column=0, sticky=tk.W)
        ox_var = tk.DoubleVar(value=edge.label_offset_x)
        ox_spin = ttk.Spinbox(off_box, textvariable=ox_var, from_=-200, to=200, increment=5, width=6)
        ox_spin.grid(row=0, column=1, padx=2, pady=2)

        ttk.Label(off_box, text="Offset Y:").grid(row=0, column=2, sticky=tk.W)
        oy_var = tk.DoubleVar(value=edge.label_offset_y)
        oy_spin = ttk.Spinbox(off_box, textvariable=oy_var, from_=-200, to=200, increment=5, width=6)
        oy_spin.grid(row=0, column=3, padx=2, pady=2)

        def commit_offsets(*_) -> None:
            try:
                edge.label_offset_x = float(ox_var.get())
                edge.label_offset_y = float(oy_var.get())
                self.state.is_dirty = True
                self.canvas_widget.redraw_all()
            except ValueError:
                pass

        ox_spin.bind("<Return>", commit_offsets)
        ox_spin.bind("<FocusOut>", commit_offsets)
        oy_spin.bind("<Return>", commit_offsets)
        oy_spin.bind("<FocusOut>", commit_offsets)

        # Delete Edge Button
        ttk.Separator(f, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        btn_del = tk.Button(
            f, text="🗑️ Xóa Đường nối này",
            command=lambda: self._delete_edge_idx(edge_idx),
            bg="#fee2e2", fg="#b91c1c", activebackground="#fca5a5",
            relief=tk.FLAT, font=("Segoe UI", 9, "bold"), pady=4
        )
        btn_del.pack(fill=tk.X)

    # --------------------------------------------------------------------------
    # Canvas Properties Form (when nothing is selected)
    # --------------------------------------------------------------------------

    def _render_canvas_properties(self) -> None:
        f = self.body_frame

        sec_lbl = ttk.Label(f, text="Khung Canvas Toàn cục", font=("Segoe UI", 10, "bold"), foreground="#334155")
        sec_lbl.pack(anchor=tk.W, pady=(0, 6))

        dim_box = ttk.LabelFrame(f, text="Kích thước Canvas (World px)", padding=6)
        dim_box.pack(fill=tk.X, pady=4)

        ttk.Label(dim_box, text="Chiều rộng (W):").grid(row=0, column=0, sticky=tk.W)
        w_var = tk.DoubleVar(value=self.state.width)
        w_spin = ttk.Spinbox(dim_box, textvariable=w_var, from_=400, to=5000, increment=50, width=8)
        w_spin.grid(row=0, column=1, padx=4, pady=2)

        ttk.Label(dim_box, text="Chiều cao (H):").grid(row=1, column=0, sticky=tk.W)
        h_var = tk.DoubleVar(value=self.state.height)
        h_spin = ttk.Spinbox(dim_box, textvariable=h_var, from_=300, to=5000, increment=50, width=8)
        h_spin.grid(row=1, column=1, padx=4, pady=2)

        def commit_dim(*_) -> None:
            try:
                self.state.push_snapshot()
                self.state.width = float(w_var.get())
                self.state.height = float(h_var.get())
                self.state.is_dirty = True
                self.canvas_widget.redraw_all()
            except ValueError:
                pass

        w_spin.bind("<Return>", commit_dim)
        w_spin.bind("<FocusOut>", commit_dim)
        h_spin.bind("<Return>", commit_dim)
        h_spin.bind("<FocusOut>", commit_dim)

        # Statistics
        stat_box = ttk.LabelFrame(f, text="Thống kê sơ đồ", padding=6)
        stat_box.pack(fill=tk.X, pady=8)

        ttk.Label(stat_box, text=f"• Tổng số Node (Màn hình): {len(self.state.nodes)}").pack(anchor=tk.W)
        ttk.Label(stat_box, text=f"• Tổng số Edge (Luồng chuyển): {len(self.state.edges)}").pack(anchor=tk.W)
        ttk.Label(stat_box, text=f"• Snap Grid: {DiagramCanvas.GRID_SIZE:.0f}px").pack(anchor=tk.W)

        # Quick Tips
        tip_box = ttk.LabelFrame(f, text="💡 Mẹo thao tác", padding=6)
        tip_box.pack(fill=tk.X, pady=8)
        tips = (
            "• Click Node để di chuyển hoặc chỉnh sửa.\n"
            "• Click Edge để chỉnh cổng và nhãn.\n"
            "• Giữ Space + Kéo chuột để Pan.\n"
            "• Cuộn chuột để Zoom phóng to/thu nhỏ.\n"
            "• Phím Delete: Xóa đối tượng đang chọn.\n"
            "• Ctrl+Z: Undo / Ctrl+Y: Redo.\n"
            "• Nút [Fit View] tự động căn chỉnh giữa."
        )
        ttk.Label(tip_box, text=tips, font=("Segoe UI", 8), foreground="#475569", justify=tk.LEFT).pack(anchor=tk.W)


# ==============================================================================
# PHASE 5: DIAGRAM EDITOR APP (TOPLEVEL & STANDALONE)
# ==============================================================================

class DiagramEditorApp:
    """
    Main application window for Diagram Canvas Editor.
    Integrates toolbar, canvas, sidebar, status bar, and native PNG exporter.
    """

    def __init__(self, master: Optional[tk.Tk | tk.Toplevel] = None, spec_path: Optional[str] = None) -> None:
        self.is_standalone = master is None
        self.root = tk.Tk() if self.is_standalone else tk.Toplevel(master)
        self.state = DiagramState(spec_path)

        self.root.title(self._get_window_title())
        self.root.geometry("1240x820")
        self.root.minsize(960, 640)
        self.root.configure(bg="#f8fafc")

        self._build_toolbar()
        self._build_main_area()
        self._build_statusbar()
        self._setup_keybindings()

        # Handle window closing with dirty guard
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Initial auto-fit view
        self.root.after(100, self.canvas_widget.fit_view)

    def _get_window_title(self) -> str:
        filename = os.path.basename(self.state.spec_path) if self.state.spec_path else "Untitled"
        dirty_marker = " *" if self.state.is_dirty else ""
        return f"📐 Precision Diagram Canvas Editor — [{filename}]{dirty_marker}"

    def _sync_title(self) -> None:
        self.root.title(self._get_window_title())
        status_text = f"Đã lưu: {self.state.spec_path}" if not self.state.is_dirty else "Có thay đổi chưa lưu (*)"
        self.lbl_file_status.config(text=status_text)

    # --------------------------------------------------------------------------
    # UI Layout & Toolbar
    # --------------------------------------------------------------------------

    def _build_toolbar(self) -> None:
        tb = ttk.Frame(self.root, padding=(8, 6, 8, 6))
        tb.pack(fill=tk.X, side=tk.TOP)

        # File actions
        btn_open = ttk.Button(tb, text="📂 Mở JSON...", command=self._action_open)
        btn_open.pack(side=tk.LEFT, padx=(0, 4))

        btn_save = ttk.Button(tb, text="💾 Lưu JSON", command=self._action_save)
        btn_save.pack(side=tk.LEFT, padx=(0, 4))

        btn_export = ttk.Button(tb, text="🖼️ Xuất PNG (300+ DPI)", command=self._action_export_png)
        btn_export.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # Edit actions
        btn_add_node = ttk.Button(tb, text="➕ Thêm Node", command=self._action_add_node)
        btn_add_node.pack(side=tk.LEFT, padx=(4, 4))

        btn_fit = ttk.Button(tb, text="🔍 Fit View", command=self._action_fit_view)
        btn_fit.pack(side=tk.LEFT, padx=(0, 4))

        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # Undo / Redo
        btn_undo = ttk.Button(tb, text="↩️ Hoàn tác", command=self._action_undo)
        btn_undo.pack(side=tk.LEFT, padx=(4, 4))

        btn_redo = ttk.Button(tb, text="↪️ Làm lại", command=self._action_redo)
        btn_redo.pack(side=tk.LEFT, padx=(0, 8))

        # Collision Check Button
        btn_check = ttk.Button(tb, text="🛡️ Kiểm tra va chạm", command=self._action_check_collisions)
        btn_check.pack(side=tk.RIGHT, padx=4)

    def _build_main_area(self) -> None:
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Left: Interactive Canvas
        self.canvas_widget = DiagramCanvas(
            main_paned,
            self.state,
            on_selection_changed=self._on_canvas_selection_changed,
            on_state_modified=self._on_canvas_state_modified,
        )
        main_paned.add(self.canvas_widget, weight=4)

        # Right: Properties Sidebar
        self.props_panel = PropertiesPanel(main_paned, self.state, self.canvas_widget)
        main_paned.add(self.props_panel, weight=1)

    def _build_statusbar(self) -> None:
        sb = ttk.Frame(self.root, padding=(8, 2, 8, 2))
        sb.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_file_status = ttk.Label(
            sb,
            text=f"Tệp: {self.state.spec_path or 'Chưa lưu'}",
            font=("Segoe UI", 8),
            foreground="#475569"
        )
        self.lbl_file_status.pack(side=tk.LEFT)

        self.lbl_info = ttk.Label(
            sb,
            text="Phím tắt: [Ctrl+S] Lưu | [Ctrl+Z] Undo | [Ctrl+Y] Redo | [Space+Drag] Pan | [Del] Xóa",
            font=("Segoe UI", 8),
            foreground="#64748b"
        )
        self.lbl_info.pack(side=tk.RIGHT)

    def _setup_keybindings(self) -> None:
        self.root.bind("<Control-s>", lambda e: self._action_save())
        self.root.bind("<Control-z>", lambda e: self._action_undo())
        self.root.bind("<Control-y>", lambda e: self._action_redo())
        self.root.bind("<Control-Shift-Z>", lambda e: self._action_redo())

    # --------------------------------------------------------------------------
    # Callbacks
    # --------------------------------------------------------------------------

    def _on_canvas_selection_changed(self) -> None:
        self.props_panel.refresh()

    def _on_canvas_state_modified(self) -> None:
        self._sync_title()
        self.props_panel.refresh()

    # --------------------------------------------------------------------------
    # Toolbar Actions
    # --------------------------------------------------------------------------

    def _action_open(self) -> None:
        if self.state.is_dirty:
            resp = messagebox.askyesnocancel("Lưu thay đổi", "Sơ đồ hiện tại có thay đổi chưa lưu. Bạn có muốn lưu trước không?")
            if resp is None:
                return
            if resp is True:
                self._action_save()

        path = filedialog.askopenfilename(
            parent=self.root,
            title="Chọn tệp JSON Spec Diagram",
            filetypes=[("JSON Spec Files", "*.json"), ("All Files", "*.*")]
        )
        if path:
            self.state.load_from_json(path)
            self._sync_title()
            self.canvas_widget.clear_selection()
            self.canvas_widget.fit_view()

    def _action_save(self) -> bool:
        if not self.state.spec_path:
            path = filedialog.asksaveasfilename(
                parent=self.root,
                title="Lưu tệp JSON Spec Diagram",
                defaultextension=".json",
                filetypes=[("JSON Spec Files", "*.json"), ("All Files", "*.*")]
            )
            if not path:
                return False
            self.state.spec_path = path

        self.state.save_to_json()
        self._sync_title()
        messagebox.showinfo("Đã lưu", f"Đã lưu sơ đồ thành công vào:\n{self.state.spec_path}")
        return True

    def _action_export_png(self) -> None:
        # Prompt for PNG output path
        default_name = "diagram_export.png"
        if self.state.spec_path:
            base = os.path.splitext(os.path.basename(self.state.spec_path))[0]
            default_name = f"{base}.png"

        out_path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Xuất sơ đồ sang PNG độ nét cao (300+ DPI)",
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png")]
        )
        if not out_path:
            return

        try:
            # Build precision diagram from current state dict
            diag = PrecisionDiagram.from_spec(self.state.to_dict())
            meta = diag.render_to_png(out_path, scale=3)

            msg = (
                f"Xuất PNG thành công!\n\n"
                f"• Đường dẫn: {meta['png_path']}\n"
                f"• Kích thước: {meta['dimensions_px'][0]} x {meta['dimensions_px'][1]} px\n"
                f"• Tỷ lệ Scale: {meta['scale']}x (Publication-Grade)\n"
                f"• Dung lượng: {meta['file_size_bytes'] / 1024:.1f} KB"
            )
            messagebox.showinfo("Xuất PNG hoàn tất", msg)

            # Open file preview if on Windows
            if sys.platform == "win32":
                try:
                    os.startfile(out_path)
                except Exception:
                    pass

        except Exception as err:
            messagebox.showerror("Lỗi xuất PNG", f"Không thể xuất PNG bằng Chromium headless:\n{err}")

    def _action_add_node(self) -> None:
        """Add a new screen node at visible viewport center."""
        # Find unique new id
        base_id = "new_screen"
        idx = 1
        new_id = f"{base_id}_{idx}"
        while new_id in self.state.nodes:
            idx += 1
            new_id = f"{base_id}_{idx}"

        # Place near center of current view
        vw = self.canvas_widget.canvas.winfo_width() / 2.0
        vh = self.canvas_widget.canvas.winfo_height() / 2.0
        wx, wy = self.canvas_widget.screen_to_world(vw, vh)
        # Snap to grid
        wx = round(wx / DiagramCanvas.GRID_SIZE) * DiagramCanvas.GRID_SIZE
        wy = round(wy / DiagramCanvas.GRID_SIZE) * DiagramCanvas.GRID_SIZE

        ok, msg, node = self.state.add_node(
            node_id=new_id,
            label=f"New Screen {idx}",
            x=wx - 70,
            y=wy - 21,
            width=140,
            height=42,
            node_type="standard"
        )
        if ok:
            self._sync_title()
            self.canvas_widget.select_node(new_id)

    def _action_fit_view(self) -> None:
        self.canvas_widget.fit_view()

    def _action_undo(self) -> None:
        if self.state.undo():
            self._sync_title()
            self.canvas_widget.redraw_all()
            self.props_panel.refresh()

    def _action_redo(self) -> None:
        if self.state.redo():
            self._sync_title()
            self.canvas_widget.redraw_all()
            self.props_panel.refresh()

    def _action_check_collisions(self) -> None:
        """Run engine collision check between labels and nodes."""
        diag = PrecisionDiagram.from_spec(self.state.to_dict())
        warnings = diag.check_label_node_collisions()
        if not warnings:
            messagebox.showinfo("Kiểm tra va chạm", "✅ Tuyệt vời! Không phát hiện va chạm nào giữa nhãn và khối màn hình.")
        else:
            w_text = "\n".join(warnings[:10])
            if len(warnings) > 10:
                w_text += f"\n... và {len(warnings) - 10} cảnh báo khác."
            messagebox.showwarning("Cảnh báo va chạm", f"Phát hiện {len(warnings)} vị trí có thể bị che khuất:\n\n{w_text}")

    def _on_close(self) -> None:
        if self.state.is_dirty:
            resp = messagebox.askyesnocancel("Lưu thay đổi", "Sơ đồ có thay đổi chưa được lưu. Bạn có muốn lưu trước khi đóng?")
            if resp is None:
                return  # Cancel
            if resp is True:
                if not self._action_save():
                    return

        self.root.destroy()

    def run(self) -> None:
        if self.is_standalone:
            self.root.mainloop()


def open_diagram_editor(parent: Optional[tk.Tk | tk.Toplevel] = None, spec_path: Optional[str] = None) -> DiagramEditorApp:
    """Convenience helper to launch the editor window from another UI."""
    return DiagramEditorApp(master=parent, spec_path=spec_path)


# ==============================================================================
# CLI ENTRY POINT
# ==============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Precision Diagram Interactive Canvas Editor")
    parser.add_argument("--spec", "-s", type=str, default=None, help="Path to JSON spec diagram file")
    args = parser.parse_args()

    app = DiagramEditorApp(spec_path=args.spec)
    app.run()


if __name__ == "__main__":
    main()
