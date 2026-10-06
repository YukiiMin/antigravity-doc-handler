"""
doctools.core.docx.template.jinja_normalizer
Hàn gắn các thẻ Jinja2 bị Word băm nhỏ qua nhiều runs theo Mục 4.14:
- Loại bỏ các phần tử rác chen giữa: w:proofErr, w:lastRenderedPageBreak.
- Bảo toàn tuyệt đối w:noProof, w:lang, rsid* trong rPr.
- Thống nhất định dạng theo run đầu tiên, phát cảnh báo W-TPL-MIXED-FORMAT khi có xung đột style.
- Giữ nguyên xml:space="preserve" khi có khoảng trắng biên.
- Sinh bản mới không ghi đè bản gốc (D-09).
"""

from __future__ import annotations
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from lxml import etree

from doctools.contract import Engine, FixableBy, Issue, Location, Severity
from doctools.core.docx.package_io import PackageReader, PackageWriter, safe_read_package

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = f"{{{_W_NS}}}"
_XML_NS = "http://www.w3.org/XML/1998/namespace"
_XML_SPACE = f"{{{_XML_NS}}}space"

# Các phần tử rác chen giữa cần loại bỏ hoàn toàn
_TRASH_TAGS = {
    f"{_W}proofErr",
    f"{_W}lastRenderedPageBreak",
}

# Các thuộc tính rPr được phép bỏ qua khi so sánh xung đột format
_IGNORED_RPR_TAGS = {
    f"{_W}noProof",
    f"{_W}lang",
}


@dataclass
class NormalizationResult:
    """Kết quả chuẩn hóa template."""
    normalized_bytes: bytes
    diff_summary: Dict[str, Any]
    issues: List[Issue]


