"""
Unit test suite for doctools.infra.
Kiểm tra toàn diện: FileStore (TTL, SHA-256, Zombie Locks ERR_CONV_004),
SandboxRunner (Timeout, UTF-8), và AuditLogger (Request ID traceability).
"""

from __future__ import annotations
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

from doctools.infra import (
    FileStore,
    SandboxRunner,
    AuditLogger,
    get_request_id,
    set_request_id,
)


class TestFileStore(unittest.TestCase):
    """Kiểm tra FileStore và các rào chắn kỹ thuật."""

    def setUp(self) -> None:
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_filestore_"))
        self.store = FileStore(base_dir=self.test_dir, default_ttl_hours=24)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_store_bytes_and_resolve(self) -> None:
        data = b"Hello OpenXML Document Stream"
        fileref = self.store.store_bytes(
            data=data,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            engine="docx",
            filename_hint="doc.docx",
        )
        self.assertTrue(fileref.uri.startswith("resource://docx/files/"))
        self.assertEqual(fileref.size, len(data))
        self.assertEqual(fileref.sha256, hashlib.sha256(data).hexdigest().lower())

        resolved_path = self.store.resolve(fileref)
        self.assertTrue(resolved_path.is_file())
        with open(resolved_path, "rb") as f:
            self.assertEqual(f.read(), data)

    def test_store_file_from_disk(self) -> None:
        temp_input = self.test_dir / "sample_input.xlsx"
        sample_bytes = b"Sample Excel Binary Content"
        with open(temp_input, "wb") as f:
            f.write(sample_bytes)

        fileref = self.store.store_file(
            source_path=temp_input,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            engine="xlsx",
        )
        self.assertEqual(fileref.size, len(sample_bytes))
        self.assertEqual(fileref.mime, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def test_integrity_check_failure_detected(self) -> None:
        data = b"Original Safe Content"
        fileref = self.store.store_bytes(data=data, mime="text/plain", engine="doctools")
        resolved = self.store.resolve(fileref)

        # Cố ý làm sai lệch nội dung trên đĩa (Tampering simulation)
        with open(resolved, "wb") as f:
            f.write(b"Tampered Corrupt Content")

        # Khi resolve lại với FileRef mang sha256 cũ, bắt buộc phát hiện mismatch
        with self.assertRaises(ValueError):
            self.store.resolve(fileref)

    def test_ttl_cleanup_expired(self) -> None:
        data = b"Temporary Expiring Content"
        # Lưu tệp với TTL âm (đã hết hạn)
        fileref = self.store.store_bytes(data=data, mime="text/plain", ttl_hours=-1)

        cleaned_count = self.store.cleanup_expired()
        self.assertEqual(cleaned_count, 1)

        # Sau khi cleanup, resolve phải báo FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            self.store.resolve(fileref)

    def test_zombie_locks_cleanup_err_conv_004(self) -> None:
        """Kiểm tra bất biến ERR_CONV_004: Tự động thu dọn lock LibreOffice / Office."""
        lock_dir = self.test_dir / "reports"
        lock_dir.mkdir(parents=True, exist_ok=True)

        libreoffice_lock = lock_dir / ".~lock.Report5_SRS.docx#"
        ms_office_lock = lock_dir / "~$Report5_SRS.docx"
        valid_file = lock_dir / "Report5_SRS.docx"

        libreoffice_lock.write_text("lock", encoding="utf-8")
        ms_office_lock.write_text("lock", encoding="utf-8")
        valid_file.write_text("valid content", encoding="utf-8")

        self.assertTrue(libreoffice_lock.is_file())
        self.assertTrue(ms_office_lock.is_file())
        self.assertTrue(valid_file.is_file())

        removed = self.store.cleanup_zombie_locks(target_dir=lock_dir)

        self.assertEqual(len(removed), 2)
        self.assertFalse(libreoffice_lock.exists())
        self.assertFalse(ms_office_lock.exists())
        # File hợp lệ không bị xóa
        self.assertTrue(valid_file.is_file())


class TestSandboxRunner(unittest.TestCase):
    """Kiểm tra môi trường thực thi cô lập SandboxRunner."""

    def setUp(self) -> None:
        self.runner = SandboxRunner(default_timeout_s=5.0)

    def test_successful_execution(self) -> None:
        cmd = [sys.executable, "-c", "import sys; print('Xin chao Sandbox'); sys.exit(0)"]
        result = self.runner.run(cmd)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Xin chao Sandbox", result.stdout)
        self.assertFalse(result.timed_out)
        self.assertGreater(result.duration_ms, 0.0)

    def test_timeout_enforcement(self) -> None:
        # Chạy script ngủ 3 giây nhưng timeout chỉ 0.3 giây
        cmd = [sys.executable, "-c", "import time; time.sleep(3.0)"]
        result = self.runner.run(cmd, timeout_s=0.3)

        self.assertTrue(result.timed_out)
        self.assertEqual(result.exit_code, 124)
        self.assertIn("[SANDBOX TIMEOUT]", result.stderr)


class TestAuditLogger(unittest.TestCase):
    """Kiểm tra khả năng theo dõi kiểm toán và request_id traceability."""

    def setUp(self) -> None:
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_audit_"))
        self.log_file = self.test_dir / "audit.jsonl"
        self.logger = AuditLogger(log_file=self.log_file)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_request_id_lifecycle_and_logging(self) -> None:
        custom_req = "req-custom-session-12345"
        set_request_id(custom_req)
        self.assertEqual(get_request_id(), custom_req)

        event = self.logger.log(
            engine="docx",
            action="render_template",
            success=True,
            duration_ms=45.2,
            file_uri="resource://docx/files/out-1",
            details={"template_id": "tpl-invoice-v2"},
        )

        self.assertEqual(event.request_id, custom_req)
        self.assertEqual(event.engine, "docx")
        self.assertEqual(event.action, "render_template")
        self.assertTrue(event.success)

        # Kiểm tra file audit.jsonl đã được ghi
        self.assertTrue(self.log_file.is_file())
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["request_id"], custom_req)
        self.assertEqual(record["details"]["template_id"], "tpl-invoice-v2")


if __name__ == "__main__":
    unittest.main()
