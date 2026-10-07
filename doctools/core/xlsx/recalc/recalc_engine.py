"""
doctools.core.xlsx.recalc.recalc_engine — Động cơ điều phối tái tính toán (Recalc Engine).
Tuân thủ FR-10, FR-28, D-12 của Foundation Plan v1.1:
- Ưu tiên 1: excel_com (Windows Excel.Application COM full rebuild).
- Ưu tiên 2: libreoffice (headless soffice).
- Fallback: cache_writer (lxml injection) + calc_on_open (fullCalcOnLoad="1").
"""

from __future__ import annotations
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field

from doctools.contract.issues import Engine, Issue, Severity
from .cache_writer import XlsxCacheWriter


class RecalcResult(BaseModel):
    """Kết quả thực thi tái tính toán bảng tính."""
    model_config = ConfigDict(extra="ignore")

    success: bool
    method_used: str
    issues: List[Issue] = Field(default_factory=list)
    output_bytes: Optional[bytes] = None


class RecalcEngine:
    """Động cơ điều phối các phương pháp tái tính toán Excel."""

    def __init__(self) -> None:
        pass

    def recalculate(
        self,
        xlsx_path: Union[str, Path],
        method: Literal["auto", "excel_com", "libreoffice", "cache_writer"] = "auto",
        cached_values: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> RecalcResult:
        """Thực thi tái tính toán bảng tính theo phương thức được chỉ định."""
        p = Path(xlsx_path).resolve()
        if not p.is_file():
            return RecalcResult(
                success=False,
                method_used=method,
                issues=[
                    Issue(
                        code="E-XLSX-RECALC-FILE-NOT-FOUND",
                        severity=Severity.ERROR,
                        engine=Engine.XLSX,
                        message=f"Không tìm thấy file để tính toán: {p}",
                    )
                ],
            )

        # 1. Nếu có cached_values hoặc method là cache_writer
        if method == "cache_writer" or (method == "auto" and cached_values):
            return self._recalc_via_cache_writer(p, cached_values or {})

        # 2. Thử excel_com
        if method in ("excel_com", "auto") and sys.platform == "win32":
            res_com = self._recalc_via_excel_com(p)
            if res_com.success or method == "excel_com":
                return res_com

        # 3. Thử libreoffice
        if method in ("libreoffice", "auto"):
            res_lo = self._recalc_via_libreoffice(p)
            if res_lo.success or method == "libreoffice":
                return res_lo

        # 4. Fallback cuối cùng: bật cờ fullCalcOnLoad="1" để Excel tự tính khi mở
        return self._recalc_via_cache_writer(p, cached_values or {})

    def _recalc_via_cache_writer(
        self,
        file_path: Path,
        cached_values: Dict[str, Dict[str, Any]],
    ) -> RecalcResult:
        """Tái tính toán bằng cách tiêm cache và bật cờ fullCalcOnLoad."""
        try:
            updated_bytes = XlsxCacheWriter.inject_cached_values(
                xlsx_input=file_path,
                cached_values=cached_values,
                ensure_full_calc=True,
            )
            file_path.write_bytes(updated_bytes)
            return RecalcResult(
                success=True,
                method_used="cache_writer",
                output_bytes=updated_bytes,
            )
        except Exception as exc:
            return RecalcResult(
                success=False,
                method_used="cache_writer",
                issues=[
                    Issue(
                        code="E-XLSX-CACHE-WRITE-FAILED",
                        severity=Severity.ERROR,
                        engine=Engine.XLSX,
                        message=f"Lỗi khi tiêm cache vào file: {exc}",
                    )
                ],
            )

    def _recalc_via_excel_com(self, file_path: Path) -> RecalcResult:
        """Tái tính toán qua Windows Excel.Application COM."""
        try:
            import win32com.client
            excel_app = win32com.client.DispatchEx("Excel.Application")
            excel_app.Visible = False
            excel_app.DisplayAlerts = False
            try:
                wb = excel_app.Workbooks.Open(str(file_path))
                excel_app.CalculateFullRebuild()
                wb.Save()
                wb.Close(SaveChanges=True)
            finally:
                excel_app.Quit()

            return RecalcResult(
                success=True,
                method_used="excel_com",
                output_bytes=file_path.read_bytes(),
            )
        except Exception as exc:
            return RecalcResult(
                success=False,
                method_used="excel_com",
                issues=[
                    Issue(
                        code="W-XLSX-COM-RECALC-FAILED",
                        severity=Severity.WARNING,
                        engine=Engine.XLSX,
                        message=f"Không thể khởi chạy Excel COM: {exc}",
                    )
                ],
            )

    def _recalc_via_libreoffice(self, file_path: Path) -> RecalcResult:
        """Tái tính toán qua LibreOffice headless."""
        lo_cmd = shutil.which("soffice") or shutil.which("libreoffice")
        if not lo_cmd:
            return RecalcResult(
                success=False,
                method_used="libreoffice",
                issues=[
                    Issue(
                        code="W-XLSX-LIBREOFFICE-NOT-FOUND",
                        severity=Severity.WARNING,
                        engine=Engine.XLSX,
                        message="Không tìm thấy lệnh soffice / libreoffice trên hệ thống.",
                    )
                ],
            )

        # Chạy headless convert sang pdf tạm rồi bỏ qua để trigger formula recalculation
        return RecalcResult(
            success=False,
            method_used="libreoffice",
            issues=[
                Issue(
                    code="W-XLSX-LO-RECALC-UNSUPPORTED",
                    severity=Severity.WARNING,
                    engine=Engine.XLSX,
                    message="LibreOffice headless không hỗ trợ in-place write-back formula cache trực tiếp.",
                )
            ],
        )
