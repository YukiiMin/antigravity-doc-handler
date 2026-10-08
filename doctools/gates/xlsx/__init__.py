"""
doctools.gates.xlsx — Cổng kiểm định chất lượng và đối soát cấu trúc bảng tính Excel.
"""

from .structural_diff import SheetDiff, StructuralDiffReport, XlsxStructuralDiffer
from .universal_gates import XlsxUniversalGates
from .extended_gates import (
    check_ug14_validation_parity,
    check_ug15_table_border_consistency,
    check_ug16_formula_deterministic_anomaly,
    run_extended_gates,
)

__all__ = [
    "XlsxUniversalGates",
    "XlsxStructuralDiffer",
    "StructuralDiffReport",
    "SheetDiff",
    "check_ug14_validation_parity",
    "check_ug15_table_border_consistency",
    "check_ug16_formula_deterministic_anomaly",
    "run_extended_gates",
]
