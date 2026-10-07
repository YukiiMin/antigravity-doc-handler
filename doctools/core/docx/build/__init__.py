"""
doctools.core.docx.build — Document generation builders for Word (DOCX).
Includes:
- JinjaRenderer: Path A template-driven document rendering.
"""

from .jinja_renderer import JinjaRenderer, jinja_renderer, RenderResult

__all__ = [
    "JinjaRenderer",
    "jinja_renderer",
    "RenderResult",
]
