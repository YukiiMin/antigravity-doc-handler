"""
Unit test suite for doctools.core.docx.schema (TagOrderRegistry and SchemaHelper).
Kiểm định thứ tự phần tử con ECMA-376, các rào chắn bảng, và quy tắc The Last Paragraph Rule.
"""

from __future__ import annotations
import unittest
from lxml import etree
import docx

from doctools.core.docx.schema import (
    TagOrderRegistry,
    tag_order_registry,
    SchemaHelper,
    schema_helper,
)

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = f"{{{_W_NS}}}"


class TestTagOrderRegistry(unittest.TestCase):
    """Kiểm tra việc cưỡng chế thứ tự thẻ XML theo chuẩn ECMA-376."""

    def test_ordered_insertion_in_ppr(self) -> None:
        p_pr = etree.Element(f"{_W}pPr")
        # Chèn thẻ jc (căn lề) trước
        jc = etree.Element(f"{_W}jc")
        p_pr.append(jc)

        # Chèn thẻ keepNext (phải đứng trước jc theo schema)
        keep_next = etree.Element(f"{_W}keepNext")
        tag_order_registry.insert_child_ordered(p_pr, keep_next)

        # Chèn thẻ pStyle (phải đứng đầu tiên, trước keepNext)
        p_style = etree.Element(f"{_W}pStyle")
        tag_order_registry.insert_child_ordered(p_pr, p_style)

        children_tags = [el.tag for el in p_pr]
        expected_tags = [f"{_W}pStyle", f"{_W}keepNext", f"{_W}jc"]
        self.assertEqual(children_tags, expected_tags)

    def test_ordered_insertion_in_trpr(self) -> None:
        tr_pr = etree.Element(f"{_W}trPr")
        # cantSplit đứng trước tblHeader
        tbl_header = etree.Element(f"{_W}tblHeader")
        cant_split = etree.Element(f"{_W}cantSplit")

        tr_pr.append(tbl_header)
        tag_order_registry.insert_child_ordered(tr_pr, cant_split)

        children_tags = [el.tag for el in tr_pr]
        expected_tags = [f"{_W}cantSplit", f"{_W}tblHeader"]
        self.assertEqual(children_tags, expected_tags)

    def test_unknown_extension_tags_appended_safely(self) -> None:
        p_pr = etree.Element(f"{_W}pPr")
        p_pr.append(etree.Element(f"{_W}pStyle"))

        # Thẻ mở rộng Word 2013+ w14:textId
        custom_tag = etree.Element("{http://schemas.microsoft.com/office/word/2010/wordml}textId")
        tag_order_registry.insert_child_ordered(p_pr, custom_tag)

        # Không crash và được chèn an toàn ở cuối
        self.assertEqual(p_pr[-1], custom_tag)


class TestSchemaHelper(unittest.TestCase):
    """Kiểm tra các tiện ích thao tác OpenXML qua SchemaHelper."""

    def setUp(self) -> None:
        self.doc = docx.Document()
        self.helper = schema_helper

    def test_set_p_keep_next(self) -> None:
        p = self.doc.add_paragraph("Heading 1 Demo")
        self.helper.set_p_keep_next(p, enable=True)

        p_pr = p._p.find(f"{_W}pPr")
        self.assertIsNotNone(p_pr)
        self.assertIsNotNone(p_pr.find(f"{_W}keepNext"))

        # Gỡ bỏ keepNext
        self.helper.set_p_keep_next(p, enable=False)
        self.assertIsNone(p_pr.find(f"{_W}keepNext"))

    def test_table_row_guards_cant_split_and_header(self) -> None:
        table = self.doc.add_table(rows=2, cols=2)
        header_row = table.rows[0]
        data_row = table.rows[1]

        self.helper.set_tr_header(header_row, enable=True)
        self.helper.set_tr_cant_split(header_row, enable=True)
        self.helper.set_tr_cant_split(data_row, enable=True)

        # Kiểm tra header_row
        h_trpr = header_row._tr.find(f"{_W}trPr")
        self.assertIsNotNone(h_trpr.find(f"{_W}tblHeader"))
        self.assertIsNotNone(h_trpr.find(f"{_W}cantSplit"))

        # Kiểm tra thứ tự thẻ: cantSplit đứng trước tblHeader
        tags = [el.tag for el in h_trpr]
        self.assertLess(tags.index(f"{_W}cantSplit"), tags.index(f"{_W}tblHeader"))

    def test_cell_valign_and_shading(self) -> None:
        table = self.doc.add_table(rows=1, cols=1)
        cell = table.cell(0, 0)

        self.helper.set_tc_valign(cell, valign="center")
        self.helper.set_tc_shading(cell, color_hex="FFE8E0")

        tc_pr = cell._tc.find(f"{_W}tcPr")
        self.assertIsNotNone(tc_pr)

        valign_el = tc_pr.find(f"{_W}vAlign")
        self.assertEqual(valign_el.get(f"{_W}val"), "center")

        shd_el = tc_pr.find(f"{_W}shd")
        self.assertEqual(shd_el.get(f"{_W}fill"), "FFE8E0")

    def test_err_docx_001_last_paragraph_rule(self) -> None:
        """Kiểm tra bất biến ERR_DOCX_001: Mọi ô bảng (<w:tc>) bắt buộc kết thúc bằng <w:p>."""
        tc = etree.Element(f"{_W}tc")
        tc_pr = etree.SubElement(tc, f"{_W}tcPr")

        # Hiện tại ô rỗng chưa có paragraph nào
        self.assertEqual(len(tc.findall(f"{_W}p")), 0)

        # ensure_cell_last_p phải tự sinh thẻ <w:p>
        last_p = self.helper.ensure_cell_last_p(tc)
        self.assertIsNotNone(last_p)
        self.assertEqual(tc[-1].tag, f"{_W}p")


if __name__ == "__main__":
    unittest.main()
