# Rule: XLSX Engine & Spreadsheet Processing Standards

> **Scope**: Bắt buộc áp dụng cho mọi tác vụ đọc, sửa, tạo, kiểm tra, kiểm định và chuyển đổi bảng tính Excel (`.xlsx`, `.xls`) trong bộ công cụ AI-Native `doctools` / `pdf_to_docx_converter`.
> **Căn cứ kỹ thuật**: Xlsx Engine MCP — Kế hoạch Nền tảng (Foundation Plan v1.1), các thực nghiệm EV-01..EV-13, bộ quy tắc E1..E14 và mã lỗi chuẩn `ERR_XLSX_001..007`.

---

## 1. Triết Lý Thiết Kế Cốt Lõi (Core Philosophy)

1. **Engine tất định, AI quyết định**: Engine là MCP Server tất định, không chứa prompt nội suy, không tự ý tóm tắt dữ liệu, không phỏng đoán định dạng. AI (Client) chịu trách nhiệm cấu trúc nội dung, điều phối công cụ và xử lý cảnh báo.
2. **Template là chân lý, không phá hủy (Template is Ground Truth & Non-destructive)**:
   - Hình thức do template quyết định. Tuyệt đối không hardcode font, màu, border trong code nếu không có đối chiếu.
   - Thao tác ghi **luôn làm việc trên bản sao**, không bao giờ ghi đè file gốc (bảo toàn `sha256` file gốc, NFR-08).
3. **Một đường dịch chuyển duy nhất (Single Shift Manager Path)**:
   - Mọi thay đổi về dòng/cột đi qua **Shift Manager**. Nghiêm cấm dịch công thức bằng regex trên toàn chuỗi (D-03).
4. **Quét trước, chọn chiến lược theo rủi ro (Preflight & Fidelity Tiers)**:
   - Preflight Scanner lập Package Inventory (ảnh, chart, pivot, table, CF, DV, tên đã định nghĩa) trước khi ghi.
   - Phân cấp Tier: T1 (openpyxl), T2 (vá XML lxml), T3 (từ chối hoặc hỏi người dùng).
5. **Recalc Backend & Cache Writer (D-12, D-22, EV-13)**:
   - Tính lại công thức trên bản sao độc lập (LibreOffice headless sandbox / Excel COM).
   - **Ghi giá trị cache (`<v>`) và thuộc tính kiểu (`t`) đúng chuẩn (`n`/`str`/`b`/`e`) vào XML `sheetN.xml` của file giao bằng `lxml`**, bảo toàn 100% thẻ `<f>`. Đảm bảo các consumer không có engine tính toán (pandas, openpyxl `data_only=True`, Explorer Preview) thấy đủ số liệu mà công thức vẫn sống.
6. **Kiểm định hai tầng (Two-tier Verification, D-08)**:
   - Tầng UG: 12 Universal Gates đo được, áp dụng cho mọi template.
   - Tầng PG: Profile Gates cho từng loại template cụ thể (trong đó 12 Quality Gates cũ trở thành profile `unit_test_matrix`).
7. **Lệch khỏi template cần con người duyệt (Grill-Before-Deviate, D-18)**:
   - Mọi cải tiến UX lệch template phát cảnh báo `W-DEV-*` (`fixable_by=human`), chỉ áp dụng khi có `approved_deviations` trong spec.

---

## 2. Bảng Bất Biến Kỹ Thuật XLSX (XLSX Critical Invariants)

