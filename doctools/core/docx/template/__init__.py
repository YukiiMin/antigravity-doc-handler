"""
doctools.core.docx.template — Bộ công cụ kiểm định và chuẩn hóa template DOCX Jinja2.
Bao gồm:
- TemplateLinter: Quét tĩnh, phát hiện lỗi cú pháp, biến, split tags, dynamic fields, SSTI.
- JinjaNormalizer: Hàn gắn các thẻ Jinja bị băm nhỏ, dọn rác w:proofErr/w:lastRenderedPageBreak.
"""

from .template_linter import TemplateLinter, template_linter, TemplateLintReport
from .jinja_normalizer import JinjaNormalizer, jinja_normalizer, NormalizationResult

__all__ = [
    "TemplateLinter",
    "template_linter",
    "TemplateLintReport",
    "JinjaNormalizer",
    "jinja_normalizer",
    "NormalizationResult",
]
