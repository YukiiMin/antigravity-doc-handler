"""
Modern Desktop GUI for Universal Document Studio (PDF <-> DOCX <-> Markdown)
Supports drag-and-drop, full 6-way matrix conversions, page range selection,
CSS/YAML style metadata, and live logs.
"""

from __future__ import annotations
import os
import sys
import threading
import time
from typing import List, Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

try:
    from .converter_engine import convert_universal, get_pdf_page_count
except (ImportError, ValueError):
    from converter_engine import convert_universal, get_pdf_page_count  # type: ignore


class UniversalDocStudioApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Universal Document Studio — PDF ↔ DOCX ↔ Markdown")
        self.root.geometry("860x720")
        self.root.minsize(800, 640)

        self.is_converting = False
        self.last_output_path = ""
        self.batch_files: List[str] = []

        self._setup_style()
        self._build_ui()
        self._setup_dnd()

    def _setup_style(self) -> None:
        style = ttk.Style(self.root)
        available_themes = style.theme_names()
        if "vista" in available_themes:
            style.theme_use("vista")
        elif "clam" in available_themes:
            style.theme_use("clam")

        self.root.configure(bg="#f8fafc")

    def _build_ui(self) -> None:
        # Header banner
        header_frame = tk.Frame(self.root, bg="#0f172a", height=78)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🔄 Universal Document Studio (PDF ↔ DOCX ↔ MD)",
            font=("Segoe UI", 15, "bold"),
            fg="#f8fafc",
            bg="#0f172a"
        )
        title_label.pack(anchor=tk.W, padx=20, pady=(8, 0))

        sub_label = tk.Label(
            header_frame,
            text="Bộ chuyển đổi 6 chiều giữ nguyên bố cục (Smart TOC, Bullets, Tables) & nhúng Style Meta (CSS/YAML) trong Markdown",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#0f172a"
        )
        sub_label.pack(anchor=tk.W, padx=22, pady=(2, 0))

        # Main Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(10, 4))

        self.tab_single = ttk.Frame(self.notebook, padding=12)
        self.tab_batch = ttk.Frame(self.notebook, padding=12)

        self.notebook.add(self.tab_single, text="  Chuyển đổi File đơn lẻ  ")
        self.notebook.add(self.tab_batch, text="  Chuyển đổi Hàng loạt (Batch)  ")

        self._build_single_tab()
        self._build_batch_tab()
        self._build_bottom_panel()

    def _build_single_tab(self) -> None:
        # Source File Section
        file_box = ttk.LabelFrame(self.tab_single, text=" Tệp Nguồn đầu vào (PDF / DOCX / MD) ", padding=10)
        file_box.pack(fill=tk.X, pady=(0, 10))

        f_row = ttk.Frame(file_box)
        f_row.pack(fill=tk.X)

        self.single_src_var = tk.StringVar()
        self.single_src_entry = ttk.Entry(f_row, textvariable=self.single_src_var, font=("Segoe UI", 9))
        self.single_src_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        btn_browse_src = ttk.Button(f_row, text="Chọn Tệp...", command=self._browse_single_src)
        btn_browse_src.pack(side=tk.RIGHT)

        dnd_text = "💡 Kéo & thả file (.pdf, .docx, .md) trực tiếp vào ô trên hoặc bấm 'Chọn Tệp...'" if HAS_DND else "💡 Bấm 'Chọn Tệp...' để duyệt tệp"
        lbl_hint = tk.Label(file_box, text=dnd_text, font=("Segoe UI", 8), fg="#64748b", bg=self.root["bg"])
        lbl_hint.pack(anchor=tk.W, pady=(4, 0))

        # Target Format & Output Path Section
        target_box = ttk.LabelFrame(self.tab_single, text=" Tùy chọn Định dạng & Tệp đầu ra ", padding=10)
        target_box.pack(fill=tk.X, pady=(0, 10))

        fmt_row = ttk.Frame(target_box)
        fmt_row.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(fmt_row, text="Định dạng đích cần chuyển sang:").pack(side=tk.LEFT, padx=(0, 10))
        self.target_fmt_var = tk.StringVar(value=".docx")
        self.combo_target_fmt = ttk.Combobox(
            fmt_row,
            textvariable=self.target_fmt_var,
            values=["Word Document (.docx)", "Markdown Document (.md - kèm CSS Meta)", "PDF Document (.pdf)"],
            state="readonly",
            width=36
        )
        self.combo_target_fmt.pack(side=tk.LEFT)
        self.combo_target_fmt.current(0)
        self.combo_target_fmt.bind("<<ComboboxSelected>>", self._on_target_fmt_changed)

        out_row = ttk.Frame(target_box)
        out_row.pack(fill=tk.X)

        self.single_out_var = tk.StringVar()
        self.single_out_entry = ttk.Entry(out_row, textvariable=self.single_out_var, font=("Segoe UI", 9))
        self.single_out_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        btn_browse_out = ttk.Button(out_row, text="Đổi nơi lưu...", command=self._browse_single_out)
        btn_browse_out.pack(side=tk.RIGHT)

        # Advanced Settings
        cfg_box = ttk.LabelFrame(self.tab_single, text=" Tùy chọn bổ trợ & Bố cục ", padding=10)
        cfg_box.pack(fill=tk.X, pady=(0, 10))

        e_row = ttk.Frame(cfg_box)
        e_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(e_row, text="Chế độ xử lý:").pack(side=tk.LEFT, padx=(0, 8))
        lbl_badge = tk.Label(
            e_row,
            text=" Flow Document Native + Smart Post-Processor v3 (Chuẩn ApowerPDF) ",
            bg="#ecfdf5",
            fg="#047857",
            font=("Segoe UI", 9, "bold"),
            relief="groove",
            bd=1,
            padx=6,
            pady=2
        )
        lbl_badge.pack(side=tk.LEFT)

        p_row = ttk.Frame(cfg_box)
        p_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(p_row, text="Khoảng trang (nếu tệp nguồn là PDF):").pack(side=tk.LEFT, padx=(0, 8))
        self.page_range_var = tk.StringVar(value="Tất cả")
        self.entry_pages = ttk.Entry(p_row, textvariable=self.page_range_var, width=18, font=("Segoe UI", 9))
        self.entry_pages.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(p_row, text="(VD: 'Tất cả' hoặc '1-5, 8, 11-15')", font=("Segoe UI", 8), foreground="#64748b").pack(side=tk.LEFT)

        chk_row = ttk.Frame(cfg_box)
        chk_row.pack(fill=tk.X, pady=(4, 0))

        self.auto_open_doc_var = tk.BooleanVar(value=True)
        chk_open_doc = ttk.Checkbutton(chk_row, text="Tự động mở file kết quả sau khi hoàn tất", variable=self.auto_open_doc_var)
        chk_open_doc.pack(side=tk.LEFT, padx=(0, 16))

        self.auto_open_folder_var = tk.BooleanVar(value=False)
        chk_open_folder = ttk.Checkbutton(chk_row, text="Mở thư mục chứa kết quả", variable=self.auto_open_folder_var)
        chk_open_folder.pack(side=tk.LEFT)

    def _build_batch_tab(self) -> None:
        batch_top = ttk.Frame(self.tab_batch)
        batch_top.pack(fill=tk.X, pady=(0, 8))

        btn_add_files = ttk.Button(batch_top, text="Thêm Tệp (.pdf / .docx / .md)...", command=self._batch_add_files)
        btn_add_files.pack(side=tk.LEFT, padx=(0, 8))

        btn_add_folder = ttk.Button(batch_top, text="Quét cả thư mục...", command=self._batch_add_folder)
        btn_add_folder.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(batch_top, text="Chuyển tất cả sang:").pack(side=tk.LEFT, padx=(16, 6))
        self.batch_target_fmt_var = tk.StringVar(value=".docx")
        combo_batch_fmt = ttk.Combobox(
            batch_top,
            textvariable=self.batch_target_fmt_var,
            values=[".docx", ".md", ".pdf"],
            state="readonly",
            width=8
        )
        combo_batch_fmt.pack(side=tk.LEFT)
        combo_batch_fmt.current(0)

        btn_clear = ttk.Button(batch_top, text="Xóa danh sách", command=self._batch_clear)
        btn_clear.pack(side=tk.RIGHT)

        # Listbox
        list_frame = ttk.Frame(self.tab_batch)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.batch_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            font=("Consolas", 9),
            bg="#ffffff",
            relief=tk.SOLID,
            borderwidth=1
        )
        sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.batch_listbox.yview)
        self.batch_listbox.configure(yscrollcommand=sb.set)

        self.batch_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.lbl_batch_count = ttk.Label(self.tab_batch, text="Tổng số file: 0")
        self.lbl_batch_count.pack(anchor=tk.W)

    def _build_bottom_panel(self) -> None:
        bottom_frame = ttk.Frame(self.root, padding=(16, 0, 16, 10))
        bottom_frame.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)

        btn_row = ttk.Frame(bottom_frame)
        btn_row.pack(fill=tk.X, pady=(0, 8))

        self.btn_convert = tk.Button(
            btn_row,
            text="🚀 BẮT ĐẦU CHUYỂN ĐỔI",
            command=self._start_conversion,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=16,
            pady=8,
            cursor="hand2"
        )
        self.btn_convert.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_open_file = ttk.Button(btn_row, text="Mở File Kết Quả", command=self._open_last_file, state=tk.DISABLED)
        self.btn_open_file.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_open_dir = ttk.Button(btn_row, text="Mở Thư Mục Chứa", command=self._open_last_dir, state=tk.DISABLED)
        self.btn_open_dir.pack(side=tk.LEFT)

        self.btn_diagram_editor = tk.Button(
            btn_row,
            text="📐 Canvas Diagram Editor",
            command=self._open_diagram_editor,
            bg="#0f172a",
            fg="#f8fafc",
            activebackground="#1e293b",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        self.btn_diagram_editor.pack(side=tk.RIGHT)

        prog_row = ttk.Frame(bottom_frame)
        prog_row.pack(fill=tk.X, pady=(0, 4))

        self.progress_bar = ttk.Progressbar(prog_row, orient=tk.HORIZONTAL, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.lbl_percent = ttk.Label(prog_row, text="0%", width=5, anchor=tk.E, font=("Segoe UI", 9, "bold"))
        self.lbl_percent.pack(side=tk.RIGHT)

        self.lbl_status = ttk.Label(bottom_frame, text="Sẵn sàng", font=("Segoe UI", 9), foreground="#475569")
        self.lbl_status.pack(anchor=tk.W, pady=(0, 6))

        # Log box
        log_box = ttk.LabelFrame(bottom_frame, text=" Nhật ký hoạt động ", padding=6)
        log_box.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_box,
            height=6,
            font=("Consolas", 8),
            bg="#0f172a",
            fg="#e2e8f0",
            relief=tk.FLAT,
            state=tk.NORMAL
        )
        log_sb = ttk.Scrollbar(log_box, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_sb.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.log("Khởi động Universal Document Studio thành công. Hỗ trợ đầy đủ PDF ↔ DOCX ↔ Markdown.")

    def _setup_dnd(self) -> None:
        if not HAS_DND:
            return
        try:
            register_fn = getattr(self.root, "drop_target_register", None)
            bind_fn = getattr(self.root, "dnd_bind", None)
            if callable(register_fn):
                register_fn(DND_FILES)
            if callable(bind_fn):
                bind_fn("<<Drop>>", self._handle_drop)
        except Exception as err:
            self.log(f"[WARN] DND Warning: {err}")

    def _handle_drop(self, event) -> None:
        data = event.data.strip()
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        valid_exts = (".pdf", ".docx", ".md")
        files = [f.strip() for f in data.split() if f.strip().lower().endswith(valid_exts)]
        if not files:
            return

        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            self.set_single_file(files[0])
        else:
            for f in files:
                if f not in self.batch_files and os.path.isfile(f):
                    self.batch_files.append(f)
                    self.batch_listbox.insert(tk.END, f)
            self.lbl_batch_count.config(text=f"Tổng số file: {len(self.batch_files)}")
            self.log(f"[INFO] Đã thêm {len(files)} file qua kéo thả.")

    def set_single_file(self, file_path: str) -> None:
        self.single_src_var.set(file_path)
        src_ext = os.path.splitext(file_path)[1].lower()

        # Suggest default target format based on input
        if src_ext == ".pdf":
            self.combo_target_fmt.current(0)  # Word (.docx)
            self.entry_pages.config(state=tk.NORMAL)
            p_count = get_pdf_page_count(file_path)
            self.log(f"[FILE] Đã chọn PDF: {os.path.basename(file_path)} ({p_count} trang)")
        elif src_ext == ".docx":
            self.combo_target_fmt.current(1)  # Markdown (.md)
            self.entry_pages.config(state=tk.DISABLED)
            self.log(f"[FILE] Đã chọn Word DOCX: {os.path.basename(file_path)}")
        elif src_ext == ".md":
            self.combo_target_fmt.current(0)  # Word (.docx)
            self.entry_pages.config(state=tk.DISABLED)
            self.log(f"[FILE] Đã chọn Markdown: {os.path.basename(file_path)}")

        self._update_output_path()

    def _get_selected_target_ext(self) -> str:
        val = self.combo_target_fmt.get().lower()
        if "word" in val or ".docx" in val:
            return ".docx"
        elif "markdown" in val or ".md" in val:
            return ".md"
        elif "pdf" in val or ".pdf" in val:
            return ".pdf"
        return ".docx"

    def _on_target_fmt_changed(self, event=None) -> None:
        self._update_output_path()

    def _update_output_path(self) -> None:
        src = self.single_src_var.get().strip()
        if not src:
            return
        base = os.path.splitext(src)[0]
        ext = self._get_selected_target_ext()
        self.single_out_var.set(f"{base}{ext}")

    def _browse_single_src(self) -> None:
        selected = filedialog.askopenfilename(
            title="Chọn tệp nguồn cần chuyển đổi",
            filetypes=[
                ("Supported Documents (*.pdf, *.docx, *.md)", "*.pdf;*.docx;*.md"),
                ("PDF Documents (*.pdf)", "*.pdf"),
                ("Word Documents (*.docx)", "*.docx"),
                ("Markdown Documents (*.md)", "*.md"),
                ("All Files (*.*)", "*.*")
            ]
        )
        if selected:
            self.set_single_file(os.path.normpath(selected))

    def _browse_single_out(self) -> None:
        ext = self._get_selected_target_ext()
        ext_label = ext.lstrip(".").upper()
        selected = filedialog.asksaveasfilename(
            title=f"Chọn nơi lưu file {ext_label}",
            defaultextension=ext,
            filetypes=[(f"{ext_label} Document", f"*{ext}")]
        )
        if selected:
            self.single_out_var.set(os.path.normpath(selected))

    def _batch_add_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title="Chọn một hoặc nhiều tệp",
            filetypes=[("Documents (*.pdf, *.docx, *.md)", "*.pdf;*.docx;*.md")]
        )
        for f in selected:
            norm = os.path.normpath(f)
            if norm not in self.batch_files:
                self.batch_files.append(norm)
                self.batch_listbox.insert(tk.END, norm)
        self.lbl_batch_count.config(text=f"Tổng số file: {len(self.batch_files)}")

    def _batch_add_folder(self) -> None:
        folder = filedialog.askdirectory(title="Chọn thư mục chứa tài liệu")
        if not folder:
            return
        count = 0
        valid_exts = (".pdf", ".docx", ".md")
        for root_dir, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(valid_exts):
                    full_path = os.path.normpath(os.path.join(root_dir, file))
                    if full_path not in self.batch_files:
                        self.batch_files.append(full_path)
                        self.batch_listbox.insert(tk.END, full_path)
                        count += 1
        self.lbl_batch_count.config(text=f"Tổng số file: {len(self.batch_files)}")
        self.log(f"[BATCH] Đã quét thư mục, thêm {count} file.")

    def _batch_clear(self) -> None:
        self.batch_files.clear()
        self.batch_listbox.delete(0, tk.END)
        self.lbl_batch_count.config(text="Tổng số file: 0")

    def log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def _start_conversion(self) -> None:
        if self.is_converting:
            return

        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            src_path = self.single_src_var.get().strip()
            if not src_path or not os.path.isfile(src_path):
                messagebox.showerror("Lỗi", "Vui lòng chọn một tệp nguồn hợp lệ trước khi chuyển đổi.")
                return

            out_path = self.single_out_var.get().strip()
            target_ext = self._get_selected_target_ext()
            page_range = self.page_range_var.get().strip()

            self._set_converting_state(True)
            threading.Thread(
                target=self._run_single_thread,
                args=(src_path, out_path, target_ext, page_range),
                daemon=True
            ).start()
        else:
            if not self.batch_files:
                messagebox.showerror("Lỗi", "Danh sách batch đang trống. Vui lòng thêm ít nhất một tệp.")
                return

            target_ext = self.batch_target_fmt_var.get().strip()
            self._set_converting_state(True)
            threading.Thread(
                target=self._run_batch_thread,
                args=(list(self.batch_files), target_ext),
                daemon=True
            ).start()

    def _set_converting_state(self, converting: bool) -> None:
        self.is_converting = converting
        if converting:
            self.btn_convert.config(text="⏳ ĐANG CHUYỂN ĐỔI...", state=tk.DISABLED, bg="#64748b")
            self.btn_open_file.config(state=tk.DISABLED)
            self.btn_open_dir.config(state=tk.DISABLED)
            self.progress_bar["value"] = 0
            self.lbl_percent.config(text="0%")
        else:
            self.btn_convert.config(text="🚀 BẮT ĐẦU CHUYỂN ĐỔI", state=tk.NORMAL, bg="#2563eb")
            if self.last_output_path and os.path.isfile(self.last_output_path):
                self.btn_open_file.config(state=tk.NORMAL)
                self.btn_open_dir.config(state=tk.NORMAL)

    def _update_progress(self, percent: float, status_msg: str) -> None:
        self.root.after(0, lambda: self._apply_progress(percent, status_msg))

    def _apply_progress(self, percent: float, status_msg: str) -> None:
        self.progress_bar["value"] = percent
        self.lbl_percent.config(text=f"{int(percent)}%")
        self.lbl_status.config(text=status_msg)
        self.log(status_msg)

    def _run_single_thread(self, src: str, out: str, target_ext: str, page_range: str) -> None:
        engine_code = "pdf2docx"

        success, result, elapsed = convert_universal(
            source_path=src,
            target_path=out,
            target_ext=target_ext,
            page_range=page_range,
            engine=engine_code,
            progress_callback=self._update_progress
        )

        def on_complete():
            self._set_converting_state(False)
            if success:
                self.last_output_path = result
                self.lbl_status.config(text=f"Hoàn thành ({elapsed:.2f}s): {os.path.basename(result)}")
                self.log(f"[THÀNH CÔNG] Đã tạo file: {result} ({elapsed:.2f}s)")
                if self.auto_open_doc_var.get():
                    self._open_last_file()
                if self.auto_open_folder_var.get():
                    self._open_last_dir()
            else:
                self.lbl_status.config(text="Chuyển đổi thất bại")
                self.log(f"[LỖI] {result}")
                messagebox.showerror("Thất bại", f"Lỗi trong quá trình chuyển đổi:\n\n{result}")

        self.root.after(0, on_complete)

    def _run_batch_thread(self, files: List[str], target_ext: str) -> None:
        total = len(files)
        success_count = 0
        self.log(f"[BATCH] Bắt đầu chuyển đổi hàng loạt {total} file sang {target_ext.upper()}...")

        for idx, src in enumerate(files, 1):
            base_percent = ((idx - 1) / total) * 100
            file_name = os.path.basename(src)
            self._update_progress(base_percent, f"Đang xử lý ({idx}/{total}): {file_name}")

            base_no_ext = os.path.splitext(src)[0]
            out_file = f"{base_no_ext}{target_ext}"

            ok, res, elapsed = convert_universal(
                source_path=src,
                target_path=out_file,
                target_ext=target_ext
            )
            if ok:
                success_count += 1
                self.last_output_path = res
                self.log(f"[BATCH {idx}/{total}] Xong {file_name} ({elapsed:.2f}s)")
            else:
                self.log(f"[BATCH {idx}/{total} LỖI] {file_name}: {res}")

        def on_batch_done():
            self._set_converting_state(False)
            self.progress_bar["value"] = 100
            self.lbl_percent.config(text="100%")
            msg = f"Hoàn tất chuyển đổi hàng loạt: {success_count}/{total} file thành công."
            self.lbl_status.config(text=msg)
            self.log(f"[BATCH HOÀN TẤT] {msg}")
            messagebox.showinfo("Hoàn tất Batch", msg)

        self.root.after(0, on_batch_done)

    def _open_last_file(self) -> None:
        if self.last_output_path and os.path.isfile(self.last_output_path):
            try:
                os.startfile(self.last_output_path)
            except Exception as err:
                self.log(f"[LỖI] Không thể mở file: {err}")

    def _open_last_dir(self) -> None:
        if self.last_output_path:
            folder = os.path.dirname(os.path.abspath(self.last_output_path))
            if os.path.isdir(folder):
                try:
                    os.startfile(folder)
                except Exception as err:
                    self.log(f"[LỖI] Không thể mở thư mục: {err}")

    def _open_diagram_editor(self) -> None:
        """Launch the Precision Diagram Canvas Editor in a child window."""
        try:
            try:
                from .diagram_editor import DiagramEditorApp
            except (ImportError, ValueError):
                from diagram_editor import DiagramEditorApp  # type: ignore

            spec_path = filedialog.askopenfilename(
                parent=self.root,
                title="Chọn tệp JSON Spec Diagram để chỉnh sửa (hoặc Huỷ để tạo sơ đồ trống)",
                filetypes=[("JSON Spec Diagram", "*.json"), ("All Files", "*.*")]
            )
            DiagramEditorApp(master=self.root, spec_path=spec_path or None)
        except Exception as err:
            messagebox.showerror("Lỗi khởi động Editor", f"Không thể mở Diagram Canvas Editor:\n{err}")


def launch_gui(initial_file: Optional[str] = None) -> None:
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = UniversalDocStudioApp(root)
    if initial_file and os.path.isfile(initial_file):
        app.set_single_file(os.path.abspath(initial_file))

    root.mainloop()
