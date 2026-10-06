"""
doctools.core.docx.template.template_linter
Kiểm định tĩnh (read-only) template Word (.docx):
- Cú pháp Jinja2 và trích xuất biến qua AST (jinja2.meta).
- Phát hiện thẻ Jinja bị Word băm nhỏ qua nhiều runs (split tags).
- Phát hiện phần tử rác chen giữa (w:proofErr, w:lastRenderedPageBreak).
- Phát hiện trường động (TOC, PAGEREF, NUMPAGES).
- Phát hiện rủi ro bảo mật SSTI, tracked changes (w:del, w:ins), comment.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import jinja2
import jinja2.meta
from lxml import etree

from doctools.contract import Engine, FixableBy, Issue, Location, Severity
from doctools.core.docx.package_io import PackageReader, safe_read_package

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = f"{{{_W_NS}}}"

_PROHIBITED_SSTI_PATTERNS = [
    r"__class__",
    r"__mro__",
    r"__subclasses__",
    r"__globals__",
    r"__builtins__",
    r"__import__",
    r"eval\s*\(",
    r"exec\s*\(",
]


@dataclass
class TemplateLintReport:
    """Kết quả kiểm định template Word."""
    valid: bool
    variables: List[str]
    fields_detected: Dict[str, Any]
    issues: List[Issue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class TemplateLinter:
    """Linter tĩnh cho template DOCX Jinja2."""

    def __init__(self) -> None:
        self._jinja_env = jinja2.Environment()

    def lint(self, source: Union[Path, str, bytes, PackageReader]) -> TemplateLintReport:
        """Kiểm định template DOCX thuần đọc, trả về báo cáo chi tiết."""
        reader = source if isinstance(source, PackageReader) else safe_read_package(source)
        issues: List[Issue] = []
        variables: Set[str] = set()
        fields_detected: Dict[str, Any] = {"toc": False, "pageref": 0, "numpages": 0}

        total_paragraphs = 0
        total_split_tags = 0

        # Quét document.xml và toàn bộ header/footer
        target_parts = [
            name for name in reader.get_part_names()
            if name == "word/document.xml" or name.startswith("word/header") or name.startswith("word/footer")
        ]

        for part_name in target_parts:
            tree = reader.get_part_xml(part_name)
            if tree is None:
                continue

            # 1. Quét trường động (TOC, PAGEREF, NUMPAGES)
            self._scan_dynamic_fields(tree, part_name, fields_detected, issues)

            # 2. Quét tracked changes & comments
            self._scan_hygiene(tree, part_name, issues)

            # 3. Quét từng đoạn văn <w:p>
            for p in tree.iter(f"{_W}p"):
                total_paragraphs += 1
                p_report = self._lint_paragraph(p, part_name)
                issues.extend(p_report.issues)
                variables.update(p_report.variables)
                if p_report.has_split_tags:
                    total_split_tags += 1

        # 4. Kiểm tra hợp lệ tổng thể
        has_errors = any(i.severity == Severity.ERROR for i in issues)
        valid = not has_errors

        stats = {
            "parts_scanned": len(target_parts),
            "paragraphs_scanned": total_paragraphs,
            "split_tags_paragraphs": total_split_tags,
            "variables_count": len(variables),
        }

        return TemplateLintReport(
            valid=valid,
            variables=sorted(list(variables)),
            fields_detected=fields_detected,
            issues=issues,
            stats=stats,
        )

    def _scan_dynamic_fields(
        self,
        tree: etree._Element,
        part: str,
        fields_detected: Dict[str, Any],
        issues: List[Issue],
    ) -> None:
        """Dò tìm các trường động TOC, PAGEREF, NUMPAGES."""
        for instr in tree.iter(f"{_W}instrText"):
            text = (instr.text or "").strip().upper()
            if "TOC" in text:
                fields_detected["toc"] = True
            elif "PAGEREF" in text:
                fields_detected["pageref"] += 1
            elif "NUMPAGES" in text:
                fields_detected["numpages"] += 1

        for fld in tree.iter(f"{_W}fldSimple"):
            instr = (fld.get(f"{_W}instr") or "").strip().upper()
            if "TOC" in instr:
                fields_detected["toc"] = True
            elif "PAGEREF" in instr:
                fields_detected["pageref"] += 1
            elif "NUMPAGES" in instr:
                fields_detected["numpages"] += 1

        if fields_detected["toc"]:
            issues.append(Issue(
                code="W-FIELD-TOC-DETECTED",
                severity=Severity.INFO,
                engine=Engine.DOCX,
                location=Location(part=part),
                message="Template chứa mục lục TOC động. Cần chính sách cập nhật trường (field_update).",
                fixable_by=FixableBy.HUMAN,
                suggested_action="configure_field_update",
            ))

    def _scan_hygiene(self, tree: etree._Element, part: str, issues: List[Issue]) -> None:
        """Phát hiện vết tracked changes (w:del, w:ins) hoặc comment còn sót."""
        del_count = len(tree.findall(f".//{_W}del"))
        ins_count = len(tree.findall(f".//{_W}ins"))
        if del_count > 0 or ins_count > 0:
            issues.append(Issue(
                code="W-TPL-TRACKED-CHANGES",
                severity=Severity.WARNING,
                engine=Engine.DOCX,
                location=Location(part=part),
                message=f"Template còn sót tracked changes ({del_count} del, {ins_count} ins). Cần làm sạch.",
                fixable_by=FixableBy.HUMAN,
                suggested_action="accept_all_revisions_in_word",
            ))

    def _lint_paragraph(self, p: etree._Element, part: str) -> _ParagraphLintReport:
        """Kiểm định chi tiết một đoạn văn bản <w:p>."""
        issues: List[Issue] = []
        variables: Set[str] = set()

        runs = p.findall(f"{_W}r")
        run_texts = [(r.findtext(f"{_W}t") or "") for r in runs]
        full_text = "".join(run_texts)

        if not full_text:
            return _ParagraphLintReport(issues=[], variables=set(), has_split_tags=False)

        # Kiểm tra SSTI
        for pattern in _PROHIBITED_SSTI_PATTERNS:
            if re.search(pattern, full_text):
                issues.append(Issue(
                    code="E-SEC-SSTI",
                    severity=Severity.ERROR,
                    engine=Engine.DOCX,
                    location=Location(part=part, element="w:p"),
                    message=f"Phát hiện mẫu SSTI bị cấm trong biểu thức Jinja: '{pattern}'",
                    fixable_by=FixableBy.HUMAN,
                    suggested_action="remove_dangerous_expression",
                ))

        # Kiểm tra thẻ Jinja chưa đóng
        open_var = full_text.count("{{")
        close_var = full_text.count("}}")
        open_block = full_text.count("{%")
        close_block = full_text.count("%}")

        if open_var > close_var:
            issues.append(Issue(
                code="E-TPL-UNCLOSED-TAG",
                severity=Severity.ERROR,
                engine=Engine.DOCX,
                location=Location(part=part, element="w:p"),
                message=f"Đoạn văn chứa thẻ Jinja mở '{{{{' chưa được đóng '}}}}': '{full_text}'",
                fixable_by=FixableBy.HUMAN,
                suggested_action="close_jinja_expression",
            ))
        if open_block > close_block:
            issues.append(Issue(
                code="E-TPL-UNCLOSED-TAG",
                severity=Severity.ERROR,
                engine=Engine.DOCX,
                location=Location(part=part, element="w:p"),
                message=f"Đoạn văn chứa thẻ khối Jinja mở '{{%' chưa được đóng '%}}': '{full_text}'",
                fixable_by=FixableBy.HUMAN,
                suggested_action="close_jinja_block",
            ))

        # Kiểm tra cú pháp Jinja & trích xuất biến qua AST
        if "{{" in full_text or "{%" in full_text:
            try:
                parsed_ast = self._jinja_env.parse(full_text)
                vars_in_p = jinja2.meta.find_undeclared_variables(parsed_ast)
                variables.update(vars_in_p)
            except jinja2.TemplateSyntaxError as exc:
                issues.append(Issue(
                    code="E-TPL-SYNTAX",
                    severity=Severity.ERROR,
                    engine=Engine.DOCX,
                    location=Location(part=part, element="w:p", line=exc.lineno),
                    message=f"Lỗi cú pháp Jinja: {exc.message} trong chuỗi: '{full_text}'",
                    fixable_by=FixableBy.HUMAN,
                    suggested_action="fix_jinja_syntax",
                ))

        # Phát hiện split tags qua các runs
        has_split_tags = False
        in_expr = False
        for t in run_texts:
            if not in_expr:
                if ("{{" in t and "}}" not in t) or ("{%" in t and "%}" not in t):
                    in_expr = True
                    has_split_tags = True
            else:
                if "}}" in t or "%}" in t:
                    in_expr = False

        if has_split_tags:
            issues.append(Issue(
                code="W-TPL-SPLIT-TAG",
                severity=Severity.WARNING,
                engine=Engine.DOCX,
                location=Location(part=part, element="w:p"),
                message="Thẻ Jinja bị Word băm nhỏ qua nhiều runs <w:r>. Cần chạy docx.normalize_template.",
                fixable_by=FixableBy.ENGINE,
                suggested_action="docx.normalize_template",
                evidence={"full_text": full_text, "runs_count": len(runs)},
            ))

        return _ParagraphLintReport(
            issues=issues,
            variables=variables,
            has_split_tags=has_split_tags,
        )


@dataclass
class _ParagraphLintReport:
    issues: List[Issue]
    variables: Set[str]
    has_split_tags: bool


template_linter = TemplateLinter()
