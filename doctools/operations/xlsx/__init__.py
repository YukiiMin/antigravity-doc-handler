"""
doctools.operations.xlsx — Các thao tác nghiệp vụ và công cụ MCP cho XLSX Engine.
"""

from .build_ops import (
    register_xlsx_build_tools,
    xlsx_build,
)
from .export_ops import (
    register_xlsx_export_tools,
    xlsx_export_legacy_xls,
)
from .inspect_ops import (
    register_xlsx_inspect_tools,
    xlsx_analyze_formulas,
    xlsx_coverage_report,
    xlsx_describe_formats,
    xlsx_function_catalog,
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
from .recalc_ops import (
    register_xlsx_recalc_tools,
    xlsx_recalc,
)
from .repair_ops import (
    register_xlsx_repair_tools,
    xlsx_repair,
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
    "xlsx_coverage_report",
    "xlsx_analyze_formulas",
    "xlsx_describe_formats",
    "xlsx_function_catalog",
    "register_xlsx_inspect_tools",
    "xlsx_recalc",
    "register_xlsx_recalc_tools",
    "xlsx_build",
    "register_xlsx_build_tools",
    "xlsx_repair",
    "register_xlsx_repair_tools",
    "xlsx_export_legacy_xls",
    "register_xlsx_export_tools",
]
