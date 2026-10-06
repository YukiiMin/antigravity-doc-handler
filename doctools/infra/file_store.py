"""
Hạ tầng lưu trữ FileStore — Quản lý vòng đời tệp tin mờ (Opaque File Store).
Đảm bảo tính bất biến:
- Giao tiếp 100% qua FileRef mờ (không truyền payload lớn qua stream).
- TTL 24h tự động thu dọn tệp quá hạn.
- Cơ chế dọn rác zombie locks (ERR_CONV_004: .~lock.* và ~$*).
- Bảo vệ chống tấn công vượt thư mục (Path Traversal Guard).
"""

from __future__ import annotations
import hashlib
import json
import mimetypes
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..contract.fileref import FileRef


class FileStore:
    """
    Quản lý kho tệp tin mờ nội bộ của doctools với TTL, kiểm tra băm SHA-256,
    và thu dọn khóa tệp zombie của Office / LibreOffice.
    """

    def __init__(
        self,
        base_dir: Optional[Union[str, Path]] = None,
        default_ttl_hours: int = 24,
    ) -> None:
        if base_dir is None:
            self.base_dir = Path(tempfile.gettempdir()) / "doctools_filestore"
        else:
            self.base_dir = Path(base_dir).resolve()

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir = self.base_dir / ".metadata"
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl_hours = default_ttl_hours

    def _get_meta_path(self, file_id: str) -> Path:
        return self.meta_dir / f"{file_id}.json"

    def _save_metadata(self, file_id: str, meta: Dict) -> None:
        meta_path = self._get_meta_path(file_id)
        tmp_meta = meta_path.with_suffix(".tmp")
        with open(tmp_meta, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        os.replace(tmp_meta, meta_path)

    def _load_metadata(self, file_id: str) -> Optional[Dict]:
        meta_path = self._get_meta_path(file_id)
        if not meta_path.is_file():
            return None
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def store_bytes(
        self,
        data: bytes,
        mime: str,
        engine: str = "doctools",
        filename_hint: Optional[str] = None,
        ttl_hours: Optional[int] = None,
    ) -> FileRef:
        """
        Lưu khối dữ liệu bytes vào FileStore và trả về đối tượng FileRef.
        """
        sha256_hash = hashlib.sha256(data).hexdigest().lower()
        size = len(data)
        file_id = f"{uuid.uuid4().hex}"
        
        ext = ""
        if filename_hint:
            ext = Path(filename_hint).suffix
        elif mime:
            guessed_ext = mimetypes.guess_extension(mime)
            if guessed_ext:
                ext = guessed_ext

        stored_filename = f"{file_id}{ext}"
        stored_path = self.base_dir / stored_filename

        # Ghi nguyên tử (Atomic write via tempfile)
        tmp_file = self.base_dir / f".tmp_{file_id}"
        with open(tmp_file, "wb") as f:
            f.write(data)
        os.replace(tmp_file, stored_path)

        ttl = ttl_hours if ttl_hours is not None else self.default_ttl_hours
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl)

        uri = f"resource://{engine}/files/{file_id}"

        meta = {
            "file_id": file_id,
            "filename": stored_filename,
            "sha256": sha256_hash,
            "size": size,
            "mime": mime,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_metadata(file_id, meta)

        return FileRef(
            uri=uri,
            sha256=sha256_hash,
            size=size,
            mime=mime,
            expires_at=expires_at,
        )

    def store_file(
        self,
        source_path: Union[str, Path],
        mime: Optional[str] = None,
        engine: str = "doctools",
        ttl_hours: Optional[int] = None,
    ) -> FileRef:
        """
        Đọc và lưu một tệp tin hiện hữu trên ổ đĩa vào FileStore.
        """
        src = Path(source_path).resolve()
        if not src.is_file():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        detected_mime = mime
        if not detected_mime:
            guessed, _ = mimetypes.guess_type(str(src))
            detected_mime = guessed or "application/octet-stream"

        with open(src, "rb") as f:
            data = f.read()

        return self.store_bytes(
            data=data,
            mime=detected_mime,
            engine=engine,
            filename_hint=src.name,
            ttl_hours=ttl_hours,
        )

    def resolve(self, target: Union[FileRef, str]) -> Path:
        """
        Phân giải FileRef hoặc URI thành đường dẫn tệp tin thực tế trên đĩa.
        Kèm kiểm tra chống path traversal và kiểm tra hạn sử dụng TTL.
        """
        if isinstance(target, FileRef):
            uri = target.uri
            expected_sha256 = target.sha256
        else:
            uri = target
            expected_sha256 = None

        if uri.startswith("file://"):
            local_path = Path(uri[7:]).resolve()
            if not local_path.is_file():
                raise FileNotFoundError(f"File URI target not found: {uri}")
            return local_path

        if not uri.startswith("resource://"):
            raise ValueError(f"Unsupported URI scheme: '{uri}'")

        # Bóc tách file_id từ format: resource://<engine>/files/<file_id>
        parts = uri.split("/")
        if len(parts) < 5 or parts[3] != "files":
            raise ValueError(f"Malformed resource URI: '{uri}'")

        file_id = parts[4]
        meta = self._load_metadata(file_id)
        if not meta:
            raise FileNotFoundError(f"FileRef metadata not found for URI: '{uri}'")

        # Kiểm tra hạn TTL
        if meta.get("expires_at"):
            exp_dt = datetime.fromisoformat(meta["expires_at"])
            if datetime.now(timezone.utc) > exp_dt:
                raise FileNotFoundError(f"FileRef expired for URI: '{uri}'")

        stored_filename = meta["filename"]
        target_path = (self.base_dir / stored_filename).resolve()

        # Path Traversal Guard: Bắt buộc nằm trong base_dir
        if not target_path.is_relative_to(self.base_dir):
            raise PermissionError(f"Security Alert: Path traversal attempt detected for URI '{uri}'")

        if not target_path.is_file():
            raise FileNotFoundError(f"Physical file missing in FileStore for URI: '{uri}'")

        # Xác thực tính toàn vẹn sha256 nếu có
        if expected_sha256:
            with open(target_path, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
            if actual_hash != expected_sha256.lower():
                raise ValueError(
                    f"Integrity check failed for '{uri}': expected sha256 {expected_sha256}, got {actual_hash}"
                )

        return target_path

    def get_bytes(self, target: Union[FileRef, str]) -> bytes:
        """Đọc toàn bộ nội dung bytes của tệp đã giải quyết."""
        resolved = self.resolve(target)
        with open(resolved, "rb") as f:
            return f.read()

    def cleanup_expired(self) -> int:
        """
        Dọn dẹp các tệp tin đã vượt quá thời hạn TTL. Trả về số lượng tệp đã xóa.
        """
        now = datetime.now(timezone.utc)
        removed_count = 0

        for meta_file in list(self.meta_dir.glob("*.json")):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                exp_str = meta.get("expires_at")
                if exp_str:
                    exp_dt = datetime.fromisoformat(exp_str)
                    if now > exp_dt:
                        target_path = self.base_dir / meta["filename"]
                        if target_path.is_file():
                            target_path.unlink(missing_ok=True)
                        meta_file.unlink(missing_ok=True)
                        removed_count += 1
            except Exception:
                continue

        return removed_count

    def cleanup_zombie_locks(
        self,
        target_dir: Optional[Union[str, Path]] = None,
    ) -> List[Path]:
        """
        Thực thi nguyên tắc ERR_CONV_004: Quét và thu gom sạch file rác lock
        .~lock.* (LibreOffice) và ~$* (Microsoft Office).
        """
        scan_dir = Path(target_dir).resolve() if target_dir else self.base_dir
        if not scan_dir.is_dir():
            return []

        removed_locks: List[Path] = []
        for root, _, files in os.walk(scan_dir):
            for file_name in files:
                if file_name.startswith(".~lock.") or file_name.startswith("~$"):
                    lock_file = Path(root) / file_name
                    try:
                        lock_file.unlink(missing_ok=True)
                        removed_locks.append(lock_file)
                    except OSError:
                        pass

        return removed_locks
