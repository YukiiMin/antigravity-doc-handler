"""
Hợp đồng dữ liệu Issue & Diagnostics — Cấu trúc chuẩn hóa chẩn đoán lỗi và cảnh báo
dành cho toàn bộ các engine (DOCX, XLSX, DIAGRAM, INFRA) và MCP Client triage.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class Severity(str, Enum):
    """Mức độ nghiêm trọng của Issue."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Engine(str, Enum):
    """Định danh phân hệ sinh ra Issue."""
    DOCX = "docx"
    XLSX = "xlsx"
    DIAGRAM = "diagram"
    INFRA = "infra"


class FixableBy(str, Enum):
    """Đối tượng có thẩm quyền và khả năng sửa Issue."""
    ENGINE = "engine"
    AI = "ai"
    HUMAN = "human"


class Location(BaseModel):
    """Vị trí tọa độ hoặc thành phần phát sinh Issue trong tài liệu / sơ đồ."""
    model_config = ConfigDict(extra="forbid")

    sheet: Optional[str] = Field(default=None, description="Tên Sheet trong workbook Excel")
    cell: Optional[str] = Field(default=None, description="Tọa độ ô Excel (vd: 'B7', 'D14')")
    range: Optional[str] = Field(default=None, description="Dải ô Excel (vd: 'B7:H34')")
    part: Optional[str] = Field(default=None, description="Đường dẫn OpenXML Part (vd: 'word/document.xml')")
    element: Optional[str] = Field(default=None, description="Tên thẻ XML (vd: 'w:tc', 'w:tbl', 'mxCell')")
    node_id: Optional[str] = Field(default=None, description="ID của Node / Cell trong sơ đồ Draw.io")
    edge_id: Optional[str] = Field(default=None, description="ID của Edge / Cạnh nối trong sơ đồ Draw.io")
    line: Optional[int] = Field(default=None, ge=1, description="Số dòng trong văn bản / DSL (1-indexed)")
    col: Optional[int] = Field(default=None, ge=1, description="Số cột trong văn bản / DSL (1-indexed)")


class Issue(BaseModel):
    """
    Cấu trúc chi tiết một Issue trong báo cáo chẩn đoán (Diagnostics).
    Tuân thủ schema chẩn đoán đồng nhất trên cả 3 module theo Master Plan v6.
    """
    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        ...,
        min_length=3,
        description="Mã lỗi / cảnh báo định danh chuẩn (vd: 'E-DOCX-OPENXML-TC-P', 'W-DEV-STYLE-MISMATCH')"
    )
    severity: Severity = Field(
        ...,
        description="Mức độ nghiêm trọng ('error', 'warning', 'info')"
    )
    engine: Engine = Field(
        ...,
        description="Module phát sinh ('docx', 'xlsx', 'diagram', 'infra')"
    )
    message: str = Field(
        ...,
        min_length=1,
        description="Mô tả nguyên nhân kỹ thuật và ngữ cảnh chi tiết của Issue"
    )
    location: Optional[Location] = Field(
        default=None,
        description="Tọa độ hoặc thành phần chi tiết phát sinh Issue"
    )
    fixable_by: Optional[FixableBy] = Field(
        default=None,
        description="Chỉ định đối tượng có thể sửa chữa ('engine', 'ai', 'human')"
    )
    suggested_action: Optional[str] = Field(
        default=None,
        description="Hành động gợi ý cho Agent hoặc kỹ sư để khắc phục"
    )
    evidence: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dữ liệu bằng chứng kỹ thuật hỗ trợ triage (vd: AST diff, font value, bounding box)"
    )
