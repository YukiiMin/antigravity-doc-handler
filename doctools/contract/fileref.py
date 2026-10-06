"""
Hợp đồng giao tiếp FileRef — Đối tượng tham chiếu tệp mờ (Opaque File Reference).
Tuyệt đối không truyền payload binary lớn qua chat stream; chỉ trao đổi qua FileRef.
"""

from __future__ import annotations
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

_SHA256_REGEX = re.compile(r"^[a-fA-F0-9]{64}$")


class FileRef(BaseModel):
    """
    Opaque File Reference contract across all doctools engines and MCP clients.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    uri: str = Field(
        ...,
        description="Đường dẫn URI định danh tài nguyên (vd: resource://docx/files/uuid-123 hoặc file:///abs/path)"
    )
    sha256: str = Field(
        ...,
        description="Mã băm SHA-256 gồm đúng 64 ký tự hex biểu thị tính toàn vẹn của tệp"
    )
    size: int = Field(
        ...,
        ge=0,
        description="Kích thước tệp tin tính bằng bytes (>= 0)"
    )
    mime: str = Field(
        ...,
        min_length=3,
        description="MIME type tiêu chuẩn (vd: application/vnd.openxmlformats-officedocument.wordprocessingml.document)"
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Thời điểm hết hạn TTL của tệp tin trong FileStore (nếu có)"
    )

    @field_validator("sha256")
    @classmethod
    def validate_sha256_hex(cls, v: str) -> str:
        clean_v = v.strip().lower()
        if not _SHA256_REGEX.match(clean_v):
            raise ValueError(f"sha256 must be exactly 64 hexadecimal characters, got: '{v}'")
        return clean_v

    @field_validator("uri")
    @classmethod
    def validate_uri_format(cls, v: str) -> str:
        clean_v = v.strip()
        if not clean_v:
            raise ValueError("uri cannot be empty")
        if not (clean_v.startswith("resource://") or clean_v.startswith("file://") or clean_v.startswith("/")):
            raise ValueError(f"uri must start with 'resource://', 'file://', or absolute path, got: '{v}'")
        return clean_v
