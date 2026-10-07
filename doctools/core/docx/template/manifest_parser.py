"""
doctools.core.docx.template.manifest_parser
Parser and validator for DOCX Template Manifests (YAML/JSON/Dict).
"""

from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Union

import yaml
from pydantic import ValidationError

from doctools.contract import Engine, Issue, Severity
from doctools.contract.docx.manifest import TemplateManifest

_VALID_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class ManifestParseError(Exception):
    """Raised when a template manifest cannot be parsed or validated."""
    pass


def parse_manifest(manifest_input: Union[str, Path, Dict[str, Any], TemplateManifest]) -> TemplateManifest:
    """
    Parses manifest from a dictionary, YAML/JSON string, Path, or returns the TemplateManifest instance directly.
    """
    if isinstance(manifest_input, TemplateManifest):
        return manifest_input

    raw_dict: Dict[str, Any] = {}

    if isinstance(manifest_input, dict):
        raw_dict = manifest_input
    elif isinstance(manifest_input, Path) or (
        isinstance(manifest_input, str) and "\n" not in manifest_input and Path(manifest_input).is_file()
    ):
        path = Path(manifest_input).resolve()
        content = path.read_text(encoding="utf-8")
        try:
            loaded = yaml.safe_load(content)
            if not isinstance(loaded, dict):
                raise ManifestParseError(f"Manifest file at {path} did not resolve to a dictionary.")
            raw_dict = loaded
        except Exception as exc:
            raise ManifestParseError(f"Failed to parse manifest file {path}: {exc}") from exc
    elif isinstance(manifest_input, str):
        import textwrap
        content = textwrap.dedent(manifest_input).strip()
        try:
            # Try JSON first, fallback to YAML
            if content.startswith("{"):
                raw_dict = json.loads(content)
            else:
                loaded = yaml.safe_load(content)
                if not isinstance(loaded, dict):
                    raise ManifestParseError("Manifest string did not parse into a dictionary.")
                raw_dict = loaded
        except Exception as exc:
            raise ManifestParseError(f"Failed to parse manifest content string: {exc}") from exc
    else:
        raise ManifestParseError(f"Unsupported manifest input type: {type(manifest_input).__name__}")

    try:
        return TemplateManifest.model_validate(raw_dict)
    except ValidationError as err:
        raise ManifestParseError(f"Invalid template manifest schema: {err}") from err


def validate_manifest_against_template(
    manifest: TemplateManifest,
    template_data: Union[bytes, Path, str],
) -> List[Issue]:
    """
    Validates manifest integrity against the actual template .docx content:
    - Verifies sha256 checksum match if specified in manifest.
    - Checks variable naming validity.
    """
    issues: List[Issue] = []

    if not manifest.template_id or not manifest.template_id.strip():
        issues.append(
            Issue(
                code="E-DOCX-MANIFEST-INVALID",
                severity=Severity.ERROR,
                engine=Engine.DOCX,
                message="Template manifest must define a non-empty 'template_id'.",
                fixable_by="human",
            )
        )

    # Compute template sha256
    file_bytes: bytes
    if isinstance(template_data, bytes):
        file_bytes = template_data
    else:
        path = Path(template_data).resolve()
        if not path.is_file():
            issues.append(
                Issue(
                    code="E-FILE-NOT-FOUND",
                    severity=Severity.ERROR,
                    engine=Engine.DOCX,
                    message=f"Template file not found at {path}",
                    fixable_by="human",
                )
            )
            return issues
        file_bytes = path.read_bytes()

    computed_hash = hashlib.sha256(file_bytes).hexdigest()

    if manifest.sha256 and manifest.sha256.strip():
        if manifest.sha256.lower().strip() != computed_hash.lower():
            issues.append(
                Issue(
                    code="E-DOCX-TPL-HASH-MISMATCH",
                    severity=Severity.ERROR,
                    engine=Engine.DOCX,
                    message=(
                        f"Template SHA-256 hash mismatch: manifest expected '{manifest.sha256}', "
                        f"actual file hash is '{computed_hash}'."
                    ),
                    evidence={
                        "expected_sha256": manifest.sha256,
                        "actual_sha256": computed_hash,
                    },
                    fixable_by="engine",
                    suggested_action="update_manifest_sha256",
                )
            )

    # Validate variable slot names
    for var_name in manifest.variables.keys():
        if not _VALID_IDENTIFIER.match(var_name):
            issues.append(
                Issue(
                    code="E-DOCX-MANIFEST-INVALID-VARIABLE",
                    severity=Severity.WARNING,
                    engine=Engine.DOCX,
                    message=f"Variable name '{var_name}' is not a standard identifier.",
                    location={"variable": var_name},
                    fixable_by="human",
                )
            )

    return issues
