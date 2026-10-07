"""
doctools.core.xlsx.export.legacy_exporter — Bộ xuất định dạng Excel 97-2003 .xls (Legacy Exporter).
Tuân thủ FR-17, D-02 của Foundation Plan v1.1:
- Chuyển đổi tệp .xlsx hiện đại sang định dạng cổ điển .xls (BIFF8).
- Ưu tiên 1: Microsoft Excel COM (FileFormat=56 xlExcel8) trên Windows.
- Ưu tiên 2: LibreOffice headless (soffice --headless --convert-to xls).
"""

from __future__ import annotations
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import List, Optional, Tuple, Union

from doctools.contract.issues import Engine, Issue, Severity

_XL_EXCEL8_FORMAT = 56  # BIFF8 Excel 97-2003 .xls in Excel Object Model


class XlsxLegacyExporter:
    """Bộ chuyển đổi định dạng sang Excel 97-2003 (.xls)."""

    def export_to_xls(
        self,
        xlsx_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
    ) -> Tuple[Optional[Path], List[Issue]]:
        """Xuất workbook .xlsx sang tệp .xls cổ điển."""
        issues: List[Issue] = []
        src_path = Path(xlsx_path).resolve()

        if not src_path.is_file():
            issues.append(
                Issue(
                    code="E-XLSX-SRC-NOT-FOUND",
                    severity=Severity.ERROR,
                    engine=Engine.XLSX,
                    message=f"Tệp nguồn .xlsx không tồn tại: {src_path}",
                )
            )
            return None, issues

        if output_path is not None:
            dest_path = Path(output_path).resolve()
        else:
            dest_path = src_path.with_suffix(".xls")

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Thử Excel COM trên Windows
        if sys.platform == "win32":
            res_path, com_issues = self._export_via_excel_com(src_path, dest_path)
            if res_path is not None and res_path.is_file():
                return res_path, com_issues
            issues.extend(com_issues)

        # 2. Thử LibreOffice headless
        res_lo, lo_issues = self._export_via_libreoffice(src_path, dest_path)
        if res_lo is not None and res_lo.is_file():
            return res_lo, lo_issues
        issues.extend(lo_issues)

        issues.append(
            Issue(
                code="E-XLSX-LEGACY-CONVERTER-UNAVAILABLE",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message="Không thể chuyển đổi sang .xls vì cả Excel COM và LibreOffice đều không khả dụng.",
                suggested_action="Cài đặt Microsoft Excel trên Windows hoặc cài đặt LibreOffice (soffice).",
            )
        )
        return None, issues

    def _export_via_excel_com(
        self, src_path: Path, dest_path: Path
    ) -> Tuple[Optional[Path], List[Issue]]:
        """Chuyển đổi sang .xls qua Windows Excel COM."""
        issues: List[Issue] = []
        try:
            import win32com.client
            app = win32com.client.DispatchEx("Excel.Application")
            app.Visible = False
            app.DisplayAlerts = False
            try:
                wb = app.Workbooks.Open(str(src_path))
                # FileFormat=56 tương ứng xlExcel8 (.xls)
                wb.SaveAs(str(dest_path), FileFormat=_XL_EXCEL8_FORMAT)
                wb.Close(SaveChanges=False)
            finally:
                app.Quit()

            if dest_path.is_file():
                issues.append(
                    Issue(
                        code="I-XLSX-EXPORT-COM-SUCCESS",
                        severity=Severity.INFO,
                        engine=Engine.XLSX,
                        message=f"Đã xuất sang file Excel 97-2003 (.xls) thành công qua Excel COM: {dest_path.name}",
                    )
                )
                return dest_path, issues
        except Exception as exc:
            issues.append(
                Issue(
                    code="W-XLSX-COM-EXPORT-FAILED",
                    severity=Severity.WARNING,
                    engine=Engine.XLSX,
                    message=f"Thử nghiệm xuất qua Excel COM không thành công: {exc}",
                )
            )
        return None, issues

    def _export_via_libreoffice(
        self, src_path: Path, dest_path: Path
    ) -> Tuple[Optional[Path], List[Issue]]:
        """Chuyển đổi sang .xls qua LibreOffice headless."""
        issues: List[Issue] = []
        lo_bin = shutil.which("soffice") or shutil.which("libreoffice")
        if not lo_bin:
            return None, issues

        try:
            out_dir = dest_path.parent
            cmd = [lo_bin, "--headless", "--convert-to", "xls", str(src_path), "--outdir", str(out_dir)]
            subprocess.run(cmd, check=True, timeout=30, capture_output=True)
            expected_out = out_dir / f"{src_path.stem}.xls"
            if expected_out.is_file():
                if expected_out != dest_path:
                    shutil.move(str(expected_out), str(dest_path))
                return dest_path, issues
        except Exception as exc:
            issues.append(
                Issue(
                    code="W-XLSX-LO-EXPORT-FAILED",
                    severity=Severity.WARNING,
                    engine=Engine.XLSX,
                    message=f"Thử nghiệm xuất qua LibreOffice không thành công: {exc}",
                )
            )
        return None, issues
