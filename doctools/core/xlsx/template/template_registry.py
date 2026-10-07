"""
doctools.core.xlsx.template.template_registry — Kho lưu trữ và quản lý phiên bản XLSX Template.
Đảm bảo tính bất biến của template, xác minh toàn vẹn sha256 và bảo vệ DrawingML.
"""

from __future__ import annotations
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field

from doctools.contract.envelope import FileRef
from doctools.contract.issues import Engine, Issue, Severity
from doctools.contract.xlsx.manifest import XlsxTemplateManifest
from doctools.contract.xlsx.preflight import PackageInventory
from doctools.core.xlsx.preflight.scanner import PreflightScanner
from doctools.infra.file_store import FileStore
from .manifest_parser import (
    ManifestParseError,
    parse_manifest,
    validate_manifest_against_template,
)

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class XlsxTemplateRecord(BaseModel):
    """Bản ghi bất biến của một phiên bản XLSX Template đã đăng ký."""
    model_config = ConfigDict(extra="ignore")

    template_id: str
    version: int
    manifest: XlsxTemplateManifest
    file_ref: FileRef
    inventory: PackageInventory
    sha256: str
    registered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class XlsxTemplateRegistry:
    """
    Kho đăng ký tập trung cho XLSX Template.
    Quản lý phiên bản, kiểm tra toàn vẹn sha256 và lưu trữ inventory để bảo vệ DrawingML.
    """

    def __init__(self, file_store: Optional[FileStore] = None) -> None:
        self._file_store = file_store or FileStore()
        # Storage: template_id -> {version: XlsxTemplateRecord}
        self._store: Dict[str, Dict[int, XlsxTemplateRecord]] = {}

    @property
    def file_store(self) -> FileStore:
        return self._file_store

    def register(
        self,
        template_ref: Union[FileRef, Dict[str, Any], Path, str],
        manifest_input: Union[XlsxTemplateManifest, Dict[str, Any], Path, str],
        force_version: Optional[int] = None,
    ) -> Tuple[Optional[XlsxTemplateRecord], List[Issue]]:
        """
        Đăng ký template vào kho kèm manifest.
        Tính hash sha256, chạy Preflight Scanner ghi nhận package inventory.
        """
        issues: List[Issue] = []

        try:
            manifest = parse_manifest(manifest_input)
        except ManifestParseError as pe:
            issues.append(Issue(
                code="E-TPL-MANIFEST-PARSE-FAILED",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=str(pe),
            ))
            return None, issues

        template_path: Path
        try:
            if isinstance(template_ref, FileRef):
                template_path = self._file_store.resolve(template_ref)
            elif isinstance(template_ref, dict) and "uri" in template_ref:
                template_path = self._file_store.resolve(FileRef(**template_ref))
            elif isinstance(template_ref, str) and (template_ref.startswith("resource://") or template_ref.startswith("file://")):
                template_path = self._file_store.resolve(template_ref)
            else:
                template_path = Path(template_ref).resolve()
        except Exception as e:
            issues.append(Issue(
                code="E-TPL-RESOLVE-FAILED",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Không thể giải mã đường dẫn template: {e}",
            ))
            return None, issues

        if not template_path.exists() or not template_path.is_file():
            issues.append(Issue(
                code="E-TPL-FILE-NOT-FOUND",
                severity=Severity.ERROR,
                engine=Engine.XLSX,
                message=f"Tệp template không tồn tại: {template_path}",
            ))
            return None, issues

        raw_bytes = template_path.read_bytes()
        actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()

        # Kiểm định manifest đối chiếu với nội dung workbook thực tế
        val_issues = validate_manifest_against_template(manifest, template_path)
        issues.extend(val_issues)
        if any(i.severity == Severity.ERROR for i in issues):
            return None, issues

        # Chạy PreflightScanner để lưu trữ package inventory
        scanner = PreflightScanner()
        scan_res = scanner.scan(template_path)
        issues.extend(scan_res.issues)
        if any(i.severity == Severity.ERROR for i in issues):
            return None, issues
        inventory = scan_res.inventory

        target_version = force_version or manifest.version
        tid = manifest.template_id

        if tid in self._store and target_version in self._store[tid]:
            existing_rec = self._store[tid][target_version]
            if existing_rec.sha256 == actual_sha256 and force_version is None:
                return existing_rec, issues
            if force_version is None:
                issues.append(Issue(
                    code="E-TPL-VERSION-COLLISION",
                    severity=Severity.ERROR,
                    engine=Engine.XLSX,
                    message=(
                        f"Template '{tid}' phiên bản {target_version} đã tồn tại trong kho "
                        f"với sha256 khác. Hãy tăng version hoặc dùng force_version."
                    ),
                    evidence={"existing_sha": existing_rec.sha256, "new_sha": actual_sha256},
                ))
                return None, issues

        stored_ref = self._file_store.store_file(
            template_path,
            mime=_XLSX_MIME,
            engine="xlsx",
        )

        record = XlsxTemplateRecord(
            template_id=tid,
            version=target_version,
            manifest=manifest,
            file_ref=stored_ref,
            inventory=inventory,
            sha256=actual_sha256,
        )

        if tid not in self._store:
            self._store[tid] = {}
        self._store[tid][target_version] = record

        return record, issues

    def get(self, template_id: str, version: Optional[int] = None) -> Optional[XlsxTemplateRecord]:
        """Truy xuất bản ghi template theo ID và version (mặc định lấy bản mới nhất)."""
        versions = self._store.get(template_id)
        if not versions:
            return None
        if version is not None:
            return versions.get(version)
        max_ver = max(versions.keys())
        return versions[max_ver]

    def list_templates(self) -> List[Dict[str, Any]]:
        """Liệt kê danh sách tất cả template và phiên bản đã đăng ký."""
        results = []
        for tid, ver_map in self._store.items():
            for ver, rec in ver_map.items():
                results.append({
                    "template_id": tid,
                    "version": ver,
                    "reference_sheet": rec.manifest.reference_sheet,
                    "sha256": rec.sha256,
                    "registered_at": rec.registered_at,
                    "tier": (
                        rec.inventory.fidelity_tier.value
                        if hasattr(rec.inventory.fidelity_tier, "value")
                        else str(rec.inventory.fidelity_tier)
                    ),
                    "file_uri": rec.file_ref.uri,
                })
        return sorted(results, key=lambda x: (x["template_id"], x["version"]))


_DEFAULT_REGISTRY: Optional[XlsxTemplateRegistry] = None


def get_default_xlsx_template_registry() -> XlsxTemplateRegistry:
    """Singleton mặc định cho XlsxTemplateRegistry."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = XlsxTemplateRegistry()
    return _DEFAULT_REGISTRY
