"""
doctools.core.docx.template.template_registry
In-memory and persistent inventory registry for DOCX templates and manifests.
"""

from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from doctools.contract import Engine, FileRef, Issue, Severity
from doctools.contract.docx.manifest import TemplateManifest
from doctools.core.docx.template.manifest_parser import (
    ManifestParseError,
    parse_manifest,
    validate_manifest_against_template,
)
from doctools.infra.file_store import FileStore


class TemplateRecord(BaseModel):
    """Immutable record of a registered template version."""
    model_config = ConfigDict(extra="ignore")

    template_id: str
    version: int
    manifest: TemplateManifest
    file_ref: FileRef
    registered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TemplateRegistry:
    """
    Centralized inventory registry for DOCX templates.
    Manages template versions, manifests, sha256 hashes, and metadata lookup.
    """

    def __init__(self, file_store: Optional[FileStore] = None) -> None:
        self._file_store = file_store or FileStore()
        # Storage: template_id -> {version: TemplateRecord}
        self._store: Dict[str, Dict[int, TemplateRecord]] = {}

    @property
    def file_store(self) -> FileStore:
        return self._file_store

    def register(
        self,
        template_ref: Union[FileRef, Dict[str, Any], Path, str],
        manifest_input: Union[TemplateManifest, Dict[str, Any], Path, str],
        force_version: Optional[int] = None,
    ) -> Tuple[Optional[TemplateRecord], List[Issue]]:
        """
        Registers a template and its accompanying manifest.
        Validates manifest schema and sha256 checksum against actual template content.
        """
        issues: List[Issue] = []

        # 1. Resolve template file
        resolved_path: Path
        ref_obj: FileRef
        if isinstance(template_ref, FileRef):
            ref_obj = template_ref
            resolved_path = self._file_store.resolve(ref_obj)
        elif isinstance(template_ref, dict) and "uri" in template_ref:
            ref_obj = FileRef(**template_ref)
            resolved_path = self._file_store.resolve(ref_obj)
        else:
            resolved_path = Path(template_ref).resolve()
            if not resolved_path.is_file():
                issues.append(
                    Issue(
                        code="E-FILE-NOT-FOUND",
                        severity=Severity.ERROR,
                        engine=Engine.DOCX,
                        message=f"Template file not found at {resolved_path}",
                    )
                )
                return None, issues
            ref_obj = self._file_store.store_file(
                resolved_path,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                engine="docx",
            )

        if not resolved_path.is_file():
            issues.append(
                Issue(
                    code="E-FILE-NOT-FOUND",
                    severity=Severity.ERROR,
                    engine=Engine.DOCX,
                    message=f"Template file does not exist: {resolved_path}",
                )
            )
            return None, issues

        # 2. Parse and validate manifest
        try:
            manifest = parse_manifest(manifest_input)
        except ManifestParseError as err:
            issues.append(
                Issue(
                    code="E-DOCX-MANIFEST-INVALID",
                    severity=Severity.ERROR,
                    engine=Engine.DOCX,
                    message=f"Failed to parse manifest: {err}",
                )
            )
            return None, issues

        # 3. Validate manifest against template content
        file_bytes = resolved_path.read_bytes()
        actual_hash = hashlib.sha256(file_bytes).hexdigest()

        content_issues = validate_manifest_against_template(manifest, file_bytes)
        for iss in content_issues:
            issues.append(iss)
            if iss.severity == Severity.ERROR:
                return None, issues

        # Inject actual sha256 if omitted
        if not manifest.sha256:
            manifest.sha256 = actual_hash

        # 4. Determine version
        tid = manifest.template_id
        if tid not in self._store:
            self._store[tid] = {}

        if force_version is not None:
            ver = force_version
        elif manifest.version and manifest.version not in self._store[tid]:
            ver = manifest.version
        else:
            current_max = max(self._store[tid].keys(), default=0)
            ver = current_max + 1

        manifest.version = ver

        # 5. Create and save record
        record = TemplateRecord(
            template_id=tid,
            version=ver,
            manifest=manifest,
            file_ref=ref_obj,
        )
        self._store[tid][ver] = record

        return record, issues

    def get(self, template_id: str, version: Optional[int] = None) -> Optional[TemplateRecord]:
        """Retrieves a template record by ID and optional version (defaults to latest)."""
        versions_dict = self._store.get(template_id)
        if not versions_dict:
            return None

        if version is not None:
            return versions_dict.get(version)

        # Return latest version
        max_ver = max(versions_dict.keys())
        return versions_dict[max_ver]

    def get_manifest(self, template_id: str, version: Optional[int] = None) -> Optional[TemplateManifest]:
        """Retrieves template manifest by ID and optional version."""
        rec = self.get(template_id, version)
        return rec.manifest if rec else None

    def list_templates(self) -> List[Dict[str, Any]]:
        """Returns summary inventory of all registered templates."""
        results: List[Dict[str, Any]] = []
        for tid, versions in self._store.items():
            if not versions:
                continue
            latest_ver = max(versions.keys())
            latest_record = versions[latest_ver]
            manifest = latest_record.manifest
            results.append({
                "template_id": tid,
                "latest_version": latest_ver,
                "versions_available": sorted(list(versions.keys())),
                "title": manifest.title or tid,
                "description": manifest.description,
                "variables_count": len(manifest.variables),
                "sha256": manifest.sha256,
                "updated_at": latest_record.registered_at,
            })
        return sorted(results, key=lambda x: x["template_id"])

    def clear(self) -> None:
        """Clears all registered templates (for testing purposes)."""
        self._store.clear()


# Global singleton instance for operational dispatch
_default_registry: Optional[TemplateRegistry] = None


def get_default_template_registry() -> TemplateRegistry:
    """Returns the process-wide default TemplateRegistry instance."""
    global _default_registry
    if _default_registry is None:
        _default_registry = TemplateRegistry()
    return _default_registry
