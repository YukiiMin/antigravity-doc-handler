"""
doctools.contract.docx.docspec
Pydantic contracts for Path B DocSpec-driven document generation.
Allows AI agents and workflows to generate documents from scratch via structured JSON.
"""

from __future__ import annotations
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class RunSpec(BaseModel):
    """Specification for an inline run of text."""
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="Nội dung chuỗi ký tự")
    bold: Optional[bool] = Field(default=None, description="Định dạng in đậm")
    italic: Optional[bool] = Field(default=None, description="Định dạng in nghiêng")
    color: Optional[str] = Field(default=None, description="Mã màu HEX (vd: 'FF0000')")


class ParagraphBlock(BaseModel):
    """A standard body paragraph with text or rich runs."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["paragraph"] = "paragraph"
    text: Optional[str] = Field(default=None, description="Chuỗi văn bản đơn giản")
    runs: Optional[List[RunSpec]] = Field(default=None, description="Danh sách run có định dạng chi tiết")
    style: Optional[str] = Field(default=None, description="Tên style tham chiếu trong base template")


class HeadingBlock(BaseModel):
    """A heading element from level 1 to 6."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["heading"] = "heading"
    text: str = Field(..., min_length=1, description="Tiêu đề mục")
    level: int = Field(default=1, ge=1, le=6, description="Cấp độ tiêu đề (1..6)")
    style: Optional[str] = Field(default=None, description="Tên style heading tùy biến")


class ListBlock(BaseModel):
    """An unordered or ordered list."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["list"] = "list"
    items: List[str] = Field(..., min_length=1, description="Danh sách các mục con")
    ordered: bool = Field(default=False, description="True nếu là danh sách có thứ tự (số)")
    style: Optional[str] = Field(default=None, description="Tên style list tùy biến")


class TableBlock(BaseModel):
    """A data table with optional headers and cells."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["table"] = "table"
    headers: Optional[List[str]] = Field(default=None, description="Danh sách nhãn tiêu đề cột")
    rows: List[List[str]] = Field(..., description="Dữ liệu hàng và cột trong bảng")
    style: Optional[str] = Field(default="Table Grid", description="Tên table style")
    col_widths: Optional[List[float]] = Field(default=None, description="Độ rộng cột theo cm")


class ImageBlock(BaseModel):
    """An image element reference."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["image"] = "image"
    source: str = Field(..., min_length=1, description="Đường dẫn tệp, FileRef URI, hoặc base64")
    caption: Optional[str] = Field(default=None, description="Chú thích hình ảnh")
    width_cm: Optional[float] = Field(default=None, gt=0, le=15.92, description="Độ rộng ảnh theo cm (<= 15.92cm)")


class CalloutBlock(BaseModel):
    """A highlighted callout box for notes, warnings, or tips."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["callout"] = "callout"
    text: str = Field(..., min_length=1, description="Nội dung hộp ghi chú")
    title: Optional[str] = Field(default=None, description="Tiêu đề hộp ghi chú")
    kind: Literal["info", "warning", "tip", "note"] = Field(default="info", description="Loại callout")


class PageBreakBlock(BaseModel):
    """Explicit page break."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["page_break"] = "page_break"


DocBlock = Annotated[
    Union[
        ParagraphBlock,
        HeadingBlock,
        ListBlock,
        TableBlock,
        ImageBlock,
        CalloutBlock,
        PageBreakBlock,
    ],
    Field(discriminator="type"),
]


class PageSetupSpec(BaseModel):
    """Page geometry and margins."""
    model_config = ConfigDict(extra="forbid")

    orientation: Literal["portrait", "landscape"] = Field(default="portrait", description="Hướng trang")
    margin_top_cm: Optional[float] = Field(default=2.54, ge=0.5, le=10.0)
    margin_bottom_cm: Optional[float] = Field(default=2.54, ge=0.5, le=10.0)
    margin_left_cm: Optional[float] = Field(default=2.54, ge=0.5, le=10.0)
    margin_right_cm: Optional[float] = Field(default=2.54, ge=0.5, le=10.0)


class DocSpec(BaseModel):
    """
    Root specification for Path B document generation.
    Deterministic JSON description of document blocks, theme, and layout.
    """
    model_config = ConfigDict(extra="forbid")

    docspec_version: str = Field(default="1.0", description="Phiên bản chuẩn DocSpec")
    title: Optional[str] = Field(default=None, description="Tiêu đề tài liệu tổng quát")
    base_template: Optional[str] = Field(default=None, description="ID template đăng ký hoặc đường dẫn base template")
    page_setup: Optional[PageSetupSpec] = Field(default=None, description="Cấu hình trang")
    blocks: List[DocBlock] = Field(default_factory=list, description="Danh sách các khối nội dung tuần tự")
