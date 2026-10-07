"""
doctools.contract.docx
Pydantic contracts and schemas for DOCX operations, templates, and DocSpec.
"""

from doctools.contract.docx.manifest import (
    LayoutPolicy,
    TemplateManifest,
    VariableDef,
)
from doctools.contract.docx.docspec import (
    CalloutBlock,
    DocBlock,
    DocSpec,
    HeadingBlock,
    ImageBlock,
    ListBlock,
    PageBreakBlock,
    PageSetupSpec,
    ParagraphBlock,
    RunSpec,
    TableBlock,
)

__all__ = [
    "LayoutPolicy",
    "TemplateManifest",
    "VariableDef",
    "CalloutBlock",
    "DocBlock",
    "DocSpec",
    "HeadingBlock",
    "ImageBlock",
    "ListBlock",
    "PageBreakBlock",
    "PageSetupSpec",
    "ParagraphBlock",
    "RunSpec",
    "TableBlock",
]
