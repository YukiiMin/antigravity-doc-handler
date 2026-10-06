# Rule: XLSX Engine & Spreadsheet Processing Standards

> **Scope**: Bắt buộc áp dụng cho mọi tác vụ đọc, sửa, tạo, kiểm định và chuyển đổi bảng tính Excel (`.xlsx`, `.xls`) trong `doctools` / `pdf_to_docx_converter`.  
> **Căn cứ**: Xlsx Foundation Plan v1.1, thực nghiệm EV-01..13, bộ quy tắc E1..E14 và mã lỗi `ERR_XLSX_001..007`.

---

## 1. Triết Lý Thiết Kế Cốt Lõi (Core Philosophy)

1. **Engine tất định, AI quyết định**: Engine là MCP Server tất định, không tự gọi AI, không tóm tắt dữ liệu. AI (Client) chịu trách nhiệm cấu trúc nội dung, điều phối công cụ và xử lý cảnh báo.
2. **Template là chân lý, không phá hủy (Non-destructive)**:
   - Mọi token kiểu dáng (font, fill, border, alignment) lấy từ template. Cấm hardcode trong mã sinh dữ liệu.
   - Thao tác ghi **luôn làm việc trên bản sao**, bảo toàn 100% hash `sha256` file gốc (NFR-08).
3. **Một đường dịch chuyển duy nhất (Single Shift Manager Path)**: Mọi thay đổi dòng/cột đi qua Shift Manager AST Tokenizer. Nghiêm cấm regex toàn chuỗi (D-03).
4. **Quét trước, chọn chiến lược theo rủi ro (Preflight & Fidelity Tiers)**: Phân cấp T1 (openpyxl), T2 (vá XML lxml), T3 (từ chối hoặc hỏi người dùng).
5. **Recalc Backend & Cache Writer (D-12, D-22, EV-13)**: Tính lại công thức qua LibreOffice headless sandbox/Excel COM. Ghi cache `<v>` và thuộc tính `t` (`n`/`str`/`b`/`e`) vào `sheetN.xml` bằng `lxml`, bảo toàn 100% thẻ `<f>`.
6. **Kiểm định hai tầng (D-08)**: 13 Universal Gates (UG) cho mọi template + Profile Gates (PG) theo từng nghiệp vụ.
7. **Lệch template cần duyệt (Grill-Before-Deviate, D-18)**: Phát cảnh báo `W-DEV-*`, chỉ áp dụng khi có `approved_deviations` trong spec.

---

## 2. Bảng 14 Bất Biến Kỹ Thuật XLSX (E1–E14)

| Mã | Tên Bất Biến | Hành Vi Bị Cấm | Giải Pháp Cưỡng Chế Bắt Buộc |
|---|---|---|---|
| **E1** | **Template-Driven Format** | Hardcode font, màu, border trong code. | Trích xuất 100% format tokens từ reference sheet (`Example`/`Template`). |
| **E2** | **Grill-Before-Deviate** | Tự ý thêm freeze panes, viền mới không xin phép. | Phát `W-DEV-*`, dừng lại, hỏi người dùng qua `/grill-me`. |
| **E3** | **Live Dynamic Formulas** | Hardcode số tĩnh vào ô tổng hợp. | Ô tổng hợp/KPI bắt buộc là công thức sống: `='Sheet'!Cell`, `=COUNTIF`, `=SUM`. |
| **E4** | **Chronological Era Data** | Để sót năm cũ 2000, 2007, 2009 từ mẫu cũ. | Dữ liệu mock phải khớp niên đại hiện tại của hệ thống (2026+). |
| **E5** | **Sibling Symmetry** | Các sheet song song bị lệch cột, dòng, freeze panes. | Đồng bộ 100% hình học và styles giữa các sibling sheets theo template mẫu. |
| **E6** | **Automated Diff QA** | Báo hoàn thành chỉ vì script ra exit code 0. | Chạy Structural Diff và Gate Verification: `mutate → diff → gates → deliver`. |
| **E7** | **Unified Box Geometry** | Chỉ set style ô có chữ, để hở viền dọc giữa B-C-D. | Khởi tạo khối 3 cột: B (`left=thin`), C (no vertical), D (`right=thin`), fill solid white. |
| **E8** | **Strict Group Hierarchy** | Lặp lại tên nhóm (Precondition) ở Col B dòng con. | Tên nhóm CHỈ nằm ở Col B dòng đầu tiên; các dòng con Col B để trống, text ở Col D. |
| **E9** | **Cross-Zone Token Isolation** | Dùng chung style ô điều kiện cho ô kết quả footer. | Trích xuất style riêng biệt theo từng vùng (Header, Condition, Confirm, Result). |
| **E10** | **Multi-Tier Hierarchy** | Gom phẳng tham số vào Precondition, mất Level 2. | Giữ đủ 3 cấp: Level 1 (Precondition), Level 2 (Param Name), Level 3 (Value). |
| **E11** | **Untrusted Input Isolation** | Copy font size/family từ file input (lỗi Arial 8.5pt). | Input chỉ lấy giá trị thô (`cell.value`). Kiểu dáng 100% lấy từ Template. |
| **E12** | **Dynamic Chart Relink** | Nhân bản sheet có chart nhưng không relink chuỗi. | Relink `chart.series` vào dòng Subtotal mới và dời anchor xuống dưới. |
| **E13** | **UX Dynamic Scaling** | Dùng row height cố định làm text dài bị cắt cụt. | Tính toán: `Row Height = max(min_h, total_lines * line_h)` kèm `wrap_text=True`. |
| **E14** | **Summary Regional Parity** | Tô màu accent kín dòng Subtotal hoặc mất 5 dòng KPI. | Endpoint navy (Col A/B & Total), nền trắng giữa (C..H); giữ đủ 5 KPI metrics. |

