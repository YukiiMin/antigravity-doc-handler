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

__all__ = [
    # Convert pipeline
    "convert_file", "parse_page_range", "get_pdf_page_count",
    "launch_gui", "run_cli",
    # AI editing toolkit — DOCX
    "read_docx", "read_docx_to_json",
    "write_docx", "write_docx_from_json_file",
    # AI editing toolkit — XLSX
    "read_xlsx", "read_xlsx_to_json",
    "write_xlsx", "write_xlsx_from_json_file",
]
