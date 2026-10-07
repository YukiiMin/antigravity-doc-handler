"""
doctools.core.docx.fields.field_manager
Discovers dynamic document fields (TOC, PAGEREF, NUMPAGES) and manages update flags (FR-12).
Injects w:updateFields into word/settings.xml to ensure pagination accuracy on opening.
"""

from __future__ import annotations
import io
from pathlib import Path
import re
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
import zipfile

import docx
from lxml import etree

from doctools.contract import Engine, FixableBy, Issue, Location, Severity

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_SETTINGS_PATH = "word/settings.xml"


class FieldDiscoveryResult:
    """Holds discovered field types, locations, and whether updates are required."""

    def __init__(
        self,
        has_toc: bool,
        has_body_pageref: bool,
        has_body_numpages: bool,
        fields_found: List[Dict[str, Any]],
    ) -> None:
        self.has_toc = has_toc
        self.has_body_pageref = has_body_pageref
        self.has_body_numpages = has_body_numpages
        self.fields_found = fields_found

    @property
    def requires_page_update(self) -> bool:
        """True if document contains fields requiring Word rendering/pagination update."""
        return self.has_toc or self.has_body_pageref or self.has_body_numpages


class FieldManager:
    """
    Scans DOCX package for dynamic fields and manages settings.xml update flags.
    Enforces D-16 (discovery over manifest flags) and FR-12.
    """

    def discover_fields(self, doc_input: Union[Path, bytes, str, docx.Document]) -> FieldDiscoveryResult:
        """Inspects body and paragraph XML for dynamic fields (w:fldSimple, w:fldChar, w:sdt)."""
        raw_bytes: bytes
        if isinstance(doc_input, bytes):
            raw_bytes = doc_input
        elif hasattr(doc_input, "save"):
            buf = io.BytesIO()
            doc_input.save(buf)
            raw_bytes = buf.getvalue()
        else:
            raw_bytes = Path(doc_input).resolve().read_bytes()

        fields_found: List[Dict[str, Any]] = []
        has_toc = False
        has_body_pageref = False
        has_body_numpages = False

        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as zf:
                if "word/document.xml" not in zf.namelist():
                    return FieldDiscoveryResult(False, False, False, [])
                doc_xml = zf.read("word/document.xml")
        except Exception:
            return FieldDiscoveryResult(False, False, False, [])

        root = etree.fromstring(doc_xml)

        # 1. Scan w:fldSimple
        for fld in root.iter(f"{_W}fldSimple"):
            instr = fld.get(f"{_W}instr", "")
            field_type = instr.strip().split()[0].upper() if instr.strip() else "UNKNOWN"
            info = {"type": field_type, "container": "fldSimple", "instr": instr}
            fields_found.append(info)
            if "TOC" in field_type:
                has_toc = True
            elif "PAGEREF" in field_type:
                has_body_pageref = True
            elif "NUMPAGES" in field_type:
                has_body_numpages = True

        # 2. Scan w:instrText inside complex fields
        for instr_elem in root.iter(f"{_W}instrText"):
            text = (instr_elem.text or "").strip()
            if text:
                token = text.split()[0].upper()
                info = {"type": token, "container": "fldChar", "instr": text}
                fields_found.append(info)
                if "TOC" in token:
                    has_toc = True
                elif "PAGEREF" in token:
                    has_body_pageref = True
                elif "NUMPAGES" in token:
                    has_body_numpages = True

        # 3. Scan w:sdt (Structured Document Tags for TOC)
        for sdt in root.iter(f"{_W}sdt"):
            doc_part = sdt.find(f".//{_W}docPartObj/{_W}docPartGallery")
            if doc_part is not None and doc_part.get(f"{_W}val") == "Table of Contents":
                has_toc = True
                fields_found.append({"type": "TOC", "container": "sdt", "instr": "TOC Gallery"})

        return FieldDiscoveryResult(
            has_toc=has_toc,
            has_body_pageref=has_body_pageref,
            has_body_numpages=has_body_numpages,
            fields_found=fields_found,
        )

    def apply_update_policy(
        self,
        raw_bytes: bytes,
        field_update: Literal["auto", "none", "update_on_open"] = "auto",
        toc_mode: Literal["with_page_numbers", "no_page_numbers"] = "with_page_numbers",
    ) -> Tuple[bytes, List[Issue], List[str], Dict[str, Any]]:
        """
        Applies field update policy per FR-12:
        - Resolves 'auto' based on detected fields.
        - Injects w:updateFields into settings.xml when enabled.
        - Issues W-FIELD-UPDATE-REQUIRED warning when human action is needed.
        """
        issues: List[Issue] = []
        guarantees: List[str] = []
        discovery = self.discover_fields(raw_bytes)

        should_update_on_open = False
        if field_update == "update_on_open":
            should_update_on_open = True
        elif field_update == "auto":
            if discovery.requires_page_update and toc_mode == "with_page_numbers":
                should_update_on_open = True

        output_bytes = raw_bytes
        if should_update_on_open:
            output_bytes = self._inject_update_fields_setting(raw_bytes)
            guarantees.append("fields:update_on_open_injected")
            issues.append(
                Issue(
                    code="W-FIELD-UPDATE-REQUIRED",
                    severity=Severity.WARNING,
                    engine=Engine.DOCX,
                    message=(
                        "Document contains dynamic fields (TOC/PAGEREF). "
                        "'w:updateFields' injected; user must click 'Yes' on opening Word dialog."
                    ),
                    location=Location(part=_SETTINGS_PATH),
                    evidence={"dialog_expected": True, "fields_count": len(discovery.fields_found)},
                    fixable_by=FixableBy.HUMAN,
                    suggested_action="Open in Microsoft Word and confirm field update prompt, or press Ctrl+A then F9.",
                )
            )
        elif discovery.requires_page_update and field_update == "none":
            issues.append(
                Issue(
                    code="W-FIELD-UPDATE-REQUIRED",
                    severity=Severity.WARNING,
                    engine=Engine.DOCX,
                    message="Document contains dynamic fields but field_update is set to 'none'. Page numbers may be outdated.",
                    location=Location(part=_SETTINGS_PATH),
                    evidence={"update_applied": False},
                    fixable_by=FixableBy.HUMAN,
                )
            )

        stats = {
            "fields_detected": len(discovery.fields_found),
            "has_toc": discovery.has_toc,
            "update_on_open_applied": should_update_on_open,
        }

        return output_bytes, issues, guarantees, stats

    def _inject_update_fields_setting(self, raw_bytes: bytes) -> bytes:
        """Injects <w:updateFields w:val="true"/> into word/settings.xml."""
        in_buf = io.BytesIO(raw_bytes)
        out_buf = io.BytesIO()

        with zipfile.ZipFile(in_buf, "r") as in_zf, zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as out_zf:
            for item in in_zf.infolist():
                if item.filename == _SETTINGS_PATH:
                    settings_xml = in_zf.read(_SETTINGS_PATH)
                    root = etree.fromstring(settings_xml)
                    uf = root.find(f"{_W}updateFields")
                    if uf is None:
                        uf = etree.SubElement(root, f"{_W}updateFields")
                    uf.set(f"{_W}val", "true")
                    new_xml = etree.tostring(root, xml_declaration=True, encoding="utf-8", standalone=True)
                    out_zf.writestr(_SETTINGS_PATH, new_xml)
                else:
                    out_zf.writestr(item, in_zf.read(item.filename))

            # If settings.xml was missing altogether, create it
            if _SETTINGS_PATH not in in_zf.namelist():
                root = etree.Element(f"{_W}settings", nsmap={"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"})
                uf = etree.SubElement(root, f"{_W}updateFields")
                uf.set(f"{_W}val", "true")
                new_xml = etree.tostring(root, xml_declaration=True, encoding="utf-8", standalone=True)
                out_zf.writestr(_SETTINGS_PATH, new_xml)

        return out_buf.getvalue()


# Global singleton
field_manager = FieldManager()
