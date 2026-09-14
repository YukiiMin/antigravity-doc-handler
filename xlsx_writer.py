"""
xlsx_writer.py — JSON Snapshot → XLSX for AI editing round-trip.

Takes a JSON snapshot (produced by xlsx_reader.py) and writes it back
to an XLSX file using xlwings (requires Microsoft Excel to be installed).

Supports writing:
  - Cell values and formulas
  - Cell formatting: font name/size/bold/italic/color, fill color, number format
  - Merged cell ranges

NOTE: Chart objects and images are not re-created (read-only in v1).
"""

from __future__ import annotations

import json
import os
from typing import Any


def _hex_to_rgb_tuple(hex_color: str | None) -> tuple[int, int, int] | None:
    """Convert '#RRGGBB' hex string to (R, G, B) tuple for xlwings."""
    if not hex_color:
        return None
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return None
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return None


def _write_sheet(wb, sheet_data: dict[str, Any]) -> None:
    """Write a single sheet from snapshot data into the workbook."""
    sheet_name = sheet_data.get("sheet_name", "Sheet1")

    # Get or create the sheet
    if sheet_name in [s.name for s in wb.sheets]:
        sheet = wb.sheets[sheet_name]
    else:
        sheet = wb.sheets.add(name=sheet_name)

    for cell_data in sheet_data.get("cells", []):
        addr    = cell_data.get("address")
        formula = cell_data.get("formula")
        value   = cell_data.get("value")

        if not addr:
            continue

        cell = sheet.range(addr)

        # Write formula if present, otherwise write value
        if formula and str(formula).startswith("="):
            cell.formula = formula
        else:
            cell.value = value

        # Apply formatting
        fmt = cell_data.get("format", {})
        if not fmt:
            continue

        try:
            font = cell.font
            if fmt.get("font_name"):
                font.name = fmt["font_name"]
            if fmt.get("font_size") is not None:
                font.size = fmt["font_size"]
            if fmt.get("bold") is not None:
                font.bold = fmt["bold"]
            if fmt.get("italic") is not None:
                font.italic = fmt["italic"]
            font_color = _hex_to_rgb_tuple(fmt.get("font_color"))
            if font_color:
                font.color = font_color
        except Exception:
            pass

        try:
            fill_color = _hex_to_rgb_tuple(fmt.get("fill_color"))
            if fill_color:
                cell.color = fill_color
        except Exception:
            pass

        try:
            if fmt.get("number_format"):
                cell.number_format = fmt["number_format"]
        except Exception:
            pass

    # Apply merged cells last (after values are written)
    for merge_range in sheet_data.get("merged_cells", []):
        try:
            sheet.range(merge_range).merge()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_xlsx(
    snapshot: dict[str, Any],
    output_path: str,
    template_path: str | None = None,
) -> str:
    """
    Write an XLSX file from a JSON snapshot.

    Args:
        snapshot:      Dict produced by xlsx_reader.read_xlsx().
        output_path:   Destination .xlsx path.
        template_path: Optional original XLSX to use as template base.
                       When provided, opens the template and writes into it.

    Returns:
        Absolute path of the written file.
    """
    try:
        import xlwings as xw
    except ImportError as exc:
        raise ImportError(
            "xlwings is required for xlsx-write. Install with: pip install xlwings"
        ) from exc

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    app = xw.App(visible=False, add_book=False)
    try:
        if template_path and os.path.isfile(template_path):
            wb = app.books.open(os.path.abspath(template_path))
        else:
            wb = app.books.add()

        try:
            for sheet_data in snapshot.get("sheets", []):
                _write_sheet(wb, sheet_data)

            wb.save(os.path.abspath(output_path))
            return os.path.abspath(output_path)
        finally:
            wb.close()
    finally:
        app.quit()


def write_xlsx_from_json_file(
    json_path: str,
    output_path: str,
    template_path: str | None = None,
) -> str:
    """
    Load a JSON snapshot from file and write it to an XLSX.

    Args:
        json_path:     Path to the .json snapshot file.
        output_path:   Destination .xlsx path.
        template_path: Optional original XLSX for style anchoring.

    Returns:
        Absolute path of the written XLSX.
    """
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"JSON snapshot not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    return write_xlsx(snapshot, output_path, template_path)
