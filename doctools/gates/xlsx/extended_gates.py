"""
doctools.gates.xlsx.extended_gates — Extended Quality Gates (UG-14, UG-15, UG-16).
Detection-only gates enforcing invariants without implicit mutations (EV-15, FR-12, UG-14..16):
- UG-14: Validation & Object Parity Gate (E-XLSX-UG14-VALIDATION-DROPPED)
- UG-15: Table Border Consistency Gate (W-XLSX-UG15-INCONSISTENT-BORDERS)
- UG-16: Formula Deterministic Anomaly Gate (W-XLSX-UG16-EMPTY-CELL-REF)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from doctools.contract.issues import Engine, Issue, Location, Severity
from doctools.core.xlsx.inspect.formula_profiler import FormulaProfiler


def check_ug14_validation_parity(
    wb: openpyxl.Workbook,
    template_inventory: Optional[Dict[str, Any]] = None,
    reference_sheet: Optional[str] = None,
) -> List[Issue]:
    """
    UG-14: Detects dropped Data Validations or CF across cloned/mutated sheets.
    Emits E-XLSX-UG14-VALIDATION-DROPPED if validations were lost.
    """
    issues: List[Issue] = []

    # 1. Compare against reference_sheet if specified
    ref_ws = wb[reference_sheet] if reference_sheet and reference_sheet in wb.sheetnames else None
    ref_dv_count = 0
    if ref_ws and hasattr(ref_ws, "data_validations"):
        ref_dv_count = len(getattr(ref_ws.data_validations, "dataValidation", []))

    for ws in wb.worksheets:
        ws_dv_count = len(getattr(ws.data_validations, "dataValidation", [])) if hasattr(ws, "data_validations") else 0

        # If reference sheet had validations but this sibling sheet has 0
        if ref_ws and ws.title != reference_sheet and ref_dv_count > 0 and ws_dv_count == 0:
            # Check if this sheet is a data table sheet (max_row > 5)
            if ws.max_row > 5:
                issues.append(
                    Issue(
                        code="E-XLSX-UG14-VALIDATION-DROPPED",
                        severity=Severity.ERROR,
                        engine=Engine.XLSX,
                        message=(
                            f"Sheet '{ws.title}' has 0 Data Validations but reference sheet "
                            f"'{reference_sheet}' has {ref_dv_count} validations (EV-15.1)."
                        ),
                        location=Location(sheet=ws.title),
                        evidence={"sheet": ws.title, "ref_sheet": reference_sheet, "ref_count": ref_dv_count},
                    )
                )

        # 2. Check against template_inventory
        if template_inventory and "validations_per_sheet" in template_inventory:
            expected = template_inventory["validations_per_sheet"].get(ws.title, 0)
            if expected > 0 and ws_dv_count == 0:
                issues.append(
                    Issue(
                        code="E-XLSX-UG14-VALIDATION-DROPPED",
                        severity=Severity.ERROR,
                        engine=Engine.XLSX,
                        message=f"Sheet '{ws.title}' dropped all {expected} Data Validations expected from template.",
                        location=Location(sheet=ws.title),
                    )
                )

    return issues


def check_ug15_table_border_consistency(wb: openpyxl.Workbook) -> List[Issue]:
    """
    UG-15: Scans table ranges to detect broken or missing borders (W-XLSX-UG15-INCONSISTENT-BORDERS).
    Detection-only: does NOT mutate or auto-repair borders silently.
    """
    issues: List[Issue] = []

    for ws in wb.worksheets:
        max_col = min(ws.max_column + 1, 30)
        max_row = min(ws.max_row + 1, 80)

        for col in range(1, max_col):
            has_proto_border = False
            proto_row = None

            # Detect prototype row border (first 5 rows)
            for row in range(1, min(max_row, 6)):
                cell = ws.cell(row=row, column=col)
                if cell.value is not None and cell.border:
                    has_border = any(
                        getattr(getattr(cell.border, side, None), "style", None) is not None
                        for side in ("top", "bottom", "left", "right")
                    )
                    if has_border:
                        has_proto_border = True
                        proto_row = row
                        break

            # If prototype row had border, scan data rows for gaps
            if has_proto_border and proto_row is not None:
                for row in range(proto_row + 1, max_row):
                    cell = ws.cell(row=row, column=col)
                    # If data cell has value but lacks border
                    if cell.value is not None:
                        has_border = cell.border and any(
                            getattr(getattr(cell.border, side, None), "style", None) is not None
                            for side in ("top", "bottom", "left", "right")
                        )
                        if not has_border:
                            issues.append(
                                Issue(
                                    code="W-XLSX-UG15-INCONSISTENT-BORDERS",
                                    severity=Severity.WARNING,
                                    engine=Engine.XLSX,
                                    message=(
                                        f"Inconsistent border at {ws.title}!{cell.coordinate}: "
                                        f"missing border present in prototype row {proto_row}."
                                    ),
                                    location=Location(sheet=ws.title, cell=cell.coordinate),
                                    evidence={"prototype_row": proto_row, "cell": cell.coordinate},
                                )
                            )
                            # Flag at most 3 warnings per column to prevent token flooding
                            break

    return issues


def check_ug16_formula_deterministic_anomaly(wb: openpyxl.Workbook) -> List[Issue]:
    """
    UG-16: Detects deterministic formula anomalies like empty-cell references in math.
    Emits W-XLSX-UG16-EMPTY-CELL-REF. Heuristic guesses are tagged estimated and do not block.
    """
    issues: List[Issue] = []
    profiler = FormulaProfiler(wb)
    report = profiler.profile()

    for item in report.get("empty_cell_references", []):
        issues.append(
            Issue(
                code="W-XLSX-UG16-EMPTY-CELL-REF",
                severity=Severity.WARNING,
                engine=Engine.XLSX,
                message=item.get("message", "Formula references an empty cell."),
                location=Location(sheet=item.get("sheet"), cell=item.get("cell")),
                evidence={"formula": item.get("formula"), "target": item.get("target")},
            )
        )

    return issues


def run_extended_gates(
    wb: openpyxl.Workbook,
    template_inventory: Optional[Dict[str, Any]] = None,
    reference_sheet: Optional[str] = None,
) -> List[Issue]:
    """Runs UG-14, UG-15, and UG-16 sequentially."""
    issues: List[Issue] = []
    issues.extend(check_ug14_validation_parity(wb, template_inventory, reference_sheet))
    issues.extend(check_ug15_table_border_consistency(wb))
    issues.extend(check_ug16_formula_deterministic_anomaly(wb))
    return issues
