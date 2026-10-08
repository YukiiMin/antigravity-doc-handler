"""
doctools.core.xlsx.inspect.format_profiler
Format Describer inspecting 12 number classes, fonts, fills, borders, alignments,
theme color resolution, and table border gaps (FR-33, D-26, EV-15).
"""

from __future__ import annotations
from collections import defaultdict
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import openpyxl
from openpyxl.styles.colors import Color

# Standard 12 Office theme base hex colors
THEME_PALETTE = [
    "FFFFFF",  # 0: Light 1 (Background 1)
    "000000",  # 1: Dark 1 (Text 1)
    "EEECE1",  # 2: Light 2 (Background 2)
    "1F497D",  # 3: Dark 2 (Text 2)
    "4F81BD",  # 4: Accent 1
    "C0504D",  # 5: Accent 2
    "9BBB59",  # 6: Accent 3
    "8064A2",  # 7: Accent 4
    "4BACC6",  # 8: Accent 5
    "F79646",  # 9: Accent 6
    "0000FF",  # 10: Hyperlink
    "800080",  # 11: Followed Hyperlink
]


def resolve_color(color: Optional[Color]) -> Optional[Dict[str, Any]]:
    """Resolves openpyxl Color (rgb, theme, indexed, tint) into readable dict."""
    if not color:
        return None

    tint = getattr(color, "tint", 0.0) or 0.0
    if color.type == "theme":
        idx = getattr(color, "theme", 0)
        base_hex = THEME_PALETTE[idx] if 0 <= idx < len(THEME_PALETTE) else "000000"
        return {"type": "theme", "theme_index": idx, "base_hex": base_hex, "tint": tint}
    if color.type == "rgb":
        rgb_val = str(color.rgb) if color.rgb else "000000"
        return {"type": "rgb", "hex": rgb_val, "tint": tint}
    if color.type == "indexed":
        return {"type": "indexed", "index": getattr(color, "indexed", 0), "tint": tint}
    return {"type": "auto"}


def classify_number_format(num_fmt: Optional[str]) -> str:
    """Classifies a format string into one of the 12 canonical ECMA classes (FR-33)."""
    if not num_fmt or num_fmt.strip().lower() in ("general", ""):
        return "General"

    fmt = num_fmt.strip()
    if fmt == "@":
        return "Text"
    if "%" in fmt:
        return "Percentage"
    if "/" in fmt and any(k in fmt for k in ("?", "#", "0")):
        if not any(k in fmt.lower() for k in ("yy", "mm", "dd")):
            return "Fraction"
    if "e+" in fmt.lower() or "e-" in fmt.lower():
        return "Scientific"
    if any(k in fmt for k in ("$", "₫", "€", "£", "¥")):
        if "(" in fmt and ")" in fmt and "_" in fmt:
            return "Accounting"
        return "Currency"
    if any(k in fmt.lower() for k in ("yy", "yyyy", "mmm", "mmmm", "dd", "d-", "/d")):
        return "Date"
    if any(k in fmt.lower() for k in ("hh", "ss", "am/pm", "a/p")):
        return "Time"
    if any(k in fmt for k in ("0", "#")):
        if ";" in fmt or "[" in fmt:
            return "Custom"
        return "Number"
    return "Custom"


class FormatProfiler:
    """Audits spreadsheet styles, fonts, fills, borders, alignments, and gap anomalies."""

    def __init__(self, wb: openpyxl.Workbook) -> None:
        self.wb = wb

    def profile(self, target_sheet: Optional[str] = None) -> Dict[str, Any]:
        """Runs comprehensive format profiling across workbook sheets."""
        sheets = [self.wb[target_sheet]] if target_sheet and target_sheet in self.wb.sheetnames else self.wb.worksheets

        num_fmt_counts: Dict[str, int] = defaultdict(int)
        font_signatures: Set[str] = set()
        fill_signatures: Set[str] = set()
        border_styles_found: Set[str] = set()
        border_gaps: List[Dict[str, Any]] = []

        for ws in sheets:
            # 1. Audit cell-level styles
            for r in range(1, min(ws.max_row + 1, 200)):
                for c in range(1, min(ws.max_column + 1, 50)):
                    cell = ws.cell(row=r, column=c)
                    if cell.value is None and not cell.has_style:
                        continue

                    # Number Format
                    nf_class = classify_number_format(cell.number_format)
                    num_fmt_counts[nf_class] += 1

                    # Font
                    if cell.font:
                        c_info = resolve_color(cell.font.color)
                        font_sig = f"{cell.font.name}_{cell.font.size}_{'B' if cell.font.bold else ''}_{'I' if cell.font.italic else ''}_{c_info.get('hex', '') if c_info else ''}"
                        font_signatures.add(font_sig)

                    # Fill
                    if cell.fill and cell.fill.fill_type:
                        c_info = resolve_color(cell.fill.fgColor)
                        fill_signatures.add(f"{cell.fill.fill_type}_{c_info.get('hex', '') if c_info else ''}")

                    # Border styles
                    if cell.border:
                        for side_name in ("top", "bottom", "left", "right"):
                            side = getattr(cell.border, side_name, None)
                            if side and side.style:
                                border_styles_found.add(side.style)

            # 2. EV-15 Table Border Gap Detection (TC-60)
            self._detect_border_gaps(ws, border_gaps)

        # 3. Classify CF (18 types) and DV (7 types)
        cf_types: Dict[str, int] = defaultdict(int)
        dv_types: Dict[str, int] = defaultdict(int)
        for ws in sheets:
            for cf in getattr(ws, "conditional_formatting", []):
                for rule in getattr(cf, "rules", []):
                    cf_types[getattr(rule, "type", "cellIs")] += 1

            dvs = getattr(ws.data_validations, "dataValidation", []) if hasattr(ws, "data_validations") else []
            for dv in dvs:
                dv_types[getattr(dv, "type", "list")] += 1

        return {
            "number_format_classes": dict(sorted(num_fmt_counts.items(), key=lambda kv: -kv[1])),
            "unique_fonts_count": len(font_signatures),
            "unique_fills_count": len(fill_signatures),
            "border_styles_present": sorted(list(border_styles_found)),
            "border_gaps_detected": border_gaps,
            "conditional_formatting_types": dict(cf_types),
            "data_validation_types": dict(dv_types),
        }

    def _detect_border_gaps(self, ws: openpyxl.worksheet.worksheet.Worksheet, gaps: List[Dict[str, Any]]) -> None:
        """Flags table cells that have missing borders when neighboring prototype cells possess them."""
        for col in range(1, min(ws.max_column + 1, 25)):
            has_prototype_border = False
            prototype_style = None

            for row in range(1, min(ws.max_row + 1, 50)):
                cell = ws.cell(row=row, column=col)
                has_side_border = bool(
                    cell.border
                    and any(getattr(getattr(cell.border, s, None), "style", None) is not None for s in ("top", "bottom", "left", "right"))
                )
                side_style = getattr(getattr(cell.border, "bottom", None), "style", None)

                if row <= 5 and has_side_border and cell.value is not None:
                    has_prototype_border = True
                    prototype_style = side_style or "thin"
                elif has_prototype_border and row > 5 and cell.value is not None:
                    if not has_side_border:
                        gaps.append({
                            "code": "W-XLSX-BORDER-GAP",
                            "sheet": ws.title,
                            "coord": cell.coordinate,
                            "expected_style": prototype_style,
                            "message": f"Cell {cell.coordinate} in column {openpyxl.utils.get_column_letter(col)} is missing border present in prototype row.",
                        })
                        break
