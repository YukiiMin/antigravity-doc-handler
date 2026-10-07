"""
doctools.core.docx.merge — Multi-part document composition and merge engine.
"""

from .docx_merger import DocxMerger, docx_merger, MergeResult, StyleConflictPolicy

__all__ = [
    "DocxMerger",
    "docx_merger",
    "MergeResult",
    "StyleConflictPolicy",
]
