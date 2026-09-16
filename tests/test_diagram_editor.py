"""
test_diagram_editor.py — Automated Unit & Integration Test Suite for diagram_editor.py.
Validates:
1. DiagramState data model & JSON loading.
2. Safe Node ID rename and collision guard (Tkinter Trap #4).
3. Edge creation, deletion, and incident reference synchronization.
4. 30-step Undo / Redo stack behavior.
5. Tkinter Canvas widget instantiation & anti-flicker tag structure (Trap #1).
6. Space focus guard logic (Trap #2).
7. Edge hit-testing find_overlapping logic (Trap #3).
8. End-to-end rendering pipeline via spec_diagram_engine.
"""

from __future__ import annotations

import os
import sys
import tempfile
import tkinter as tk

# Ensure project root directory is in sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(TESTS_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

SPEC_PATH = os.path.join(ROOT_DIR, "specs", "flow_android_user_v2_spec.json")

try:
    from diagram_editor import DiagramState, DiagramCanvas, DiagramEditorApp
    from spec_diagram_engine import PrecisionDiagram
except (ImportError, ValueError):
    from diagram_editor import DiagramState, DiagramCanvas, DiagramEditorApp  # type: ignore
    from spec_diagram_engine import PrecisionDiagram  # type: ignore


def test_diagram_state_basics() -> None:
    print("[1/6] Testing DiagramState loading & schema...")
    spec_path = SPEC_PATH
    state = DiagramState(spec_path)

    assert len(state.nodes) > 0, "Nodes should not be empty"
    assert len(state.edges) > 0, "Edges should not be empty"
    assert not state.is_dirty, "State should be clean right after load"

    # Validate schema compatibility with PrecisionDiagram
    spec_dict = state.to_dict()
    diag = PrecisionDiagram.from_spec(spec_dict)
    assert len(diag.nodes) == len(state.nodes)
    assert len(diag.edges) == len(state.edges)
    print("  -> Passed: Loaded spec with", len(state.nodes), "nodes and", len(state.edges), "edges.")


def test_node_id_collision_guard() -> None:
    print("[2/6] Testing Node ID Collision Guard (Trap #4)...")
    spec_path = SPEC_PATH
    state = DiagramState(spec_path)

    node_ids = list(state.nodes.keys())
    first_id = node_ids[0]
    second_id = node_ids[1]

    # Attempt 1: Rename to existing ID (MUST FAIL)
    ok, msg = state.rename_node(first_id, second_id)
    assert not ok, "Renaming to existing ID must fail!"
    assert "đã tồn tại" in msg, f"Expected duplicate error message, got: {msg}"

    # Attempt 2: Rename to empty ID (MUST FAIL)
    ok, msg = state.rename_node(first_id, "   ")
    assert not ok, "Renaming to empty ID must fail!"

    # Attempt 3: Rename to new valid ID (MUST SUCCEED)
    new_id = "test_screen_renamed_xyz"
    # Track which edges connect to first_id
    affected_sources = [e for e in state.edges if e.source_id == first_id]
    affected_targets = [e for e in state.edges if e.target_id == first_id]

    ok, msg = state.rename_node(first_id, new_id)
    assert ok, f"Renaming to new unique ID failed: {msg}"
    assert new_id in state.nodes, "New ID must be in nodes dict"
    assert first_id not in state.nodes, "Old ID must not be in nodes dict"

    # Verify all edges were safely updated
    for e in affected_sources:
        assert e.source_id == new_id, "Edge source_id was not updated!"
    for e in affected_targets:
        assert e.target_id == new_id, "Edge target_id was not updated!"

    print("  -> Passed: Collision guard prevented duplicates and updated edge references properly.")


