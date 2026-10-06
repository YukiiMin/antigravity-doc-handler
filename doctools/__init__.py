"""
doctools — AI-Native Office Document & Technical Diagram Toolkit.
Modular 5-layer architecture supporting DOCX, XLSX, and DIAGRAM engines.
"""

from .registry import ToolRegistry, ToolDefinition

__version__ = "2.0.0"

# Singleton / Default Registry instance for global registration
default_registry = ToolRegistry()

__all__ = [
    "ToolRegistry",
    "ToolDefinition",
    "default_registry",
]