| # | Mã Bất Biến | Tên Quy Tắc | Hành Vi Vi Phạm (Bị Cấm) | Giải Pháp Cưỡng Chế Bắt Buộc |
|---|---|---|---|---|
| 1 | **E1** | **Template-Driven Format Extraction** | Hardcode `font='Tahoma'`, `fill='#000080'` trong mã sinh dữ liệu. | Trích xuất 100% format tokens từ reference sheet (`Example`/`Template`/`Pattern`). |
| 2 | **E2 / D-18** | **Grill-Before-Deviate** | Tự ý thêm freeze panes, badge màu, viền mới mà chưa xin phép. | Phát `W-DEV-*`, dừng lại, hỏi người dùng qua `/grill-me` trước khi áp dụng. |
| 3 | **E3** | **Live Dynamic Formulas** | Hardcode số tĩnh vào ô tổng hợp (`Passed: 10`). | Ô tổng hợp/KPI bắt buộc là công thức sống: `='Sheet'!Cell`, `=COUNTIF`, `=SUM`, `=IF`. |
| 4 | **E4** | **Chronological Era Data** | Để sót năm cũ `2000`, `2007`, `2009` từ template khung cũ. | Dữ liệu mock phải khớp niên đại hiện tại của hệ thống (2026+). |
| 5 | **E5 / UG-11**| **Sibling Symmetry** | Các sheet song song (`Function 1..N`) bị lệch độ rộng cột, chiều cao dòng, freeze panes. | Đồng bộ 100% hình học và styles giữa các sibling sheets theo sheet tham chiếu. |
| 6 | **E6** | **Automated Diff Before Delivery** | Báo "XONG" chỉ vì script chạy ra `exit code 0`. | Chạy Structural Diff và Gate Verification trước khi bàn giao. Luồng: `mutate → diff → gates → deliver`. |
| 7 | **E7** | **Unified Box Geometry (B-C-D)** | Chỉ set style cho ô có text, để hở viền dọc giữa B-C-D. | Khởi tạo khối 3 cột: B (`left=thin`), C (no vertical), D (`right=thin`), fill solid white. |
| 8 | **E8** | **Strict Group Hierarchy** | Lặp lại tên nhóm (e.g. `Precondition`) ở Col B trên nhiều dòng con. | Tên nhóm CHỈ nằm ở Col B dòng đầu tiên; các dòng con Col B để trống, text ở Col D. |
| 9 | **E9** | **Cross-Zone Token Isolation** | Tái sử dụng style ô điều kiện cho ô kết quả footer hoặc KPI summary. | Trích xuất style riêng biệt theo từng phân vùng (Header, Condition, Confirm, Result). |
| 10 | **E10** | **Multi-Tier Hierarchy** | Gom phẳng tham số vào Precondition, mất cấp Level 2. | Giữ đủ 3 cấp: Level 1 (Precondition B10), Level 2 (Param Name B), Level 3 (Value D). |
| 11 | **E11** | **Untrusted Input Isolation** | Copy font size/family từ file dữ liệu đầu vào (làm dính lỗi Arial 8.5pt). | Input chỉ lấy giá trị (`cell.value`). Kiểu dáng 100% lấy từ Template. |
| 12 | **E12 / FR-17**| **Dynamic Chart Re-Anchoring** | Nhân bản sheet có chart nhưng không relink chuỗi hoặc anchor đè bảng. | Script relink `chart.series[].val.numRef.f` vào dòng Subtotal mới và dời anchor xuống dưới. |
| 13 | **E13 / FR-18**| **UX Dynamic Auto-Scaling** | Dùng row height cố định khiến text dài bị cắt chữ, tràn lề. | Tính toán: `Row Height = max(min_h, total_lines * line_h)` kèm `wrap_text=True`. |
| 14 | **E14** | **Summary Regional Parity** | Tô màu accent kín dòng Subtotal hoặc mất 5 dòng KPI chuẩn. | Endpoint navy (Col A/B & Total), nền trắng giữa (C..H); giữ đủ 5 KPI metrics. |

---

## 3. Bảng Mã Lỗi Ngăn Ngừa Lỗi OOXML & Engine (`ERR_XLSX_001..007`)

| Mã Lỗi | Tên Lỗi | Mô Tả & Rủi Ro Kỹ Thuật | Biện Pháp Khắc Phục Bắt Buộc |
|---|---|---|---|
| `ERR_XLSX_001` | **Prototype Row Style Cloning** | Dòng chèn mới bị mất viền, font default Calibri 11pt. | Clone toàn bộ font, fill (rgb/theme/indexed), border, alignment, format `@`, protection từ dòng mẫu. |
| `ERR_XLSX_002` | **Formula Shifter via Tokenizer** | Dùng regex làm hỏng tên hàm `LOG10` $\rightarrow$ `LOG13`, chuỗi `"TC001"` $\rightarrow$ `"TC1"`, tên `FY2024` $\rightarrow$ `FY2027` (EV-01, EV-02). | Sử dụng `openpyxl.formula.Tokenizer`. Chỉ dịch toán hạng ô/dải trỏ vào sheet đích; quét toàn workbook; cấm regex toàn chuỗi (D-03). |
| `ERR_XLSX_003` | **Semantic Anchor Discovery** | Hardcode vị trí header dòng 9, data dòng 10, total dòng 34. | Quét tìm Anchor theo từ khóa/công thức (`kind`: header/table/keyword, `scope`: first_table). Báo `E-TPL-ANCHOR-*` nếu mơ hồ. |
| `ERR_XLSX_004` | **Safe Merged-Cell Handling** | Ghi vào ô thứ 2 của merged cell làm corrupt XML; viền ô gộp bị rách. | Chỉ ghi giá trị vào ô Top-Left; đồng bộ viền toàn bộ dải ô merged (`sync_merged_borders`). |
| `ERR_XLSX_005` | **Freeze Panes & Dynamic Height** | Freeze panes che mất header; text nhiều dòng bị cắt cụt. | Freeze Panes tại giao điểm Header+1; Chiều cao tính động bằng công thức số dòng $\times$ line height. |
| `ERR_XLSX_006` | **DrawingML Preservation** | Mở bằng `Workbook()` rỗng làm bay màu logo, shapes, header graphics. | Luôn load trực tiếp template gốc bằng `load_workbook(data_only=False)`; cấm fallback im lặng về `Workbook()` rỗng. |
| `ERR_XLSX_007` | **Identifier Number Format** | Mã định danh (`001`, `020`) bị Excel ép về số `1`, `20`. | Cột mã định danh bắt buộc set kiểu string và gán `number_format = '@'`. |

