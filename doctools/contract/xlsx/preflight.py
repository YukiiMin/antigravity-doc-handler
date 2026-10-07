"""
doctools.contract.xlsx.preflight
Pydantic contracts for XLSX Preflight Scanner and Package Inventory (FR-01, FR-02).
Categorizes workbook components and selects the appropriate Fidelity Tier (T1..T4).
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

FidelityTier = Literal["T1", "T2", "T3", "T4"]


class SheetInventory(BaseModel):
    """Structural inventory of an individual worksheet in the workbook."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Tên bảng tính (Worksheet)")
    visible_state: Literal["visible", "hidden", "veryHidden"] = Field(
        default="visible", description="Trạng thái hiển thị của sheet"
    )
    max_row: int = Field(default=0, ge=0, description="Chỉ số hàng lớn nhất chứa dữ liệu")
    max_column: int = Field(default=0, ge=0, description="Chỉ số cột lớn nhất chứa dữ liệu")
    formulas_count: int = Field(default=0, ge=0, description="Số lượng ô chứa công thức")
    merges_count: int = Field(default=0, ge=0, description="Số lượng dải ô đã merge")
    has_autofilter: bool = Field(default=False, description="Có bộ lọc AutoFilter hay không")
    conditional_formats_count: int = Field(default=0, ge=0, description="Số luật định dạng có điều kiện")
    data_validations_count: int = Field(default=0, ge=0, description="Số luật xác thực dữ liệu Data Validation")


class PackageInventory(BaseModel):
    """
    Comprehensive package inventory mapping OpenXML parts and risk features.
    Provides ground truth (D-16) for fidelity preservation and quality gates.
    """
    model_config = ConfigDict(extra="forbid")

    file_name: str = Field(..., description="Tên tệp bảng tính")
    sheets: List[SheetInventory] = Field(default_factory=list, description="Danh sách các sheet con")
    total_formulas: int = Field(default=0, ge=0, description="Tổng số công thức trong toàn bộ workbook")
    total_merges: int = Field(default=0, ge=0, description="Tổng số dải ô merge")
    has_drawingml: bool = Field(default=False, description="Chứa part DrawingML (ảnh, logo, shapes)")
    has_images: bool = Field(default=False, description="Chứa tệp hình ảnh trong xl/media")
    has_charts: bool = Field(default=False, description="Chứa biểu đồ trong xl/charts")
    has_pivot_tables: bool = Field(default=False, description="Chứa Pivot Table")
    has_vba_macros: bool = Field(default=False, description="Chứa macro xl/vbaProject.bin")
    has_external_links: bool = Field(default=False, description="Chứa liên kết dữ liệu ngoài xl/externalLinks")
    has_slicers: bool = Field(default=False, description="Chứa Slicer hoặc Timeline điều khiển")
    defined_names_count: int = Field(default=0, ge=0, description="Số lượng Defined Names trong workbook")
    fidelity_tier: FidelityTier = Field(
        default="T1",
        description="Fidelity Tier được chọn: T1 (Pure openpyxl), T2 (Preserve XML parts), T3 (Warning), T4 (Macro rejected)"
    )
