"""Chống lệch tài liệu: mọi `tool:<tên>` trong .agent/ phải có trong registry, và mọi công cụ phải được nhắc ít nhất một lần."""
from __future__ import annotations

import re
from pathlib import Path

from .registry import REGISTRY

REF = re.compile(r"tool:([a-z0-9_]+)")


def check(agent_dir: Path) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for md in sorted(agent_dir.rglob("*.md")):
        for name in REF.findall(md.read_text(encoding="utf-8")):
            seen.add(name)
            if name not in REGISTRY:
                problems.append(f"{md.relative_to(agent_dir.parent)}: nhắc công cụ không tồn tại 'tool:{name}'")
    for name in REGISTRY:
        if name not in seen:
            problems.append(f"Công cụ '{name}' chưa được nhắc trong .agent/ (AI sẽ không biết khi nào dùng)")
    return problems
