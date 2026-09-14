"""
Unified Conversion Engine supporting 6-way conversions between PDF, DOCX, and Markdown (.md).
Includes Smart Post-Processing for layout fixes and styling metadata preservation.
"""

from __future__ import annotations
import os
import sys
import time
from typing import Callable, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .smart_post_processor import post_process_docx
from .markdown_converter import (
    pdf_to_markdown,
    docx_to_markdown,
    markdown_to_docx,
    docx_to_pdf,
    markdown_to_pdf
)


def parse_page_range(range_str: str, total_pages: int) -> Optional[List[int]]:
    """Parse 1-indexed page range string into 0-indexed list."""
    cleaned = range_str.strip().lower()
    if not cleaned or cleaned in ("all", "*", "tat ca", "tất cả"):
        return None

    selected_pages: set[int] = set()
    segments = [s.strip() for s in cleaned.split(",") if s.strip()]

    for seg in segments:
        if "-" in seg:
            parts = seg.split("-")
            if len(parts) != 2:
                continue
            start_str, end_str = parts[0].strip(), parts[1].strip()
            if not start_str.isdigit() or not end_str.isdigit():
                continue
            start = max(1, int(start_str))
            end = min(total_pages, int(end_str))
            if start <= end:
                selected_pages.update(range(start - 1, end))
        elif seg.isdigit():
            val = int(seg)
            if 1 <= val <= total_pages:
                selected_pages.add(val - 1)

    if not selected_pages:
        return None

    return sorted(list(selected_pages))


def get_pdf_page_count(pdf_path: str) -> int:
    """Return total page count of a PDF file using pymupdf."""
    if not os.path.isfile(pdf_path):
        return 0
    try:
        import pymupdf
        doc = pymupdf.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 0


def get_safe_target_path(target_path: str, max_retries: int = 3, retry_delay: float = 1.5) -> str:
    """
    Check if target_path is writable.
    Retries up to max_retries in case of temporary lock.
    If still locked by Microsoft Word, generates a versioned candidate ({stem}_v2.docx).
    """
    for attempt in range(max_retries):
        try:
            if os.path.exists(target_path):
                with open(target_path, "a+"):
                    pass
            return target_path
        except PermissionError:
            if attempt < max_retries - 1:
                print(f"[FileLock] '{os.path.basename(target_path)}' is locked by Word (attempt {attempt+1}/{max_retries}). Retrying in {retry_delay}s...")
                time.sleep(retry_delay)

    dir_name, base_name = os.path.split(target_path)
    stem, ext = os.path.splitext(base_name)
    v = 2
    while True:
        candidate = os.path.join(dir_name, f"{stem}_v{v}{ext}")
        try:
            if os.path.exists(candidate):
                with open(candidate, "a+"):
                    pass
            print(f"[FileLock] '{base_name}' is locked in Microsoft Word. Automatically saving to: '{os.path.basename(candidate)}'")
            return candidate
        except PermissionError:
            v += 1


