"""
doctools.gates.xlsx — Cổng kiểm định chất lượng và đối soát cấu trúc bảng tính Excel.
"""

from .structural_diff import SheetDiff, StructuralDiffReport, XlsxStructuralDiffer
from .universal_gates import XlsxUniversalGates

__all__ = [
    "XlsxUniversalGates",
    "XlsxStructuralDiffer",
    "StructuralDiffReport",
    "SheetDiff",
]
