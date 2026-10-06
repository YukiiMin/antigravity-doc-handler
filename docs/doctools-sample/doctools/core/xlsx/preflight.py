"""Preflight: quét gói .xlsx (chỉ đọc), lập Inventory, đánh giá rủi ro."""
from __future__ import annotations

import importlib.util
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

from ...contract.models import Issue
from ..errors import DocToolsError

MAX_UNCOMPRESSED = 200 * 1024 * 1024  # chặn zip bomb (bản production: thêm giới hạn tỷ lệ nén, dùng defusedxml)
X14_MARK = "2009/9/main"               # namespace phần mở rộng x14 (sparkline, CF/DV nâng cao...)


def _tags(zf: zipfile.ZipFile, name: str, wanted: set[str]) -> dict[str, int]:
    counts = dict.fromkeys(wanted | {"x14"}, 0)
    for el in ET.fromstring(zf.read(name)).iter():
        if X14_MARK in el.tag:
            counts["x14"] += 1
        local = el.tag.rsplit("}", 1)[-1]
        if local in wanted:
            counts[local] += 1
    return counts


def scan(path: Path) -> dict[str, int]:
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise DocToolsError("E-PKG-ZIP", "Không phải gói .xlsx hợp lệ.", evidence={"path": str(path)},
                            fixable_by="human", suggested_action="Kiểm tra file nguồn có bị hỏng hoặc sai định dạng không.")
    with zf:
        infos = zf.infolist()
        if sum(i.file_size for i in infos) > MAX_UNCOMPRESSED:
            raise DocToolsError("E-SEC-ZIP", "Dung lượng sau giải nén vượt giới hạn.", fixable_by="human")
        for i in infos:
            p = PurePosixPath(i.filename)
            if p.is_absolute() or ".." in p.parts:
                raise DocToolsError("E-SEC-ZIP", "Gói chứa đường dẫn nguy hiểm.", evidence={"entry": i.filename},
                                    fixable_by="human", suggested_action="Từ chối file này.")
        names = [i.filename for i in infos]
        under = lambda prefix, suffix=".xml": [n for n in names if n.startswith(prefix) and n.endswith(suffix)]  # noqa: E731

        inv = dict.fromkeys(["worksheets", "images", "charts", "drawings", "pivot_tables", "tables", "formulas",
                             "conditional_formats", "data_validations", "merged_ranges", "defined_names",
                             "shapes", "x14_elements", "macros", "external_links"], 0)
        inv["worksheets"] = len(under("xl/worksheets/sheet"))
        inv["images"] = len([n for n in names if n.startswith("xl/media/")])
        inv["charts"] = len(under("xl/charts/chart"))
        inv["drawings"] = len(under("xl/drawings/drawing"))
        inv["pivot_tables"] = len(under("xl/pivotTables/pivotTable"))
        inv["tables"] = len(under("xl/tables/table"))
        inv["macros"] = int("xl/vbaProject.bin" in names)
        inv["external_links"] = len(under("xl/externalLinks/externalLink"))

        for n in under("xl/worksheets/sheet"):
            c = _tags(zf, n, {"f", "conditionalFormatting", "dataValidation", "mergeCell"})
            inv["formulas"] += c["f"]
            inv["conditional_formats"] += c["conditionalFormatting"]
            inv["data_validations"] += c["dataValidation"]
            inv["merged_ranges"] += c["mergeCell"]
            inv["x14_elements"] += c["x14"]
        for n in under("xl/drawings/drawing"):
            inv["shapes"] += _tags(zf, n, {"sp"})["sp"]          # hình khối/text box (ảnh là <pic>, không tính)
        if "xl/workbook.xml" in names:
            inv["defined_names"] = _tags(zf, "xl/workbook.xml", {"definedName"})["definedName"]
    return inv


def assess(inv: dict[str, int]) -> tuple[str, list[Issue]]:
    """Chọn mức xử lý (Fidelity Tier) và nêu rủi ro bằng Issue có cấu trúc."""
    issues: list[Issue] = []
    if inv["macros"]:
        issues.append(Issue(code="E-SEC-MACRO", severity="error", message="File chứa macro VBA; từ chối mặc định.",
                            fixable_by="human", suggested_action="Hỏi người dùng: dùng bản .xlsx không macro?"))
    if inv["external_links"]:
        issues.append(Issue(code="E-SEC-EXTLINK", severity="error", message="File có liên kết ngoài; không theo liên kết.",
                            evidence={"external_links": inv["external_links"]}, fixable_by="human"))
    if any(i.severity == "error" for i in issues):
        return "REJECT", issues
    if inv["shapes"] or inv["x14_elements"]:
        issues.append(Issue(code="W-PKG-UNSUPPORTED", severity="warning",
                            message="Có hình khối/phần mở rộng x14 mà openpyxl có thể làm rơi khi lưu.",
                            evidence={"shapes": inv["shapes"], "x14_elements": inv["x14_elements"]},
                            fixable_by="human", suggested_action="Hỏi người dùng: chấp nhận mất hay đổi template; chạy diff_inventory_xlsx sau khi sửa."))
        return "T2", issues
    if inv["images"] and importlib.util.find_spec("PIL") is None:
        issues.append(Issue(code="W-PKG-IMAGE-NEEDS-PILLOW", severity="warning",
                            message="Có ảnh nhưng môi trường thiếu Pillow: ảnh sẽ bị mất khi lưu.",
                            fixable_by="human", suggested_action="Cài Pillow trước khi sửa file."))
        return "T2", issues
    return "T1", issues
