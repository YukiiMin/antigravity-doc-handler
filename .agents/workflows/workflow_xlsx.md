# Workflow: Module XLSX (Spreadsheet Engine)

> **Mô-đun**: XLSX Engine (`xlsx.*`)  
> **Căn cứ**: Xlsx Foundation Plan v1.1, [rule_xlsx_engine_standards.md](../rules/rule_xlsx_engine_standards.md).  
> **Phạm vi**: 5 quy trình tác nghiệp chuẩn: Nhập kho template, đột biến in-place 9 bước, dựng XlsxSpec, kiểm định 13 UG Gates, và kiểm soát cache.

---

## 1. Danh Mục Workflows Cho Module XLSX

```
                                  [Tác Vụ XLSX]
                                        │
      ┌──────────────────┬──────────────┴──────────────┬──────────────────┐
      ▼                  ▼                             ▼                  ▼
[WF-XLSX-01: Nhập Mẫu] [WF-XLSX-02: Mutate Path]     [WF-XLSX-03: Spec] [WF-XLSX-04/05]
preflight & lint       9-step in-place mutation      XlsxSpec builder   diff & recalc
```

---

## 2. Chi Tiết Từng Quy Trình Tác Nghiệp

### WF-XLSX-01: Khảo Sát & Nhập Kho Template Excel (Preflight & Ingestion)
Quy trình thẩm định và nạp template bảng tính Excel vào hệ thống.

1. **Khảo sát Inventory**: Gọi `xlsx.preflight(file_ref)` quét hình ảnh, chart, pivot, CF, DV, bảng và xác định Fidelity Tier (T1/T2/T3).
2. **Kiểm tra Mẫu**: Gọi `xlsx.lint_template(template_ref)` quét anchors (`header`, `data_start`, `summary`), kiểm tra Prototype Row và vùng khóa `locked_zones`.
3. **Soạn thảo Manifest YAML**: Khai báo `reference_sheet`, `sibling_sheets`, `anchors`, `locked_zones`, `id_columns`, `calc_policy`.
4. **Đăng ký**: Gọi `xlsx.register_template(template_ref, manifest)` lưu phiên bản và hash sha256.

---

### WF-XLSX-02: Đột Biến Bảng Tính Theo Dữ Liệu (Path A: In-Place Mutation)
Quy trình chuẩn cho mọi tác vụ điền dữ liệu, mở rộng dòng/cột trên template có sẵn.

1. **Khảo sát cấu trúc**: Gọi `xlsx.inspect(template_ref)` lấy snapshot anchors và `values_status`.
2. **Lập MutationSpec JSON**: Khai báo `cell_updates`, `table_expansions` (anchor, prototype_row, rows[], id_columns format '@'), `calc_policy`, và `approved_deviations` (nếu có).
3. **Thực thi 9 Bước Nội Bộ Của Engine**:
   - *Bước 3.1*: Tạo bản sao làm việc, bảo toàn 100% hash file gốc.
   - *Bước 3.2*: Preflight bản sao, xác thực MutationSpec (chống chuỗi '=', NFC).
   - *Bước 3.3*: Phân giải Semantic Anchor (kind, scope, khớp cột theo header).
   - *Bước 3.4*: Shift Manager AST Tokenizer: Dịch toán hạng ô/dải trỏ vào sheet đích trên toàn workbook; bảo toàn tên hàm, chuỗi, tên định danh; dịch đồng thời merge, CF, DV, AutoFilter, defined names, charts.
   - *Bước 3.5*: Style & Layout: Clone 100% Prototype Row, đồng bộ viền merged, freeze panes, tính row height động.
   - *Bước 3.6*: Lưu file giao tạm thời qua openpyxl.
   - *Bước 3.7*: Recalc Backend: Gửi bản sao sang LibreOffice headless / Excel COM tính lại công thức và quét lỗi.
   - *Bước 3.8*: Cache Writer (`lxml`): Mở `sheetN.xml`, tiêm thẻ `<v>` và thuộc tính `t` (`n`/`str`/`b`/`e`) cho các node `<c>` có `<f>`, bảo toàn 100% thẻ `<f>`. Tự kiểm tra bằng Gate UG-13.
   - *Bước 3.9*: Kiểm định 13 Universal Gates + Profile Gates + Structural Diff.
4. **Bàn giao**: Nhận `file_ref` và báo cáo `diagnostics`.

---

### WF-XLSX-03: Tạo Workbook Mới Từ Đầu (Path B: XlsxSpec Builder)
Dành cho trường hợp tạo file Excel hoàn toàn mới khi không có template mẫu.

1. **Lập Đặc tả XlsxSpec JSON**: Soạn thảo sheets, bảng biểu, danh sách cột, dữ liệu.
2. **Khai báo Design Tokens**: Chọn theme và đường viền chuẩn (`theme: "corporate_blue"`, `border: "thin_grid"`). Cấm đưa mã màu hex tùy ý.
3. **Biên dịch**: Engine dựng workbook qua XlsxWriter, gán conditional formatting dạng công thức cho các hàng zebra.
4. **Tính toán & Tiêm Cache**: Chạy qua Recalc Backend và Cache Writer để mở ở đâu cũng có sẵn số liệu.
5. **Kiểm định**: Vượt qua bộ cổng `UG-01..13` và xuất `file_ref`.

---

### WF-XLSX-04: Kiểm Định & Đối Chiếu Cấu Trúc Độc Lập (Validation & QA)
Dành cho kiểm thử chất lượng, CI/CD runner và nghiệm thu kỹ thuật.

1. **Kiểm định Cổng**: Gọi `xlsx.validate(file_ref, profile="unit_test_matrix")` chạy 13 Universal Gates và Profile Gates.
2. **Structural Diff**: Gọi `xlsx.diff(file_ref_before, file_ref_after)` phân loại khác biệt `declared` và `undeclared`. Nếu có mất mát ngoài ý muốn $\rightarrow$ Gate UG-02 thất bại, dừng phát hành.

---

### WF-XLSX-05: Đọc Cấu Trúc & Kiểm Soát Trạng Thái Giá Trị
Dành cho AI khi cần khảo sát số liệu bảng tính trước khi ra quyết định.

1. Gọi `xlsx.inspect(file_ref)`.
2. Kiểm tra cờ `values_status`:
   - `cached`: Đã có cache số liệu sẵn, đọc an toàn.
   - `missing`: Chưa có cache $\rightarrow$ gọi `xlsx.recalc(file_ref)` để backend tính và bổ sung cache trước khi đọc.
   - `recalculated`: Giá trị vừa được tính lại tươi mới.
