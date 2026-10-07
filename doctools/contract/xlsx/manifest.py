"""
doctools.contract.xlsx.manifest — Khế ước Manifest và Profile cho XLSX Template.
Quy định schema cho manifest của template bảng tính Excel theo chuẩn v1.1.
Hỗ trợ kiểm định vùng khóa (locked_zones), sheet chân lý (reference_sheet),
semantic anchors, id_columns, calc_policy, range_policy.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class AnchorConfig(BaseModel):
    """Cấu hình semantic anchor cho bảng hoặc tiêu đề."""
    model_config = ConfigDict(extra="ignore")

    kind: Literal["header", "data_start", "summary", "custom"] = "header"
    keyword: Optional[str] = None
    keywords: Optional[List[str]] = None
    match: Literal["exact", "contains", "regex"] = "exact"
    scope: Literal["first_table", "sheet", "all"] = "first_table"
    scan_rows: int = Field(default=150, ge=1, le=10000)
    or_formula: Optional[str] = None


class RequiredPackageConfig(BaseModel):
    """Yêu cầu bảo toàn các thành phần trong OOXML package."""
    model_config = ConfigDict(extra="ignore")

    images: Literal["preserve", "ignore", "forbid"] = "preserve"
    charts: Literal["preserve_relink", "preserve", "ignore"] = "preserve_relink"
    data_validations: Literal["preserve_shift", "ignore"] = "preserve_shift"
    conditional_formats: Literal["preserve_shift", "ignore"] = "preserve_shift"
    defined_names: Literal["preserve_shift", "ignore"] = "preserve_shift"


class CalcPolicyConfig(BaseModel):
    """Chính sách tính toán lại và lưu cache."""
    model_config = ConfigDict(extra="ignore")

    recalc: Literal["oracle_verify", "headless", "none"] = "oracle_verify"
    cache: Literal["write", "skip"] = "write"
    calc_on_open: Literal["auto", "always", "never"] = "auto"


class XlsxTemplateManifest(BaseModel):
    """
    Manifest khai báo quy tắc, vùng khóa và đặc tả cấu trúc của một XLSX Template.
    Tuân thủ mục 4.5 của Foundation Plan v1.1.
    """
    model_config = ConfigDict(extra="ignore")

    template_id: str = Field(..., min_length=1, description="Định danh template duy nhất")
    version: int = Field(default=1, ge=1, description="Phiên bản template")
    description: Optional[str] = Field(default=None, description="Mô tả mục đích template")
    reference_sheet: str = Field(..., min_length=1, description="Sheet chân lý về định dạng và kiểu dáng")
    sibling_sheets: List[str] = Field(default_factory=list, description="Các sheet đối xứng cấu trúc (E5)")
    anchors: Dict[str, Union[AnchorConfig, str, Dict[str, Any]]] = Field(
        default_factory=dict, description="Bộ định vị ngữ nghĩa (semantic anchors)"
    )
    prototype_rows: Dict[str, int] = Field(
        default_factory=dict, description="Dòng mẫu dùng để clone style theo từng sheet"
    )
    locked_zones: List[str] = Field(
        default_factory=list, description="Vùng cấm ghi đè (vd: Statistics!C12:I19, *!A1:T8)"
    )
    id_columns: List[Union[str, int]] = Field(
        default_factory=list, description="Cột mã/định danh cần ép kiểu chuỗi '@' (vd: ['Test ID'])"
    )
    calc_policy: CalcPolicyConfig = Field(default_factory=CalcPolicyConfig)
    range_policy: Literal["table_aware", "excel_native", "shrink_safe"] = "table_aware"
    gates_profile: Optional[str] = Field(default="unit_test_matrix", description="Profile cổng kiểm định")
    required_package: RequiredPackageConfig = Field(default_factory=RequiredPackageConfig)
    placeholders: Dict[str, List[str]] = Field(
        default_factory=lambda: {"forbid_unreplaced": ["{{", "<...>"]},
        description="Quy tắc kiểm tra placeholder chưa thay thế",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ sung")