---

## 3. Ngăn Ngừa Lỗi OOXML & Engine (`ERR_XLSX_001..007`)

- `ERR_XLSX_001` (**Prototype Row Cloning**): Clone toàn bộ font, fill, border, alignment, format `@`, protection từ dòng mẫu.
- `ERR_XLSX_002` (**Formula Shifter via Tokenizer**): Dùng `openpyxl.formula.Tokenizer`. Chỉ dịch toán hạng ô/dải trỏ vào sheet đích; quét toàn workbook; cấm regex toàn chuỗi (D-03).
- `ERR_XLSX_003` (**Semantic Anchor Discovery**): Quét tìm Anchor theo từ khóa/công thức (`kind`: header/table, `scope`: first_table). Báo `E-TPL-ANCHOR-*` nếu mơ hồ.
- `ERR_XLSX_004` (**Safe Merged-Cell Handling**): Chỉ ghi giá trị vào ô Top-Left; đồng bộ viền toàn bộ dải ô merged (`sync_merged_borders`).
- `ERR_XLSX_005` (**Freeze Panes & Dynamic Height**): Freeze Panes tại giao điểm Header+1; Chiều cao tính động bằng công thức số dòng $\times$ line height.
- `ERR_XLSX_006` (**DrawingML Preservation**): Luôn load template gốc bằng `load_workbook(data_only=False)`; cấm tạo `Workbook()` rỗng làm bay màu logo/shapes.
- `ERR_XLSX_007` (**Identifier Number Format**): Cột mã định danh bắt buộc set kiểu string và gán `number_format = '@'`.

---

## 4. Shift Manager & AST Tokenizer (FR-07, D-03, D-04)

1. **Phân rã Token**: Chỉ toán hạng ô/dải mới được dịch. Tên hàm (`LOG10`, `DAYS360`), chuỗi (`"TC001"`), tên định danh (`FY2024`) TUYỆT ĐỐI KHÔNG BỊ ĐỤNG CHẠM.
2. **Sheet đích**: Không có tiền tố sheet $\rightarrow$ chỉ dịch trên sheet hiện tại. Có tiền tố sheet $\rightarrow$ chỉ dịch khi khớp sheet đích.
3. **Range Policy (D-04)**: `table_aware` mở rộng dải tổng khi chèn ở biên; `excel_native` giữ nguyên dải khi chèn thô.
4. **Đối tượng phụ thuộc dịch đồng thời**: Công thức toàn workbook, Merged cells, CF, DV, bảng ListObject, AutoFilter, Defined Names, Print Area, Charts, Chiều cao dòng.
5. **Xóa dòng/cột**: Báo `E-SHIFT-ORPHAN` nếu sinh tham chiếu mồ côi, cấm âm thầm sinh `#REF!`.

---

## 5. Recalc Backend & Cache Writer (D-12, D-22, EV-13)

