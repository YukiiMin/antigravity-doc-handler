"""
PackageReader — Đọc và phân giải gói tệp ECMA-376 (.docx) an toàn.
Rào chắn bảo mật:
- Chống Zip Bomb: Giới hạn kích thước giải nén tối đa (500MB) và tỷ lệ nén (> 100x).
- Chống XXE: Sử dụng lxml.etree.XMLParser với resolve_entities=False và no_network=True.
"""

from __future__ import annotations
import io
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Union
from lxml import etree
import docx

_MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024  # 500MB
_MAX_COMPRESSION_RATIO = 100.0


def get_safe_xml_parser() -> etree.XMLParser:
    """Tạo bộ parser XML phòng chống XXE và tấn công thực thể mạng."""
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        recover=False,
        remove_blank_text=False,
    )


class PackageReader:
    """
    Quản lý đọc gói ZIP ECMA-376 và bóc tách các part XML an toàn.
    """

    def __init__(self, source: Union[str, Path, bytes, io.BytesIO]) -> None:
        if isinstance(source, (str, Path)):
            self._src_bytes = Path(source).read_bytes()
        elif isinstance(source, bytes):
            self._src_bytes = source
        elif isinstance(source, io.BytesIO):
            self._src_bytes = source.getvalue()
        else:
            raise TypeError(f"Unsupported source type: {type(source)}")

        self._validate_zip_safety(self._src_bytes)
        self._parts: Dict[str, bytes] = {}
        self._load_parts()

    def _validate_zip_safety(self, data: bytes) -> None:
        """Kiểm tra rào chắn chống Zip Bomb."""
        try:
            with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
                total_uncompressed = 0
                compressed_size = len(data)

                for info in zf.infolist():
                    total_uncompressed += info.file_size
                    if total_uncompressed > _MAX_UNCOMPRESSED_BYTES:
                        raise ValueError(
                            f"Security Alert (Zip Bomb): Uncompressed size exceeds limit {_MAX_UNCOMPRESSED_BYTES} bytes."
                        )

                if compressed_size > 0:
                    ratio = total_uncompressed / compressed_size
                    if ratio > _MAX_COMPRESSION_RATIO:
                        raise ValueError(
                            f"Security Alert (Zip Bomb): Compression ratio {ratio:.1f}x exceeds safe threshold."
                        )
        except zipfile.BadZipFile as err:
            raise ValueError(f"Invalid Word document package: {err}")

    def _load_parts(self) -> None:
        """Nạp toàn bộ các part vào bộ nhớ."""
        with zipfile.ZipFile(io.BytesIO(self._src_bytes), "r") as zf:
            for name in zf.namelist():
                self._parts[name] = zf.read(name)

    def get_part_names(self) -> List[str]:
        """Danh sách tất cả các part trong gói DOCX."""
        return list(self._parts.keys())

    def get_part_bytes(self, part_name: str) -> Optional[bytes]:
        """Đọc dữ liệu thô của một part."""
        return self._parts.get(part_name)

    def get_part_xml(self, part_name: str) -> Optional[etree._Element]:
        """Phân giải part XML an toàn bằng safe XML parser."""
        content = self.get_part_bytes(part_name)
        if not content:
            return None
        parser = get_safe_xml_parser()
        return etree.fromstring(content, parser=parser)

    def to_docx_document(self) -> docx.Document:
        """Chuyển đổi thành đối tượng python-docx Document để thao tác."""
        return docx.Document(io.BytesIO(self._src_bytes))


def safe_read_package(source: Union[str, Path, bytes, io.BytesIO]) -> PackageReader:
    """Hàm tiện ích đọc gói tệp DOCX an toàn."""
    return PackageReader(source)
