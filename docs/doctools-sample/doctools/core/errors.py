from __future__ import annotations

from typing import Any

from ..contract.models import FixableBy, Issue


class DocToolsError(Exception):
    """Lỗi có mã ổn định; được registry đổi thành Issue có cấu trúc."""

    def __init__(self, code: str, message: str, *, location: dict[str, Any] | None = None,
                 evidence: dict[str, Any] | None = None, fixable_by: FixableBy = "ai",
                 suggested_action: str | None = None):
        super().__init__(message)
        self.code, self.message = code, message
        self.location, self.evidence = location, evidence
        self.fixable_by, self.suggested_action = fixable_by, suggested_action

    def to_issue(self) -> Issue:
        return Issue(code=self.code, severity="error", message=self.message, location=self.location,
                     evidence=self.evidence, fixable_by=self.fixable_by, suggested_action=self.suggested_action)
