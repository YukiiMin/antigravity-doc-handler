"""
doctools.core.xlsx.inspect
Package for tiered spreadsheet inspection and capability coverage analysis.
"""

from doctools.core.xlsx.inspect.coverage_analyzer import (
    CoverageAnalyzer,
    CoverageState,
    FeatureCategory,
)
from doctools.core.xlsx.inspect.sheet_inspector import TieredSheetInspector

__all__ = [
    "CoverageAnalyzer",
    "CoverageState",
    "FeatureCategory",
    "TieredSheetInspector",
]
