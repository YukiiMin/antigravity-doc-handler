"""
doctools.infra — Tầng hạ tầng dùng chung cho toàn bộ các engine.
Bao gồm: FileStore (quản lý tệp mờ & TTL), SandboxRunner (thực thi cô lập), và AuditLogger.
"""

from .file_store import FileStore
from .sandbox import SandboxRunner, SandboxResult
from .audit import AuditLogger, get_request_id, set_request_id

__all__ = [
    "FileStore",
    "SandboxRunner",
    "SandboxResult",
    "AuditLogger",
    "get_request_id",
    "set_request_id",
]