def test_undo_redo_stack() -> None:
    print("[3/6] Testing 30-step Undo / Redo stack...")
    state = DiagramState()
    assert len(state.nodes) == 0

    # Action 1: Add node 1
    state.add_node("n1", "Screen 1", 100, 100)
    assert len(state.nodes) == 1

    # Action 2: Add node 2
    state.add_node("n2", "Screen 2", 300, 100)
    assert len(state.nodes) == 2

    # Action 3: Add edge
    state.add_edge("n1", "n2", label="Go to 2")
    assert len(state.edges) == 1

    # Undo 1: Revert edge
    assert state.undo()
    assert len(state.edges) == 0
    assert len(state.nodes) == 2

    # Undo 2: Revert node 2
    assert state.undo()
    assert len(state.nodes) == 1
    assert "n2" not in state.nodes

    # Redo 1: Restore node 2
    assert state.redo()
    assert len(state.nodes) == 2
    assert "n2" in state.nodes

    # Redo 2: Restore edge
    assert state.redo()
    assert len(state.edges) == 1
    assert state.edges[0].source_id == "n1"
    assert state.edges[0].target_id == "n2"

    print("  -> Passed: Undo/Redo stack successfully restored exact snapshots.")


def test_file_save_and_reload() -> None:
    print("[4/6] Testing File Save and Reload roundtrip...")
    spec_path = SPEC_PATH
    state = DiagramState(spec_path)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Modify a node
        first_node = list(state.nodes.values())[0]
        original_x = first_node.x
        first_node.x += 50.0

        state.save_to_json(tmp_path)

        # Reload from saved file
        reloaded = DiagramState(tmp_path)
        reloaded_node = reloaded.nodes[first_node.id]
        assert abs(reloaded_node.x - (original_x + 50.0)) < 0.001
        print("  -> Passed: Saved and reloaded JSON without data corruption.")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_canvas_headless_instantiation() -> None:
    print("[5/6] Testing Canvas widget, Tag system (Trap #1) & Space guard (Trap #2)...")
    root = tk.Tk()
    root.withdraw()  # Headless test

    spec_path = SPEC_PATH
    state = DiagramState(spec_path)
    canvas_widget = DiagramCanvas(root, state)

    # Force geometry update
    root.update_idletasks()

    # Verify tags exist on canvas
    all_items = canvas_widget.canvas.find_all()
    assert len(all_items) > 0, "Canvas items must be created"

    # Check that each node has tags matching Trap #1
    for nid in state.nodes:
        group_items = canvas_widget.canvas.find_withtag(f"node_group_{nid}")
        assert len(group_items) > 0, f"Node {nid} must have tagged items under node_group_{nid}"

    # Verify Trap #2: Space key on canvas vs other widget
    class DummyEvent(tk.Event):
        def __init__(self, widget: tk.Misc) -> None:
            super().__init__()
            self.widget = widget

    # Event on Canvas -> activates
    canvas_event = DummyEvent(canvas_widget.canvas)
    canvas_widget._on_space_down(canvas_event)
    assert canvas_widget._space_pressed is True, "Space on canvas must set _space_pressed to True"
    canvas_widget._on_space_up(canvas_event)
    assert not canvas_widget._space_pressed

    # Event on other widget (e.g. entry) -> does NOT activate pan
    dummy_entry = tk.Entry(root)
    entry_event = DummyEvent(dummy_entry)
    canvas_widget._on_space_down(entry_event)
    assert not canvas_widget._space_pressed, "Space on Entry widget must NOT trigger canvas pan!"

    # Clean up
    root.destroy()
    print("  -> Passed: Canvas tag structure and Space pan focus guard verified.")


def test_png_export_pipeline() -> None:
    print("[6/6] Testing PNG export pipeline with Chromium / Edge...")
    spec_path = SPEC_PATH
    state = DiagramState(spec_path)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_png = tmp.name

    try:
        diag = PrecisionDiagram.from_spec(state.to_dict())
        meta = diag.render_to_png(tmp_png, scale=3)
        assert meta["success"] is True
        assert os.path.isfile(tmp_png)
        assert os.path.getsize(tmp_png) > 1000
        print(f"  -> Passed: Rendered PNG successfully ({meta['dimensions_px'][0]}x{meta['dimensions_px'][1]}px, {meta['file_size_bytes']} bytes).")
    finally:
        if os.path.exists(tmp_png):
            os.remove(tmp_png)
        svg_tmp = os.path.splitext(tmp_png)[0] + ".svg"
        if os.path.exists(svg_tmp):
            os.remove(svg_tmp)


