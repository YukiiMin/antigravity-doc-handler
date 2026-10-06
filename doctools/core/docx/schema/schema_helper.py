"""
SchemaHelper — Lớp trợ thủ thao tác phần tử OOXML an toàn tuyệt đối.
Đảm bảo:
- Mọi thay đổi XML đều tuân thủ TagOrderRegistry (ECMA-376).
- Cưỡng chế các rào chắn bảng bắt buộc: cantSplit, tblHeader, vAlign="center".
- Cưỡng chế ERR_DOCX_001: The Last Paragraph Rule cho mọi ô bảng (<w:tc>).
"""

from __future__ import annotations
from typing import Any, Optional, Union
from lxml import etree
from .tag_order_registry import tag_order_registry, local_name

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = f"{{{_W_NS}}}"


def _get_xml_element(target: Any) -> etree._Element:
    """Trích xuất lxml Element từ python-docx object hoặc trả về chính nó."""
    if hasattr(target, "_tc"):
        return target._tc
    if hasattr(target, "_tr"):
        return target._tr
    if hasattr(target, "_p"):
        return target._p
    if hasattr(target, "_tbl"):
        return target._tbl
    if hasattr(target, "_r"):
        return target._r
    if hasattr(target, "_element"):
        return target._element
    return target


class SchemaHelper:
    """
    Tập hợp các phương thức thao tác cấu trúc OpenXML an toàn cho Word.
    """

    def __init__(self) -> None:
        self.registry = tag_order_registry

    def get_or_create_pr(
        self,
        element: etree._Element,
        pr_tag_local: str,
    ) -> etree._Element:
        """Lấy hoặc tạo thẻ thuộc tính (vd: pPr, tcPr, trPr, tblPr)."""
        full_tag = f"{_W}{pr_tag_local}"
        pr = element.find(full_tag)
        if pr is None:
            pr = etree.Element(full_tag)
            element.insert(0, pr)  # pr luôn đứng đầu container của chính nó
        return pr

    def set_p_keep_next(self, paragraph: Any, enable: bool = True) -> None:
        """Gán hoặc gỡ thuộc tính <w:keepNext/> cho đoạn văn (chống mồ côi cuối trang)."""
        p = _get_xml_element(paragraph)
        p_pr = self.get_or_create_pr(p, "pPr")
        tag = f"{_W}keepNext"
        existing = p_pr.find(tag)

        if enable and existing is None:
            node = etree.Element(tag)
            self.registry.insert_child_ordered(p_pr, node)
        elif not enable and existing is not None:
            p_pr.remove(existing)

    def set_tr_cant_split(self, row: Any, enable: bool = True) -> None:
        """Cưỡng chế <w:cantSplit/> trên hàng bảng (chống rách dòng qua trang)."""
        tr = _get_xml_element(row)
        tr_pr = self.get_or_create_pr(tr, "trPr")
        tag = f"{_W}cantSplit"
        existing = tr_pr.find(tag)

        if enable and existing is None:
            node = etree.Element(tag)
            self.registry.insert_child_ordered(tr_pr, node)
        elif not enable and existing is not None:
            tr_pr.remove(existing)

    def set_tr_header(self, row: Any, enable: bool = True) -> None:
        """Cưỡng chế <w:tblHeader/> trên hàng tiêu đề (lặp lại header trên mọi trang)."""
        tr = _get_xml_element(row)
        tr_pr = self.get_or_create_pr(tr, "trPr")
        tag = f"{_W}tblHeader"
        existing = tr_pr.find(tag)

        if enable and existing is None:
            node = etree.Element(tag)
            self.registry.insert_child_ordered(tr_pr, node)
        elif not enable and existing is not None:
            tr_pr.remove(existing)

    def set_tc_valign(self, cell: Any, valign: str = "center") -> None:
        """Cưỡng chế <w:vAlign w:val="..."/> căn dọc ô bảng."""
        tc = _get_xml_element(cell)
        tc_pr = self.get_or_create_pr(tc, "tcPr")
        tag = f"{_W}vAlign"
        existing = tc_pr.find(tag)

        if existing is not None:
            existing.set(f"{_W}val", valign)
        else:
            node = etree.Element(tag)
            node.set(f"{_W}val", valign)
            self.registry.insert_child_ordered(tc_pr, node)

    def set_tc_shading(self, cell: Any, color_hex: str) -> None:
        """Thiết lập màu nền <w:shd w:fill="..."/> cho ô bảng."""
        tc = _get_xml_element(cell)
        tc_pr = self.get_or_create_pr(tc, "tcPr")
        clean_hex = color_hex.lstrip("#").upper()
        tag = f"{_W}shd"
        existing = tc_pr.find(tag)

        if existing is not None:
            existing.set(f"{_W}fill", clean_hex)
            existing.set(f"{_W}val", "clear")
        else:
            node = etree.Element(tag)
            node.set(f"{_W}val", "clear")
            node.set(f"{_W}fill", clean_hex)
            self.registry.insert_child_ordered(tc_pr, node)

    def ensure_cell_last_p(self, cell: Any) -> etree._Element:
        """
        Cưỡng chế bất biến ERR_DOCX_001 (The Last Paragraph Rule):
        Mọi ô bảng (<w:tc>) bắt buộc phải kết thúc bằng tối thiểu một thẻ <w:p>.
        """
        tc = _get_xml_element(cell)
        p_tag = f"{_W}p"
        paragraphs = tc.findall(p_tag)

        if not paragraphs or tc[-1].tag != p_tag:
            new_p = etree.Element(p_tag)
            tc.append(new_p)
            return new_p

        return paragraphs[-1]


# Singleton dùng chung cho toàn bộ module docx
schema_helper = SchemaHelper()
