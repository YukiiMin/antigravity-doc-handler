"""
doctools.operations.docx — Nghiệp vụ MCP Tools cho phân hệ DOCX.
"""

from .template_ops import (
    docx_lint_template,
    docx_normalize_template,
    docx_register_template,
    docx_list_templates,
    docx_get_template_manifest,
    register_template_ops,
)
from .build_ops import (
    docx_render_template,
    docx_build_document,
    register_build_ops,
)

__all__ = [
    "docx_lint_template",
    "docx_normalize_template",
    "docx_register_template",
    "docx_list_templates",
    "docx_get_template_manifest",
    "register_template_ops",
    "docx_render_template",
    "docx_build_document",
    "register_build_ops",
]
