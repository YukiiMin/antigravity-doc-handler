"""
Command Line Interface (CLI) for Universal Document Studio
Supports 6-way conversion between PDF, DOCX, and Markdown (.md).
"""

from __future__ import annotations
import argparse
import os
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .converter_engine import convert_universal, get_pdf_page_count


def run_cli() -> int:
    parser = argparse.ArgumentParser(
        description="Chuyển đổi đa chiều giữa PDF ↔ Word (DOCX) ↔ Markdown (.md) bảo toàn định dạng & style meta.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Chuyển đổi PDF sang Word (mặc định):
  python tool/pdf_to_docx_converter/main.py "document.pdf"

  # Chuyển đổi PDF sang Markdown (.md kèm style CSS/YAML):
  python tool/pdf_to_docx_converter/main.py "document.pdf" -t md

  # Chuyển đổi Word DOCX sang Markdown:
  python tool/pdf_to_docx_converter/main.py "document.docx" -t md

  # Chuyển đổi Markdown sang Word DOCX:
  python tool/pdf_to_docx_converter/main.py "document.md" -t docx

  # Chuyển đổi Word DOCX sang PDF:
  python tool/pdf_to_docx_converter/main.py "document.docx" -t pdf

  # Chuyển đổi Markdown sang PDF:
  python tool/pdf_to_docx_converter/main.py "document.md" -t pdf

  # Chuyển đổi khoảng trang PDF (trang 1-5 và trang 8):
  python tool/pdf_to_docx_converter/main.py "document.pdf" --pages "1-5, 8"

  # Chuyển đổi toàn bộ thư mục sang định dạng mong muốn (Batch mode):
  python tool/pdf_to_docx_converter/main.py "my_folder/" -t docx --batch
        """
    )

    parser.add_argument("path", nargs="?", help="Đường dẫn tệp nguồn (.pdf, .docx, .md) hoặc thư mục")
    parser.add_argument("-o", "--output", help="Đường dẫn tệp kết quả hoặc thư mục xuất")
    parser.add_argument("-t", "--target", choices=["docx", "md", "pdf"], default=None, help="Định dạng đích (docx, md, pdf)")
    parser.add_argument("-p", "--pages", default=None, help="Khoảng trang cần chuyển đổi nếu nguồn là PDF (ví dụ: '1-5', '1,3,7-10')")
    parser.add_argument("-e", "--engine", default="pdf2docx", help="Engine chuyển đổi PDF -> Word: pdf2docx + Smart Post-Processor v3 (chuẩn Flow Document)")
    parser.add_argument("-b", "--batch", action="store_true", help="Chế độ chuyển đổi hàng loạt cho thư mục")
    parser.add_argument("--style", default=None, help="Đường dẫn tệp Style YAML (.style.yaml) tùy chỉnh khi chuyển đổi từ Markdown")
    parser.add_argument("--open", action="store_true", help="Tự động mở file kết quả sau khi hoàn tất")
    parser.add_argument("--gui", action="store_true", help="Khởi chạy giao diện đồ họa Desktop GUI")

    args = parser.parse_args()

    if args.gui or not args.path:
        from .gui import launch_gui
        launch_gui(args.path)
        return 0

    target_path = os.path.abspath(args.path)

    if args.batch or os.path.isdir(target_path):
        return _handle_batch_cli(target_path, args.output, args.target or "docx", args.engine, args.open)
    else:
        return _handle_single_cli(target_path, args.output, args.target, args.pages, args.engine, args.style, args.open)


def _handle_single_cli(src_file: str, output_file: str | None, target_fmt: str | None, page_range: str | None, engine: str, style_path: str | None, auto_open: bool) -> int:
    if not os.path.isfile(src_file):
        print(f"[LỖI] Không tìm thấy tệp nguồn: {src_file}", file=sys.stderr)
        return 1

    src_ext = os.path.splitext(src_file)[1].lower()
    print(f"[*] Đọc tệp nguồn: {os.path.basename(src_file)} ({src_ext.upper()}) | Engine: {engine}")

    def progress(p: float, msg: str):
        print(f"  [{int(p):3d}%] {msg}")

    ok, result, elapsed = convert_universal(
        source_path=src_file,
        target_path=output_file,
        target_ext=f".{target_fmt}" if target_fmt else None,
        page_range=page_range,
        engine=engine,
        style_path=style_path,
        progress_callback=progress
    )

    if ok:
        print(f"[THÀNH CÔNG] File kết quả: {result}")
        print(f"[THỜI GIAN] Hoàn tất trong: {elapsed:.2f} giây")
        if auto_open:
            try:
                os.startfile(result)
            except Exception as err:
                print(f"[CẢNH BÁO] Không thể tự động mở file: {err}")
        return 0
    else:
        print(f"[THẤT BẠI] Lỗi: {result}", file=sys.stderr)
        return 2


def _handle_batch_cli(folder_path: str, output_dir: str | None, target_fmt: str, engine: str = "pdf2docx", auto_open: bool = False) -> int:
    if not os.path.isdir(folder_path):
        print(f"[LỖI] Thư mục không tồn tại: {folder_path}", file=sys.stderr)
        return 1

    valid_exts = (".pdf", ".docx", ".md")
    files: list[str] = []
    for root_dir, _, dir_files in os.walk(folder_path):
        for f in dir_files:
            if f.lower().endswith(valid_exts):
                files.append(os.path.join(root_dir, f))

    if not files:
        print(f"[THÔNG BÁO] Không tìm thấy file tài liệu nào trong: {folder_path}")
        return 0

    target_ext = f".{target_fmt.lower()}"
    print(f"[*] Tìm thấy {len(files)} file cần xử lý sang định dạng {target_ext.upper()} (Engine: {engine}).")
    success_count = 0

    for idx, src in enumerate(files, 1):
        src_name = os.path.basename(src)
        base_name = os.path.splitext(src_name)[0]
        if output_dir:
            out_file = os.path.join(output_dir, f"{base_name}{target_ext}")
        else:
            out_file = os.path.join(os.path.dirname(src), f"{base_name}{target_ext}")

        print(f"\n--- [{idx}/{len(files)}] {src_name} -> {target_ext.upper()} ---")
        ok, result, elapsed = convert_universal(
            source_path=src,
            target_path=out_file,
            target_ext=target_ext,
            engine=engine
        )
        if ok:
            success_count += 1
            print(f"  -> Xong trong {elapsed:.2f}s: {result}")
        else:
            print(f"  -> Lỗi: {result}", file=sys.stderr)

    print(f"\n==========================================")
    print(f"Tổng kết Batch: Hoàn thành {success_count}/{len(files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
