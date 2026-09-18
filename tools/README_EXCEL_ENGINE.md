# Enterprise Excel Generation & Format Assurance Engine

Bộ công cụ sinh và kiểm định định dạng bảng tính mẫu đạt chuẩn 100% template fidelity tuân thủ các Invariants `E1`–`E14`.

---

## 1. Thành phần Cốt lõi (Core Components)

1. [`build_final_workbook.py`](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/tool/pdf_to_docx_converter/tools/build_final_workbook.py):
   - **Template-Driven Token Extractor**: Trích xuất 100% token kiểu dáng từ sheet chuẩn (`Example`).
   - **Data Ingestion Engine**: Trích xuất dữ liệu thô từ file input, giữ style isolation.
   - **Multi-Sheet Batch Builder**: Tạo toàn bộ các function test sheets, cập nhật metadata, công thức KPI hàng 7, và sheet tổng quan `Cover`, `Functions`, `Statistics`.
   - **Dynamic Chart Relinker**: Tự động viết lại formula chuỗi và dời tọa độ neo cho OpenPyXL Pie Charts khi bảng mở rộng dòng.
   - **UX Dynamic Auto-Scaler**: Tính toán chiều cao hàng tự động `max(min_h, lines * line_h)` và kích hoạt `wrap_text`.

2. [`format_diff_excel.py`](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/tool/pdf_to_docx_converter/tools/format_diff_excel.py):
   - **12 Quality Gates Diff Engine**: Đối chiếu từng cell (font, fill, border, align, number format, merge, DV, geometry) giữa sheet mục tiêu và sheet tham chiếu.

---

## 2. Cách chạy và Tái sử dụng (CLI Commands)

### A. Sinh Workbook Hoàn chỉnh
```bash
python tool/pdf_to_docx_converter/tools/build_final_workbook.py
```

### B. Kiểm định Quality Gates (Format Diff)
```bash
python tool/pdf_to_docx_converter/tools/format_diff_excel.py <path_to_final_xlsx> <target_sheet_name> <reference_sheet_name>
```

**Ví dụ:**
```bash
python tool/pdf_to_docx_converter/tools/format_diff_excel.py "tool/AI-Docx-Testing-Product/dataset1/output/Report5_Unit Test-Final.xlsx" "NAV-SVC" "Example"
```

---

## 3. Checklist Invariants Bắt buộc (E1–E14)
- **E1**: Trích xuất token từ Template (`Example`), không hardcode style.
- **E2**: Hỏi qua `/grill-me` trước khi thay đổi UX khác biệt template.
- **E3**: Toàn bộ chỉ số tổng quan là live dynamic formulas (`=COUNTIF`, `=SUM`).
- **E5**: Đồng bộ kích thước cột và cấu trúc giữa tất cả các function sheets.
- **E6**: Bắt buộc chạy 12-Gate Diff trước khi xuất xưởng (`exit code 0 = clean`).
- **E7**: Khối 3 cột thống nhất B-C-D (bật viền ngoài, ẩn viền dọc bên trong).
- **E8**: Tên nhóm chỉ xuất hiện ở Col B dòng đầu tiên, các dòng con Col B để trống.
- **E9**: Không dùng lẫn token giữa Header, Condition, Confirm và Result footer.
- **E10**: Giữ đúng 3 cấp phân cấp Precondition -> Parameters -> Values.
- **E11**: File input là UNTRUSTED về styling, chỉ lấy raw values.
- **E12**: Relink chart series formula (`$F$34:$H$34`) và anchor row khi mở rộng bảng.
- **E13**: Auto-scaling chiều cao hàng dựa trên độ dài chuỗi và dòng ngắt `\n`.
- **E14**: Hàng Subtotal nền trắng ở giữa, navy ở 2 đầu; đủ 5 dòng KPI tỷ lệ.
