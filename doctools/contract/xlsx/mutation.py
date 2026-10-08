"""
doctools.contract.xlsx.mutation — Hợp đồng đặc tả đột biến bảng tính (MutationSpec).
Tuân thủ FR-05, FR-06, FR-09, D-02, E1..E14 của Foundation Plan v1.1.
Khai báo cấu trúc JSON MutationSpec cho phép AI điều khiển việc chèn dữ liệu,
nhân bản dòng mẫu (Prototype Row), áp dụng range_policy và kiểm soát vùng khóa.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class CellUpdate(BaseModel):
    """Cập nhật giá trị trực tiếp cho một ô đơn lẻ."""
    model_config = ConfigDict(extra="ignore")

    sheet: str
    coordinate: str
    value: Any
    is_formula: bool = False


class TableExpansion(BaseModel):
    """Đặc tả mở rộng bảng dữ liệu theo dòng và nhân bản dòng mẫu."""
    model_config = ConfigDict(extra="ignore")

    sheet: str
    start_row: Optional[int] = Field(
        default=None, description="Dòng bắt đầu chèn dữ liệu (mặc định lấy sau header hoặc prototype_row)"
    )
    prototype_row: Optional[int] = Field(
        default=None, description="Dòng mẫu dùng để clone 100% token định dạng (E1..E14)"
    )
    consume_prototype: bool = Field(
        default=True, description="Consume prototype row: ghi đè dòng mẫu bằng bản ghi đầu tiên"
    )
    rows_data: List[Union[Dict[str, Any], List[Any]]] = Field(
        ..., description="Danh sách bản ghi cần chèn vào bảng"
    )
    columns_mapping: Optional[Dict[str, Union[str, int]]] = Field(
        default=None, description="Ánh xạ từ khóa dữ liệu sang cột Excel (vd: {'test_id': 'A', 'desc': 'B'})"
    )
    id_columns: List[Union[str, int]] = Field(
        default_factory=list, description="Cột mã định danh cần ép kiểu chuỗi '@' để giữ số 0 đầu"
    )
    range_policy: Literal["table_aware", "excel_native", "shrink_safe"] = Field(
        default="table_aware", description="Chính sách co giãn dải ô công thức tổng hợp"
    )
    border_policy: Literal["preserve_exact", "inherit_prototype"] = Field(
        default="preserve_exact", description="Chính sách viền bảng: preserve_exact (không sửa ngầm) hoặc inherit_prototype"
    )


class MutationSpec(BaseModel):
    """
    MutationSpec JSON điều khiển đột biến bảng tính Excel có schema chặt chẽ.
    Engine từ chối mã hoặc XML tùy tiện do AI viết; chỉ thực thi theo MutationSpec.
    """
    model_config = ConfigDict(extra="ignore")

    template_ref_or_id: str = Field(
        ..., description="Định danh template đã đăng ký hoặc FileRef/URI của file Excel gốc"
    )
    border_policy: Literal["preserve_exact", "inherit_prototype"] = Field(
        default="preserve_exact", description="Chính sách viền toàn cục: preserve_exact hoặc inherit_prototype"
    )
    expansions: List[TableExpansion] = Field(
        default_factory=list, description="Danh sách các bảng cần mở rộng dữ liệu"
    )
    cell_updates: List[CellUpdate] = Field(
        default_factory=list, description="Các cập nhật ô đơn lẻ (phải ngoài vùng khóa locked_zones)"
    )
    locked_zones: List[str] = Field(
        default_factory=list, description="Vùng cấm ghi đè (vd: ['Statistics!C12:I19', '*!A1:T8'])"
    )
    output_filename_hint: Optional[str] = Field(
        default=None, description="Gợi ý tên tệp đầu ra"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata nghiệp vụ đi kèm"
    )
