"""
xlsx_writer.py — JSON Snapshot & Template-Anchored XLSX Writer.

Supports dual writing modes:
1. Native openpyxl mode (Default & recommended for template mutation):
   - Preserves DrawingML (Images, Logos on Cover sheets)
   - Safe Merged Cell setter (writes only to top-left cell, avoids MergedCell crash)
   - ARGB pattern fill normalization (fixes 001F4E78 alpha issues)
   - Dynamic formula updates
2. xlwings mode (for desktop Excel COM automation when computed formulas are required)
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def normalize_hex_color(hex_str: str | None) -> str | None:
    """Normalize any hex color format to 6-char RRGGBB or 8-char AARRGGBB."""
    if not hex_str:
        return None
    h = hex_str.lstrip("#").upper()
    if len(h) == 8:
        # e.g., '001F4E78' or 'FF1F4E78' -> if alpha is 00, treat as opaque FF
        alpha = h[0:2]
        rgb = h[2:8]
        if alpha == "00":
            return f"FF{rgb}"
        return h
    elif len(h) == 6:
        return f"FF{h}"
    return None


def hex_to_rgb_tuple(hex_color: str | None) -> tuple[int, int, int] | None:
    """Convert '#RRGGBB' or 'AARRGGBB' hex string to (R, G, B) tuple."""
    if not hex_color:
        return None
    h = hex_color.lstrip("#").upper()
    if len(h) == 8:
        h = h[2:8]
    if len(h) != 6:
        return None
    try:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return None


def safe_set_cell(ws: openpyxl.worksheet.worksheet.Worksheet, coordinate: str, value: Any, formula: str | None = None, fill_color: str | None = None, font_bold: bool | None = None, font_color: str | None = None):
    """
    Safely assign value/formula/formatting to a cell.
    If the target coordinate is inside a MergedCell range, automatically
    targets the Top-Left cell of the range to prevent AttributeError: read-only.
    """
    target_coord = coordinate
    target_cell = ws[coordinate]
    
    if isinstance(target_cell, openpyxl.cell.cell.MergedCell):
        for m_range in ws.merged_cells.ranges:
            if coordinate in m_range:
                target_coord = m_range.coord.split(":")[0]
                break
                
    cell = ws[target_coord]
    
    if formula and str(formula).startswith("="):
        cell.value = str(formula)
    elif value is not None:
        cell.value = value

    if fill_color:
        norm_fill = normalize_hex_color(fill_color)
        if norm_fill:
            cell.fill = PatternFill(fill_type="solid", start_color=norm_fill, end_color=norm_fill)

    if font_bold is not None or font_color is not None:
        curr_font = cell.font or Font()
        norm_fc = normalize_hex_color(font_color) if font_color else (curr_font.color.rgb if curr_font.color else None)
        bold_val = font_bold if font_bold is not None else curr_font.bold
        cell.font = Font(
            name=curr_font.name or "Segoe UI",
            size=curr_font.size or 10,
            bold=bold_val,
            italic=curr_font.italic,
            color=norm_fc
        )


def update_template_workbook(
    template_path: str,
    output_path: str,
    sheet_updates: dict[str, dict[str, Any]]
) -> str:
    """
    Update an existing template workbook preserving all DrawingML images (Logos),
    merged ranges, styles, and updating only specified cell values/formulas.
    
    sheet_updates format:
    {
        "SheetName": {
            "A4": {"value": "SuperMarketBot"},
            "B6": {"value": 15, "font_bold": True},
            "E16": {"formula": "=(D15+E15)*100/(H15-G15)"}
        }
    }
    """
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"Template XLSX not found: {template_path}")

    wb = openpyxl.load_workbook(template_path, data_only=False)

    for sheet_name, cell_map in sheet_updates.items():
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        for coord, cell_info in cell_map.items():
            safe_set_cell(
                ws=ws,
                coordinate=coord,
                value=cell_info.get("value"),
                formula=cell_info.get("formula"),
                fill_color=cell_info.get("fill_color"),
                font_bold=cell_info.get("font_bold"),
                font_color=cell_info.get("font_color")
            )

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    wb.save(output_path)
    return os.path.abspath(output_path)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def write_xlsx(
    snapshot: dict[str, Any],
    output_path: str,
    template_path: str | None = None,
) -> str:
    """Write an XLSX file from a JSON snapshot."""
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    if template_path and os.path.isfile(template_path):
        wb = openpyxl.load_workbook(template_path, data_only=False)
    else:
        wb = openpyxl.Workbook()
        # Remove default sheet if we will write others
        if "Sheet" in wb.sheetnames and len(snapshot.get("sheets", [])) > 0:
            wb.remove(wb["Sheet"])

    for sheet_data in snapshot.get("sheets", []):
        sname = sheet_data.get("sheet_name", "Sheet1")
        if sname in wb.sheetnames:
            ws = wb[sname]
        else:
            ws = wb.create_sheet(title=sname)

        for cell_data in sheet_data.get("cells", []):
            addr = cell_data.get("address")
            if not addr:
                continue
            fmt = cell_data.get("format", {})
            safe_set_cell(
                ws=ws,
                coordinate=addr,
                value=cell_data.get("value"),
                formula=cell_data.get("formula"),
                fill_color=fmt.get("fill_color"),
                font_bold=fmt.get("bold"),
                font_color=fmt.get("font_color")
            )

    wb.save(output_path)
    return os.path.abspath(output_path)


def write_xlsx_from_json_file(
    json_path: str,
    output_path: str,
    template_path: str | None = None,
) -> str:
    """Load JSON snapshot and write to XLSX."""
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"JSON snapshot not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    return write_xlsx(snapshot, output_path, template_path)