---

## 4. Shift Manager & Quy Tắc Dịch Chuyển (FR-07, D-03, D-04)

1. **Nguyên tắc phân tích Token**:
   - Sử dụng `openpyxl.formula.Tokenizer`.
   - Phân loại token: Toán hạng ô/dải, tên hàm, chuỗi, tên định danh, toán tử.
   - **Chỉ toán hạng ô/dải mới được dịch**. Tên hàm (`LOG10`, `ATAN2`, `BIN2DEC`, `DAYS360`), chuỗi ký tự (`"TC001"`), tên định danh (`FY2024`) TUYỆT ĐỐI KHÔNG BỊ ĐỤNG CHẠM.
2. **Sheet đích (Target-sheet Aware)**:
   - Công thức không có tiền tố sheet: Chỉ dịch khi công thức nằm trên chính sheet đang chèn dòng.
   - Công thức có tiền tố sheet (`'Data'!A1`): Chỉ dịch khi tiền tố sheet trùng khớp với sheet đang chèn dòng.
3. **Range Policy (D-04)**:
   - `table_aware` (Mặc định cho mở rộng bảng `table_expansions`): Khi chèn tại dòng đầu hoặc ngay dưới dòng cuối của dải dữ liệu, mở rộng dải công thức tổng hợp để bao bọc các dòng mới.
   - `excel_native` (Mặc định cho chèn dòng thô): Mô phỏng đúng Excel gốc (chèn ngay dưới dòng cuối thì không mở rộng dải).
4. **Đối tượng phụ thuộc phải dịch đồng thời**:
   - Công thức toàn workbook, Merged cells, `sqref` của Conditional Formatting, `sqref` của Data Validation, `ref` của bảng Excel (ListObject) và AutoFilter, Defined Names, Print Area, Print Titles, Chart series & anchor, Hyperlink, Cell comments, Chiều cao dòng.
   - Xóa dòng/cột: Nếu tạo ra tham chiếu mồ côi $\rightarrow$ Báo `E-SHIFT-ORPHAN` và dừng, TUYỆT ĐỐI không âm thầm sinh `#REF!`.

---

## 5. Recalc Backend & Cache Writer (FR-10, FR-28, D-12, D-22, EV-13)

1. **Vấn đề cốt lõi (P-05)**: `openpyxl` không tự tính công thức và lưu ra thẻ `<v>` rỗng. Các consumer không có engine tính toán (`pandas`, openpyxl `data_only=True`, Explorer Preview, mobile viewer) sẽ thấy ô trống/None.
2. **Quy trình xử lý**:
   - Bước 1: Lưu file tạm từ openpyxl.
   - Bước 2: Tạo bản sao gửi sang Recalc Backend (LibreOffice headless trong sandbox) để tính lại công thức, lấy giá trị và quét lỗi (`#REF!`, `#DIV/0!`, `#VALUE!`).
   - Bước 3: **Cache Writer (`lxml`)** mở part `xl/worksheets/sheetN.xml` của file giao, tìm node `<c>` có `<f>` và chèn thẻ `<v>` kèm thuộc tính `t`:
     - Số / Ngày tháng: `t="n"` (hoặc bỏ `t`), `<v>giá trị số</v>`.
     - Chuỗi: `t="str"`, `<v>chuỗi đã escape XML</v>`.
     - Boolean: `t="b"`, `<v>1</v>` hoặc `<v>0</v>`.
     - Lỗi: `t="e"`, `<v>#DIV/0!</v>`.
   - Bước 4: Giữ nguyên 100% thẻ `<f>`, thuộc tính `s` (styles), `ref`, `si`. Tự kiểm tra lại bằng UG-13 (đọc lại qua `data_only=True` phải khớp giá trị Recalc).
