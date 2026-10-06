"""
doctools.contract — Hợp đồng dữ liệu Pydantic chuẩn hóa toàn hệ thống.
Bao gồm: FileRef, ResultEnvelope, Diagnostics, Issue, Location, và BaseSpec.
"""

from .fileref import FileRef
from .issues import Severity, Engine, FixableBy, Location, Issue
from .envelope import Diagnostics, Stats, ResultEnvelope
from .spec_base import BaseSpec

__all__ = [
    # File References
    "FileRef",
    # Diagnostic Issues
    "Severity",
    "Engine",
    "FixableBy",
    "Location",
    "Issue",
    # Result Envelopes
    "Diagnostics",
    "Stats",
    "ResultEnvelope",
    # Base Specification
    "BaseSpec",
]
