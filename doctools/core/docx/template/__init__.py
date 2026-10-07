"""
doctools.core.docx.template — Bộ công cụ kiểm định, chuẩn hóa và quản lý template DOCX.
Bao gồm:
- TemplateLinter: Quét tĩnh, phát hiện lỗi cú pháp, biến, split tags, dynamic fields, SSTI.
- JinjaNormalizer: Hàn gắn các thẻ Jinja bị băm nhỏ, dọn rác w:proofErr/w:lastRenderedPageBreak.
- ManifestParser: Phân tích cú pháp và kiểm định Template Manifest schema (YAML/JSON/Dict).
- TemplateRegistry: Quản lý kho lưu trữ, tra cứu phiên bản và manifest của template.
"""

from .template_linter import TemplateLinter, template_linter, TemplateLintReport
from .jinja_normalizer import JinjaNormalizer, jinja_normalizer, NormalizationResult
from .manifest_parser import (
    ManifestParseError,
    parse_manifest,
    validate_manifest_against_template,
)
from .template_registry import (
    TemplateRecord,
    TemplateRegistry,
    get_default_template_registry,
)

__all__ = [
    "TemplateLinter",
    "template_linter",
    "TemplateLintReport",
    "JinjaNormalizer",
    "jinja_normalizer",
    "NormalizationResult",
    "ManifestParseError",
    "parse_manifest",
    "validate_manifest_against_template",
    "TemplateRecord",
    "TemplateRegistry",
    "get_default_template_registry",
]
