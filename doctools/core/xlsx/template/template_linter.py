"""
doctools.core.xlsx.template.template_linter — Bộ kiểm định tĩnh (Linter) cho XLSX Template.
Kiểm tra an toàn cấu trúc trước khi đăng ký hoặc chỉnh sửa:
- Phát hiện placeholder chưa thay thế ({{...}}, <...>)
- Phát hiện rủi ro dòng mẫu lọt vào công thức tổng hợp (W-TPL-SAMPLE-ROW)
- Cảnh báo sheet ẩn, bảng rỗng, công thức bị lỗi sẵn (#REF!, #VALUE!)
- Hoạt động thuần túy ở chế độ đọc, không làm biến đổi file gốc.
"""

from __future__ import annotations
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Union
import openpyxl
from pydantic import BaseModel, ConfigDict, Field

from doctools.contract.issues import Engine, Issue, Severity
from doctools.contract.xlsx.manifest import XlsxTemplateManifest
from .manifest_parser import validate_manifest_against_template


class XlsxLintReport(BaseModel):
    """Báo cáo kết quả kiểm định tĩnh template Excel."""
    model_config = ConfigDict(extra="ignore")

    valid: bool
    issues: List[Issue] = Field(default_factory=list)
    placeholders_found: List[str] = Field(default_factory=list)
    sheets_scanned: List[str] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)


class XlsxTemplateLinter:
    """Bộ kiểm tra chất lượng và cảnh báo rủi ro template Excel."""

    def __init__(self, forbid_placeholders: Optional[List[str]] = None) -> None:
        self.forbid_placeholders = forbid_placeholders or ["{{", "<...>"]

    def lint(
        self,
        template_path: Union[str, Path],
        manifest: Optional[XlsxTemplateManifest] = None,
    ) -> XlsxLintReport:
        p = Path(template_path)
        if not p.exists() or not p.is_file():
            issue = Issue(
                code="E-TPL-NOT-FOUND",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Tệp template không tồn tại: {p}",
            )
            return XlsxLintReport(valid=False, issues=[issue])

        issues: List[Issue] = []
        if manifest is not None:
            manifest_issues = validate_manifest_against_template(manifest, p)
            issues.extend(manifest_issues)

        wb: Optional[openpyxl.Workbook] = None
        placeholders_found: Set[str] = set()
        total_cells_scanned = 0
        total_formulas = 0

        try:
            wb = openpyxl.load_workbook(p, data_only=False, read_only=False)
            sheets_scanned = wb.sheetnames

            for sheet_name in sheets_scanned:
                ws = wb[sheet_name]
                if ws.sheet_state == "hidden":
                    issues.append(Issue(
                        code="W-PKG-HIDDEN",
                        severity=Severity.WARNING,
                        engine=Engine.XLSX,
                        message=f"Sheet '{sheet_name}' đang ở trạng thái ẩn (hidden).",
                        evidence={"sheet": sheet_name},
                    ))

                max_r = ws.max_row or 0
                max_c = ws.max_column or 0
                if max_r == 0 or max_c == 0:
                    continue

                for r in range(1, max_r + 1):
                    for c in range(1, max_c + 1):
                        cell = ws.cell(row=r, column=c)
                        val = cell.value
                        total_cells_scanned += 1
                        if val is None:
                            continue

                        val_str = str(val).strip()

                        # 1. Quét công thức có lỗi cú pháp sẵn
                        if isinstance(val, str) and val.startswith("="):
                            total_formulas += 1
                            if any(err in val for err in ["#REF!", "#NAME?", "#VALUE!", "#DIV/0!"]):
                                issues.append(Issue(
                                    code="W-TPL-BROKEN-FORMULA",
                                    severity=Severity.WARNING,
                                    engine=Engine.XLSX,
                                    message=f"Công thức tại {sheet_name}!{cell.coordinate} chứa mã lỗi: {val}",
                                    evidence={"sheet": sheet_name, "cell": cell.coordinate, "formula": val},
                                ))

                        # 2. Quét placeholder chưa thay thế
                        for marker in self.forbid_placeholders:
                            if marker == "<...>" and "<" in val_str and ">" in val_str:
                                if re.search(r"<[^>]+>", val_str):
                                    placeholders_found.add(val_str)
                            elif marker in val_str:
                                placeholders_found.add(val_str)

                # 3. Quét kiểm tra rủi ro dòng mẫu (W-TPL-SAMPLE-ROW)
                # Nếu có prototype row khai báo trong manifest và bảng có dòng tổng cộng bên dưới
                if manifest and sheet_name in manifest.prototype_rows:
                    proto_r = manifest.prototype_rows[sheet_name]
                    # Nếu có bất kỳ ô nào chứa chuỗi ví dụ như "Example", "Mẫu", "Sample"
                    for c in range(1, max_c + 1):
                        c_val = ws.cell(row=proto_r, column=c).value
                        if c_val and any(s in str(c_val).lower() for s in ["sample", "mẫu", "ví dụ"]):
                            issues.append(Issue(
                                code="W-TPL-SAMPLE-ROW",
                                severity=Severity.WARNING,
                                engine=Engine.XLSX,
                                message=(
                                    f"Dòng mẫu thứ {proto_r} trên sheet '{sheet_name}' chứa dữ liệu mẫu "
                                    f"'{c_val}' có nguy cơ bị tính nhầm vào công thức tổng hợp sau khi mở rộng."
                                ),
                                evidence={"sheet": sheet_name, "row": proto_r, "content": str(c_val)},
                            ))
                            break

            if placeholders_found:
                issues.append(Issue(
                    code="W-TPL-PLACEHOLDERS-DETECTED",
                    severity=Severity.WARNING,
                    engine=Engine.XLSX,
                    message=f"Phát hiện {len(placeholders_found)} mẫu placeholder trong template: {sorted(list(placeholders_found))[:5]}",
                    evidence={"placeholders": sorted(list(placeholders_found))},
                ))

            has_errors = any(i.severity == Severity.ERROR for i in issues)
            return XlsxLintReport(
                valid=not has_errors,
                issues=issues,
                placeholders_found=sorted(list(placeholders_found)),
                sheets_scanned=sheets_scanned,
                stats={
                    "total_cells_scanned": total_cells_scanned,
                    "total_formulas": total_formulas,
                    "sheets_count": len(sheets_scanned),
                },
            )

        except Exception as exc:
            issues.append(Issue(
                code="E-TPL-LINT-EXCEPTION",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Ngoại lệ khi kiểm định template: {exc}",
            ))
            return XlsxLintReport(valid=False, issues=issues)
        finally:
            if wb is not None:
                wb.close()
