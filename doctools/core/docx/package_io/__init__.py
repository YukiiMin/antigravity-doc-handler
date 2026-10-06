"""doctools.core.docx.package_io — Đọc và ghi gói tệp ECMA-376 (.docx) an toàn."""

from .package_reader import PackageReader, safe_read_package
from .package_writer import PackageWriter, safe_write_package

__all__ = [
    "PackageReader",
    "safe_read_package",
    "PackageWriter",
    "safe_write_package",
]
