"""
AuditLogger — Hệ thống ghi nhật ký kiểm toán và theo dõi vòng đời tác vụ (Traceability).
Gắn kết xuyên suốt một request_id duy nhất qua ContextVar cho mọi chuỗi thao tác liên mô-đun.
"""

from __future__ import annotations
import json
import os
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

_REQUEST_ID_CTX: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> str:
    """Lấy request_id của ngữ cảnh hiện tại; nếu chưa có thì khởi tạo ngẫu nhiên."""
    req_id = _REQUEST_ID_CTX.get()
    if req_id is None:
        req_id = f"req-{uuid.uuid4().hex[:12]}"
        _REQUEST_ID_CTX.set(req_id)
    return req_id


def set_request_id(request_id: Optional[str] = None) -> str:
    """Thiết lập thủ công request_id cho ngữ cảnh tác vụ hiện tại."""
    new_id = request_id or f"req-{uuid.uuid4().hex[:12]}"
    _REQUEST_ID_CTX.set(new_id)
    return new_id


class AuditEvent(BaseModel):
    """Bản ghi sự kiện kiểm toán cấu trúc JSON."""
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(..., description="ID định danh ngữ cảnh truy vấn xuyên suốt")
    timestamp: str = Field(..., description="Thời điểm ghi nhận sự kiện (ISO 8601 UTC)")
    engine: str = Field(..., description="Phân hệ thực thi ('docx', 'xlsx', 'diagram', 'infra')")
    action: str = Field(..., description="Hành động tác vụ thực hiện")
    success: bool = Field(..., description="Trạng thái hoàn thành thành công")
    duration_ms: Optional[float] = Field(default=None, description="Thời gian thực thi")
    file_uri: Optional[str] = Field(default=None, description="URI của tệp tin liên quan")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Chi tiết mở rộng")


class AuditLogger:
    """
    Quản lý lưu vết nhật ký kiểm toán vào tệp JSON Lines (audit.jsonl)
    và lưu trữ bộ đệm sự kiện gần nhất phục vụ kiểm tra tức thì.
    """

    def __init__(self, log_file: Optional[Path] = None, max_in_memory: int = 100) -> None:
        self.log_file = log_file
        self.max_in_memory = max_in_memory
        self._history: List[AuditEvent] = []

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        engine: str,
        action: str,
        success: bool,
        duration_ms: Optional[float] = None,
        file_uri: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Ghi nhận một sự kiện kiểm toán."""
        event = AuditEvent(
            request_id=get_request_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            engine=engine,
            action=action,
            success=success,
            duration_ms=duration_ms,
            file_uri=file_uri,
            details=details,
        )

        self._history.append(event)
        if len(self._history) > self.max_in_memory:
            self._history.pop(0)

        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(event.model_dump_json() + "\n")
            except OSError:
                pass

        return event

    def get_recent_events(self, limit: int = 50) -> List[AuditEvent]:
        """Truy xuất danh sách các sự kiện kiểm toán gần nhất trong bộ nhớ."""
        return self._history[-limit:]
