"""
doctools.operations.docx — Nghiệp vụ MCP Tools cho phân hệ DOCX.
"""

from .template_ops import (
    docx_lint_template,
    docx_normalize_template,
    register_template_ops,
)

__all__ = [
    "docx_lint_template",
    "docx_normalize_template",
    "register_template_ops",
]

