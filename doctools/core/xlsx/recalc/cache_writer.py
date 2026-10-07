"""
doctools.core.xlsx.recalc.cache_writer — Bộ tiêm giá trị cache <v> bằng lxml (Cache Writer).
Tuân thủ FR-10, FR-28, D-12 của Foundation Plan v1.1:
- Tiêm giá trị cache <v> trực tiếp vào XML của ô công thức mà không làm biến dạng <f>.
- Ép kiểu thuộc tính t="str", t="b", t="e", t="n" tương ứng.
- Cấu hình <calcPr fullCalcOnLoad="1"/> trong xl/workbook.xml để Excel tự động tính lại khi mở.
"""

from __future__ import annotations
import io
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import zipfile
from lxml import etree

_NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


class XlsxCacheWriter:
    """Bộ ghi cache <v> trực tiếp vào tệp OpenXML .xlsx sử dụng lxml."""

    @staticmethod
    def _get_sheet_path_map(zip_pkg: zipfile.ZipFile) -> Dict[str, str]:
        """Lập ánh xạ từ tên Sheet sang đường dẫn file XML tương ứng trong package."""
        mapping: Dict[str, str] = {}
        if "xl/workbook.xml" not in zip_pkg.namelist() or "xl/_rels/workbook.xml.rels" not in zip_pkg.namelist():
            return mapping

        wb_tree = etree.fromstring(zip_pkg.read("xl/workbook.xml"))
        rels_tree = etree.fromstring(zip_pkg.read("xl/_rels/workbook.xml.rels"))

        rel_map: Dict[str, str] = {}
        for rel in rels_tree.findall(".//r:Relationship", {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}):
            r_id = rel.attrib.get("Id")
            target = rel.attrib.get("Target", "")
            if r_id:
                clean_target = target.lstrip("/")
                if not clean_target.startswith("xl/"):
                    clean_target = f"xl/{clean_target}"
                rel_map[r_id] = clean_target

        for sheet in wb_tree.findall(".//s:sheet", _NS):
            name = sheet.attrib.get("name")
            r_id = sheet.attrib.get(f"{{{_R_NS}}}id")
            if name and r_id and r_id in rel_map:
                mapping[name] = rel_map[r_id]

        return mapping

    @classmethod
    def inject_cached_values(
        cls,
        xlsx_input: Union[str, Path, bytes],
        cached_values: Dict[str, Dict[str, Any]],
        ensure_full_calc: bool = True,
    ) -> bytes:
        """
        Tiêm các giá trị cache vào các ô tương ứng mà không làm thay đổi công thức.
        cached_values format: {"Sheet1": {"B5": 1250, "C5": "Approved", "D5": True}}
        """
        if isinstance(xlsx_input, (str, Path)):
            raw_bytes = Path(xlsx_input).read_bytes()
        else:
            raw_bytes = xlsx_input

        in_buf = io.BytesIO(raw_bytes)
        out_buf = io.BytesIO()

        with zipfile.ZipFile(in_buf, "r") as in_zip:
            sheet_map = cls._get_sheet_path_map(in_zip)
            modified_files: Dict[str, bytes] = {}

            # 1. Cập nhật từng sheet theo cached_values
            for sheet_name, cell_dict in cached_values.items():
                sheet_file = sheet_map.get(sheet_name)
                if not sheet_file or sheet_file not in in_zip.namelist():
                    continue

                sheet_xml = in_zip.read(sheet_file)
                tree = etree.fromstring(sheet_xml)
                tree_dirty = False

                for coord, val in cell_dict.items():
                    # Tìm ô <c r="COORD">
                    cells = tree.xpath(f'.//s:c[@r="{coord}"]', namespaces=_NS)
                    if not cells:
                        continue
                    cell_el = cells[0]

                    # Xác định kiểu và chuỗi giá trị
                    val_str, type_attr = cls._format_val(val)
                    if type_attr:
                        cell_el.attrib["t"] = type_attr
                    else:
                        cell_el.attrib.pop("t", None)

                    # Tìm hoặc thêm thẻ <v>
                    v_nodes = cell_el.findall("s:v", _NS)
                    if v_nodes:
                        v_node = v_nodes[0]
                    else:
                        v_node = etree.Element(f"{{{_NS['s']}}}v")
                        cell_el.append(v_node)

                    v_node.text = val_str
                    tree_dirty = True

                if tree_dirty:
                    modified_files[sheet_file] = etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True)

            # 2. Cấu hình fullCalcOnLoad="1" trong xl/workbook.xml
            if ensure_full_calc and "xl/workbook.xml" in in_zip.namelist():
                wb_xml = in_zip.read("xl/workbook.xml")
                wb_tree = etree.fromstring(wb_xml)
                calc_nodes = wb_tree.findall("s:calcPr", _NS)
                if calc_nodes:
                    calc_nodes[0].attrib["fullCalcOnLoad"] = "1"
                else:
                    calc_el = etree.Element(f"{{{_NS['s']}}}calcPr", fullCalcOnLoad="1")
                    # Chèn trước sheets nếu có
                    sheets_nodes = wb_tree.findall("s:sheets", _NS)
                    if sheets_nodes:
                        sheets_nodes[0].addprevious(calc_el)
                    else:
                        wb_tree.append(calc_el)

                modified_files["xl/workbook.xml"] = etree.tostring(wb_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

            # 3. Ghi lại toàn bộ package ZIP
            with zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
                for item in in_zip.infolist():
                    if item.filename in modified_files:
                        out_zip.writestr(item, modified_files[item.filename])
                    else:
                        out_zip.writestr(item, in_zip.read(item.filename))

        return out_buf.getvalue()

    @staticmethod
    def _format_val(val: Any) -> Tuple[str, Optional[str]]:
        """Định dạng giá trị val và xác định thuộc tính kiểu t trong XML OpenXML."""
        if val is None:
            return "", None
        if isinstance(val, bool):
            return "1" if val else "0", "b"
        if isinstance(val, (int, float)):
            return str(val), "n"
        str_val = str(val).strip()
        if str_val.startswith("#") and str_val.endswith("!"):
            return str_val, "e"
        return str_val, "str"
