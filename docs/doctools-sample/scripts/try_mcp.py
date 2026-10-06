"""Chạy thử adapter MCP đầu-cuối: khởi động server qua stdio, liệt kê công cụ, gọi một công cụ."""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
from helpers import make_fixture  # noqa: E402


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fx = make_fixture(Path(tmp).resolve())
        env = {**os.environ, "PYTHONPATH": str(ROOT), "DOCTOOLS_ROOTS": str(Path(tmp).resolve())}
        params = StdioServerParameters(command=sys.executable, args=["-m", "doctools.adapters.mcp_server"], env=env)
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                tools = (await s.list_tools()).tools
                print("TOOLS:", [(t.name, t.annotations.read_only_hint) for t in tools])
                res = await s.call_tool("preflight_xlsx", {"path": str(fx)})
                data = json.loads(res.content[0].text)
                print("preflight ->", data["data"]["fidelity_tier"], data["data"]["inventory"]["images"], "ảnh")
                res = await s.call_tool("set_cells_xlsx", {"path": str(fx), "sheet": "Data", "updates": {"B10": "x"}})
                print("set_cells (ô gộp) ->", [i["code"] for i in json.loads(res.content[0].text)["issues"]])
                res = await s.call_tool("set_cells_xlsx", {"path": 123})
                print("sai schema ->", res.is_error, res.content[0].text[:120])


asyncio.run(main())
