"""
doctools.operations.xlsx — Các thao tác nghiệp vụ và công cụ MCP cho XLSX Engine.
"""

from .inspect_ops import (
    register_xlsx_inspect_tools,
    xlsx_inspect,
)
from .mutate_ops import (
    register_xlsx_mutate_tools,
    xlsx_mutate,
)
from .preflight_ops import (
    register_xlsx_preflight_tools,
    xlsx_preflight,
)
from .template_ops import (
    register_xlsx_template_tools,
    xlsx_lint_template,
    xlsx_list_templates,
    xlsx_register_template,
)
from .validate_ops import (
    register_xlsx_validate_tools,
    xlsx_diff,
    xlsx_validate,
)

__all__ = [
    "xlsx_preflight",
    "register_xlsx_preflight_tools",
    "xlsx_register_template",
    "xlsx_lint_template",
    "xlsx_list_templates",
    "register_xlsx_template_tools",
    "xlsx_mutate",
    "register_xlsx_mutate_tools",
    "xlsx_validate",
    "xlsx_diff",
    "register_xlsx_validate_tools",
    "xlsx_inspect",
    "register_xlsx_inspect_tools",
]
