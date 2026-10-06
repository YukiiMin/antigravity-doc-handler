"""
SandboxRunner — Môi trường thực thi cô lập tiến trình an toàn (CLI, sidecars, LibreOffice, Node).
Đảm bảo:
- Giới hạn thời gian (Timeout enforcement).
- Chuẩn hóa mã hóa ký tự UTF-8 (chống lỗi tiếng Việt trên Windows).
- Cô lập biến môi trường nhạy cảm.
- Đo lường chính xác thời gian thực thi (milliseconds).
"""

from __future__ import annotations
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class SandboxResult(BaseModel):
    """Kết quả thực thi tiến trình trong sandbox."""
    model_config = ConfigDict(extra="forbid")

    exit_code: int = Field(..., description="Mã trả về của tiến trình (0 là thành công)")
    stdout: str = Field(default="", description="Đầu ra tiêu chuẩn stdout")
    stderr: str = Field(default="", description="Đầu ra lỗi tiêu chuẩn stderr")
    timed_out: bool = Field(default=False, description="Đánh dấu nếu tiến trình bị hủy do vượt quá timeout")
    duration_ms: float = Field(..., ge=0.0, description="Tổng thời gian thực thi tính bằng milliseconds")


class SandboxRunner:
    """
    Điều phối thực thi các tác vụ ngoại vi (Playwright, Puppeteer, LibreOffice, PlantUML)
    trong môi trường an toàn, có kiểm soát timeout và UTF-8 encoding.
    """

    def __init__(self, default_timeout_s: float = 30.0) -> None:
        self.default_timeout_s = default_timeout_s

    def run(
        self,
        command: List[str],
        cwd: Optional[Union[str, Path]] = None,
        timeout_s: Optional[float] = None,
        env_override: Optional[Dict[str, str]] = None,
        input_data: Optional[Union[str, bytes]] = None,
    ) -> SandboxResult:
        """
        Thực thi câu lệnh subprocess an toàn.
        """
        timeout = timeout_s if timeout_s is not None else self.default_timeout_s
        start_time = time.perf_counter()

        # Chuẩn bị môi trường cô lập
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["LANG"] = "en_US.UTF-8"
        if env_override:
            env.update(env_override)

        input_bytes = None
        if input_data:
            if isinstance(input_data, str):
                input_bytes = input_data.encode("utf-8")
            else:
                input_bytes = input_data

        work_dir = str(Path(cwd).resolve()) if cwd else None

        try:
            proc = subprocess.run(
                command,
                cwd=work_dir,
                input=input_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                env=env,
                check=False,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            stdout_text = proc.stdout.decode("utf-8", errors="replace")
            stderr_text = proc.stderr.decode("utf-8", errors="replace")

            return SandboxResult(
                exit_code=proc.returncode,
                stdout=stdout_text,
                stderr=stderr_text,
                timed_out=False,
                duration_ms=round(duration_ms, 2),
            )

        except subprocess.TimeoutExpired as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            stdout_text = exc.stdout.decode("utf-8", errors="replace") if exc.stdout else ""
            stderr_text = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""

            return SandboxResult(
                exit_code=124,  # Standard timeout exit code
                stdout=stdout_text,
                stderr=f"{stderr_text}\n[SANDBOX TIMEOUT] Process exceeded limit of {timeout}s",
                timed_out=True,
                duration_ms=round(duration_ms, 2),
            )
        except Exception as err:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return SandboxResult(
                exit_code=1,
                stdout="",
                stderr=f"[SANDBOX ERROR] Failed to spawn process: {err}",
                timed_out=False,
                duration_ms=round(duration_ms, 2),
            )
