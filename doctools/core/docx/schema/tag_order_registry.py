"""
TagOrderRegistry — Cưỡng chế thứ tự thẻ con theo chuẩn ECMA-376 XML Schema.
Ngăn chặn 100% lỗi Word cảnh báo 'Unreadable content' hoặc 'Repair' do chèn thẻ sai vị trí.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from lxml import etree

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def local_name(elem_or_tag: etree._Element | str) -> str:
    """Trích xuất tên cục bộ của thẻ (bỏ qua URI namespace {http:...})."""
    tag_str = elem_or_tag.tag if hasattr(elem_or_tag, "tag") else str(elem_or_tag)
    if "}" in tag_str:
        return tag_str.split("}", 1)[1]
    if ":" in tag_str:
        return tag_str.split(":", 1)[1]
    return tag_str


class TagOrderRegistry:
    """
    Sổ cái quy chuẩn thứ tự phần tử con ECMA-376 WML.
    """

    # Thứ tự thẻ chuẩn hóa từ ECMA-376 cho các container thông dụng
    CANONICAL_ORDERS: Dict[str, List[str]] = {
        # CT_PPr (Đoạn văn)
        "pPr": [
            "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr",
            "widowControl", "numPr", "pBdr", "shd", "tabs", "suppressAutoHyphens",
            "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE",
            "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind",
            "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc",
            "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl",
            "divId", "cnfStyle", "rPr", "sectPr", "pPrChange",
        ],
        # CT_RPr (Đoạn chữ run)
        "rPr": [
            "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps",
            "strike", "dstrike", "outline", "shadow", "emboss", "imprint", "noProof",
            "snapToGrid", "vanish", "color", "spacing", "w", "kern", "position",
            "sz", "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText",
            "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish",
            "oMath", "rPrChange",
        ],
        # CT_TcPr (Ô bảng)
        "tcPr": [
            "cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd",
            "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark",
            "headers", "cellIns", "cellDel", "cellMerge", "tcPrChange",
        ],
        # CT_TrPr (Hàng bảng)
        "trPr": [
            "cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter",
            "cantSplit", "trHeight", "tblHeader", "tblCellSpacing", "jc", "hidden",
            "ins", "del", "trPrChange",
        ],
        # CT_TblPr (Thuộc tính bảng)
        "tblPr": [
            "tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
            "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd",
            "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption",
            "tblDescription", "tblPrChange",
        ],
    }

    def __init__(self, custom_orders: Optional[Dict[str, List[str]]] = None) -> None:
        self._orders = dict(self.CANONICAL_ORDERS)
        if custom_orders:
            self._orders.update(custom_orders)

    def get_order_list(self, parent_tag: str) -> Optional[List[str]]:
        """Lấy danh sách thứ tự theo thẻ container."""
        return self._orders.get(local_name(parent_tag))

    def insert_child_ordered(
        self,
        parent: etree._Element,
        child: etree._Element,
    ) -> etree._Element:
        """
        Chèn child vào parent đúng thứ tự quy định của ECMA-376.
        Nếu thẻ chưa có trong danh sách (vd: w14:*, mc:*), chèn vào cuối cùng an toàn.
        """
        p_name = local_name(parent)
        order_list = self.get_order_list(p_name)

        if not order_list:
            parent.append(child)
            return child

        c_name = local_name(child)
        if c_name not in order_list:
            parent.append(child)
            return child

        target_rank = order_list.index(c_name)

        # Duyệt các phần tử con hiện có để tìm vị trí chèn
        insert_idx = None
        for idx, existing_child in enumerate(parent):
            ex_name = local_name(existing_child)
            if ex_name in order_list:
                ex_rank = order_list.index(ex_name)
                if ex_rank > target_rank:
                    insert_idx = idx
                    break

        if insert_idx is not None:
            parent.insert(insert_idx, child)
        else:
            parent.append(child)

        return child


# Singleton dùng chung cho toàn bộ module docx
tag_order_registry = TagOrderRegistry()
