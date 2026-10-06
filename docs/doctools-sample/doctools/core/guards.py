"""Rào chắn do CODE cưỡng chế (không dựa vào lời nhắc trong prompt)."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from ..contract.models import FileRef
from .errors import DocToolsError


def allowed_roots() -> list[Path]:
    raw = os.environ.get("DOCTOOLS_ROOTS")
    roots = [r for r in raw.split(os.pathsep) if r] if raw else [os.getcwd()]
    return [Path(r).resolve() for r in roots]


def resolve_in_roots(p: str) -> Path:
    path = Path(p).expanduser().resolve()
    if not any(path == r or r in path.parents for r in allowed_roots()):
        raise DocToolsError(
            "E-SEC-PATH", "Đường dẫn nằm ngoài vùng được cấp quyền.",
            evidence={"path": str(path), "roots": [str(r) for r in allowed_roots()]},
            fixable_by="human", suggested_action="Đặt file trong thư mục được cấp quyền (biến DOCTOOLS_ROOTS).",
        )
    return path


def make_file_ref(path: Path) -> FileRef:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return FileRef(path=str(path), sha256=h.hexdigest(), size=path.stat().st_size)