class JinjaNormalizer:
    """Bộ chuẩn hóa và hàn gắn thẻ Jinja2 cho tài liệu DOCX."""

    def normalize(
        self,
        source: Union[Path, str, bytes, PackageReader],
    ) -> NormalizationResult:
        """Hàn gắn toàn bộ thẻ Jinja2 bị vỡ trong template và xuất gói byte mới."""
        reader = source if isinstance(source, PackageReader) else safe_read_package(source)
        issues: List[Issue] = []

        total_runs_consolidated = 0
        total_trash_removed = 0
        paragraphs_modified = 0

        # Lưu trữ các parts đã cập nhật
        modified_parts: Dict[str, bytes] = {}

        target_parts = [
            name for name in reader.get_part_names()
            if name == "word/document.xml" or name.startswith("word/header") or name.startswith("word/footer")
        ]

        for part_name in target_parts:
            tree = reader.get_part_xml(part_name)
            if tree is None:
                continue

            part_modified = False

            # Duyệt các đoạn văn bản <w:p>
            for p in tree.iter(f"{_W}p"):
                mod_runs, mod_trash, p_issues = self._normalize_paragraph(p, part_name)
                if mod_runs > 0 or mod_trash > 0:
                    total_runs_consolidated += mod_runs
                    total_trash_removed += mod_trash
                    paragraphs_modified += 1
                    part_modified = True
                    issues.extend(p_issues)

            if part_modified:
                modified_parts[part_name] = etree.tostring(
                    tree, xml_declaration=True, encoding="utf-8", standalone=True
                )

        # Tạo gói mới với các parts đã sửa
        new_package_bytes = PackageWriter.create_modified_package(reader, modified_parts)

        diff_summary = {
            "runs_consolidated": total_runs_consolidated,
            "trash_elements_removed": total_trash_removed,
            "paragraphs_modified": paragraphs_modified,
            "modified_parts_count": len(modified_parts),
        }

        return NormalizationResult(
            normalized_bytes=new_package_bytes,
            diff_summary=diff_summary,
            issues=issues,
        )

    def _normalize_paragraph(
        self,
        p: etree._Element,
        part_name: str,
    ) -> Tuple[int, int, List[Issue]]:
        """Chuẩn hóa một đoạn văn <w:p>, gộp các cụm run chứa thẻ Jinja bị băm."""
        issues: List[Issue] = []
        runs_consolidated = 0
        trash_removed = 0

        # Kiểm tra nhanh: đoạn có thẻ Jinja bị vỡ không
        runs = [child for child in p if child.tag == f"{_W}r"]
        run_texts = [(r.findtext(f"{_W}t") or "") for r in runs]
        full_text = "".join(run_texts)

        if not self._has_split_jinja(run_texts):
            return 0, 0, []

        # Xóa các phần tử rác w:proofErr và w:lastRenderedPageBreak
        for child in list(p):
            if child.tag in _TRASH_TAGS:
                p.remove(child)
                trash_removed += 1

        # Duyệt và gộp các run Jinja bị băm
        # Duyệt lại danh sách run sau khi dọn rác
        current_runs = [child for child in p if child.tag == f"{_W}r"]
        idx = 0
        while idx < len(current_runs):
            r = current_runs[idx]
            t_el = r.find(f"{_W}t")
            t_text = t_el.text if (t_el is not None and t_el.text) else ""

            # Kiểm tra nếu run này mở thẻ Jinja nhưng chưa đóng
            if self._opens_jinja_tag(t_text) and not self._closes_jinja_tag(t_text):
                # Gom cụm các runs kế tiếp cho tới khi thẻ được đóng
                cluster: List[etree._Element] = [r]
                cluster_text = [t_text]
                j = idx + 1
                while j < len(current_runs):
                    next_r = current_runs[j]
                    next_t_el = next_r.find(f"{_W}t")
                    next_text = next_t_el.text if (next_t_el is not None and next_t_el.text) else ""
                    cluster.append(next_r)
                    cluster_text.append(next_text)
                    if self._closes_jinja_tag(next_text):
                        break
                    j += 1

                # Nếu cụm > 1 run, tiến hành gộp vào run đầu tiên
                if len(cluster) > 1:
                    primary_r = cluster[0]
                    merged_str = "".join(cluster_text)

                    # So sánh rPr giữa các run trong cụm
                    primary_rpr = primary_r.find(f"{_W}rPr")
                    for secondary_r in cluster[1:]:
                        sec_rpr = secondary_r.find(f"{_W}rPr")
                        if self._is_different_formatting(primary_rpr, sec_rpr):
                            issues.append(Issue(
                                code="W-TPL-MIXED-FORMAT",
                                severity=Severity.WARNING,
                                engine=Engine.DOCX,
                                location=Location(part=part_name, element="w:r"),
                                message=f"Thẻ Jinja '{merged_str}' có định dạng font/màu khác nhau giữa các runs. Đã thống nhất theo run đầu.",
                                fixable_by=FixableBy.HUMAN,
                                suggested_action="unify_expression_formatting_in_word",
                            ))

                    # Cập nhật text cho run chính
                    pri_t = primary_r.find(f"{_W}t")
                    if pri_t is None:
                        pri_t = etree.SubElement(primary_r, f"{_W}t")
                    pri_t.text = merged_str

                    # Đặt xml:space="preserve" nếu có khoảng trắng đầu hoặc cuối
                    if merged_str.startswith(" ") or merged_str.endswith(" "):
                        pri_t.set(_XML_SPACE, "preserve")

                    # Xóa các run phụ khỏi paragraph
                    for secondary_r in cluster[1:]:
                        p.remove(secondary_r)
                        runs_consolidated += 1

                    # Cập nhật lại danh sách current_runs để tiếp tục
                    current_runs = [child for child in p if child.tag == f"{_W}r"]

            idx += 1

        return runs_consolidated, trash_removed, issues

    @staticmethod
    def _has_split_jinja(run_texts: List[str]) -> bool:
        """Kiểm tra xem danh sách text của các run có chứa thẻ Jinja bị băm không."""
        in_expr = False
        for t in run_texts:
            if not in_expr:
                if ("{{" in t and "}}" not in t) or ("{%" in t and "%}" not in t) or ("{#" in t and "#}" not in t):
                    in_expr = True
                    return True
            else:
                if "}}" in t or "%}" in t or "#}" in t:
                    in_expr = False
        return False

    @staticmethod
    def _opens_jinja_tag(text: str) -> bool:
        """Kiểm tra xem chuỗi có chứa mở thẻ Jinja không."""
        return ("{{" in text) or ("{%" in text) or ("{#" in text)

    @staticmethod
    def _closes_jinja_tag(text: str) -> bool:
        """Kiểm tra xem chuỗi có chứa đóng thẻ Jinja không."""
        return ("}}" in text) or ("%}" in text) or ("#}" in text)

    @staticmethod
    def _is_different_formatting(
        rpr1: Optional[etree._Element],
        rpr2: Optional[etree._Element],
    ) -> bool:
        """So sánh hai rPr, bỏ qua noProof, lang và rsid* theo Mục 4.14."""
        if rpr1 is None and rpr2 is None:
            return False
        if rpr1 is None or rpr2 is None:
            return True

        def get_filtered_tags(rpr: etree._Element) -> Dict[str, Dict[str, str]]:
            tags: Dict[str, Dict[str, str]] = {}
            for child in rpr:
                if child.tag in _IGNORED_RPR_TAGS:
                    continue
                # Bỏ qua rsid* trong attributes
                filtered_attribs = {k: v for k, v in child.attrib.items() if not k.endswith("rsid")}
                tags[child.tag] = filtered_attribs
            return tags

        return get_filtered_tags(rpr1) != get_filtered_tags(rpr2)


jinja_normalizer = JinjaNormalizer()
