"""
doctools.core.xlsx.template — Module quản lý template, manifest và static linter cho XLSX.
"""

from .manifest_parser import (
    ManifestParseError,
    parse_locked_zone,
    parse_manifest,
    validate_manifest_against_template,
)
from .template_linter import (
    XlsxLintReport,
    XlsxTemplateLinter,
)
from .template_registry import (
    XlsxTemplateRecord,
    XlsxTemplateRegistry,
    get_default_xlsx_template_registry,
)

__all__ = [
    "ManifestParseError",
    "parse_locked_zone",
    "parse_manifest",
    "validate_manifest_against_template",
    "XlsxLintReport",
    "XlsxTemplateLinter",
    "XlsxTemplateRecord",
    "XlsxTemplateRegistry",
    "get_default_xlsx_template_registry",
]
