"""
doctools.contract.docx.patch
Pydantic contracts for declarative document patching (FR-11).
Enforces anchor-based modifications while preserving formatting and OpenXML invariants.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class PatchOp(BaseModel):
    """
    Individual patch operation targeting an anchored element in the document.
    Supported operations:
    - replace_text: replaces text in paragraph or cell runs while keeping formatting
    - insert_paragraph_after: inserts a new paragraph immediately following the anchor
    - delete: removes the anchored paragraph or table
    - update_cell: updates table cell text strictly preserving cell run styling
    """
    model_config = ConfigDict(extra="forbid")

    anchor: str = Field(..., min_length=1, description="Tọa độ anchor đích (vd: '/body/p[2]', '/body/tbl[0]/tr[1]/tc[0]')")
    op: Literal["replace_text", "insert_paragraph_after", "delete", "update_cell"] = Field(..., description="Thao tác sửa đổi")
    target_text: Optional[str] = Field(default=None, description="Chuỗi con cụ thể cần thay thế (nếu bỏ trống, thay toàn bộ)")
    payload: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Dữ liệu nội dung mới để chèn hoặc thay thế")


class PatchSpec(BaseModel):
    """Collection of declarative patch operations to be executed atomically."""
    model_config = ConfigDict(extra="forbid")

    operations: List[PatchOp] = Field(..., min_length=1, description="Danh sách các thao tác patch tuần tự")
