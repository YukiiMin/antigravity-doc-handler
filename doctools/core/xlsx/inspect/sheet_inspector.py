"""
doctools.core.xlsx.inspect.sheet_inspector
Tiered Sheet Inspector implementing the 4-level inspection model (FR-30, D-26).
Levels: summary, structure, objects, cells with pagination and token efficiency.
"""

from __future__ import annotations
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from doctools.core.xlsx.inspect.coverage_analyzer import CoverageAnalyzer

ERROR_LITERALS = {"#REF!", "#DIV/0!", "#VALUE!", "#N/A", "#NAME?", "#NUM!", "#NULL!"}
FUNCTION_REGEX = re.compile(r"([A-Z0-9_\.]+)\(")


class TieredSheetInspector:
    """Provides tiered, token-efficient inspection for Excel workbooks."""

    def __init__(self, wb: openpyxl.Workbook, package_parts: Optional[List[str]] = None) -> None:
        self.wb = wb
        self.package_parts = package_parts or []

    def inspect_summary(self) -> Dict[str, Any]:
        """Level: summary — High-level overview in few hundred tokens."""
        sheets_summary: List[Dict[str, Any]] = []
        total_val_cells = 0
        total_f_cells = 0
        total_err_cells = 0
        all_functions: Set[str] = set()

        for ws in self.wb.worksheets:
            val_c = 0
            f_c = 0
            err_c = 0

            for row in ws.iter_rows(values_only=True):
                for v in row:
                    if v is not None:
                        val_c += 1
                        sv = str(v).strip()
                        if sv.startswith("="):
                            f_c += 1
                            for fn in FUNCTION_REGEX.findall(sv):
                                all_functions.add(fn.upper())
                        elif sv in ERROR_LITERALS:
                            err_c += 1

            total_val_cells += val_c
            total_f_cells += f_c
            total_err_cells += err_c

            sheets_summary.append({
                "name": ws.title,
                "state": ws.sheet_state or "visible",
                "dimensions": ws.dimensions or f"A1:{openpyxl.utils.get_column_letter(ws.max_column)}{ws.max_row}",
                "max_row": ws.max_row,
                "max_column": ws.max_column,
                "value_cells": val_c,
                "formula_cells": f_c,
                "error_cells": err_c,
            })

        coverage_data = CoverageAnalyzer.analyze_workbook(self.wb, self.package_parts)

        return {
            "level": "summary",
            "sheets_count": len(self.wb.worksheets),
            "sheets": sheets_summary,
            "total_value_cells": total_val_cells,
            "total_formulas": total_f_cells,
            "total_errors": total_err_cells,
            "unique_functions_count": len(all_functions),
            "unique_functions": sorted(list(all_functions)),
            "coverage_health": coverage_data["active_states_distribution"],
            "truncated": False,
        }

    def inspect_structure(self) -> Dict[str, Any]:
        """Level: structure — Tables, semantic anchors, merges, freeze panes, sibling sheets."""
        structure_by_sheet: List[Dict[str, Any]] = []
        sheet_fingerprints: Dict[str, List[str]] = {}

        for ws in self.wb.worksheets:
            tables = [
                {"name": t.name, "range": t.ref, "columns": [c.name for c in t.tableColumns]}
                for t in ws.tables.values()
            ]

            # Discover header anchors
            anchors: List[Dict[str, Any]] = []
            for r_idx in range(1, min(ws.max_row + 1, 15)):
                non_empty = [c.value for c in ws[r_idx] if c.value is not None]
                if len(non_empty) >= 3 and all(isinstance(v, str) for v in non_empty[:3]):
                    anchors.append({
                        "kind": "header",
                        "row": r_idx,
                        "columns_sample": [str(v) for v in non_empty[:5]],
                    })

            for t in tables:
                anchors.append({"kind": "table", "name": t["name"], "range": t["range"]})

            merged = [str(rng) for rng in ws.merged_cells.ranges]
            freeze = ws.freeze_panes or "none"

            cols_sample = [str(ws.cell(1, col).value) for col in range(1, min(ws.max_column + 1, 20))]
            sheet_fingerprints[ws.title] = cols_sample

            structure_by_sheet.append({
                "sheet": ws.title,
                "tables": tables,
                "anchors": anchors,
                "merged_cells_count": len(merged),
                "merged_ranges_sample": merged[:10],
                "freeze_panes": freeze,
            })

        # Sibling sheets detection (identical column signatures)
        sibling_groups: List[List[str]] = []
        seen: Set[str] = set()
        titles = [ws.title for ws in self.wb.worksheets]
        for i, t1 in enumerate(titles):
            if t1 in seen:
                continue
            group = [t1]
            for t2 in titles[i + 1:]:
                if sheet_fingerprints[t1] == sheet_fingerprints[t2] and len(sheet_fingerprints[t1]) > 2:
                    group.append(t2)
                    seen.add(t2)
            if len(group) > 1:
                sibling_groups.append(group)

        return {
            "level": "structure",
            "sheets_structure": structure_by_sheet,
            "defined_names": [
                {"name": dn.name, "value": dn.value}
                for dn in self.wb.defined_names.definedName
            ] if hasattr(self.wb.defined_names, "definedName") else [],
            "sibling_sheet_groups": sibling_groups,
            "truncated": False,
        }

    def inspect_objects(self, page: int = 1, max_items: int = 50) -> Dict[str, Any]:
        """Level: objects — Comprehensive inventory of all embedded elements with coverage state."""
        all_objects: List[Dict[str, Any]] = []

        for ws in self.wb.worksheets:
            # Data Validations
            dvs = getattr(ws.data_validations, "dataValidation", []) if hasattr(ws, "data_validations") else []
            for dv in dvs:
                all_objects.append({
                    "sheet": ws.title,
                    "type": "data_validation",
                    "validation_type": getattr(dv, "type", "list"),
                    "sqref": str(getattr(dv, "sqref", "")),
                    "formula1": getattr(dv, "formula1", None),
                    "coverage_state": "READ_WRITE",
                })

            # Conditional Formatting
            for cf in getattr(ws, "conditional_formatting", []):
                all_objects.append({
                    "sheet": ws.title,
                    "type": "conditional_formatting",
                    "sqref": str(cf.sqref),
                    "rules_count": len(cf.rules),
                    "coverage_state": "READ_WRITE",
                })

            # Tables
            for tbl in ws.tables.values():
                all_objects.append({
                    "sheet": ws.title,
                    "type": "table",
                    "name": tbl.name,
                    "range": tbl.ref,
                    "coverage_state": "READ_WRITE",
                })

            # Images
            for img in getattr(ws, "_images", []):
                all_objects.append({
                    "sheet": ws.title,
                    "type": "image",
                    "anchor": str(getattr(img, "anchor", "embedded")),
                    "coverage_state": "PRESERVE_ONLY",
                })

        total = len(all_objects)
        start_idx = max(0, (page - 1) * max_items)
        end_idx = start_idx + max_items
        sliced = all_objects[start_idx:end_idx]

        return {
            "level": "objects",
            "page": page,
            "max_items": max_items,
            "total_objects": total,
            "total_pages": math.ceil(total / max_items) if max_items > 0 else 1,
            "truncated": end_idx < total,
            "objects": sliced,
        }

    def inspect_cells(
        self,
        sheet_name: Optional[str] = None,
        anchor: Optional[str] = None,
        page: int = 1,
        max_items: int = 100,
    ) -> Dict[str, Any]:
        """Level: cells — Drill-down into exact cell values, formulas and formats."""
        ws: Worksheet
        if sheet_name and sheet_name in self.wb.sheetnames:
            ws = self.wb[sheet_name]
        else:
            ws = self.wb.active or self.wb.worksheets[0]

        # Resolve bounding coordinates
        min_r, min_c, max_r, max_c = 1, 1, ws.max_row, ws.max_column
        if anchor:
            if ":" in anchor:
                try:
                    min_c_l, min_r_l, max_c_l, max_r_l = openpyxl.utils.range_boundaries(anchor)
                    min_r, min_c = min_r_l or 1, min_c_l or 1
                    max_r, max_c = max_r_l or ws.max_row, max_c_l or ws.max_column
                except Exception:
                    pass
            elif anchor in ws.tables:
                tbl = ws.tables[anchor]
                min_c_l, min_r_l, max_c_l, max_r_l = openpyxl.utils.range_boundaries(tbl.ref)
                min_r, min_c, max_r, max_c = min_r_l, min_c_l, max_r_l, max_r_l

        # Collect cell items
        cell_items: List[Dict[str, Any]] = []
        merged_cells_set = {str(cell) for rng in ws.merged_cells.ranges for cell in rng.cells}

        for r in range(min_r, min_r + min(max_r - min_r + 1, 500)):
            for c in range(min_c, min_c + min(max_c - min_c + 1, 50)):
                cell = ws.cell(row=r, column=c)
                if cell.value is not None:
                    coord = cell.coordinate
                    val_str = str(cell.value)
                    is_formula = val_str.startswith("=")
                    cell_items.append({
                        "coord": coord,
                        "row": r,
                        "col": c,
                        "value": val_str if not is_formula else None,
                        "formula": val_str if is_formula else None,
                        "data_type": cell.data_type,
                        "number_format": cell.number_format,
                        "is_merged": coord in merged_cells_set,
                    })

        total = len(cell_items)
        start_idx = max(0, (page - 1) * max_items)
        end_idx = start_idx + max_items
        sliced = cell_items[start_idx:end_idx]

        return {
            "level": "cells",
            "sheet": ws.title,
            "anchor": anchor,
            "page": page,
            "max_items": max_items,
            "total_cells": total,
            "total_pages": math.ceil(total / max_items) if max_items > 0 else 1,
            "next_page": page + 1 if end_idx < total else None,
            "truncated": end_idx < total,
            "cells": sliced,
        }
