"""Adapter MCP (tuỳ chọn). Danh sách công cụ và schema SINH TỪ registry — không viết tay.

Đã chạy thử với mcp 2.3.0 (API máy chủ cấp thấp dùng callback on_list_tools/on_call_tool).
SDK MCP đổi API giữa các bản lớn, vì vậy adapter được giữ MỎNG: toàn bộ logic nằm ở core/registry.
"""
from __future__ import annotations

import asyncio

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from ..registry import REGISTRY, run


async def _list_tools(ctx, params) -> types.ListToolsResult:
    return types.ListToolsResult(tools=[types.Tool(
        name=op.name, description=op.description, input_schema=op.input_model.model_json_schema(),
        annotations=types.ToolAnnotations(read_only_hint=op.read_only, idempotent_hint=op.idempotent,
                                          destructive_hint=False),
    ) for op in REGISTRY.values()])


async def _call_tool(ctx, params: types.CallToolRequestParams) -> types.CallToolResult:
    result = await asyncio.to_thread(run, params.name, params.arguments or {})   # việc nặng chạy ngoài event loop
    return types.CallToolResult(content=[types.TextContent(type="text", text=result.model_dump_json())],
                                is_error=not result.success)


server = Server("doctools", on_list_tools=_list_tools, on_call_tool=_call_tool)


async def _main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
