"""
doctools.core.xlsx.inspect
Package for tiered spreadsheet inspection and capability coverage analysis.
"""

from doctools.core.xlsx.inspect.coverage_analyzer import (
    CoverageAnalyzer,
    CoverageState,
    FeatureCategory,
)
from doctools.core.xlsx.inspect.formula_profiler import (
    FormulaProfiler,
    a1_to_r1c1_coordinate,
    normalize_formula_to_r1c1,
)
from doctools.core.xlsx.inspect.sheet_inspector import TieredSheetInspector

__all__ = [
    "CoverageAnalyzer",
    "CoverageState",
    "FeatureCategory",
    "FormulaProfiler",
    "TieredSheetInspector",
    "a1_to_r1c1_coordinate",
    "normalize_formula_to_r1c1",
]