3. **Cờ `calc_on_open`**: Điều khiển `fullCalcOnLoad="1"` theo `calc_policy`:
   - Mặc định `auto`: Bật khi dùng LibreOffice; tắt khi dùng Excel COM.

---

## 6. Input Validation & Bảo Vệ An Ninh (FR-09, SEC-01..10)

1. **Chặn chèn công thức ngoài ý muốn (SEC-04, EV-12)**:
   - Dữ liệu do AI hoặc người dùng cung cấp bắt đầu bằng dấu `=` mặc định được coi là **văn bản thuần (text)**, trừ khi MutationSpec khai báo rõ ràng kiểu `formula`.
2. **Khóa vùng bảo vệ (Locked Zones, FR-09)**:
   - Mọi thao tác ghi vào ô/dải thuộc `locked_zones` trong manifest bị từ chối ngay lập tức với mã lỗi `E-LOCK-001`.
3. **Chuẩn hóa văn bản & Control Characters (FR-24, SEC-02)**:
   - Chuẩn hóa Unicode NFC cho toàn bộ chuỗi văn bản tiếng Việt.
   - Loại bỏ triệt để các ký tự điều khiển không hợp lệ trong XML 1.0 (`\x00..\x08`, `\x0B..\x0C`, `\x0E..\x1F`).
4. **Từ chối Macro & Liên kết ngoài (SEC-02, SEC-03)**:
   - Mặc định từ chối các file `.xlsm`, `vbaProject.bin`, OLE objects và liên kết ngoài (phát `E-SEC-MACRO`, `E-SEC-EXTLINK`).

---

## 7. Hệ Thống Cổng Kiểm Định 2 Tầng (UG & PG)

1. **Universal Gates (UG-01..13)** — Áp dụng cho mọi workbook:
   - `UG-01`: Package OOXML hợp lệ, mở được trên Excel/LibreOffice không báo lỗi Repair.
   - `UG-02`: Package Inventory Parity (không mất âm thầm ảnh, chart, CF, DV, bảng, pivot).
   - `UG-03`: Toàn vẹn công thức (không đổi token hàm/chuỗi; số tổng hợp phải là công thức sống).
   - `UG-04`: Không có lỗi tính lại (`#REF!`, `#NAME?`, `#DIV/0!`, `#VALUE!`) ngoài danh mục cho phép.
   - `UG-05`: Chữ ký kiểu dáng trùng 100% Prototype Row (font, fill, border, wrap_text, format).
   - `UG-06`: Ô gộp không chồng lấn, chỉ ghi Top-Left, viền đồng bộ.
   - `UG-07`: Đối tượng phụ thuộc vị trí nhất quán với dữ liệu sau dịch.
   - `UG-08`: Cảnh báo nguy cơ hiển thị `###` hoặc text dài bị cắt cụt (gắn nhãn `estimated`).
   - `UG-09`: Cột định danh có `number_format='@'` và giữ nguyên số 0 ở đầu.
   - `UG-10`: Zero placeholder thừa (`{{...}}`, `<...>`).
   - `UG-11`: Đối xứng cấu trúc và kiểu dáng giữa các Sibling Sheets.
   - `UG-12`: Tẩy rửa an ninh (không macro, không liên kết ngoài độc hại).
   - `UG-13`: Cache nhất quán (data_only khớp values_summary, thẻ `<f>` nguyên vẹn).
2. **Profile Gates (PG)** — Cổng nghiệp vụ khai báo theo template:
   - Profile `unit_test_matrix`: Kế thừa toàn bộ 12 Quality Gates hiện tại (PG-UT-01..12: Header A2..T8, Row 7 KPI, Row 9 TC headers, Col A continuous navy, Col B-C-D unified box, Grid & O-marks, Result typography, Closing borders, Data validations).

---

## 8. Hướng Dẫn Tác Nghiệp & Exit Codes

- **Mã thoát CLI/CI**:
  - `0`: Sạch sẽ 100% (Clean).
  - `1`: Có cảnh báo hình thức hoặc đề xuất lệch template (`W-LAYOUT-*`, `W-DEV-*`).
  - `2`: Lỗi nghiêm trọng (Hỏng OOXML, gãy công thức, mất thành phần, ghi vào vùng khóa: `E-*`).
- **Xử lý cảnh báo lệch template (`W-DEV-*`)**:
  - Khi AI phát hiện cơ hội tối ưu UX nhưng lệch template mẫu: Bắt buộc dừng lại, giữ nguyên template, lập danh sách trước/sau và hỏi người dùng qua `/grill-me`. Tuyệt đối không tự ý áp đặt.
