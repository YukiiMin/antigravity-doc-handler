"""
Lớp cơ sở BaseSpec — Nền tảng cấu trúc đặc tả JSON cho cả 3 mô-đun:
DocSpec (Word), MutationSpec / XlsxSpec (Excel), và DiagramSpec (Draw.io).
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T", bound="BaseSpec")


class BaseSpec(BaseModel):
    """
    Lớp cơ sở trừu tượng cho tất cả các JSON Specifications trong doctools.
    Nguyên tắc:
    - extra="forbid": Nghiêm cấm trường lạ ngoài schema để bảo đảm tính tất định.
    - Hỗ trợ phương thức serialization / deserialization tiện lợi.
    """
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    version: str = Field(
        default="2.0",
        description="Phiên bản chuẩn của Specification (mặc định '2.0')"
    )
    title: Optional[str] = Field(
        default=None,
        description="Tiêu đề tài liệu, bảng tính hoặc tên sơ đồ kỹ thuật"
    )
    description: Optional[str] = Field(
        default=None,
        description="Mô tả tóm tắt mục đích hoặc phân hệ nghiệp vụ"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Thuộc tính metadata mở rộng có kiểm soát"
    )

    def to_json(self, indent: int = 2) -> str:
        """Xuất đặc tả ra chuỗi JSON có format đẹp."""
        return self.model_dump_json(indent=indent)

    def to_dict(self) -> Dict[str, Any]:
        """Xuất đặc tả ra dictionary nguyên thủy."""
        return self.model_dump()

    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Đọc và kiểm thực đặc tả từ chuỗi JSON."""
        return cls.model_validate_json(json_str)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Đọc và kiểm thực đặc tả từ dictionary."""
        return cls.model_validate(data)
