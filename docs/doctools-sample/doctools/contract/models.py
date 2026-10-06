"""Hợp đồng đầu ra: mọi công cụ trả cùng một phong bì Result."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["error", "warning", "info"]
FixableBy = Literal["engine", "ai", "human"]


class Issue(BaseModel):
    code: str                                   # ổn định, tra cứu được: E-LOCK-001, W-PKG-...
    severity: Severity
    message: str
    location: dict[str, Any] | None = None      # sheet/ô/part: để AI chỉ đúng chỗ
    evidence: dict[str, Any] | None = None      # số liệu đo được, không phỏng đoán
    fixable_by: FixableBy = "ai"                # ai tự sửa / engine tự sửa / phải hỏi người
    suggested_action: str | None = None         # lỗi phải "dạy" được bước tiếp theo


class FileRef(BaseModel):
    path: str
    sha256: str
    size: int


class Result(BaseModel):
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    file_ref: FileRef | None = None
    issues: list[Issue] = Field(default_factory=list)

    @property
    def exit_code(self) -> int:
        """0 sạch, 1 có cảnh báo, 2 có lỗi (dùng cho CLI/CI)."""
        if not self.success or any(i.severity == "error" for i in self.issues):
            return 2
        if any(i.severity == "warning" for i in self.issues):
            return 1
        return 0
