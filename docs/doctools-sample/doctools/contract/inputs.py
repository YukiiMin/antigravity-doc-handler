"""Hợp đồng đầu vào: AI gửi JSON có schema, không gửi code."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PreflightIn(BaseModel):
    path: str = Field(description="Đường dẫn file .xlsx cần quét (phải nằm trong thư mục được cấp quyền).")


class SetCellsIn(BaseModel):
    path: str = Field(description="File .xlsx nguồn. Không bao giờ bị ghi đè.")
    sheet: str = Field(description="Tên sheet cần sửa.")
    updates: dict[str, str | int | float | None] = Field(
        description='Ô -> giá trị, ví dụ {"B2": 95, "A1": "Tiêu đề"}. Chuỗi bắt đầu bằng "=" được lưu như văn bản trừ khi allow_formulas=true.'
    )
    out_path: str | None = Field(default=None, description="File đầu ra. Mặc định: <tên>_out.xlsx cạnh file nguồn.")
    locked_zones: list[str] = Field(default_factory=list, description='Vùng cấm ghi, ví dụ ["A1:D3", "Data!F5:F20"].')
    allow_formulas: bool = Field(default=False, description="Cho phép giá trị bắt đầu bằng '=' trở thành công thức.")


class DiffInventoryIn(BaseModel):
    before: str = Field(description="File .xlsx trước khi sửa.")
    after: str = Field(description="File .xlsx sau khi sửa.")
    declared_changes: dict[str, int] = Field(
        default_factory=dict,
        description='Thay đổi có chủ đích: khoá Inventory -> chênh lệch mong đợi, ví dụ {"formulas": 2}.',
    )
