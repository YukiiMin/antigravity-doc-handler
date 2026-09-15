"""
ai_tools_cli.py — CLI toolkit for AI-driven document editing.

Provides structured read/write/diff operations on DOCX and XLSX files,
outputting JSON snapshots that AI (Antigravity IDE) can read and modify.

Subcommands:
  docx-read       — Read DOCX → JSON snapshot
  docx-write      — Write JSON snapshot → DOCX (with optional style template)
  docx-diff       — Compare two JSON snapshots → before/after diff report
  docx-inject     — Surgically inject paragraphs, runs, and images into DOCX
  mermaid-render  — Render Mermaid code to high-res PNG and inject into DOCX
  plantuml-render — Render PlantUML code to high-res PNG and inject into DOCX
  diagram-render  — Unified multi-engine dispatcher (canvas | mermaid | plantuml)
  spec-render     — Render SVG Canvas Precision Diagram to high-res PNG
  diagram-editor  — Interactive Canvas Editor for Precision Diagram JSON specs
  xlsx-read       — Read XLSX → JSON snapshot (xlwings, requires Excel)
  xlsx-write      — Write JSON snapshot → XLSX

Usage examples:
  python ai_tools_cli.py diagram-render --spec spec.json -o out.png
  python ai_tools_cli.py plantuml-render erd_spec.json -o erd.png
  python ai_tools_cli.py docx-read file.docx -o snap.json
  python ai_tools_cli.py docx-write snap.json --template file.docx -o out.docx
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            getattr(sys.stderr, "reconfigure")(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# docx-read
# ---------------------------------------------------------------------------

def cmd_docx_read(args: argparse.Namespace) -> int:
    from .docx_reader import read_docx_to_json

    src = os.path.abspath(args.file)
    if not os.path.isfile(src):
        print(f"[ERROR] File not found: {src}", file=sys.stderr)
        return 1

    t0 = time.time()
    try:
        result = read_docx_to_json(src, output_path=args.output)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    elapsed = time.time() - t0
    if args.output:
        print(f"[OK] Snapshot written to: {result}  ({elapsed:.2f}s)")
    else:
        print(result)
    return 0


# ---------------------------------------------------------------------------
# docx-write
# ---------------------------------------------------------------------------

def cmd_docx_write(args: argparse.Namespace) -> int:
    from .docx_writer import write_docx_from_json_file

    json_path = os.path.abspath(args.snapshot)
    if not os.path.isfile(json_path):
        print(f"[ERROR] Snapshot not found: {json_path}", file=sys.stderr)
        return 1

    template_path = os.path.abspath(args.template) if args.template else None
    if template_path and not os.path.isfile(template_path):
        print(f"[ERROR] Template DOCX not found: {template_path}", file=sys.stderr)
        return 1

    output_path = args.output or os.path.splitext(json_path)[0] + "_written.docx"
    output_path = os.path.abspath(output_path)

    t0 = time.time()
    try:
        result = write_docx_from_json_file(json_path, output_path, template_path)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    elapsed = time.time() - t0
    print(f"[OK] DOCX written to: {result}  ({elapsed:.2f}s)")
    return 0


# ---------------------------------------------------------------------------
# docx-inject
# ---------------------------------------------------------------------------

def cmd_docx_inject(args: argparse.Namespace) -> int:
    from .docx_writer import inject_content_into_docx

    src = os.path.abspath(args.file)
    if not os.path.isfile(src):
        print(f"[ERROR] Source DOCX not found: {src}", file=sys.stderr)
        return 1

    spec_path = os.path.abspath(args.spec)
    if not os.path.isfile(spec_path):
        print(f"[ERROR] Injection spec JSON not found: {spec_path}", file=sys.stderr)
        return 1

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    out_path = os.path.abspath(args.output) if args.output else src

    t0 = time.time()
    try:
        result = inject_content_into_docx(src, spec, out_path)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    elapsed = time.time() - t0
    print(f"[OK] Content injected into: {result}  ({elapsed:.2f}s)")
    return 0


# ---------------------------------------------------------------------------
# mermaid-render
# ---------------------------------------------------------------------------

def cmd_mermaid_render(args: argparse.Namespace) -> int:
    from .mermaid_renderer import render_mermaid_to_png

    spec_path = os.path.abspath(args.spec)
    if not os.path.isfile(spec_path):
        print(f"[ERROR] Mermaid spec JSON not found: {spec_path}", file=sys.stderr)
        return 1

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # CLI flag overrides
    if args.output:
        spec["output_path"] = args.output
    if args.inject:
        spec["inject_into"] = args.inject
    if args.theme:
        spec["theme_preset"] = args.theme
    if args.scale:
        spec["scale"] = args.scale

    base_dir = os.path.dirname(spec_path)
    t0 = time.time()
    try:
        result = render_mermaid_to_png(spec, base_dir=base_dir)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    elapsed = time.time() - t0
    png_path = result["png_path"]
    w_cm = result["width_cm"]
    h_cm = result["height_cm"]
    w_px, h_px = result["dimensions_px"]
    f_size = result["file_size_bytes"]

    print(f"[OK] Diagram rendered: {png_path}  ({elapsed:.2f}s)")
    print(f"     Resolution: {w_px}x{h_px}px | Doc Layout: {w_cm}cm x {h_cm}cm | Size: {f_size} bytes")

    if result.get("injected"):
        print(f"[OK] Injected into DOCX: {result.get('docx_path')}")

    return 0


# ---------------------------------------------------------------------------
# plantuml-render
# ---------------------------------------------------------------------------

def cmd_plantuml_render(args: argparse.Namespace) -> int:
    try:
        from .plantuml_renderer import render_plantuml_to_png
    except (ImportError, ValueError):
        from plantuml_renderer import render_plantuml_to_png  # type: ignore

    spec_path = os.path.abspath(args.spec)
    if not os.path.isfile(spec_path):
        print(f"[ERROR] PlantUML spec JSON not found: {spec_path}", file=sys.stderr)
        return 1

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    if args.output:
        spec["output_path"] = args.output
    if args.inject:
        spec["inject_into"] = args.inject
    if args.dpi:
        spec["dpi"] = args.dpi

    base_dir = os.path.dirname(spec_path)
    t0 = time.time()
    try:
        result = render_plantuml_to_png(spec, base_dir=base_dir)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    elapsed = time.time() - t0
    png_path = result["png_path"]
    w_cm = result["width_cm"]
    h_cm = result["height_cm"]
    w_px, h_px = result["dimensions_px"]
    f_size = result["file_size_bytes"]

    print(f"[OK] PlantUML diagram rendered: {png_path}  ({elapsed:.2f}s)")
    print(f"     Resolution: {w_px}x{h_px}px | Doc Layout: {w_cm}cm x {h_cm}cm | Size: {f_size} bytes")

    if result.get("injected"):
        print(f"[OK] Injected into DOCX: {result.get('docx_path')}")

    return 0


# ---------------------------------------------------------------------------
# diagram-render (Unified Multi-Engine Technical Diagram Dispatcher)
# ---------------------------------------------------------------------------

def cmd_diagram_render(args: argparse.Namespace) -> int:
    spec_path = os.path.abspath(args.spec)
    if not os.path.isfile(spec_path):
        print(f"[ERROR] Spec file not found: {spec_path}", file=sys.stderr)
        return 1

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    if args.output:
        spec["output_path"] = args.output
    if args.inject:
        spec["inject_into"] = args.inject

    engine = str(spec.get("engine", "canvas")).strip().lower()
    base_dir = os.path.dirname(spec_path)
    out_png = args.output or spec.get("output_path") or os.path.splitext(spec_path)[0] + ".png"
    out_png = os.path.abspath(out_png)
    spec["output_path"] = out_png

    t0 = time.time()
    try:
        if engine == "canvas":
            try:
                from .spec_diagram_engine import PrecisionDiagram
            except (ImportError, ValueError):
                from spec_diagram_engine import PrecisionDiagram  # type: ignore
            scale = args.scale if args.scale is not None else spec.get("scale", 3)
            diag = PrecisionDiagram.from_spec(spec)
            result = diag.render_to_png(out_png, scale=scale)
        elif engine == "mermaid":
            try:
                from .mermaid_renderer import render_mermaid_to_png
            except (ImportError, ValueError):
                from mermaid_renderer import render_mermaid_to_png  # type: ignore
            result = render_mermaid_to_png(spec, base_dir=base_dir)
        elif engine == "plantuml":
            try:
                from .plantuml_renderer import render_plantuml_to_png
            except (ImportError, ValueError):
                from plantuml_renderer import render_plantuml_to_png  # type: ignore
            result = render_plantuml_to_png(spec, base_dir=base_dir)
        else:
            raise ValueError(f"Unknown diagram engine: '{engine}'. Supported: 'canvas', 'mermaid', 'plantuml'")
    except Exception as exc:
        print(f"[ERROR] Diagram rendering failed ({engine}): {exc}", file=sys.stderr)
        return 2

    elapsed = time.time() - t0
    w_px, h_px = result["dimensions_px"]
    f_size = result["file_size_bytes"]
    print(f"[OK] {engine.upper()} diagram rendered: {result['png_path']}  ({elapsed:.2f}s)")
    print(f"     Resolution: {w_px}x{h_px}px | Size: {f_size} bytes")

    # Windows Trap 4: Sau khi render ra result["png_path"] thành công:
    # Auto-inject vào Word nếu spec có inject_into và chưa được inject
    docx_target = spec.get("inject_into")
    if docx_target and not result.get("injected"):
        if not os.path.isabs(docx_target) and base_dir:
            docx_target = os.path.abspath(os.path.join(base_dir, docx_target))
        if os.path.exists(docx_target):
            try:
                from .docx_writer import inject_diagram_into_docx
            except (ImportError, ValueError):
                from docx_writer import inject_diagram_into_docx  # type: ignore
            inject_diagram_into_docx(
                docx_path=docx_target,
                png_path=result["png_path"],
                heading=spec.get("target_heading"),
                placeholder=spec.get("placeholder"),
                caption=spec.get("caption_template") or spec.get("caption"),
                width_cm=spec.get("width_cm", 14.0),
                max_height_cm=spec.get("max_height_cm", 20.0),
            )
            print(f"[OK] Injected diagram into {docx_target}")
        else:
            print(f"[WARN] Target DOCX for injection not found: {docx_target}")
    elif result.get("injected"):
        print(f"[OK] Injected diagram into {docx_target}")

    return 0


# ---------------------------------------------------------------------------
# spec-render (Precision Technical & Architecture Diagram Engine)
# ---------------------------------------------------------------------------

def cmd_spec_render(args: argparse.Namespace) -> int:
    from .spec_diagram_engine import PrecisionDiagram

    spec_path = os.path.abspath(args.spec)
    if not os.path.isfile(spec_path):
        print(f"[ERROR] Spec file not found: {spec_path}", file=sys.stderr)
        return 1

    with open(spec_path, "r", encoding="utf-8") as f:
        spec_dict = json.load(f)

    out_png = args.output or spec_dict.get("output_path") or os.path.splitext(spec_path)[0] + ".png"
    out_png = os.path.abspath(out_png)
    scale = args.scale if args.scale is not None else spec_dict.get("scale", 3)

    t0 = time.time()
    try:
        diag = PrecisionDiagram.from_spec(spec_dict)
        res = diag.render_to_png(out_png, scale=scale)
    except Exception as exc:
        print(f"[ERROR] Precision diagram rendering failed: {exc}", file=sys.stderr)
        return 2

    elapsed = time.time() - t0
    w_px, h_px = res["dimensions_px"]
    f_size = res["file_size_bytes"]
    ar = res["aspect_ratio"]

    print(f"[OK] Precision Diagram rendered: {res['png_path']}  ({elapsed:.2f}s)")
    print(f"     Resolution: {w_px}x{h_px}px | Aspect Ratio: {ar}:1 | Size: {f_size} bytes | Scale: {scale}x")
    return 0


def cmd_diagram_editor(args: argparse.Namespace) -> int:
    try:
        from .diagram_editor import DiagramEditorApp
    except (ImportError, ValueError):
        from diagram_editor import DiagramEditorApp  # type: ignore
    app = DiagramEditorApp(spec_path=args.spec)
    app.run()
    return 0

def _flatten_body(body: list[dict]) -> dict[int, dict]:
    """Return {element_index: element} mapping."""
    return {el.get("element_index", i): el for i, el in enumerate(body)}


def cmd_docx_diff(args: argparse.Namespace) -> int:
    before_path = os.path.abspath(args.before)
    after_path  = os.path.abspath(args.after)

    for p in (before_path, after_path):
        if not os.path.isfile(p):
            print(f"[ERROR] File not found: {p}", file=sys.stderr)
            return 1

    with open(before_path, "r", encoding="utf-8") as f:
        before_snap = json.load(f)
    with open(after_path, "r", encoding="utf-8") as f:
        after_snap = json.load(f)

    before_body = _flatten_body(before_snap.get("body", []))
    after_body  = _flatten_body(after_snap.get("body", []))

    all_indices = sorted(set(before_body.keys()) | set(after_body.keys()))

    changes = []
    for idx in all_indices:
        b = before_body.get(idx)
        a = after_body.get(idx)

        if b == a:
            continue  # No change

        entry: dict = {"element_index": idx}
        if b is None:
            entry["change_type"] = "added"
            entry["after"] = a
        elif a is None:
            entry["change_type"] = "removed"
            entry["before"] = b
        else:
            entry["change_type"] = "modified"
            entry["before"] = b
            entry["after"] = a

        changes.append(entry)

    diff_report = {
        "before_file": before_snap.get("source_file", before_path),
        "after_file":  after_snap.get("source_file", after_path),
        "total_before_elements": len(before_body),
        "total_after_elements":  len(after_body),
        "total_changes": len(changes),
        "changes": changes,
    }

    json_str = json.dumps(diff_report, ensure_ascii=False, indent=2)

    if args.output:
        out_path = os.path.abspath(args.output)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"[OK] Diff report written to: {out_path}  ({len(changes)} changes)")
    else:
        print(json_str)

    return 0


# ---------------------------------------------------------------------------
# xlsx-read
# ---------------------------------------------------------------------------

def cmd_xlsx_read(args: argparse.Namespace) -> int:
    from .xlsx_reader import read_xlsx_to_json

    src = os.path.abspath(args.file)
    if not os.path.isfile(src):
        print(f"[ERROR] File not found: {src}", file=sys.stderr)
        return 1

    t0 = time.time()
    try:
        result = read_xlsx_to_json(
            src,
            output_path=args.output,
            sheet_name=args.sheet,
            cell_range=args.range,
        )
    except ImportError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    elapsed = time.time() - t0
    if args.output:
        print(f"[OK] Snapshot written to: {result}  ({elapsed:.2f}s)")
    else:
        print(result)
    return 0


# ---------------------------------------------------------------------------
# xlsx-write
# ---------------------------------------------------------------------------

def cmd_xlsx_write(args: argparse.Namespace) -> int:
    from .xlsx_writer import write_xlsx_from_json_file

    json_path = os.path.abspath(args.snapshot)
    if not os.path.isfile(json_path):
        print(f"[ERROR] Snapshot not found: {json_path}", file=sys.stderr)
        return 1

    template_path = os.path.abspath(args.template) if args.template else None
    if template_path and not os.path.isfile(template_path):
        print(f"[ERROR] Template XLSX not found: {template_path}", file=sys.stderr)
        return 1

    output_path = args.output or os.path.splitext(json_path)[0] + "_written.xlsx"
    output_path = os.path.abspath(output_path)

    t0 = time.time()
    try:
        result = write_xlsx_from_json_file(json_path, output_path, template_path)
    except ImportError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    elapsed = time.time() - t0
    print(f"[OK] XLSX written to: {result}  ({elapsed:.2f}s)")
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai_tools_cli",
        description=(
            "AI Document Editing Toolkit — Read/write DOCX and XLSX as JSON snapshots.\n"
            "Designed for Antigravity IDE to edit non-source-code files directly."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Read DOCX to JSON snapshot:
  python ai_tools_cli.py docx-read report.docx -o report_snap.json

  # Write modified snapshot back to DOCX (with original as style anchor):
  python ai_tools_cli.py docx-write report_snap.json --template report.docx -o report_v2.docx

  # Compare two snapshots (before AI edit vs after):
  python ai_tools_cli.py docx-diff before.json after.json -o diff.json

  # Read XLSX (specific sheet + range):
  python ai_tools_cli.py xlsx-read data.xlsx --sheet "Q1 Report" --range "A1:H50" -o snap.json

  # Write XLSX from snapshot (with original as template):
  python ai_tools_cli.py xlsx-write snap.json --template data.xlsx -o data_v2.xlsx
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- docx-read ---
    p_dr = sub.add_parser("docx-read", help="Read DOCX → JSON snapshot")
    p_dr.add_argument("file", help="Path to source .docx file")
    p_dr.add_argument("-o", "--output", default=None,
                      help="Output JSON file path (prints to stdout if omitted)")
    p_dr.set_defaults(func=cmd_docx_read)

    # --- docx-write ---
    p_dw = sub.add_parser("docx-write", help="Write JSON snapshot → DOCX")
    p_dw.add_argument("snapshot", help="Path to .json snapshot file")
    p_dw.add_argument("--template", default=None,
                      help="Path to original .docx to use as style anchor (recommended)")
    p_dw.add_argument("-o", "--output", default=None,
                      help="Output .docx path (default: <snapshot>_written.docx)")
    p_dw.set_defaults(func=cmd_docx_write)

    # --- docx-inject ---
    p_di = sub.add_parser(
        "docx-inject",
        help="Surgically inject paragraphs, runs, and images into an existing DOCX without rewriting",
    )
    p_di.add_argument("file", help="Path to source/target .docx file")
    p_di.add_argument("spec", help="Path to injection spec .json file")
    p_di.add_argument(
        "-o", "--output", default=None,
        help="Output .docx path (defaults to in-place overwrite of source file)",
    )
    p_di.set_defaults(func=cmd_docx_inject)

    # --- mermaid-render ---
    p_mr = sub.add_parser(
        "mermaid-render",
        help="Render Mermaid diagram from spec JSON to high-res PNG and optionally inject into DOCX",
    )
    p_mr.add_argument("spec", help="Path to mermaid diagram spec .json file")
    p_mr.add_argument("-o", "--output", default=None,
                      help="Override output PNG path")
    p_mr.add_argument("--inject", default=None,
                      help="Override target .docx to inject into")
    p_mr.add_argument("--theme", default=None,
                      help="Override theme preset ('clean_modern', 'enterprise', or json path)")
    p_mr.add_argument("--scale", type=int, default=None,
                      help="Override scale factor (default: 2)")
    p_mr.set_defaults(func=cmd_mermaid_render)

    # --- plantuml-render ---
    p_pr = sub.add_parser(
        "plantuml-render",
        help="Render PlantUML diagram from spec JSON to high-res PNG and optionally inject into DOCX",
    )
    p_pr.add_argument("spec", help="Path to plantuml diagram spec .json file")
    p_pr.add_argument("-o", "--output", default=None,
                      help="Override output PNG path")
    p_pr.add_argument("--inject", default=None,
                      help="Override target .docx to inject into")
    p_pr.add_argument("--dpi", type=int, default=300,
                      help="Override DPI (default: 300)")
    p_pr.set_defaults(func=cmd_plantuml_render)

    # --- diagram-render (Unified Dispatcher) ---
    p_dr = sub.add_parser(
        "diagram-render",
        help="Unified multi-engine diagram dispatcher (reads 'engine': 'canvas' | 'mermaid' | 'plantuml')",
    )
    p_dr.add_argument("spec", help="Path to unified diagram spec .json file")
    p_dr.add_argument("-o", "--output", default=None,
                      help="Override output PNG path")
    p_dr.add_argument("--inject", default=None,
                      help="Override target .docx to inject into")
    p_dr.add_argument("--scale", type=int, default=None,
                      help="Override scale factor for canvas engine (default: 3)")
    p_dr.set_defaults(func=cmd_diagram_render)

    # --- spec-render ---
    p_sr = sub.add_parser(
        "spec-render",
        help="Render Precision Technical & Architecture diagram from spec JSON to high-res PNG (Chromium 300+ DPI)",
    )
    p_sr.add_argument("spec", help="Path to precision diagram spec .json file")
    p_sr.add_argument("-o", "--output", default=None,
                      help="Override output PNG path")
    p_sr.add_argument("--scale", type=int, default=None,
                      help="Override scale factor (default: 3)")
    p_sr.set_defaults(func=cmd_spec_render)

    # --- diagram-editor ---
    p_de = sub.add_parser(
        "diagram-editor",
        help="Launch Interactive Canvas Editor for Precision Diagram JSON specs",
    )
    p_de.add_argument("spec", nargs="?", default=None, help="Path to precision diagram spec .json file (optional)")
    p_de.set_defaults(func=cmd_diagram_editor)


    # --- docx-diff ---
    p_dd = sub.add_parser("docx-diff", help="Compare two JSON snapshots → diff report")
    p_dd.add_argument("before", help="Path to 'before' .json snapshot")
    p_dd.add_argument("after",  help="Path to 'after'  .json snapshot")
    p_dd.add_argument("-o", "--output", default=None,
                      help="Output diff report .json (prints to stdout if omitted)")
    p_dd.set_defaults(func=cmd_docx_diff)

    # --- xlsx-read ---
    p_xr = sub.add_parser("xlsx-read", help="Read XLSX → JSON snapshot (requires Excel)")
    p_xr.add_argument("file", help="Path to source .xlsx file")
    p_xr.add_argument("--sheet", default=None,
                      help="Sheet name to export (exports all sheets if omitted)")
    p_xr.add_argument("--range", default=None,
                      help="Cell range to limit export, e.g. 'A1:H20' (requires --sheet)")
    p_xr.add_argument("-o", "--output", default=None,
                      help="Output JSON file path (prints to stdout if omitted)")
    p_xr.set_defaults(func=cmd_xlsx_read)

    # --- xlsx-write ---
    p_xw = sub.add_parser("xlsx-write", help="Write JSON snapshot → XLSX (requires Excel)")
    p_xw.add_argument("snapshot", help="Path to .json snapshot file")
    p_xw.add_argument("--template", default=None,
                      help="Path to original .xlsx to use as base (optional)")
    p_xw.add_argument("-o", "--output", default=None,
                      help="Output .xlsx path (default: <snapshot>_written.xlsx)")
    p_xw.set_defaults(func=cmd_xlsx_write)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
