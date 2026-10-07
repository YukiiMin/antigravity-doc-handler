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
from .inspect_ops import (
    docx_inspect_structure,
    docx_validate,
    register_inspect_ops,
)
from .patch_ops import (
    docx_patch,
    register_patch_ops,
)
from .merge_ops import (
    docx_merge,
    register_merge_ops,
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
    "docx_inspect_structure",
    "docx_validate",
    "register_inspect_ops",
    "docx_patch",
    "register_patch_ops",
    "docx_merge",
    "register_merge_ops",
]
