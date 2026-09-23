"""
Universal Document Studio — PDF/DOCX/Markdown converter + AI editing toolkit.
"""
from .converter_engine import convert_file, parse_page_range, get_pdf_page_count
from .gui import launch_gui
from .cli import run_cli
from .docx_reader import read_docx, read_docx_to_json
from .docx_writer import write_docx, write_docx_from_json_file
from .xlsx_reader import read_xlsx, read_xlsx_to_json
from .xlsx_writer import write_xlsx, write_xlsx_from_json_file
from .docx_advanced_engine import (
    inject_dynamic_page_numbers,
    format_figure_captions,
    rebuild_table_of_contents,
    sanitize_emojis_and_symbols,
    translate_vn_to_en_protected,
    safe_save_docx,
)

__all__ = [
    # Convert pipeline
    "convert_file", "parse_page_range", "get_pdf_page_count",
    "launch_gui", "run_cli",
    # AI editing toolkit — DOCX
    "read_docx", "read_docx_to_json",
    "write_docx", "write_docx_from_json_file",
    # Advanced DOCX Engine
    "inject_dynamic_page_numbers",
    "format_figure_captions",
    "rebuild_table_of_contents",
    "sanitize_emojis_and_symbols",
    "translate_vn_to_en_protected",
    "safe_save_docx",
    # AI editing toolkit — XLSX
    "read_xlsx", "read_xlsx_to_json",
    "write_xlsx", "write_xlsx_from_json_file",
]
