"""
PackageWriter — Đóng gói và ghi tệp ECMA-376 (.docx) an toàn.
Đảm bảo:
- Ghi nguyên tử (Atomic write qua tempfile + os.replace).
- Nén chuẩn ZIP_DEFLATED.
- Hỗ trợ cả python-docx Document và từ điển part dictionary {part_name: bytes}.
"""

from __future__ import annotations
import io
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Union
import docx


class PackageWriter:
    """
    Quản lý ghi gói tệp DOCX nguyên tử và bảo vệ toàn vẹn file trên đĩa.
    """

    @staticmethod
    def write_document_to_path(
        document: docx.Document,
        target_path: Union[str, Path],
    ) -> Path:
        """
        Ghi python-docx Document vào đường dẫn file theo cơ chế nguyên tử.
        """
        dest = Path(target_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Ghi tạm vào tempfile cùng thư mục để bảo đảm tính nguyên tử khi rename
        temp_file = dest.parent / f".tmp_{dest.name}"
        try:
            document.save(str(temp_file))
            os.replace(temp_file, dest)
            return dest
        finally:
            if temp_file.is_file():
                temp_file.unlink(missing_ok=True)

    @staticmethod
    def write_document_to_bytes(document: docx.Document) -> bytes:
        """Xuất python-docx Document ra khối bytes."""
        bio = io.BytesIO()
        document.save(bio)
        return bio.getvalue()

    @staticmethod
    def write_parts_to_path(
        parts: Dict[str, bytes],
        target_path: Union[str, Path],
    ) -> Path:
        """
        Đóng gói dictionary các part XML thành file .docx nguyên tử.
        """
        dest = Path(target_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)

        temp_file = dest.parent / f".tmp_{dest.name}"
        try:
            with zipfile.ZipFile(temp_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for name, content in parts.items():
                    zf.writestr(name, content)
            os.replace(temp_file, dest)
            return dest
        finally:
            if temp_file.is_file():
                temp_file.unlink(missing_ok=True)

    @staticmethod
    def write_parts_to_bytes(parts: Dict[str, bytes]) -> bytes:
        """Đóng gói dictionary các part XML thành bytes."""
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for name, content in parts.items():
                zf.writestr(name, content)
        return bio.getvalue()

    @staticmethod
    def create_modified_package(
        reader: Any,
        modified_parts: Dict[str, bytes],
    ) -> bytes:
        """Tạo gói byte DOCX mới dựa trên reader gốc kèm các part đã sửa."""
        all_parts: Dict[str, bytes] = {}
        for name in reader.get_part_names():
            if name in modified_parts:
                all_parts[name] = modified_parts[name]
            else:
                data = reader.get_part_bytes(name)
                if data is not None:
                    all_parts[name] = data
        return PackageWriter.write_parts_to_bytes(all_parts)


def safe_write_package(
    source: Union[docx.Document, Dict[str, bytes]],
    target_path: Union[str, Path],
) -> Path:
    """Hàm tiện ích ghi gói tệp DOCX an toàn."""
    if isinstance(source, dict):
        return PackageWriter.write_parts_to_path(source, target_path)
    return PackageWriter.write_document_to_path(source, target_path)
