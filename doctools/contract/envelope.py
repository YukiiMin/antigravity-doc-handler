"""
Hợp đồng dữ liệu ResultEnvelope & Diagnostics — Phong bì kết quả giao tiếp thống nhất
giữa MCP Server và AI Client / CLI Runner cho toàn bộ các engine doctools.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict

from .fileref import FileRef
from .issues import Engine, Issue, Severity


class Diagnostics(BaseModel):
    """
    Báo cáo chẩn đoán chất lượng gồm 3 nhóm: errors, warnings, info.
    Hỗ trợ phương thức tiện ích để tự động phân loại Issue theo severity.
    """
    model_config = ConfigDict(extra="forbid")

    engine: Engine = Field(..., description="Engine chủ quản sinh báo cáo chẩn đoán")
    errors: List[Issue] = Field(default_factory=list, description="Danh sách lỗi nghiêm trọng vi phạm Invariants")
    warnings: List[Issue] = Field(default_factory=list, description="Danh sách cảnh báo (vd: lệch template W-DEV-*)")
    info: List[Issue] = Field(default_factory=list, description="Thông tin quan sát và tối ưu hóa bổ sung")

    def add_issue(self, issue: Issue) -> None:
        """Thêm một Issue và tự động điều hướng vào nhóm tương ứng."""
        if issue.severity == Severity.ERROR:
            self.errors.append(issue)
        elif issue.severity == Severity.WARNING:
            self.warnings.append(issue)
        else:
            self.info.append(issue)

    @property
    def has_errors(self) -> bool:
        """Kiểm tra có bất kỳ lỗi chặn nào không."""
        return len(self.errors) > 0

    @property
    def total_count(self) -> int:
        """Tổng số Issue ghi nhận được."""
        return len(self.errors) + len(self.warnings) + len(self.info)


class Stats(BaseModel):
    """Chỉ số vận hành và tài nguyên của tác vụ xử lý."""
    model_config = ConfigDict(extra="forbid")

    render_time_ms: Optional[float] = Field(default=None, ge=0.0, description="Thời gian thực thi tính bằng milliseconds")
    elements_processed: Optional[int] = Field(default=None, ge=0, description="Số lượng thành phần (nodes, cells, paras) đã xử lý")
    memory_peak_mb: Optional[float] = Field(default=None, ge=0.0, description="Dung lượng bộ nhớ RAM đỉnh (MB)")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="Các chỉ số đặc thù của từng module")


class ResultEnvelope(BaseModel):
    """
    Phong bì phản hồi thống nhất (Unified Result Envelope).
    Tất cả các MCP tool calls từ doctools đều trả về đối tượng này.
    """
    model_config = ConfigDict(extra="forbid")

    success: bool = Field(..., description="Trạng thái thành công của tác vụ")
    file_ref: Optional[FileRef] = Field(default=None, description="Tham chiếu tệp tin kết quả mờ (nếu có)")
    diagnostics: Diagnostics = Field(..., description="Khối chẩn đoán, cảnh báo và lỗi chi tiết")
    guarantees_applied: List[str] = Field(
        default_factory=list,
        description="Danh sách các rào chắn kỹ thuật đã thực thi (vd: 'cantSplit_enforced', 'AST_formula_shifted')"
    )
    stats: Optional[Stats] = Field(default=None, description="Chỉ số hiệu năng và thống kê thực thi")

    @model_validator(mode="after")
    def validate_success_and_errors_consistency(self) -> ResultEnvelope:
        """Đảm bảo tính nhất quán: Không thể có success=True nếu diagnostics chứa errors."""
        if self.success and self.diagnostics.has_errors:
            raise ValueError(
                f"ResultEnvelope inconsistency: success=True is prohibited when diagnostics contain "
                f"{len(self.diagnostics.errors)} errors."
            )
        return self