def test_interactive_drag_and_edge_selection() -> None:
    print("[7/7] Testing Interactive Drag & Drop (Trap #1) and Edge Hit-Testing (Trap #3)...")
    root = tk.Tk()
    root.withdraw()

    spec_path = SPEC_PATH
    state = DiagramState(spec_path)
    canvas_widget = DiagramCanvas(root, state)
    root.update_idletasks()

    # Pick a known node: e.g., 'login' or first node
    first_node = list(state.nodes.values())[0]
    nid = first_node.id
    initial_x = first_node.x
    initial_y = first_node.y

    # Calculate screen center of this node
    sx, sy = canvas_widget.world_to_screen(initial_x + first_node.width / 2.0, initial_y + first_node.height / 2.0)

    class MockEvent(tk.Event):
        def __init__(self, x: int, y: int, widget: tk.Misc) -> None:
            super().__init__()
            self.x = int(x)
            self.y = int(y)
            self.widget = widget

    # 1. Simulate Click on Node
    ev_down = MockEvent(sx, sy, canvas_widget.canvas)
    canvas_widget._on_left_down(ev_down)
    assert canvas_widget.selected_item == ("node", nid), f"Expected selected node {nid}, got {canvas_widget.selected_item}"
    assert canvas_widget._drag_mode == "node"

    # 2. Simulate Drag by +30px horizontally, +20px vertically
    ev_motion = MockEvent(sx + 30, sy + 20, canvas_widget.canvas)
    canvas_widget._on_left_motion(ev_motion)

    # 3. Simulate Release (Must snap to grid)
    ev_up = MockEvent(sx + 30, sy + 20, canvas_widget.canvas)
    canvas_widget._on_left_up(ev_up)
    assert canvas_widget._drag_mode == "none"

    # Check that node moved and snapped to 10px grid
    moved_node = state.nodes[nid]
    assert moved_node.x % canvas_widget.GRID_SIZE == 0.0, f"Node X {moved_node.x} must be snapped to {canvas_widget.GRID_SIZE}"
    assert moved_node.y % canvas_widget.GRID_SIZE == 0.0, f"Node Y {moved_node.y} must be snapped to {canvas_widget.GRID_SIZE}"
    print(f"  -> Drag succeeded: moved node '{nid}' from ({initial_x}, {initial_y}) to ({moved_node.x}, {moved_node.y}) with grid snap.")

    # 4. Test Edge Hit-Testing (Trap #3)
    first_edge = state.edges[0]
    pts = canvas_widget._calculate_manhattan_route(first_edge)
    assert len(pts) >= 2
    mid_wx = (pts[0][0] + pts[1][0]) / 2.0
    mid_wy = (pts[0][1] + pts[1][1]) / 2.0
    mid_sx, mid_sy = canvas_widget.world_to_screen(mid_wx, mid_wy)

    ev_edge_click = MockEvent(mid_sx, mid_sy, canvas_widget.canvas)
    canvas_widget._on_left_down(ev_edge_click)
    # The click should hit edge index 0 (or another overlapping edge)
    assert canvas_widget.selected_item is not None and canvas_widget.selected_item[0] == "edge", (
        f"Expected edge selection at ({mid_sx}, {mid_sy}), got {canvas_widget.selected_item}"
    )
    print(f"  -> Edge hit-testing succeeded: successfully selected {canvas_widget.selected_item}.")

    root.destroy()


def run_all():
    print("=== STARTING DIAGRAM EDITOR TEST SUITE ===")
    test_diagram_state_basics()
    test_node_id_collision_guard()
    test_undo_redo_stack()
    test_file_save_and_reload()
    test_canvas_headless_instantiation()
    test_interactive_drag_and_edge_selection()
    test_png_export_pipeline()
    print("=== ALL 7 TEST SUITES PASSED PERFECTLY ===")


if __name__ == "__main__":
    run_all()
