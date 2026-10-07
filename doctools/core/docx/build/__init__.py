"""
doctools.core.docx.build — Document generation builders for Word (DOCX).
Includes:
- JinjaRenderer: Path A template-driven document rendering.
- DocSpecBuilder: Path B schema-driven document builder.
"""

from .jinja_renderer import JinjaRenderer, jinja_renderer, RenderResult
from .docspec_builder import DocSpecBuilder, docspec_builder, DocSpecBuildResult

__all__ = [
    "JinjaRenderer",
    "jinja_renderer",
    "RenderResult",
    "DocSpecBuilder",
    "docspec_builder",
    "DocSpecBuildResult",
]
