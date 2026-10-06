"""Registry: MỘT nơi mô tả công cụ (tên, mô tả cho AI, schema, tính chất). Adapter đều sinh từ đây."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from .contract.models import Issue, Result
from .core.errors import DocToolsError


@dataclass(frozen=True)
class Operation:
    name: str
    description: str
    input_model: type[BaseModel]
    func: Callable[[Any], Result]
    read_only: bool
    idempotent: bool


REGISTRY: dict[str, Operation] = {}


def operation(*, name: str, description: str, input_model: type[BaseModel], read_only: bool, idempotent: bool):
    def deco(func: Callable[[Any], Result]):
        if name in REGISTRY:
            raise ValueError(f"Trùng tên công cụ: {name}")
        REGISTRY[name] = Operation(name, description, input_model, func, read_only, idempotent)
        return func
    return deco


def run(name: str, payload: dict[str, Any]) -> Result:
    """Điểm vào DUY NHẤT: không bao giờ ném ngoại lệ; luôn trả Result có cấu trúc."""
    op = REGISTRY.get(name)
    if op is None:
        return Result(success=False, issues=[Issue(
            code="E-SPEC-UNKNOWN-TOOL", severity="error", message=f"Không có công cụ '{name}'.",
            evidence={"available": sorted(REGISTRY)}, suggested_action="Chọn một tên trong 'available'.")])
    try:
        params = op.input_model.model_validate(payload)
    except ValidationError as e:
        return Result(success=False, issues=[
            Issue(code="E-SPEC-SCHEMA", severity="error", message=err["msg"],
                  location={"path": ".".join(str(p) for p in err["loc"])}, suggested_action="Sửa đầu vào theo inputSchema.")
            for err in e.errors()])
    try:
        return op.func(params)
    except DocToolsError as e:
        return Result(success=False, issues=[e.to_issue()])
    except Exception as e:  # noqa: BLE001 - biên giới adapter: không để lộ traceback cho AI
        return Result(success=False, issues=[Issue(code="E-INTERNAL", severity="error",
                      message=f"Lỗi nội bộ: {type(e).__name__}", fixable_by="human")])


def tool_schemas() -> list[dict[str, Any]]:
    """Mô tả công cụ theo dạng MCP (name/description/inputSchema/annotations) — sinh từ registry."""
    return [{
        "name": op.name, "description": op.description, "inputSchema": op.input_model.model_json_schema(),
        "annotations": {"readOnlyHint": op.read_only, "idempotentHint": op.idempotent, "destructiveHint": False},
    } for op in REGISTRY.values()]
