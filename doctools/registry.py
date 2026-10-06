"""
doctools.registry — Khung điều phối trung tâm (Central Tool Registry & MCP Protocol Dispatcher).
Đảm bảo:
- Quản lý namespace và tiền tố tường minh: docx.*, xlsx.*, diagram.*, infra.*.
- Ngăn chặn xung đột tên công cụ (Name Collision Guard).
- Middleware tự động bắt ngoại lệ và đóng gói vào ResultEnvelope chuẩn.
- Tự động tích hợp AuditLogger ghi vết request_id.
- Xuất danh mục công cụ tương thích chuẩn MCP (Model Context Protocol).
"""

from __future__ import annotations
import inspect
import time
from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import BaseModel

from .contract.envelope import Diagnostics, ResultEnvelope, Stats
from .contract.issues import Engine, Issue, Severity
from .infra.audit import AuditLogger, get_request_id
from .infra.file_store import FileStore


VALID_NAMESPACES = {
    "docx": Engine.DOCX,
    "xlsx": Engine.XLSX,
    "diagram": Engine.DIAGRAM,
    "infra": Engine.INFRA,
}


class ToolDefinition(BaseModel):
    """Định nghĩa metadata của một công cụ MCP."""
    name: str
    description: str
    engine: Engine
    input_schema: Dict[str, Any]
    handler_name: str


class ToolRegistry:
    """
    Registry tập trung quản lý và định tuyến toàn bộ MCP Tools trong doctools.
    """

    def __init__(
        self,
        file_store: Optional[FileStore] = None,
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        self.file_store = file_store or FileStore()
        self.audit_logger = audit_logger or AuditLogger()
        self._tools: Dict[str, Callable[..., ResultEnvelope]] = {}
        self._metadata: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        input_model: Optional[Type[BaseModel]] = None,
    ) -> Callable[[Callable[..., ResultEnvelope]], Callable[..., ResultEnvelope]]:
        """
        Decorator đăng ký công cụ vào Registry với kiểm tra nghiêm ngặt tiền tố namespace.
        """
        parts = name.split(".", 1)
        if len(parts) != 2 or parts[0] not in VALID_NAMESPACES:
            valid_list = ", ".join(f"'{ns}.*'" for ns in VALID_NAMESPACES)
            raise ValueError(
                f"Invalid tool name '{name}'. All tools must use a strict prefix: {valid_list}."
            )

        engine = VALID_NAMESPACES[parts[0]]

        if name in self._tools:
            raise ValueError(f"Tool collision: Tool '{name}' is already registered in registry.")

        input_schema: Dict[str, Any]
        if input_model is not None:
            input_schema = input_model.model_json_schema()
        else:
            input_schema = {"type": "object", "properties": {}}

        def decorator(handler: Callable[..., ResultEnvelope]) -> Callable[..., ResultEnvelope]:
            self._tools[name] = handler
            self._metadata[name] = ToolDefinition(
                name=name,
                description=description.strip(),
                engine=engine,
                input_schema=input_schema,
                handler_name=handler.__name__,
            )
            return handler

        return decorator

    def execute(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> ResultEnvelope:
        """
        Thực thi một công cụ đã đăng ký.
        Tự động kích hoạt:
        1. Context request_id.
        2. Đo lường thời gian thực thi (stats.render_time_ms).
        3. Middleware bắt lỗi unhandled exceptions thành ResultEnvelope(success=False).
        4. Ghi vết kiểm toán (AuditLogger).
        """
        args = arguments or {}
        req_id = get_request_id()

        if tool_name not in self._tools:
            diag = Diagnostics(engine=Engine.INFRA)
            diag.add_issue(
                Issue(
                    code="E-REGISTRY-TOOL-NOT-FOUND",
                    severity=Severity.ERROR,
                    engine=Engine.INFRA,
                    message=f"Tool '{tool_name}' is not registered in doctools registry.",
                    suggested_action=f"Available tools: {list(self._tools.keys())}",
                )
            )
            env = ResultEnvelope(success=False, diagnostics=diag)
            self.audit_logger.log(
                engine="infra",
                action=f"call:{tool_name}",
                success=False,
                details={"error": "Tool not found", "request_id": req_id},
            )
            return env

        handler = self._tools[tool_name]
        meta = self._metadata[tool_name]
        start_time = time.perf_counter()

        try:
            # Gọi handler với các arguments truyền vào
            result = handler(**args)

            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Cập nhật thời gian nếu stats chưa có
            if result.stats is None:
                result.stats = Stats(render_time_ms=round(duration_ms, 2))
            elif result.stats.render_time_ms is None:
                result.stats.render_time_ms = round(duration_ms, 2)

            # Ghi vết kiểm toán thành công
            file_uri = result.file_ref.uri if result.file_ref else None
            self.audit_logger.log(
                engine=meta.engine.value,
                action=tool_name,
                success=result.success,
                duration_ms=result.stats.render_time_ms,
                file_uri=file_uri,
                details={"guarantees": result.guarantees_applied, "request_id": req_id},
            )

            return result

        except Exception as err:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            diag = Diagnostics(engine=meta.engine)
            diag.add_issue(
                Issue(
                    code="E-SYS-UNCAUGHT-EXCEPTION",
                    severity=Severity.ERROR,
                    engine=meta.engine,
                    message=f"Unhandled exception in tool '{tool_name}': {type(err).__name__}: {str(err)}",
                    evidence={"exception_type": type(err).__name__, "args": repr(args)},
                    suggested_action="Check input arguments and engine logs.",
                )
            )

            env = ResultEnvelope(
                success=False,
                diagnostics=diag,
                stats=Stats(render_time_ms=round(duration_ms, 2)),
            )

            self.audit_logger.log(
                engine=meta.engine.value,
                action=tool_name,
                success=False,
                duration_ms=round(duration_ms, 2),
                details={"error": str(err), "request_id": req_id},
            )

            return env

    def list_tools(self, engine: Optional[Engine] = None) -> List[Dict[str, Any]]:
        """
        Liệt kê danh sách các công cụ đã đăng ký theo định dạng MCP Tool.
        """
        tools_list: List[Dict[str, Any]] = []
        for name, meta in self._metadata.items():
            if engine is not None and meta.engine != engine:
                continue
            tools_list.append({
                "name": meta.name,
                "description": meta.description,
                "inputSchema": meta.input_schema,
            })
        return tools_list

    def get_tool_metadata(self, tool_name: str) -> Optional[ToolDefinition]:
        """Lấy thông tin chi tiết của một công cụ."""
        return self._metadata.get(tool_name)

    def is_registered(self, tool_name: str) -> bool:
        """Kiểm tra xem công cụ đã có trong registry chưa."""
        return tool_name in self._tools
