"""Adapter CLI: agent nào chạy được shell đều dùng được. KHÔNG chứa logic nghiệp vụ."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import agent_docs
from ..registry import REGISTRY, run, tool_schemas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="doctools")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="Liệt kê công cụ")
    sc = sub.add_parser("schema", help="In JSON Schema của một công cụ")
    sc.add_argument("tool")
    rn = sub.add_parser("run", help="Chạy một công cụ")
    rn.add_argument("tool")
    g = rn.add_mutually_exclusive_group(required=True)
    g.add_argument("--input", help="JSON đầu vào")
    g.add_argument("--input-file", help="File JSON đầu vào")
    ck = sub.add_parser("check-docs", help="Kiểm tra .agent/ khớp registry")
    ck.add_argument("--agent-dir", default=".agent")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        for op in REGISTRY.values():
            print(f"{op.name:24s} {'[đọc]' if op.read_only else '[ghi]'}  {op.description.split('. ')[0]}")
        return 0
    if args.cmd == "schema":
        match = [s for s in tool_schemas() if s["name"] == args.tool]
        if not match:
            print(f"Không có công cụ '{args.tool}'", file=sys.stderr)
            return 2
        print(json.dumps(match[0], ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "check-docs":
        problems = agent_docs.check(Path(args.agent_dir))
        print("\n".join(problems) or "OK: .agent/ khớp registry")
        return 2 if problems else 0

    raw = args.input if args.input is not None else Path(args.input_file).read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"success": False, "issues": [{"code": "E-SPEC-JSON", "severity": "error", "message": str(e)}]}))
        return 2
    result = run(args.tool, payload)
    print(result.model_dump_json(indent=2))
    return result.exit_code