1. Gửi bản sao sang Recalc Backend (LibreOffice headless / Excel COM) tính lại công thức và quét lỗi (`#REF!`, `#DIV/0!`).
2. **Cache Writer (`lxml`)** mở `xl/worksheets/sheetN.xml`, tìm node `<c>` có `<f>` và chèn thẻ `<v>` kèm thuộc tính `t`:
   - Số/Ngày: `t="n"` (hoặc bỏ `t`), `<v>giá trị số</v>`.
   - Chuỗi: `t="str"`, `<v>chuỗi escape</v>`.
   - Boolean: `t="b"`, `<v>1</v>`/`<v>0</v>`.
   - Lỗi: `t="e"`, `<v>#DIV/0!</v>`.
3. Bảo toàn 100% thẻ `<f>` (công thức còn sống khi mở bằng Excel thật). Tự kiểm tra bằng Gate UG-13.
4. Cờ `calc_on_open`: Chế độ `auto` (bật khi dùng LibreOffice; tắt khi dùng Excel COM).

---

## 6. Input Validation & Bảo Mật (SEC-01..10)

- **Chặn chèn công thức ngoài ý muốn (SEC-04)**: Dữ liệu bắt đầu bằng `=` mặc định coi là text thuần, trừ khi spec khai báo rõ `formula`.
- **Khóa vùng bảo vệ (Locked Zones, FR-09)**: Thao tác ghi vào vùng khóa bị từ chối ngay với `E-LOCK-001`.
- **Chuẩn hóa văn bản (SEC-02)**: Chuẩn hóa Unicode NFC; loại bỏ ký tự điều khiển không hợp lệ XML 1.0 (`\x00..\x08`, `\x0B..\x0C`, `\x0E..\x1F`).
- **Từ chối Macro & Liên kết ngoài (SEC-03)**: Từ chối file `.xlsm`, `vbaProject.bin`, OLE objects, external links (`E-SEC-MACRO`, `E-SEC-EXTLINK`).

---

## 7. Hệ Thống Cổng Kiểm Định 2 Tầng (UG & PG)

1. **13 Universal Gates (UG-01..13)** — Áp dụng cho mọi workbook:
   - `UG-01`: Package OOXML hợp lệ, mở được không lỗi Repair.
   - `UG-02`: Package Inventory Parity (không mất âm thầm ảnh, chart, CF, DV, bảng).
   - `UG-03`: Toàn vẹn công thức (không đổi token hàm/chuỗi; số tổng hợp là công thức sống).
   - `UG-04`: Không có lỗi tính lại (`#REF!`, `#NAME?`, `#DIV/0!`, `#VALUE!`).
   - `UG-05`: Chữ ký kiểu dáng trùng 100% Prototype Row (font, fill, border, format).
   - `UG-06`: Ô gộp không chồng lấn, chỉ ghi Top-Left, viền đồng bộ.
   - `UG-07`: Đối tượng phụ thuộc vị trí nhất quán với dữ liệu sau dịch.
   - `UG-08`: Cảnh báo nguy cơ hiển thị `###` hoặc text bị cắt cụt.
   - `UG-09`: Cột định danh có `number_format='@'` và giữ nguyên số 0 ở đầu.
   - `UG-10`: Zero placeholder thừa (`{{...}}`, `<...>`).
   - `UG-11`: Đối xứng cấu trúc và kiểu dáng giữa các Sibling Sheets.
   - `UG-12`: Tẩy rửa an ninh (không macro, không liên kết ngoài độc hại).
   - `UG-13`: Cache nhất quán (data_only khớp values_summary, thẻ `<f>` nguyên vẹn).
2. **Profile Gates (PG)**: Khai báo theo nghiệp vụ (ví dụ: profile `unit_test_matrix` với PG-UT-01..12).

---

## 8. Hướng Dẫn Tác Nghiệp & Exit Codes

- **Mã thoát CLI/CI**: `0` = Sạch 100%; `1` = Warning hình thức/đề xuất UX lệch mẫu (`W-DEV-*`); `2` = Lỗi nghiêm trọng (`E-*`).
- **Xử lý cảnh báo `W-DEV-*`**: Dừng lại, giữ nguyên template, hỏi người dùng qua `/grill-me`. Tuyệt đối không tự ý áp đặt.
