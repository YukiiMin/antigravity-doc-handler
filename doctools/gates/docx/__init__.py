"""
doctools.gates.docx — Quality Gates for DOCX documents.
"""

from .quality_gates import DocxQualityGateEngine, docx_quality_gates

__all__ = [
    "DocxQualityGateEngine",
    "docx_quality_gates",
]