def _convert_pdf_to_docx_core(
    pdf_path: str,
    docx_path: str,
    pages: Optional[List[int]] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> str:
    """
    Convert PDF to DOCX using pdf2docx with tuned parameters to prevent missing headings,
    followed by Smart Post-Processor to split TOC and bullet lines.
    """
    from pdf2docx import Converter

    docx_path = get_safe_target_path(docx_path)

    if progress_callback:
        progress_callback(10.0, "Khởi tạo Converter engine...")

    cv = Converter(pdf_path)

    try:
        if progress_callback:
            progress_callback(30.0, "Đang phân tích cấu trúc, bảng biểu và đồ họa...")

        # Tuned parameters: set page margin factor to 0.35 to preserve natural margin bounds
        kwargs = {
            "page_margin_factor_top": 0.35,
            "page_margin_factor_bottom": 0.35,
            "line_separate_threshold": 2.0,
            "new_paragraph_free_space_ratio": 0.1
        }

        if pages is not None and len(pages) > 0:
            cv.convert(docx_path, pages=pages, **kwargs)
        else:
            cv.convert(docx_path, **kwargs)

        if progress_callback:
            progress_callback(85.0, "Kích hoạt Smart Post-Processor v3 (Margins, Cover, TOC & Tables)...")

        # Apply smart post-processing with PDF reference for missing cell healing
        _, actual_docx_path = post_process_docx(docx_path, pdf_path=pdf_path)

        if progress_callback:
            progress_callback(95.0, "Hoàn tất tài liệu Word...")
        return actual_docx_path
    finally:
        cv.close()


def convert_file(
    pdf_path: str,
    docx_path: Optional[str] = None,
    page_range: Optional[str] = None,
    engine: str = "pdf2docx",
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str, float]:
    """PDF to DOCX conversion using high-fidelity pdf2docx with Smart Post-Processor."""
    start_time = time.time()
    if not os.path.isfile(pdf_path):
        return False, f"File không tồn tại: {pdf_path}", 0.0

    if not docx_path:
        base_name = os.path.splitext(pdf_path)[0]
        docx_path = f"{base_name}.docx"

    out_dir = os.path.dirname(os.path.abspath(docx_path))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    total_pages = get_pdf_page_count(pdf_path)
    pages_list = parse_page_range(page_range or "", total_pages) if page_range else None

    if progress_callback:
        progress_callback(5.0, f"Chuẩn bị chuyển đổi: {os.path.basename(pdf_path)} ({total_pages} trang)")

    try:
        actual_path = _convert_pdf_to_docx_core(pdf_path, docx_path, pages_list, progress_callback)
        elapsed = time.time() - start_time
        if progress_callback:
            progress_callback(100.0, f"Hoàn tất trong {elapsed:.2f}s!")
        return True, actual_path, elapsed
    except Exception as exc:
        elapsed = time.time() - start_time
        return False, str(exc), elapsed


def convert_universal(
    source_path: str,
    target_path: Optional[str] = None,
    target_ext: Optional[str] = None,
    page_range: Optional[str] = None,
    engine: str = "pdf2docx",
    style_path: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str, float]:
    """
    Universal 6-way conversion router between PDF, DOCX, and Markdown (.md).
    Auto-detects source and target types. Supports decoupled Style YAML.
    """
    start_time = time.time()
    if not os.path.isfile(source_path):
        return False, f"File nguồn không tồn tại: {source_path}", 0.0

    src_ext = os.path.splitext(source_path)[1].lower()

    if target_path:
        dest_ext = os.path.splitext(target_path)[1].lower()
    elif target_ext:
        dest_ext = target_ext.lower() if target_ext.startswith(".") else f".{target_ext.lower()}"
        target_path = os.path.splitext(source_path)[0] + dest_ext
    else:
        # Default fallback transitions
        default_next = {".pdf": ".docx", ".docx": ".md", ".md": ".docx"}
        dest_ext = default_next.get(src_ext, ".docx")
        target_path = os.path.splitext(source_path)[0] + dest_ext

    out_dir = os.path.dirname(os.path.abspath(target_path))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    if progress_callback:
        progress_callback(5.0, f"Bắt đầu chuyển đổi: {src_ext.upper()} -> {dest_ext.upper()}")

    try:
        # Route 1: PDF -> DOCX
        if src_ext == ".pdf" and dest_ext == ".docx":
            ok, actual_docx, elap = convert_file(
                source_path, target_path, page_range=page_range, engine=engine, progress_callback=progress_callback
            )
            return ok, actual_docx, elap

        # Route 2: PDF -> MD
        elif src_ext == ".pdf" and dest_ext == ".md":
            ok, res = pdf_to_markdown(source_path, target_path, progress_callback)
            return ok, res, time.time() - start_time

        # Route 3: DOCX -> MD
        elif src_ext == ".docx" and dest_ext == ".md":
            ok, res = docx_to_markdown(source_path, target_path, progress_callback)
            return ok, res, time.time() - start_time

        # Route 4: DOCX -> PDF
        elif src_ext == ".docx" and dest_ext == ".pdf":
            ok, res = docx_to_pdf(source_path, target_path, progress_callback)
            return ok, res, time.time() - start_time

        # Route 5: MD -> DOCX
        elif src_ext == ".md" and dest_ext == ".docx":
            ok, res = markdown_to_docx(source_path, target_path, style_yaml_path=style_path, progress_callback=progress_callback)
            return ok, res, time.time() - start_time

        # Route 6: MD -> PDF
        elif src_ext == ".md" and dest_ext == ".pdf":
            ok, res = markdown_to_pdf(source_path, target_path, style_yaml_path=style_path, progress_callback=progress_callback)
            return ok, res, time.time() - start_time

        # Same format or unsupported
        elif src_ext == dest_ext:
            return False, f"Định dạng nguồn và đích trùng nhau: {src_ext}", 0.0
        else:
            return False, f"Không hỗ trợ cặp chuyển đổi từ {src_ext} sang {dest_ext}", 0.0

    except Exception as exc:
        elapsed = time.time() - start_time
        return False, str(exc), elapsed
