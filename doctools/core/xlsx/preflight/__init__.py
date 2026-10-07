"""
doctools.core.xlsx.preflight — Package preflight analysis and inventory.
"""

from .scanner import PreflightScanner, preflight_scanner, PreflightScanResult

__all__ = [
    "PreflightScanner",
    "preflight_scanner",
    "PreflightScanResult",
]
