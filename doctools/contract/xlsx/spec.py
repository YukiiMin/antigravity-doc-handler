"""
doctools.contract.xlsx.spec — Hợp đồng đặc tả bảng tính thuần (XlsxSpec Schema).
Tuân thủ Path B (Spec Builder), FR-08, FR-15 của Foundation Plan v1.1:
- Khai báo cấu trúc JSON XlsxSpec cho phép AI dựng mới bảng tính hoàn chỉnh từ đầu.
- Hỗ trợ đặc tả ô (CellSpec), bảng biểu (TableSpec), kiểu dáng (StyleSpec) và biểu đồ (ChartSpec).
- Sinh native DrawingML charts trong openpyxl mà không cần qua template mẫu.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class StyleSpec(BaseModel):
    """Đặc tả kiểu dáng trình bày của một ô tính."""
    model_config = ConfigDict(extra="ignore")

    font_name: Optional[str] = "Arial"
    font_size: Optional[float] = 11.0
    bold: Optional[bool] = False
    italic: Optional[bool] = False
    font_color: Optional[str] = None  # RGB Hex, vd: "000000"
    fill_color: Optional[str] = None  # RGB Hex, vd: "FFFF00"
    border_style: Optional[str] = None  # "thin", "medium", "double"
    border_color: Optional[str] = "000000"
    alignment_h: Optional[Literal["left", "center", "right", "justify"]] = None
    alignment_v: Optional[Literal["top", "center", "bottom"]] = "center"
    number_format: Optional[str] = None  # "@", "#,##0", "0.00%"


class CellSpec(BaseModel):
    """Đặc tả một ô tính riêng lẻ."""
    model_config = ConfigDict(extra="ignore")

    coordinate: str = Field(..., description="Tọa độ ô, vd: 'A1'")
    value: Any = Field(default=None, description="Giá trị ô")
    is_formula: bool = Field(default=False, description="Đánh dấu giá trị là công thức nếu bắt đầu bằng '='")
    style: Optional[StyleSpec] = None


class TableSpec(BaseModel):
    """Đặc tả bảng dữ liệu dạng khối (Block Table)."""
    model_config = ConfigDict(extra="ignore")

    start_coordinate: str = Field(default="A1", description="Góc trên cùng bên trái của bảng")
    headers: List[str] = Field(default_factory=list, description="Danh sách tiêu đề cột")
    rows: List[List[Any]] = Field(default_factory=list, description="Danh sách các dòng dữ liệu")
    id_columns: List[int] = Field(default_factory=list, description="Chỉ số các cột mã định danh cần ép format '@'")
    header_style: Optional[StyleSpec] = None
    row_style: Optional[StyleSpec] = None


class ChartSpec(BaseModel):
    """Đặc tả biểu đồ DrawingML native."""
    model_config = ConfigDict(extra="ignore")

    chart_type: Literal["bar", "col", "line", "pie", "area", "doughnut"] = Field(
        ..., description="Loại biểu đồ"
    )
    title: Optional[str] = None
    data_min_col: int
    data_min_row: int
    data_max_col: int
    data_max_row: int
    titles_from_data: bool = True
    categories_min_col: Optional[int] = None
    categories_min_row: Optional[int] = None
    categories_max_col: Optional[int] = None
    categories_max_row: Optional[int] = None
    anchor: str = Field(default="E2", description="Ô neo vị trí biểu đồ trên sheet")
    width_cm: float = 15.0
    height_cm: float = 8.0


class SheetSpec(BaseModel):
    """Đặc tả một worksheet trong workbook."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Tên worksheet")
    cells: List[CellSpec] = Field(default_factory=list, description="Danh sách các ô riêng lẻ")
    tables: List[TableSpec] = Field(default_factory=list, description="Danh sách các khối bảng")
    charts: List[ChartSpec] = Field(default_factory=list, description="Danh sách các biểu đồ DrawingML")
    merged_ranges: List[str] = Field(default_factory=list, description="Các dải ô gộp, vd: ['A1:E1']")
    column_widths: Dict[str, float] = Field(default_factory=dict, description="Độ rộng cột, vd: {'A': 15.0}")
    freeze_panes: Optional[str] = Field(default=None, description="Tọa độ ô cố định dòng/cột, vd: 'A3'")


class XlsxSpec(BaseModel):
    """Hợp đồng đặc tả workbook hoàn chỉnh (Path B XlsxSpec)."""
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    sheets: List[SheetSpec] = Field(default_factory=list, description="Danh sách các worksheet")
    output_filename_hint: Optional[str] = "generated_workbook.xlsx"
    metadata: Dict[str, Any] = Field(default_factory=dict)
