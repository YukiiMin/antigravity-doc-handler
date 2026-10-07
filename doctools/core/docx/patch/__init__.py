"""
doctools.core.docx.patch — Format-preserving in-place document modification.
"""

from .docx_patcher import DocxPatcher, docx_patcher, PatchResult

__all__ = [
    "DocxPatcher",
    "docx_patcher",
    "PatchResult",
]
