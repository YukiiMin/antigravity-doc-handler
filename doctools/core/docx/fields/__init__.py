"""
doctools.core.docx.fields — Dynamic fields and TOC management.
"""

from .field_manager import FieldManager, field_manager, FieldDiscoveryResult

__all__ = [
    "FieldManager",
    "field_manager",
    "FieldDiscoveryResult",
]
