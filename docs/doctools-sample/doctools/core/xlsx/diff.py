"""Đối chiếu Inventory trước/sau: phát hiện mất/thêm thành phần không khai báo."""
from __future__ import annotations

from ...contract.models import Issue


def diff_inventory(before: dict[str, int], after: dict[str, int], declared: dict[str, int]) -> list[Issue]:
    issues: list[Issue] = []
    for key in sorted(set(before) | set(after)):
        b, a = before.get(key, 0), after.get(key, 0)
        expected = declared.get(key, 0)
        if a - b != expected:
            issues.append(Issue(
                code="E-DIFF-UNDECLARED", severity="error",
                message=f"'{key}' đổi từ {b} sang {a} nhưng không khai báo (mong đợi chênh {expected:+d}).",
                evidence={"key": key, "before": b, "after": a, "declared_delta": expected},
                fixable_by="human" if a < b else "ai",
                suggested_action="Không phát hành file; kiểm tra thành phần bị mất hoặc khai báo trong declared_changes."))
    return issues
