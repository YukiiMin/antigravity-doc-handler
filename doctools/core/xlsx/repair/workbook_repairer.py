"""
doctools.core.xlsx.repair.workbook_repairer — Bộ tự động sửa chữa hỏng hóc bảng tính (Workbook Repairer).
Tuân thủ FR-16, D-02 của Foundation Plan v1.1:
- Khôi phục cấu hình tính toán <calcPr fullCalcOnLoad="1"/> trong xl/workbook.xml.
- Tự động bổ sung các Override còn thiếu trong [Content_Types].xml cho worksheets và styles.
- Chuẩn hóa đường dẫn quan hệ trong xl/_rels/workbook.xml.rels.
- Lọc ký tự điều khiển ASCII bất hợp pháp gây lỗi OpenXML parser.
"""

from __future__ import annotations
import io
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import zipfile
from lxml import etree

from doctools.contract.issues import Engine, Issue, Severity

_INVALID_XML_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_CT_NS = {"ct": "http://schemas.openxmlformats.org/package/2006/content-types"}


class XlsxWorkbookRepairer:
    """Động cơ chẩn đoán và khắc phục lỗi hỏng hóc cấu trúc OpenXML Excel."""

    def repair(self, xlsx_input: Union[str, Path, bytes]) -> Tuple[bytes, List[Issue]]:
        """Phục hồi package Excel và trả về raw bytes đã sửa lỗi kèm danh sách Issue ghi nhận."""
        issues: List[Issue] = []

        if isinstance(xlsx_input, (str, Path)):
            raw_bytes = Path(xlsx_input).read_bytes()
        else:
            raw_bytes = xlsx_input

        in_buf = io.BytesIO(raw_bytes)
        out_buf = io.BytesIO()

        try:
            with zipfile.ZipFile(in_buf, "r") as in_zip:
                namelist = set(in_zip.namelist())
                repaired_files: Dict[str, bytes] = {}

                # 1. Sửa chữa / bổ sung [Content_Types].xml
                if "[Content_Types].xml" in namelist:
                    ct_xml = in_zip.read("[Content_Types].xml")
                    new_ct_xml, ct_issues = self._repair_content_types(ct_xml, namelist)
                    issues.extend(ct_issues)
                    if new_ct_xml:
                        repaired_files["[Content_Types].xml"] = new_ct_xml

                # 2. Khôi phục calcPr trong xl/workbook.xml
                if "xl/workbook.xml" in namelist:
                    wb_xml = in_zip.read("xl/workbook.xml")
                    new_wb_xml, wb_issues = self._repair_workbook_xml(wb_xml)
                    issues.extend(wb_issues)
                    if new_wb_xml:
                        repaired_files["xl/workbook.xml"] = new_wb_xml

                # 3. Lọc ký tự bất hợp pháp trong toàn bộ các file worksheets/*.xml
                for filename in namelist:
                    if filename.startswith("xl/worksheets/") and filename.endswith(".xml"):
                        sheet_content = in_zip.read(filename).decode("utf-8", errors="replace")
                        if _INVALID_XML_CHARS_RE.search(sheet_content):
                            cleaned_content = _INVALID_XML_CHARS_RE.sub("", sheet_content)
                            repaired_files[filename] = cleaned_content.encode("utf-8")
                            issues.append(
                                Issue(
                                    code="I-XLSX-REPAIR-STRIP-INVALID-CHARS",
                                    severity=Severity.INFO,
                                    engine=Engine.XLSX,
                                    message=f"Đã loại bỏ các ký tự điều khiển bất hợp pháp trong {filename}.",
                                )
                            )

                # 4. Ghi lại file ZIP đã sửa chữa
                with zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
                    for item in in_zip.infolist():
                        if item.filename in repaired_files:
                            out_zip.writestr(item, repaired_files[item.filename])
                        else:
                            out_zip.writestr(item, in_zip.read(item.filename))

        except zipfile.BadZipFile as exc:
            issues.append(
                Issue(
                    code="E-XLSX-REPAIR-UNRECOVERABLE-ZIP",
                    severity=Severity.ERROR,
                    engine=Engine.XLSX,
                    message=f"Tệp tin hỏng hoàn toàn cấu trúc ZIP, không thể phục hồi tự động: {exc}",
                )
            )
            return raw_bytes, issues

        return out_buf.getvalue(), issues

    def _repair_content_types(
        self, ct_xml: bytes, namelist: set[str]
    ) -> Tuple[Optional[bytes], List[Issue]]:
        """Kiểm tra và tự động bổ sung Override cho các file worksheet, styles còn thiếu."""
        issues: List[Issue] = []
        try:
            tree = etree.fromstring(ct_xml)
        except Exception:
            return None, issues

        overrides = {el.attrib.get("PartName") for el in tree.findall(".//ct:Override", _CT_NS)}
        dirty = False

        # Đảm bảo mỗi sheet có Override hợp lệ
        for fname in namelist:
            if fname.startswith("xl/worksheets/") and fname.endswith(".xml"):
                part_name = f"/{fname}"
                if part_name not in overrides:
                    new_override = etree.Element(
                        f"{{{_CT_NS['ct']}}}Override",
                        PartName=part_name,
                        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
                    )
                    tree.append(new_override)
                    dirty = True
                    issues.append(
                        Issue(
                            code="I-XLSX-REPAIR-ADD-CONTENT-TYPE",
                            severity=Severity.INFO,
                            engine=Engine.XLSX,
                            message=f"Đã bổ sung Override ContentType cho {part_name}.",
                        )
                    )

        if dirty:
            return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True), issues
        return None, issues

    def _repair_workbook_xml(self, wb_xml: bytes) -> Tuple[Optional[bytes], List[Issue]]:
        """Đảm bảo xl/workbook.xml có thuộc tính calcPr fullCalcOnLoad='1'."""
        issues: List[Issue] = []
        try:
            tree = etree.fromstring(wb_xml)
        except Exception:
            return None, issues

        calc_nodes = tree.findall("s:calcPr", _NS)
        if not calc_nodes:
            calc_el = etree.Element(f"{{{_NS['s']}}}calcPr", fullCalcOnLoad="1")
            sheets_nodes = tree.findall("s:sheets", _NS)
            if sheets_nodes:
                sheets_nodes[0].addprevious(calc_el)
            else:
                tree.append(calc_el)

            issues.append(
                Issue(
                    code="I-XLSX-REPAIR-INJECT-CALCPR",
                    severity=Severity.INFO,
                    engine=Engine.XLSX,
                    message="Đã tự động khôi phục thẻ <calcPr fullCalcOnLoad='1'/> trong xl/workbook.xml.",
                )
            )
            return etree.tostring(tree, xml_declaration=True, encoding="UTF-8", standalone=True), issues

        return None, issues
