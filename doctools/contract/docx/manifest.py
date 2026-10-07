"""
doctools.contract.docx.manifest
Pydantic model contracts for DOCX Template Manifests per Section 4.5.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class VariableDef(BaseModel):
    """Schema declaration for a single template variable slot."""
    model_config = ConfigDict(extra="ignore")

    type: str = "string"  # "string", "number", "boolean", "list[string]", "list[dict]", "dict"
    immutable: bool = False
    source_ref_required: bool = False
    max_chars: Optional[int] = None
    description: Optional[str] = None
    default: Optional[Any] = None


class LayoutPolicy(BaseModel):
    """Layout behavior configuration and guard enforcement policy."""
    model_config = ConfigDict(extra="ignore")

    apply_guards: Literal["report_only", "apply"] = "report_only"
    allow_page_break_before_heading: bool = True
    field_update: Literal["auto", "none", "update_on_open"] = "auto"
    toc_mode: Literal["with_page_numbers", "no_page_numbers"] = "with_page_numbers"
    style_conflict_policy: Literal["master_wins", "isolate_styles", "flatten_styles"] = "master_wins"


class TemplateManifest(BaseModel):
    """
    Template Manifest specification schema.
    Defines variables, types, immutability, and layout defaults for a .docx template.
    """
    model_config = ConfigDict(extra="ignore")

    template_id: str
    version: int = 1
    sha256: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    variables: Dict[str, VariableDef] = Field(default_factory=dict)
    layout_policy_default: LayoutPolicy = Field(default_factory=LayoutPolicy)
    guards_allowed: List[str] = Field(
        default_factory=lambda: [
            "keepNext",
            "keepLines",
            "cantSplit",
            "tblHeader",
            "pageBreakBefore",
        ]
    )
