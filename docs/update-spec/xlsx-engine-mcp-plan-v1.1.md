# Xlsx Engine MCP — Kế hoạch Nền tảng (Foundation Plan)

| Thuộc tính | Giá trị |
|---|---|
| Tài liệu | Foundation Plan — Core Engine cho bảng tính Excel (.xlsx) |
| Phiên bản | 1.1 (Baseline hợp nhất để đối chiếu và triển khai) |
| Ngày | 2026-10-06 |
| Chủ sở hữu | MinMin |
| Trạng thái | Draft chờ phê duyệt baseline |
| Phạm vi tài liệu | Core engine (MCP Server) cho `.xlsx`. Không bao gồm cách tích hợp vào Antigravity, không bao gồm module PDF/Render, không bao gồm Docx Engine |
| Tài liệu liên quan | Docx Engine MCP — Foundation Plan v1.1 (dùng chung hợp đồng `FileRef`, phong bì kết quả, họ mã lỗi, nguyên tắc tất định) |

## Lịch sử thay đổi

| Phiên bản | Nội dung |
|---|---|
| 1.0 | Bản baseline đầu tiên. Tổng hợp từ: (1) bản đồ công cụ của Gemini và báo cáo audit module Excel do Antigravity chuyển lại; (2) rà soát mã hiện trạng `xlsx_writer.py`, `xlsx_reader.py`, `xlsx_validator.py`, `test_excel_core.py` cùng bộ quy tắc `ERR_XLSX_001..007`, `E1..E14`; (3) thực nghiệm trực tiếp ngày 2026-10-05 trên `xlsx_writer.py` (Phụ lục E). Các nhận định không còn đúng sau thực nghiệm đã được đính chính (Phụ lục D, E) |
| 1.1 | Hợp nhất bản 1.0 với bản đối chiếu độc lập ngày 2026-10-06. (1) **Chốt D-12**: ghi giá trị cache vào file giao bằng `lxml` (`write_cached`), đã xác nhận bằng EV-13 trên Excel 16.0 COM và openpyxl `data_only`; viết lại 4.8; thêm D-21, D-22, UG-13, FR-28, NFR-11, SEC-10, `calc_policy`, `E-CACHE-*`, TC-38..TC-40, TC-44, R-15, R-16; chốt Q-02 (phần quyết định), ghi rõ phạm vi consumer chưa xác nhận. (2) **Bổ sung** thao tác xóa/gộp/DV/CF/tên (D-23, FR-29, TC-41, TC-42), anchor có `kind`/`scope` và cột theo tên header (D-24, TC-43), bảng dạng tham chiếu và quy tắc xóa (4.7). (3) **Khắc phục điểm yếu**: hướng dẫn cắt lát MVP (A.3), ma trận truy vết FR/NFR/SEC ↔ module ↔ TC (Phụ lục G), làm rõ "Oracle thắng" cho `range_policy` (4.7), thêm TC-45, TC-46 để lấp khoảng trống truy vết (FR-25, NFR-02, NFR-10), R-17 |

## Cách đọc tài liệu này (dành cho người và AI)

- Mỗi yêu cầu có **mã định danh** để đối chiếu: `P-xx` (vấn đề), `D-xx` (quyết định thiết kế), `FR-xx` (chức năng), `NFR-xx` (phi chức năng), `SEC-xx` (bảo mật), `UG-xx` (cổng kiểm định chung), `PG-xx` (cổng kiểm định theo profile), `TC-xx` (ca kiểm thử), `R-xx` (rủi ro), `Q-xx` (câu hỏi mở), `EV-xx` (bằng chứng thực nghiệm).
- Mức ưu tiên: **MVP** (bắt buộc cho bản đầu), **P1** (làm ngay sau MVP), **P2** (mở rộng).
- Nhãn `[ĐÃ KIỂM CHỨNG]`: nhận định đã được xác nhận bằng thực nghiệm ngày 2026-10-05 hoặc 2026-10-06 (xem Phụ lục E, mã `EV-xx`). Phạm vi xác nhận (môi trường, consumer) luôn được nêu kèm.
- Nhãn `[CẦN KIỂM CHỨNG]`: nhận định kỹ thuật chưa được xác nhận bằng thực nghiệm; phải chốt trong Phase 0 (xem Phụ lục A).
- Nhãn `[ĐỀ XUẤT]`: con số hoặc lựa chọn do tài liệu này đề xuất, chưa được chủ sở hữu phê duyệt.
- Khi mâu thuẫn, thứ tự ưu tiên: Mục 3 (Nguyên tắc và Quyết định) > Mục 4 (Kiến trúc) > các mục còn lại.

## Tóm tắt điều hành

Xlsx Engine là một **MCP Server tất định (deterministic)** chuyên sửa, tạo, kiểm tra và kiểm định bảng tính Excel `.xlsx`, với triết lý **Template là chân lý** và **không phá hủy**. AI (Antigravity) là **client**: quyết định nội dung, chọn thao tác và xử lý ngoại lệ. Engine **không tự gọi AI** và **không dựa vào AI để bảo đảm tính đúng đắn**. Engine:

1. **Quét trước (Preflight)** gói OOXML của file để biết file chứa gì (hình, chart, pivot, bảng, conditional formatting, data validation, tên đã định nghĩa, macro, liên kết ngoài...) và chọn chiến lược an toàn theo **Fidelity Tier** hoặc từ chối nếu rủi ro mất dữ liệu.
2. Nhận **MutationSpec JSON** có schema (không nhận mã hay XML do AI viết), sửa trên **bản sao** của template, mặc định không đụng bản gốc.
3. Dịch chuyển mọi thứ phụ thuộc vào vị trí dòng/cột qua **một Shift Manager duy nhất** (công thức, merge, conditional formatting, data validation, bảng, bộ lọc, vùng in, tên đã định nghĩa, chart, chiều cao dòng).
4. **Tính lại công thức trên bản sao** bằng Recalc Backend (LibreOffice headless; Excel COM tùy chọn), đọc giá trị và quét lỗi, rồi **ghi giá trị cache đúng kiểu (`n`/`str`/`b`/`e`) vào file giao bằng `lxml`** (`write_cached`, đã kiểm chứng ở EV-13) để các consumer không có engine tính toán (`pandas`, `openpyxl data_only`, trình xem trước, mobile viewer) vẫn thấy số liệu mà công thức vẫn sống. Backend chỉ cung cấp giá trị; engine, không phải backend, tạo file giao.
5. Kiểm định bằng **cổng chung (UG)**, **cổng theo profile (PG)** và **đối chiếu cấu trúc trước/sau**, rồi trả file kèm **báo cáo chẩn đoán có cấu trúc** để AI tự quyết định bước tiếp theo.
6. Cưỡng chế ở phía engine các bất biến: vùng khóa, không hardcode số liệu tổng hợp, không ghi đè bản gốc, không tin kiểu dáng từ dữ liệu đầu vào.

Engine cam kết **tính hợp lệ cấu trúc và không mất thành phần đã được hỗ trợ**, không cam kết hình thức pixel cuối cùng trong Excel và không cam kết tỷ lệ "1-shot" nào ngoài những gì đo được trên bộ corpus (xem 3.4).

---

## 1. Context

### 1.1. Bối cảnh

- Dự án Doc_Handler cung cấp cho AI Antigravity bộ công cụ làm việc với tài liệu văn phòng. Module DOCX đã được đánh giá "tạm ổn"; module Excel là hạng mục tiếp theo cần nâng cấp.
- Hiện trạng đã có lõi `UniversalExcelEngine` (trong `xlsx_writer.py`) cùng bộ quy tắc `ERR_XLSX_001..007`, `E1..E14`, bộ 12 Quality Gates (`xlsx_validator.py`) và kỹ năng `excel-automation`. Các tài sản này đúng hướng nhưng được thiết kế cho một loại template (ma trận kiểm thử) và chạy dưới dạng thư viện, chưa phải dịch vụ có hợp đồng công cụ, bảo mật và kiểm định tổng quát.
- Engine được đóng gói dưới dạng MCP, trong đó engine là server và AI là client, cùng mô hình với Docx Engine.
- Môi trường sử dụng chính là tiếng Việt; file được mở bằng Microsoft Excel (và các trình đọc khác ở mức hỗ trợ khác nhau, xem NFR-06).
- Định hướng triển khai: **chạy cục bộ trước, có khả năng thương mại hóa sau**, nên lựa chọn công nghệ ưu tiên giấy phép dễ phân phối và không phụ thuộc phần mềm Office cài sẵn trên server.

### 1.2. Phạm vi

| Trong phạm vi (In scope) | Ngoài phạm vi (Out of scope) |
|---|---|
| Sửa, tạo, kiểm tra, kiểm định, đối chiếu `.xlsx` | Cách cắm vào Antigravity (cấu hình, transport MCP) |
| Sửa template tại chỗ trên bản sao, giữ nguyên thành phần được hỗ trợ | Module PDF/Render (có core riêng, phát triển sau) |
| Mở rộng bảng theo dòng và cột, dịch chuyển mọi đối tượng phụ thuộc vị trí | Bảo đảm hình thức pixel, số trang in, kết quả hiển thị giống hệt giữa các trình đọc |
| Tính lại công thức trên bản sao để kiểm chứng giá trị; ghi giá trị cache vào file giao (`write_cached`) | Thực thi macro VBA, làm mới Pivot Table bằng Excel thật ở runtime server |
| Quét rủi ro gói OOXML, đối chiếu cấu trúc trước/sau, chẩn đoán có cấu trúc | Chức năng phân tích dữ liệu, BI, tạo dashboard tự do |
| Cưỡng chế vùng khóa, vệ sinh dữ liệu, audit | Vòng lặp tự sửa dựa trên thị giác (render ảnh, OCR, Docling) |
| Điểm mở rộng cho định dạng/adapter khác (FR-26) | Triển khai định dạng khác ngoài `.xlsx` trong bản đầu |

### 1.3. Mối quan hệ với Docx Engine và module Render

- **Docx Engine:** dùng chung ba hợp đồng: `FileRef` (URI mờ kèm `sha256`), phong bì kết quả (`success`, `file_ref`, `diagnostics`, `guarantees_applied`, `stats`) và họ mã lỗi (`E-*`, `W-*`, `I-*`). Khác nhau ở nội dung kiểm định và mã lỗi theo miền (`E-PKG-*`, `E-SHIFT-*`, `E-LOCK-*`, `W-CALC-*`...).
- **Module PDF/Render (tương lai):** chỉ là chức năng hỗ trợ, nhận `FileRef` của `.xlsx` và trả `FileRef` PDF kèm số liệu hiển thị (nếu có). Core không phụ thuộc thư viện render. Việc LibreOffice được dùng trong core chỉ nhằm **tính lại giá trị trên bản sao** và không phải để đo hình thức (NFR-05).

### 1.4. Thuật ngữ

| Thuật ngữ | Nghĩa |
|---|---|
| OOXML / SpreadsheetML | Định dạng XML của `.xlsx` (ECMA-376 / ISO/IEC 29500) |
| Package | Gói zip của `.xlsx`, gồm các part (sheet, drawing, chart, pivot, table, styles, relationships...) |
| Package Inventory | Bảng kê số lượng và loại thành phần trong package, dùng để đối chiếu trước/sau |
| Preflight | Bước quét chỉ đọc để lập Inventory, phát hiện tính năng rủi ro và chọn Fidelity Tier |
| Fidelity Tier | Mức xử lý theo rủi ro: T1 (openpyxl tại chỗ), T2 (openpyxl cộng vá XML bằng lxml), T3 (từ chối hoặc chuyển backend Excel) |
| Template | File `.xlsx` mẫu do con người thiết kế, là nguồn sự thật về hình thức |
| Manifest / Profile | Tệp YAML đi kèm template: sheet tham chiếu, anchor, dòng mẫu, vùng khóa, chính sách dịch, profile cổng kiểm định |
| MutationSpec | Mô tả thay đổi dạng JSON có schema, để AI yêu cầu sửa template |
| XlsxSpec | Mô tả workbook mới dạng JSON có schema, dùng cho đường tạo từ đầu |
| Prototype Row | Dòng dữ liệu đại diện trong template, nguồn để clone kiểu dáng sang dòng mới |
| Semantic Anchor | Mốc ngữ nghĩa (header, bắt đầu dữ liệu, dòng tổng) tìm bằng từ khóa hoặc công thức, không dựa số dòng cố định |
| Shift Manager | Thành phần duy nhất chịu trách nhiệm dịch chuyển mọi đối tượng phụ thuộc vị trí khi chèn/xóa dòng/cột |
| Range Policy | Chính sách xử lý dải ô khi chèn dòng tại biên (xem D-04) |
| Locked Zone | Vùng ô mà engine từ chối ghi (nhãn, công thức tổng hợp, tiêu đề do template khóa) |
| Recalc Backend | Thành phần tính lại công thức trên bản sao: LibreOffice headless hoặc Excel COM |
| Cached Value | Giá trị công thức lưu cùng file (thẻ `<v>`). File do openpyxl lưu ra không có; engine bổ sung bằng Cache Writer |
| Cache Writer | Thành phần ghi `<v>` và kiểu `t` đúng cho từng ô công thức trong part `sheetN.xml` của file giao bằng `lxml`, từ giá trị do Recalc Backend cung cấp (4.8) |
| Calc Policy | Bộ ba tham số `recalc`, `cache`, `calc_on_open` quyết định tính lại, ghi cache và cờ `fullCalcOnLoad` (D-21, 4.8) |
| Oracle | Phần mềm tham chiếu (Excel thật, LibreOffice) dùng để kiểm chứng; không dùng để lưu file giao |
| Gate | Một phép kiểm định có tiêu chí đo được: `UG` (chung mọi template), `PG` (theo profile) |
| FileRef | Đối tượng tham chiếu file `{uri, sha256, size, mime, expires_at}`, URI mờ, thay cho việc truyền byte |
| Diagnostics | Báo cáo lỗi/cảnh báo có cấu trúc do engine trả về |

### 1.5. Giả định và ràng buộc

- Stack lõi: Python với `openpyxl` (sửa template), `lxml` (vá XML, phân tích package và ghi giá trị cache), `Pydantic v2` (schema), `XlsxWriter` (tạo workbook mới). `LibreOffice` chạy như **tiến trình ngoài** (headless), không nhúng vào tiến trình Python.
- Giấy phép phụ thuộc phải được kiểm tra trước khi phân phối `[CẦN KIỂM CHỨNG]`. Ghi nhận hiện tại: `excel-parser` là MIT (đã xem trang repo, EV-11); `pycel`, `formulas` và `PyMuPDF` có giấy phép cần rà soát (copyleft hoặc AGPL), nên không dùng trong core (D-17).
- Người dùng doanh nghiệp tự thiết kế template trong Excel, không có kiến thức lập trình; template có thể chứa hình, chart, Pivot Table, conditional formatting, data validation, bảng, tên đã định nghĩa.
- Nội dung có thể gồm số liệu tài chính và báo cáo; công thức tổng hợp phải luôn là công thức sống (rule E3).
- Trên server Linux, font của template (Segoe UI, Tahoma, Calibri...) có thể bị thay thế khi LibreOffice tính lại/render, nên mọi đo đạc hình thức dựa trên LibreOffice chỉ mang tính ước lượng `[CẦN KIỂM CHỨNG]`.
- Thực nghiệm EV-01..EV-12 chạy trên sandbox Linux (`openpyxl 3.1.5`, LibreOffice headless). EV-13 (ghi cache) chạy trên Windows với `openpyxl 3.1.5`, `lxml 6.0.2` và Microsoft Excel 16.0 COM, do chủ sở hữu thực hiện và báo cáo lại. Hành vi trên Excel Mac/Web, Google Sheets, WPS, LibreOffice (đọc cache) và các trình xem trước chưa được xác nhận.

---

## 2. Problem

| ID | Vấn đề | Hệ quả nếu không giải quyết |
|---|---|---|
| P-01 | Bộ dịch công thức hiện tại dùng regex trên toàn chuỗi, không phân biệt tên hàm, chuỗi và tên định danh. Khi dịch: `LOG10(A5)` thành `LOG13(A8)`, `ATAN2` thành `ATAN5`, `BIN2DEC` thành `BIN5DEC`, `DAYS360` thành `DAYS363` `[ĐÃ KIỂM CHỨNG: EV-01]`; chuỗi `"TC001"` thành `"TC1"`, `"TC020"` thành `"TC23"`, tên `FY2024` thành `FY2027` `[ĐÃ KIỂM CHỨNG: EV-02]` | Công thức hỏng hoặc dữ liệu định danh bị đổi âm thầm, file vẫn mở được nên không ai phát hiện |
| P-02 | Dịch công thức không biết **sheet đích**: công thức ở sheet khác trỏ vào sheet được mở rộng **không** được dịch; công thức trong sheet được mở rộng nhưng trỏ sang sheet khác lại bị dịch **nhầm** `[ĐÃ KIỂM CHỨNG: EV-03, EV-04]` | Sheet thống kê (Statistics) trỏ sai ô sau khi mở rộng sheet chi tiết, sai số liệu tổng hợp |
| P-03 | `insert_rows` của openpyxl không dịch conditional formatting, data validation, AutoFilter, vùng in, tên đã định nghĩa và chiều cao dòng `[ĐÃ KIỂM CHỨNG: EV-05]`. Bảng (ListObject), hyperlink, comment, ảnh, pivot cần kiểm chứng thêm `[CẦN KIỂM CHỨNG]` | Màu điều kiện áp sai dòng, dropdown lệch, bộ lọc/vùng in/tên cũ trỏ sai vùng |
| P-04 | openpyxl là thư viện đọc-sửa-ghi **có mất mát**: các thành phần như shape/text box, slicer, sparkline, form control, phần mở rộng `x14` (conditional formatting, data validation), macro (nếu không giữ VBA) có nguy cơ bị bỏ khi mở và lưu lại `[CẦN KIỂM CHỨNG]` | Mất âm thầm các thành phần mà khách hàng coi là một phần của template |
| P-05 | File do openpyxl lưu ra **không có giá trị cache** (`<v>`) cho mọi công thức `[ĐÃ KIỂM CHỨNG: EV-08]`; Excel tự tính khi mở, nhưng `pandas.read_excel()`, openpyxl `data_only=True`, trình xem trước (Explorer, QuickLook), mobile viewer và AI nhìn thấy ô trống/`None`. Hướng giải quyết (ghi `<v>` bằng `lxml`) đã được kiểm chứng khả thi trên Excel 16.0 COM và openpyxl `[ĐÃ KIỂM CHỨNG: EV-13]` | AI đọc sai số liệu; file xem trên trình xem trước hiển thị trống/0 |
| P-06 | Bộ 12 Quality Gates hiện tại hardcode theo bố cục ma trận kiểm thử (header dòng 9, cột A..D, ô `O`, merge `B:D`); template khác (tài chính, nhân sự) sẽ fail toàn bộ vô nghĩa. Chữ ký ô `cell_sig` bỏ qua `wrap_text`, màu chữ và màu không dạng `rgb` (theme/indexed) nên có thể "bằng nhau" giả `[ĐÃ KIỂM CHỨNG: EV-10, đọc mã]` | Không dùng được cho template ngoài ma trận kiểm thử; lỗi hình thức bị lọt |
| P-07 | Hàm `write_xlsx` rơi âm thầm về `Workbook()` rỗng khi `template_path` thiếu hoặc sai đường dẫn; `read_xlsx(engine="auto")` thử `xlwings` (cần Excel cài sẵn) trước và nuốt mọi ngoại lệ `[ĐÃ KIỂM CHỨNG: EV-10, đọc mã]` | Mất logo/hình/định dạng mà không cảnh báo; hành vi khác nhau giữa máy dev và server |
| P-08 | Ngữ nghĩa chèn dòng không tường minh: dải ô được mở rộng khi chèn tại dòng đầu dải, nhưng **không** mở rộng khi chèn ngay dưới dòng cuối (`SUM(A5:A11)` chèn tại 12 giữ nguyên) `[ĐÃ KIỂM CHỨNG: EV-07]`; hành vi này khác Excel gốc | Hàng dữ liệu mới nằm ngoài vùng tổng hợp; kết quả phụ thuộc vị trí chèn |
| P-09 | Hình thức cuối cùng (độ rộng cột, chiều cao dòng tự co, font thay thế) do Excel quyết định; engine không thể tái tạo chính xác tuyệt đối | Mọi cam kết "đúng 100% hình thức" là sai |
| P-10 | Đầu ra LLM không tất định; dữ liệu AI truyền vào có thể bắt đầu bằng `=` (bị coi là công thức), chứa ký tự điều khiển hoặc yêu cầu sao chép kiểu dáng từ nguồn không tin cậy; openpyxl coi **mọi** chuỗi bắt đầu bằng `=` là công thức `[ĐÃ KIỂM CHỨNG: EV-12]` | Chèn công thức ngoài ý muốn, hỏng file, lệch hình thức |
| P-11 | File khách hàng là bề mặt tấn công: zip bomb, XXE, `.xlsm`/`vbaProject`, liên kết ngoài, nội dung ẩn (sheet ẩn, tên ẩn, dữ liệu cũ), metadata | Thực thi mã, lộ thông tin, hỏng file |
| P-12 | Không có phép đo chất lượng: tỷ lệ "1-shot" (65%, 60%, 55%...) trong các báo cáo là ước lượng, không đến từ bộ test. Bộ test hiện tại không chạm các ca ở P-01..P-03 và phụ thuộc thứ tự chạy (một test đọc file do test khác tạo) `[ĐÃ KIỂM CHỨNG: EV-09]` | Không biết chất lượng thật; "pass" không chứng minh được gì |
| P-13 | Giao tiếp AI-engine: truyền byte `.xlsx` làm phình context; AI không có cách trỏ lại đúng ô/vùng/đối tượng bị lỗi | Tốn token, vòng sửa không chính xác |
| P-14 | Tiếng Việt: chuẩn hóa Unicode (NFD/NFC), font thiếu glyph dấu khi tính lại/render trên server, định dạng số theo locale hiển thị `[CẦN KIỂM CHỨNG]` | Chữ lỗi, số hiển thị khác dự kiến |

---

## 3. Solution

### 3.1. Nguyên tắc thiết kế

1. **Engine tất định, AI quyết định.** Engine không chứa logic tự trị, không gọi ngược AI. "Tất định" được hiểu là tương đương về ngữ nghĩa (so sánh XML đã chuẩn hóa, bỏ timestamp, GUID, thuộc tính tự sinh), không phải trùng byte (NFR-01).
2. **Template là chân lý, không phá hủy.** Hình thức do template quyết định; không hardcode màu/font nếu không có đối chiếu; không bao giờ ghi đè file gốc (đầu ra luôn là bản mới).
3. **Một đường dịch chuyển duy nhất.** Mọi thay đổi vị trí dòng/cột đi qua Shift Manager; không dịch công thức bằng regex trên toàn chuỗi.
4. **Quét trước, chọn chiến lược theo rủi ro.** Preflight quyết định Fidelity Tier; thành phần nằm ngoài khả năng hỗ trợ bị báo hoặc từ chối, không bị mất âm thầm.
5. **Đo được thay cho đoán.** Mọi cam kết đều gắn với phép đo: Inventory trước/sau, cổng kiểm định, giá trị tính lại. Điều chỉ ước lượng được phải gắn nhãn `estimated`.
6. **Tính lại trên bản sao, không để Oracle lưu file giao.** Recalc Backend chỉ cung cấp giá trị và lỗi; file giao do engine tạo để bảo toàn kiểu dáng và cấu trúc, và **engine tự ghi giá trị cache** vào XML (Cache Writer) thay vì dùng file do backend lưu.
7. **Cam kết tường minh.** Tài liệu liệt kê rõ engine bảo đảm gì và không bảo đảm gì (3.4).
8. **Handle thay cho byte.** File đi qua `FileRef`; không truyền base64 nội tuyến.
9. **Bất biến do engine cưỡng chế.** Vùng khóa, tổng hợp sống, kiểu dáng từ template: engine từ chối vi phạm, không dựa vào lời nhắc trong prompt.
10. **Lệch khỏi template cần con người duyệt (Grill-Before-Deviate).** Engine không tự áp cải tiến UX; nó báo `W-DEV-*` kèm trước/sau và chỉ áp khi spec chứa phê duyệt tường minh.

### 3.2. Nhật ký quyết định

| ID | Quyết định | Lý do | Phương án đã loại |
|---|---|---|---|
| D-01 | Engine là MCP tool server tất định; AI là client | Server không gọi ngược client; loại phụ thuộc vòng tròn; nhất quán với Docx Engine | Engine gọi AI để tự sửa |
| D-02 | openpyxl là backend ghi mặc định cho đường template; XlsxWriter cho workbook mới; lxml cho vá XML và ghi giá trị cache | openpyxl sửa được file có sẵn; XlsxWriter mạnh định dạng/chart/CF khi tạo mới và có thể ghi kèm giá trị cache; lxml cho phần openpyxl không phủ, kể cả `<v>` | Một thư viện cho mọi việc; để LibreOffice lưu file giao |
| D-03 | Dịch công thức bằng bộ tách token (`openpyxl.formula.Tokenizer`), chỉ dịch toán hạng dạng ô/dải; có tham số **sheet đích**; quét **toàn workbook** | Loại P-01 và P-02: tên hàm, chuỗi, tên định danh nằm ngoài phạm vi dịch; công thức nào trỏ vào sheet đích mới được dịch | Regex trên toàn chuỗi (hiện trạng) |
| D-04 | `range_policy` tường minh: `excel_native` (hành vi Excel: chèn tại dòng đầu dải thì dịch cả dải, chèn ngay dưới dòng cuối thì không mở rộng) và `table_aware` (mở rộng dải bao phủ vùng dữ liệu khi chèn tại biên đầu hoặc ngay dưới dòng dữ liệu cuối); mặc định `table_aware` cho thao tác `table_expansions`, `excel_native` cho thao tác chèn thô `[ĐỀ XUẤT]` | Loại P-08; hiện trạng ngầm định một cách và sai ở biên dưới | Ngầm định theo vị trí chèn |
| D-05 | Recalc Backend là interface với hai cài đặt: **LibreOffice headless** (đa nền tảng, server) và **Excel COM** (Windows, tùy chọn, độ trung thực cao nhất); chạy trên bản sao | Giải quyết P-05 mà không phụ thuộc Office trên server; tách bạch việc tính và việc lưu | Chỉ xlwings; thư viện tính công thức thuần Python làm đường chính |
| D-06 | Preflight Scanner lập Package Inventory và chọn Fidelity Tier trước mọi thao tác ghi | Giải quyết P-04: biết trước thành phần nào có nguy cơ mất | Mở và sửa mù, kiểm tra sau |
| D-07 | Đối chiếu cấu trúc **trước/sau** (Package Inventory diff) là cổng chung bắt buộc | Phát hiện mất thành phần cho mọi template mà không cần hardcode | Chỉ so với sheet mẫu |
| D-08 | Validator hai tầng: **UG** (chung) và **PG** (profile khai báo). 12 gate hiện tại chuyển thành profile `unit_test_matrix` | Loại P-06: engine dùng được cho template bất kỳ, template đặc thù thêm profile riêng | 12 gate hardcode áp cho mọi file |
| D-09 | Template đi kèm Manifest/Profile (YAML); model Pydantic sinh từ manifest | Một nguồn sự thật cho anchor, dòng mẫu, vùng khóa, chính sách, profile | Hằng số trong mã (ví dụ dòng 9, cột `O`) |
| D-10 | Tách `lint/inspect/preflight` (chỉ đọc) khỏi `mutate/repair` (sinh bản mới); không ghi đè bản gốc; sao lưu `.bak` khi sửa tại chỗ theo yêu cầu | Công cụ kiểm tra không được âm thầm đổi file | Công cụ tự sửa tại chỗ |
| D-11 | Giao tiếp bằng **MutationSpec/XlsxSpec JSON có schema**; AI không viết mã hay XML | Loại P-10; kết quả tái lập được và kiểm tra được | AI sinh script openpyxl tự do |
| D-12 | **Ghi giá trị cache vào file giao bằng Cache Writer (`lxml`)** theo bản tính lại của Recalc Backend, kèm `fullCalcOnLoad` theo `calc_on_open` (4.8) `[ĐÃ KIỂM CHỨNG: EV-13 — Excel 16.0 COM và openpyxl data_only]`. Phạm vi consumer ngoài hai đối tượng đó còn `[CẦN KIỂM CHỨNG]` (TC-39) | Loại P-05: consumer không tính (`pandas`, `data_only`, trình xem trước, mobile) vẫn thấy số liệu; công thức vẫn sống, Excel tính lại được (EV-13) | Chỉ `fullCalcOnLoad` (cache rỗng); dùng file do LibreOffice lưu làm file giao (đổi kiểu dáng, chart) |
| D-13 | Không thực thi macro; `.xlsm`/`vbaProject` bị từ chối mặc định (giữ VBA là P2) | Loại rủi ro thực thi mã | Giữ VBA mặc định |
| D-14 | Kiểu dáng lấy từ template (clone Prototype Row, Named Style); đầu vào dữ liệu chỉ lấy **giá trị** (rule E11). Palette/typography cứng chỉ dùng cho đường tạo từ đầu (không có template), dưới dạng Design Tokens trong Pydantic và áp theo D-18 | Giữ thiết kế của con người; vẫn có chuẩn khi không có template | Hardcode màu/font trong script |
| D-15 | `FileRef` là đối tượng URI mờ kèm `sha256`; chiều vào qua `file://` trong roots do client khai báo | Dùng chung hợp đồng với Docx Engine; tránh phình context; không lộ tenant trong URI | Truyền byte nội tuyến |
| D-16 | Oracle trong CI: Excel (Windows + COM) và LibreOffice; kiểm thử **vi sai** bằng cách cho LibreOffice (UNO) chèn dòng trên cùng file rồi so công thức với Shift Manager `[ĐỀ XUẤT]` | LibreOffice là cài đặt tham chiếu độc lập cho ngữ nghĩa chèn dòng | Chỉ kiểm thủ công |
| D-17 | Core chỉ dùng phụ thuộc có giấy phép dễ phân phối; không đưa `pycel`, `formulas`, `PyMuPDF` vào core `[CẦN KIỂM CHỨNG giấy phép]`; `excel-parser` (MIT) chỉ là **Snapshot Adapter tùy chọn** sau interface, vì chỉ đọc, không tính lại và còn non trẻ (EV-11) | Phục vụ mục tiêu thương mại hóa; tránh khóa phụ thuộc | Đặt thư viện chỉ-đọc làm lõi |
| D-18 | Engine không tự áp thay đổi lệch template: phát `W-DEV-*` (có trước/sau, `fixable_by=human`); chỉ áp khi `approved_deviations[]` trong spec khớp mã | Hiện thực hóa Grill-Before-Deviate ở mức công cụ; AI hỏi người dùng, không tự quyết | Áp mặc định các cải tiến UX |
| D-19 | Không dùng `xlwings`/Excel trong đường mặc định của server; Excel COM chỉ khi cấu hình tường minh | Hành vi nhất quán giữa dev và server; không nuốt ngoại lệ | Chế độ `auto` thử Excel trước |
| D-20 | Đối tượng snapshot cho AI mang `values_status`: `cached` (kèm `origin`: `source_file` hoặc `engine_injected:<backend>`), `recalculated`, `missing` | AI biết số liệu nó đang thấy đến từ đâu (P-05) và do backend nào tính | Trả `None` không giải thích |
| D-21 | `calc_policy` tường minh gồm `recalc` (`none`/`oracle_verify`), `cache` (`none`/`write`), `calc_on_open` (`auto`/`on`/`off`); mặc định `oracle_verify` + `write` + `auto` `[ĐỀ XUẤT]`; `cache: write` mà `recalc: none` là `E-SPEC-CACHE-NEEDS-RECALC` | Mọi quyết định tính toán/cache hiển thị trong spec, stats và diagnostics; không đổi cờ toàn cục âm thầm | Cờ ngầm, bật tắt theo môi trường |
| D-22 | Cache Writer chỉ sửa node `<c>` đã có `<f>`; giữ nguyên `<f>`, `s`, `ref`, `si`; ghi `<v>` đúng kiểu; tự kiểm bằng đọc `data_only` sau khi ghi (UG-13) | Giới hạn bề mặt thay đổi; chứng minh được công thức không bị vô hiệu hóa (EV-13) | Ghi cache cho ô không công thức; sinh shared string |
| D-23 | MutationSpec bổ sung `delete_rows`, `delete_columns`, `merge`/`unmerge`, `set_validation`, `set_conditional_format`, `define_name` (P1), dùng chung Shift Manager; xóa làm tham chiếu mồ côi thì `E-SHIFT-ORPHAN`, không sinh `#REF!` im lặng | Sửa bảng tính hằng ngày cần xóa/gộp chứ không chỉ chèn | Chỉ hỗ trợ chèn |
| D-24 | Anchor có `kind` (`cell`, `range`, `table`, `header`, `keyword`) và `scope` (ví dụ `first_table`, `sheet`); cột định danh và cột dữ liệu khai báo **theo tên header**, chỉ số vẫn được chấp nhận | Giảm mơ hồ; bền khi template thêm/bớt cột | Chỉ số cứng (`id_columns: [0]`, `start_row: 10`) |

### 3.3. Tổng quan giải pháp

```
AI (client) --MCP--> [ Xlsx Engine: preflight -> validate input -> mutate (Shift Manager)
                                    -> style/layout -> recalc (bản sao) -> write_cached -> gates + diff ]
                                      |
                       FileRef + Diagnostics (có anchor, có "fixable_by", có evidence)
                                      |
AI quyết định: chấp nhận / sửa thông số / hỏi người dùng (đặc biệt W-DEV, W-PKG) / dừng
```

### 3.4. Ranh giới cam kết

| Engine bảo đảm | Engine KHÔNG bảo đảm |
|---|---|
| File hợp lệ OOXML, mở được không báo "Repair" (kiểm chứng bằng Oracle trong CI) | Hình thức pixel giống hệt giữa các trình đọc (Excel, LibreOffice, WPS, Google Sheets, Numbers) |
| Không mất thành phần mà Preflight xác định là được hỗ trợ (Inventory trước/sau khớp, trừ thay đổi khai báo) | Giữ nguyên thành phần ngoài danh sách hỗ trợ (shape/text box, slicer, sparkline, form control...): sẽ báo `W-PKG-UNSUPPORTED-*` hoặc từ chối, không đảm bảo giữ |
| Công thức được dịch đúng theo `range_policy` cho các dạng được hỗ trợ (4.7); tên hàm, chuỗi, tên định danh không bị đổi | Dịch đúng mọi dạng công thức hiếm (3D, mảng động, tham chiếu có cấu trúc) trước khi qua Phase 0 `[CẦN KIỂM CHỨNG]` |
| Mọi đối tượng phụ thuộc vị trí trong danh sách 4.7 được dịch cùng nhau và có kiểm tra nhất quán sau thao tác | Làm mới Pivot Table: chỉ đặt cờ làm mới khi mở file, không tính lại pivot trên server |
| Vùng khóa không bị ghi; dữ liệu định danh giữ nguyên chuỗi (`@`, số 0 đầu); chuỗi bắt đầu bằng `=` không bị coi là công thức ngoài ý muốn | Giá trị tính lại trùng 100% với Excel ở mọi hàm: LibreOffice có thể khác Excel ở hàm hiếm/hàm mới `[CẦN KIỂM CHỨNG]` |
| Bản sao tính lại không chứa `#REF!`, `#NAME?`, `#DIV/0!`, `#VALUE!` ngoài danh sách cho phép; mọi ô công thức mà backend tính được có `<v>` đúng kiểu trong file giao và công thức vẫn sống; ô không ghi được cache luôn được báo (`W-CALC-NO-CACHE`) | Giá trị cache trùng 100% giá trị Excel sẽ tính: cache là giá trị của backend được dùng (mặc định LibreOffice); Excel tính lại khi mở nếu `calc_on_open` bật. Ô dùng hàm biến động (`NOW`, `RAND`) chỉ có giá trị tại thời điểm build |
| Diagnostics chỉ dựa trên tiêu chí đo được; điều ước lượng mang nhãn `estimated` | Tỷ lệ thành công "1-shot" ngoài corpus đã đo; thẩm mỹ chủ quan |

---
## 4. Architecture

### 4.1. Sơ đồ logic

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ANTIGRAVITY AI (MCP Client)                       │
│ - Chọn thao tác, lập MutationSpec, phân loại nội dung                │
│ - Đọc Diagnostics, quyết định sửa / chấp nhận / hỏi người dùng       │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ MCP tool calls (FileRef, JSON)
┌───────────────────────────────▼──────────────────────────────────────┐
│                    XLSX ENGINE (MCP Server, tất định)                │
│                                                                      │
│ [A] API & Policy: xác thực tenant, giới hạn tài nguyên, audit        │
│ [B] Template Service: registry, manifest/profile, lint (chỉ đọc)     │
│ [C] Preflight Scanner: Package Inventory, Fidelity Tier, rủi ro      │
│ [D] Input Validation: Pydantic (MutationSpec/XlsxSpec), NFC, chống   │
│       công thức ngoài ý muốn, vùng khóa, ID định danh '@'            │
│ [E] Dual-Path Builder:                                               │
│       Path A: Mutate template (openpyxl tại chỗ [+ vá XML bằng lxml])│
│       Path B: Build mới từ XlsxSpec (XlsxWriter)                     │
│ [F] Shift Manager: công thức + merge + CF + DV + bảng + bộ lọc +     │
│       vùng in + tên + chart + ảnh + chiều cao dòng                   │
│ [G] Style & Layout: clone Prototype Row, merged-border sync,         │
│       freeze panes, auto-fit (ước lượng), Named Style                │
│ [H] Recalc & Cache Writer: bản sao -> giá trị + lỗi -> <v> (lxml)    │
│ [I] Validators: UG (chung) + PG (profile) + Structural Diff          │
│ [J] Diagnostics Builder: issues có anchor, severity, fixable_by      │
│                                                                      │
│ Cross-cutting: OOXML Package Helper (lxml), Sandbox process,         │
│                File Store (FileRef), Audit Log                       │
└───────┬─────────────────────────┬──────────────────────────┬─────────┘
        │ FileRef(.xlsx)          │ bản sao                  │ (tương lai)
        ▼                         ▼                          ▼
 [Người dùng mở trong      [Recalc Backend:           [Module PDF/Render
  Excel]                    LibreOffice | Excel COM]   (tách riêng)]
```

### 4.2. Thành phần và trách nhiệm

| Thành phần | Trách nhiệm | Công nghệ | Yêu cầu liên quan |
|---|---|---|---|
| API & Policy | Xác thực, giới hạn kích thước/thời gian, định tuyến công cụ, ghi audit | MCP SDK | NFR-02, SEC-05, FR-23 |
| Template Service | Lưu template theo phiên bản, manifest/profile, lint thuần đọc | `openpyxl`, `lxml`, `PyYAML` | FR-03, FR-04 |
| Preflight Scanner | Lập Package Inventory, phát hiện tính năng rủi ro, chọn Fidelity Tier | `zipfile`, `lxml` | FR-01, FR-02 |
| Input Validation | Sinh model từ manifest; NFC; loại ký tự điều khiển; chặn công thức ngoài ý muốn; kiểm vùng khóa | Pydantic v2 | FR-09, FR-24, SEC-04 |
| Dual-Path Builder | Mutate template (Path A) hoặc tạo mới (Path B) | `openpyxl`, `lxml`, `XlsxWriter` | FR-05, FR-19 |
| Shift Manager | Dịch mọi đối tượng phụ thuộc vị trí theo `range_policy` | `openpyxl.formula.Tokenizer`, `lxml` | FR-07 |
| Style & Layout | Clone dòng mẫu, đồng bộ viền merge, freeze panes, ước lượng chiều cao/độ rộng | `openpyxl` | FR-06, FR-18 |
| Recalc & Cache Writer | Tính lại trên bản sao, đọc giá trị, quét lỗi; ghi `<v>` và `t` vào file giao (4.8) | LibreOffice headless; Excel COM (tùy chọn); `lxml` | FR-10, FR-11, FR-28 |
| Validators | Chạy UG, PG và Structural Diff | `openpyxl`, `lxml` | FR-12, FR-13, FR-14 |
| Diagnostics Builder | Chuẩn hóa lỗi thành `issues` | Pydantic | FR-15 |
| OOXML Package Helper | Đọc/sửa part XML có kiểm soát (dùng cho Tier T2 và kiểm tra conformance) | `lxml` | D-06, FR-02 |
| Sandbox | Chạy LibreOffice/Excel trong tiến trình cách ly, có timeout, giới hạn CPU/RAM, không mạng | OS/container | SEC-08, NFR-03 |
| File Store | Cấp và giải `FileRef`, TTL, cách ly theo tenant | Cục bộ hoặc object store | FR-22, SEC-05 |
| Audit Log | Nhật ký thao tác có che dữ liệu nhạy cảm | JSONL/OpenTelemetry | FR-23, SEC-06 |

### 4.3. Hợp đồng công cụ MCP (v1)

| Công cụ | Mục đích | Đầu vào chính | Đầu ra chính | Ưu tiên |
|---|---|---|---|---|
| `preflight_xlsx` | Quét package, lập Inventory, đề xuất Fidelity Tier (chỉ đọc) | `file_ref` | `inventory`, `fidelity_tier`, `issues` | MVP |
| `inspect_xlsx` | Đọc cấu trúc và nội dung cho AI (snapshot có anchor, `values_status`) | `file_ref`, `sheet`, `range` | cây cấu trúc, ô, công thức, merge, bảng, `values_status` | MVP |
| `lint_template` | Kiểm tra template (chỉ đọc): placeholder, anchor mơ hồ, dòng mẫu, vùng khóa | `template_ref` | `valid`, `anchors`, `issues` | MVP |
| `register_template` / `list_templates` / `get_template_manifest` | Quản lý template và manifest/profile | `template_ref`, `manifest` | `template_id`, `version`, `manifest` | MVP |
| `mutate_xlsx` | Sửa template theo MutationSpec (Path A) | `template_id` hoặc `file_ref`, `mutation_spec` | `file_ref`, `diagnostics` | MVP |
| `recalc_xlsx` | Tính lại trên bản sao, trả giá trị và lỗi; tùy chọn ghi cache để sinh bản mới | `file_ref`, `backend`, `calc_policy` | `values_summary`, `errors`, `unsupported_functions`, `file_ref` (khi ghi cache) | MVP |
| `validate_xlsx` | Chạy UG và PG | `file_ref`, `profile`, `reference` | `issues`, `gates` | MVP |
| `diff_xlsx` | Đối chiếu cấu trúc (Inventory) và kiểu dáng giữa hai file hoặc hai sheet | `file_ref_a`, `file_ref_b` hoặc `sheet_a`, `sheet_b` | `diff` có anchor | MVP |
| `build_xlsx` | Tạo workbook mới từ XlsxSpec (Path B) | `xlsx_spec` | `file_ref`, `diagnostics` | P1 |
| `repair_xlsx` | Sửa tất định các lỗi `fixable_by=engine` và sinh `_repaired` | `file_ref`, `issues[]` | `file_ref`, `diagnostics` | P1 |
| `export_legacy_xls` | Chuyển `.xlsx` sang `.xls` qua LibreOffice | `file_ref` | `file_ref` | P2 |

Quy ước chung:

- Tất cả tệp vào/ra là `FileRef` (không truyền byte): `{uri, sha256, size, mime, expires_at}`.
- **Chiều ra (server sang client):** `uri` có dạng `resource://xlsx-engine/files/{opaque_id}`; id là mờ, không chứa tenant hay session; quyền truy cập kiểm tra ở phía server (SEC-05). `sha256` phục vụ toàn vẹn.
- **Chiều vào (client sang server):** tệp của người dùng truyền bằng `file://` nằm trong các **roots** do client khai báo (SEC-07), hoặc bằng `FileRef` do chính engine cấp.
- Việc client đọc được `resources/read` hoặc `resource_link` phụ thuộc host và phiên bản spec MCP `[CẦN KIỂM CHỨNG]`. Core chỉ định nghĩa hình dạng `FileRef`; cách vận chuyển cuối cùng chốt ở bước tích hợp (ngoài phạm vi).
- Mọi công cụ trả về cùng một phong bì kết quả. Công cụ ghi **không bao giờ ghi đè** bản gốc; luôn trả `file_ref` của bản mới.

**Phong bì kết quả**

```json
{
  "success": true,
  "file_ref": {
    "uri": "resource://xlsx-engine/files/3c9e...",
    "sha256": "...", "size": 91522,
    "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "expires_at": "2026-10-06T00:00:00Z"
  },
  "diagnostics": { "errors": [], "warnings": [], "info": [] },
  "guarantees_applied": ["ooxml_valid", "inventory_parity", "shift:formulas,merges,cf,dv,names", "cache:typed"],
  "fidelity_tier": "T1",
  "stats": {
    "sheets": 6, "rows_inserted": 3, "formulas_shifted": 41, "duration_ms": 1850,
    "recalc": { "backend": "libreoffice", "status": "ok", "errors_found": 0, "values_status": "recalculated" },
    "cache": { "written": 214, "skipped": 0, "types": { "n": 170, "str": 40, "b": 4, "e": 0 }, "calc_on_open": true }
  }
}
```

**Cấu trúc một issue**

```json
{
  "code": "E-SHIFT-002",
  "severity": "error",
  "location": { "sheet": "Statistics", "cell": "C12", "part": "xl/worksheets/sheet2.xml" },
  "message": "Công thức trỏ vào sheet 'Function 1' không được dịch sau khi mở rộng sheet này.",
  "evidence": { "formula_before": "='Function 1'!A7", "expected_after": "='Function 1'!A10", "formula_after": "='Function 1'!A7" },
  "fixable_by": "engine",
  "suggested_action": "rerun_shift_with_target_sheet"
}
```

Họ mã lỗi: `E-PKG-*` (package/OOXML hỏng hoặc thiếu part), `E-SHIFT-*` (dịch chuyển sai hoặc không nhất quán, gồm `E-SHIFT-ORPHAN`, `E-SHIFT-UNSUPPORTED-FORM`), `E-LOCK-*` (ghi vào vùng khóa), `E-SPEC-*` (MutationSpec/XlsxSpec sai schema, ví dụ `E-SPEC-CACHE-NEEDS-RECALC`), `E-TPL-*` (template/manifest/anchor), `E-CACHE-*` (cache sai kiểu hoặc giá trị không an toàn: `E-CACHE-TYPE-MISMATCH`, `E-CACHE-UNSAFE-VALUE`), `E-SEC-*` (an ninh), `W-PKG-UNSUPPORTED-*` (thành phần có nguy cơ mất), `W-CALC-*` (trạng thái tính lại/cache: `W-CALC-NO-CACHE`, `W-CALC-FUNC-UNSUPPORTED`, `W-CALC-VOLATILE`), `W-LAYOUT-*` (rủi ro hình thức đo hoặc ước lượng được), `W-STYLE-*` (lệch kiểu dáng so với dòng mẫu), `W-DEV-*` (lệch template cần con người duyệt), `I-*` (thông tin, ví dụ `I-CALC-CACHE-WRITTEN`).

Quy ước mức độ: một issue cần **người dùng làm thêm một hành động** để kết quả đúng (duyệt lệch template, chấp nhận thành phần có thể mất) là `warning` với `fixable_by=human`, không hạ xuống `info`. Exit code khi chạy CLI/CI: `0` sạch; `1` chỉ có cảnh báo; `2` có lỗi nghiêm trọng (gãy công thức, hỏng package, mất thành phần).

### 4.4. Hai đường dựng

**Path A — Mutate template (mặc định cho mọi yêu cầu có template)**

- Luồng: Preflight, nạp bản sao, áp MutationSpec, Shift Manager, Style & Layout, Recalc (bản sao), Validators, lưu `FileRef`.
- Các thao tác của MutationSpec. **MVP:** `cell_updates` (chỉ ghi ô Top-Left của merge, tôn trọng vùng khóa), `table_expansions` (theo anchor hoặc `start_row`, kèm `prototype_row`, `id_columns`), `column_expansions`, `freeze_panes`, `chart_relink`, `sheet_ops` (thêm/đổi tên sheet con theo sheet tham chiếu). **P1 (D-23):** `delete_rows`, `delete_columns`, `merge`/`unmerge`, `set_validation`, `set_conditional_format`, `define_name`; tất cả đi qua Shift Manager. `calc_policy` (D-21) là tham số cấp spec.
- Fidelity Tier quyết định cách ghi: T1 dùng openpyxl; T2 thêm vá XML bằng lxml cho phần openpyxl làm rơi; T3 từ chối và yêu cầu backend Excel hoặc quyết định của con người.

**Path B — XlsxSpec (workbook mới, không có template)**

- XlsxSpec là JSON có schema và phiên bản, gồm `sheets`, `tables`, `named_styles`, `charts`, `conditional_formats`, `data_validations`.
- Dùng XlsxWriter; kiểu dáng lấy từ **Design Tokens** (Pydantic) như `Theme.PRIMARY`, `Border.accounting_double`; AI chỉ chọn token theo tên, không sinh mã màu hay chuỗi định dạng tự do.
- Zebra và màu điều kiện dùng conditional formatting dạng công thức (ví dụ `=MOD(ROW(),2)=0`) để không vỡ khi chèn dòng về sau.
- Mọi lựa chọn UX nằm ngoài token tiêu chuẩn đi qua D-18.

Ví dụ MutationSpec:

```json
{
  "mutation_spec_version": "1.0",
  "template_id": "tpl_unit_test_matrix@2",
  "range_policy": "table_aware",
  "calc_policy": { "recalc": "oracle_verify", "cache": "write", "calc_on_open": "auto" },
  "approved_deviations": ["W-DEV-LAYOUT:freeze_panes"],
  "sheets": {
    "Function 1": {
      "cell_updates": { "A1": "PROJECT: ZSCORT Automated Test Matrix" },
      "table_expansions": [
        {
          "anchor": { "kind": "header", "text": "Test ID", "scope": "first_table" },
          "prototype_row": 10,
          "rows": [
            ["001", "Verify OAuth2 flow", "Success", 95],
            ["002", "Verify PDF conversion", "Success", 100]
          ],
          "id_columns": ["Test ID"],
          "auto_fit": true
        }
      ],
      "freeze_panes": "B10"
    }
  }
}
```

Ghi chú về spec: `anchor_keyword` và `id_columns: [0]` (dạng cũ) vẫn được chấp nhận làm bí danh, nhưng dạng khuyến nghị là anchor có `kind`/`scope` và cột theo **tên header** (D-24). Anchor khớp nhiều hơn một ô trong `scope` là `E-TPL-ANCHOR-AMBIGUOUS`; không khớp là `E-TPL-ANCHOR-MISSING`; không có `start_row` mặc định ngầm.

### 4.5. Manifest và Profile của template

```yaml
template_id: tpl_unit_test_matrix
version: 2
reference_sheet: Example            # nguồn chân lý về kiểu dáng
sibling_sheets: [Function 1, Function 2, Function 3]   # đối xứng cấu trúc (E5)
anchors:
  header: { kind: header, keyword: "Test ID", match: exact, scope: first_table, scan_rows: 150 }
  data_start: below_header
  summary: { keywords: ["Total", "Summary"], or_formula: "SUM" }
prototype_rows: { default: 10 }
locked_zones: ["Statistics!C12:I19", "*!A1:T8"]        # engine từ chối ghi
id_columns: ["Test ID"]            # theo tên header (chỉ số vẫn được chấp nhận); number_format '@'
calc_policy: { recalc: oracle_verify, cache: write, calc_on_open: auto }
range_policy: table_aware
gates_profile: unit_test_matrix     # PG-UT-*
required_package:                   # Inventory phải khớp sau khi sửa
  images: preserve
  charts: preserve_relink
  data_validations: preserve_shift
  conditional_formats: preserve_shift
  defined_names: preserve_shift
placeholders: { forbid_unreplaced: ['{{', '<...>'] }
```

Ghi chú: các khóa trên là `[ĐỀ XUẤT]`; manifest chỉ khai báo **chính sách**, còn "sự thật" về file (có chart, có pivot, có bảng) do Preflight **phát hiện** (nguyên tắc nhất quán với Docx Engine D-16).

### 4.6. Preflight và Fidelity Tier (FR-01, FR-02)

Preflight quét các part của package và đối chiếu bảng dưới đây để chọn Tier. Cột "Hành vi" là giả định đã biết hoặc cần xác nhận trong Phase 0.

| Thành phần phát hiện | Chiến lược | Mã cảnh báo | Trạng thái giả định |
|---|---|---|---|
| Ảnh/logo (`xl/media`, drawing ảnh) | T1: giữ; kiểm tra Inventory sau khi lưu | `W-PKG-IMAGE-LOST` nếu mất | Cần `Pillow` khi nạp ảnh `[CẦN KIỂM CHỨNG]` |
| Chart | T1: relink series và dời anchor (4.7); cảnh báo mất định dạng nâng cao | `W-PKG-CHART-FIDELITY` | openpyxl nạp lại chart có mất mát `[CẦN KIỂM CHỨNG]` |
| Shape, text box, WordArt | T3 hoặc T2 (vá XML); nếu không xử lý được: từ chối hoặc cần người duyệt | `W-PKG-UNSUPPORTED-SHAPE` | Thường bị bỏ khi openpyxl lưu `[CẦN KIỂM CHỨNG]` |
| Pivot Table | T1: giữ; đặt làm mới khi mở file; không tính lại trên server | `W-PKG-PIVOT-REFRESH` | openpyxl giữ pivot, không làm mới `[CẦN KIỂM CHỨNG]` |
| Slicer, Timeline, Sparkline, form control | T3: không hỗ trợ ghi; báo hoặc từ chối | `W-PKG-UNSUPPORTED-*` | Không được openpyxl phủ `[CẦN KIỂM CHỨNG]` |
| Conditional formatting (cơ bản) | T1: dịch bằng Shift Manager | — | `[ĐÃ KIỂM CHỨNG: EV-05]` openpyxl không tự dịch |
| Conditional formatting / data validation phần mở rộng `x14` (`extLst`) | T2: vá XML hoặc cảnh báo | `W-PKG-X14-EXT` | Có nguy cơ mất `[CẦN KIỂM CHỨNG]` |
| Data validation | T1: dịch bằng Shift Manager | — | `[ĐÃ KIỂM CHỨNG: EV-05]` |
| Bảng Excel (ListObject), AutoFilter | T1: cập nhật `ref` của bảng/bộ lọc | — | Cần xác nhận khi chèn dòng `[CẦN KIỂM CHỨNG]` |
| Tên đã định nghĩa, vùng in, tiêu đề in | T1: dịch bằng Shift Manager | — | `[ĐÃ KIỂM CHỨNG: EV-05]` không tự dịch |
| Hyperlink, comment/note, ảnh neo theo ô | T1: dịch cùng ô; kiểm tra Inventory | — | Cần xác nhận `[CẦN KIỂM CHỨNG]` |
| Rich text trong ô | T1 với chế độ nạp rich text | `W-PKG-RICHTEXT` | Cần chế độ nạp riêng `[CẦN KIỂM CHỨNG]` |
| Macro (`vbaProject`), `.xlsm` | Từ chối mặc định | `E-SEC-MACRO` | D-13 |
| Liên kết ngoài, OLE, DDE | Không theo liên kết; báo; từ chối theo policy | `E-SEC-EXTLINK` | SEC-04 |
| Sheet ẩn, tên ẩn, dữ liệu ẩn | Báo; scrub theo policy (FR-25) | `W-PKG-HIDDEN` | — |

Quy tắc chọn Tier: nếu tất cả thành phần phát hiện đều thuộc T1 thì dùng T1; nếu có thành phần cần vá thì T2; nếu có thành phần không thể bảo toàn thì T3 và engine **dừng**, trả `fixable_by=human` kèm danh sách thành phần có nguy cơ, để AI hỏi người dùng (chấp nhận mất, dùng backend Excel, hoặc đổi template).

### 4.7. Shift Manager (FR-07)

Mục tiêu: khi chèn/xóa dòng hoặc cột, **mọi** đối tượng phụ thuộc vị trí được dịch trong cùng một lần và một nơi, rồi kiểm tra nhất quán.

**Đối tượng phải dịch**

| Đối tượng | Quy tắc | Trạng thái hiện trạng |
|---|---|---|
| Công thức trong mọi sheet | Dịch toán hạng dạng ô/dải theo `range_policy`; chỉ dịch tham chiếu **trỏ vào sheet đích** (không prefix: chỉ khi công thức nằm trên sheet đích; có prefix: chỉ khi prefix là sheet đích) | Sai `[ĐÃ KIỂM CHỨNG: EV-01..EV-04]` |
| Merged cells | Dịch hoặc mở rộng theo vị trí chèn; sau đó đồng bộ viền | Có (cần test biên) |
| Conditional formatting | Dịch/mở rộng `sqref`; dịch tham chiếu tương đối trong công thức luật | Chưa có `[ĐÃ KIỂM CHỨNG: EV-05]` |
| Data validation | Dịch/mở rộng `sqref` và công thức danh sách | Chưa có `[ĐÃ KIỂM CHỨNG: EV-05]` |
| Bảng Excel, AutoFilter | Cập nhật `ref` (và vùng lọc) | Chưa có: AutoFilter không tự dịch `[ĐÃ KIỂM CHỨNG: EV-05]`; bảng Excel cần xác nhận `[CẦN KIỂM CHỨNG]` |
| Vùng in, tiêu đề in, tên đã định nghĩa | Dịch tham chiếu trong định nghĩa | Chưa có `[ĐÃ KIỂM CHỨNG: EV-05]` |
| Chart (series, anchor) | Relink `numRef/strRef.f`; dời anchor xuống dưới bảng tổng hợp | Có (kiểm thử đơn giản) |
| Ảnh neo, hyperlink, comment | Dịch cùng ô | Cần xác nhận `[CẦN KIỂM CHỨNG]` |
| Chiều cao dòng (`row_dimensions`) | Dịch theo dòng | Chưa có `[ĐÃ KIỂM CHỨNG: EV-05]` |
| Freeze panes, group/outline, ẩn dòng | Dịch hoặc xác nhận không đổi theo policy | Cần xác nhận |

**Quy tắc dịch công thức**

1. Dùng bộ tách token để phân loại: toán hạng ô/dải, tên hàm, chuỗi, tên định danh, toán tử. **Chỉ** toán hạng dạng ô/dải mới được dịch; tên hàm (`LOG10`, `ATAN2`, `BIN2DEC`, `DAYS360`), chuỗi (`"TC001"`), tên định danh (`FY2024`) không bao giờ bị sửa.
2. Ngữ nghĩa **chèn** khác ngữ nghĩa **sao chép**: với chèn dòng, tham chiếu tuyệt đối (`$F$10`) cũng phải dịch nếu nằm sau điểm chèn.
3. Phải hỗ trợ và có test: dải nhiều dòng/cột, ô đơn, tham chiếu có tiền tố sheet (có/không dấu nháy), dải cả cột/cả dòng (`A:A`, `5:5`), tên đã định nghĩa, công thức mảng, công thức chia sẻ; dạng chưa được xác nhận (tham chiếu 3D, tham chiếu có cấu trúc của bảng, mảng động) phải **báo `E-SHIFT-UNSUPPORTED-FORM`** thay vì dịch đoán `[CẦN KIỂM CHỨNG]`.
4. Sau thao tác: quét lại toàn workbook, bảo đảm không còn tham chiếu trỏ vào vùng đã bị xóa và không tham chiếu mồ côi (`E-SHIFT-ORPHAN`).

**Bảng dạng tham chiếu và hành vi dịch** (chèn N dòng tại dòng R; cột tương tự)

| Dạng | Quy tắc |
|---|---|
| Ô đơn có dòng ≥ R | Dịch xuống N |
| Dải có dòng đầu ≥ R | Dịch cả dải xuống N |
| Dải có dòng đầu < R ≤ dòng cuối | Mở rộng: dòng cuối + N |
| Dải có dòng cuối < R | Giữ nguyên (ngoại lệ `table_aware` ở biên, xem Range Policy) |
| Cả cột (`A:A`) khi chèn dòng | Không đổi |
| Cả dòng (`5:5`) | Dịch như ô |
| Tên đã định nghĩa (`FY2024`) trong công thức | Không sửa chuỗi tên; dịch **định nghĩa** của tên |
| Tham chiếu có cấu trúc (`Table1[Cột]`), 3D, mảng động | `E-SHIFT-UNSUPPORTED-FORM` cho tới khi qua Phase 0 |
| **Xóa** dòng/cột (D-23) | Tham chiếu vào vùng bị xóa: `E-SHIFT-ORPHAN` (không sinh `#REF!` im lặng); dải bị cắt thì co lại; mặc định `on_orphan: fail` dừng thao tác |

**Range Policy (D-04)**

| `range_policy` | Chèn tại dòng đầu dải | Chèn ngay dưới dòng cuối dải | Dùng khi |
|---|---|---|---|
| `excel_native` | Dịch cả dải xuống | Không mở rộng | Chèn thô, mô phỏng đúng Excel |
| `table_aware` | Mở rộng dải để bao các dòng mới | Mở rộng dải để bao các dòng mới | Mở rộng bảng dữ liệu có dòng tổng (mặc định cho `table_expansions`) |

Ghi chú: ngữ nghĩa của `excel_native` phải được xác nhận bằng Oracle trong Phase 0 (D-16). Khi dải bao phủ dòng mẫu (Prototype Row) còn lại trong template, engine báo `W-TPL-SAMPLE-ROW` (xem 4.14) để tránh dòng mẫu bị tính vào tổng hợp ngoài ý muốn.

Làm rõ để tránh mơ hồ khi triển khai: `table_aware` chỉ là mặc định cho `table_expansions`; mọi thao tác khác dùng `excel_native`. Khi kết quả của engine lệch Oracle ở biên (TC-04), **Oracle thắng**: kết quả được ghi vào Phase 0 trước khi khóa hành vi và trước khi viết golden test.

### 4.8. Recalc, Cache Writer và giá trị cache (FR-10, FR-11, FR-28)

**Bản chất vấn đề.** `openpyxl` chỉ ghi thẻ công thức `<f>`; thẻ giá trị `<v>` trống hoặc vắng. Excel tự tính khi mở, nhưng consumer không có engine tính toán (`pandas.read_excel()`, `openpyxl data_only=True`, Explorer Preview, QuickLook, mobile viewer) thấy ô trống/`None` (P-05).

**Luồng**

```
file giao (từ openpyxl, chưa có <v>)
   ├─> sao chép ─> Recalc Backend ─> giá trị + lỗi theo từng ô ─> values_summary, errors (UG-04)
   └─> Cache Writer (lxml) <───────── giá trị theo từng ô ────────┘
          └─> ghi <v> và t vào xl/worksheets/sheetN.xml của file giao
                └─> đọc lại bằng data_only để tự kiểm (UG-13) ─> đặt fullCalcOnLoad theo calc_on_open
```

**Bằng chứng khả thi (EV-13, ngày 2026-10-06, do chủ sở hữu thực hiện)** `[ĐÃ KIỂM CHỨNG]` trên Windows, `openpyxl 3.1.5`, `lxml 6.0.2`, Microsoft Excel 16.0 COM. File thử có 4 công thức; `lxml` can thiệp vào `xl/worksheets/sheet1.xml` để tiêm cache:

| Ô | Công thức | Cache được ghi | `openpyxl data_only=True` | Excel COM |
|---|---|---|---|---|
| `A3` | `=SUM(A1:A2)` | `<v>30</v>` (số) | `30` (`int`) | `30.0` |
| `B1` | `=IF(A1>5,"Pass","Fail")` | `t="str"`, `<v>Pass</v>` | `'Pass'` | `"Pass"` |
| `C1` | `=A1>5` | `t="b"`, `<v>1</v>` | `True` | `True` |
| `D1` | `=1/0` | `t="e"`, `<v>#DIV/0!</v>` | `'#DIV/0!'` | `#DIV/0!` |

Excel mở file không báo lỗi (không có thông báo "We found a problem with some content"). Công thức vẫn sống: đổi `A1` thành `100` rồi gọi `Calculate()` thì `A3` thành `120.0`.

**Phạm vi xác nhận (không suy rộng).** Đã xác nhận: bốn kiểu `n`, `str`, `b`, `e` trên file đơn giản; đọc bằng openpyxl `data_only` và Excel 16.0 COM; công thức không bị vô hiệu hóa. **Chưa xác nhận** `[CẦN KIỂM CHỨNG]` (TC-39, TC-44): Excel Mac/Web, Google Sheets, LibreOffice, WPS, Explorer Preview, QuickLook, mobile viewer, `pandas`; ngày/giờ; chuỗi rỗng; công thức chia sẻ (`t="shared"`) và công thức mảng; chuỗi rất dài; ký tự đặc biệt; file nhiều sheet, nhiều nghìn ô; hành vi cùng với `fullCalcOnLoad`.

**Quy tắc Cache Writer (D-22)**

1. Chỉ xét node `<c>` đã có `<f>` trong part `sheetN.xml`; không thêm `<v>` cho ô không công thức; không sinh shared string hoặc `<is>`.
2. Giữ nguyên `<f>` (kể cả thuộc tính `t="shared"`, `ref`, `si`, `t="array"`), thuộc tính `s` (kiểu dáng) và mọi node khác; đặt `<v>` ngay sau `<f>` (đúng thứ tự schema); xóa `<v/>` hoặc `<v></v>` rỗng do openpyxl để lại rồi ghi lại.
3. Giá trị lấy từ Recalc Backend theo từng ô; ô backend không tính được (hàm không hỗ trợ, mảng động, giá trị không biểu diễn được) thì **không ghi** và báo `W-CALC-NO-CACHE` kèm anchor.
4. Ánh xạ kiểu theo bảng dưới; kiểu lệch kết quả đọc lại là `E-CACHE-TYPE-MISMATCH` và **không phát hành file**.
5. Giá trị từ backend là dữ liệu không tin cậy (SEC-10): escape XML tại một điểm, loại ký tự điều khiển, giới hạn độ dài, chỉ chấp nhận mã lỗi trong danh sách cho phép; vi phạm là `E-CACHE-UNSAFE-VALUE`.
6. Ghi lại zip: các part khác giữ nguyên nội dung; chỉ các part sheet có công thức bị đổi; sau đó chạy Package Integrity (UG-01, UG-02) và UG-13.
7. Hàm biến động (`NOW`, `TODAY`, `RAND`, `RANDBETWEEN`, `OFFSET`, `INDIRECT`...): vẫn ghi cache (giá trị tại thời điểm build) và phát `W-CALC-VOLATILE`.

**Ánh xạ kiểu**

| Kết quả công thức | `t` | `<v>` |
|---|---|---|
| Số (kể cả ngày/giờ: số serial, hiển thị ngày do kiểu dáng của ô) | bỏ `t` hoặc `n` | số, biểu diễn khứ hồi (round-trip) |
| Chuỗi | `str` | văn bản đã escape; chuỗi rỗng là `<v></v>` |
| Boolean | `b` | `1` hoặc `0` |
| Lỗi | `e` | một trong `#DIV/0!`, `#N/A`, `#NAME?`, `#NULL!`, `#NUM!`, `#REF!`, `#VALUE!` |
| Mảng/động, rich value, không biểu diễn được | không ghi | `W-CALC-NO-CACHE` |

**Calc Policy (D-21)**

| Tham số | Giá trị | Hành vi |
|---|---|---|
| `recalc` | `none` | Không tính; nếu có công thức: `W-CALC-NO-CACHE` |
| | `oracle_verify` (mặc định) | Tính trên bản sao bằng Recalc Backend; quét lỗi (UG-04) |
| `cache` | `none` | Không ghi `<v>` |
| | `write` (mặc định) | Cache Writer ghi `<v>` từ kết quả `recalc`; yêu cầu `recalc` khác `none` (`E-SPEC-CACHE-NEEDS-RECALC` nếu trái) |
| `calc_on_open` | `on` | Ghi `fullCalcOnLoad="1"`: Excel tính lại khi mở, giá trị cache chỉ là bản chụp cho consumer khác |
| | `off` | Không ghi cờ: Excel hiển thị cache cho đến khi người dùng tính lại |
| | `auto` (mặc định) | `on` khi cache có nguồn không phải Excel (`libreoffice`); `off` khi cache do Excel COM tính `[ĐỀ XUẤT]`; luôn ghi vào `stats.cache.calc_on_open` |

Tác dụng phụ của `fullCalcOnLoad` (hộp thoại lưu thay đổi khi đóng, hành vi Protected View) `[CẦN KIỂM CHỨNG]` (TC-15).

**Chẩn đoán.** `I-CALC-CACHE-WRITTEN` (kèm `evidence`: số ô, theo kiểu, `origin`); `W-CALC-NO-CACHE` (ô không ghi được); `W-CALC-VOLATILE`; `W-CALC-FUNC-UNSUPPORTED`; `E-CACHE-*` (lỗi của engine, dừng).

**`values_status` cho AI (D-20).** `cached` kèm `origin` (`source_file` hoặc `engine_injected:<backend>`), `recalculated`, `missing`.

**Hạn chế phải báo thay vì giấu:** hàm không được backend hỗ trợ; giá trị khác Excel ở hàm hiếm/mới (R-03, R-15); font thay thế khi ước lượng hình thức (`estimated`).

### 4.9. Kiểm định: cổng chung (UG), cổng profile (PG) và Structural Diff (FR-12..14)

**Cổng chung (áp cho mọi template)**

| ID | Cổng | Tiêu chí đo được |
|---|---|---|
| UG-01 | Hợp lệ package | Zip nguyên vẹn; content types, relationships, part bắt buộc đầy đủ; XML đúng schema khi có XSD; mở được bằng Oracle không "Repair" |
| UG-02 | Inventory parity | Số lượng ảnh, chart, pivot, bảng, CF, DV, tên, merge, comment, hyperlink trước/sau khớp, trừ thay đổi khai báo trong spec |
| UG-03 | Toàn vẹn công thức | Số công thức bảo toàn trừ thay đổi khai báo; không token nào (hàm, chuỗi, tên) bị đổi; vùng tổng hợp khai báo là công thức sống, không phải số cứng (E3) |
| UG-04 | Không lỗi tính lại | Bản sao tính lại không có `#REF!`, `#NAME?`, `#DIV/0!`, `#VALUE!` ngoài danh sách cho phép trong manifest |
| UG-05 | Chữ ký kiểu dáng | Dòng/cột mới có chữ ký giống Prototype Row ở mọi cột: font (tên, cỡ, đậm, nghiêng, màu), fill, viền, canh lề **gồm `wrap_text`**, định dạng số, bảo vệ; màu theme/indexed được quy đổi về cùng dạng trước khi so |
| UG-06 | Merge | Không chồng lấn; chỉ ghi ô Top-Left; viền toàn dải đồng bộ |
| UG-07 | Nhất quán đối tượng phụ thuộc | `sqref` của CF/DV, `ref` của bảng/bộ lọc, vùng in, tên đã định nghĩa, chart series khớp với vị trí dữ liệu sau dịch |
| UG-08 | Hình thức ước lượng | Cột có nguy cơ `###` (độ rộng so với định dạng số và độ dài giá trị) và ô wrap text bị cắt; luôn gắn `estimated` |
| UG-09 | Định danh | Cột định danh có `number_format='@'`; giá trị giữ chuỗi và số 0 đầu |
| UG-10 | Placeholder | Không còn `{{...}}`, `<...>` chưa thay theo cấu hình |
| UG-11 | Đối xứng sheet anh em | Sheet khai báo `sibling_sheets` có hình học (độ rộng cột, chiều cao dòng, freeze panes) và kiểu dáng khớp tham chiếu (E5) |
| UG-12 | Vệ sinh bảo mật | Không liên kết ngoài, không macro; báo sheet/tên ẩn; metadata theo policy |
| UG-13 | Cache nhất quán | Mọi ô công thức mà backend tính được có `<v>` đúng kiểu (`n`/`str`/`b`/`e`); `<f>` không đổi so với trước khi ghi cache; đọc `data_only=True` khớp `values_summary`; ô không cache được có `W-CALC-NO-CACHE` |

**Cổng theo profile (PG)**: khai báo trong manifest; chỉ chạy khi `gates_profile` được chọn. Bộ 12 Quality Gates hiện tại trở thành profile `unit_test_matrix`:

| PG hiện tại (`xlsx_validator.py`) | Mã mới | Ghi chú chuyển đổi |
|---|---|---|
| Gate 1 Header block | PG-UT-01 | Tham số hóa vùng (không cố định dòng 2-8) |
| Gate 2 KPI formulas | PG-UT-02 | Cột KPI lấy từ manifest |
| Gate 3 Row 9 headers | PG-UT-03 | Dòng header theo anchor, không theo số dòng cứng |
| Gate 4 Col A navy continuous | PG-UT-04 | Màu lấy từ sheet tham chiếu, không cố định `FF000080` |
| Gate 5 Box B-C-D | PG-UT-05 | Khai báo trong profile |
| Gate 6 Duplicate header | PG-UT-06 | Có thể nâng thành UG nếu hữu ích |
| Gate 7 Matrix grid & O-marks | PG-UT-07 | Ký hiệu `O` khai báo trong profile |
| Gate 8 Result rows | PG-UT-08 | Khai báo trong profile |
| Gate 9 Merged cells (B:D) | PG-UT-09 | Khai báo trong profile |
| Gate 10 Section closing borders | PG-UT-10 | Khai báo trong profile |
| Gate 11 Data validations | PG-UT-11 | Thay bằng UG-02 và UG-07 cho phần chung |
| Gate 12 Geometry | PG-UT-12 | Phần chung chuyển về UG-08, UG-11 |

**Structural Diff (D-07)**: `diff_xlsx` so Inventory và (tùy chọn) kiểu dáng; đầu ra là danh sách khác biệt có `anchor`, phân loại `declared` (có trong spec) và `undeclared` (lỗi). `undeclared` làm UG-02 thất bại. Thay đổi `<v>` do Cache Writer là `declared` (loại `cache`), không tính là `undeclared`.

### 4.10. Xử lý đầu vào và bảo vệ dữ liệu (FR-09, FR-24)

- **Vùng khóa (Locked Zone):** ghi vào vùng khóa trả `E-LOCK-001`; engine không tự đoán ý định.
- **Chuỗi bắt đầu bằng `=`:** mặc định coi là **văn bản** trừ khi spec khai báo rõ `formula`; điều này tránh việc dữ liệu thành công thức ngoài ý muốn (thư viện mặc định coi mọi chuỗi bắt đầu bằng `=` là công thức `[ĐÃ KIỂM CHỨNG: EV-12]`).
- **Chuẩn hóa:** NFC cho văn bản; loại ký tự điều khiển XML 1.0; cột định danh luôn `@` (ERR_XLSX_007).
- **Cô lập kiểu dáng đầu vào (E11):** dữ liệu từ file người dùng chỉ lấy giá trị (`cell.value`); mọi kiểu dáng lấy từ template/token.
- **Không hardcode tổng hợp (E3):** ô tổng hợp trong vùng khai báo phải là công thức; ghi số cứng vào đó bị từ chối hoặc `W-STYLE-HARDCODED-AGG`.

### 4.11. Tiếng Việt và font (FR-24)

- Chuẩn hóa NFC; kiểm tra font khai báo có glyph tiếng Việt khi có thể; cảnh báo font thiếu glyph.
- Trên server Linux cần cài font tương thích số đo (ví dụ họ Carlito/Liberation cho Calibri/Arial) và font có đủ dấu tiếng Việt; số đo hình thức từ LibreOffice chỉ mang nhãn `estimated` `[CẦN KIỂM CHỨNG]`.
- Định dạng số lưu theo mã chuẩn của file; cách hiển thị (dấu thập phân, nhóm nghìn) phụ thuộc locale của máy mở file `[CẦN KIỂM CHỨNG]`.

### 4.12. Yêu cầu phi chức năng

| ID | Yêu cầu | Chỉ tiêu `[ĐỀ XUẤT]` |
|---|---|---|
| NFR-01 | Tất định theo ngữ nghĩa: cùng đầu vào cho cùng XML sau khi chuẩn hóa (bỏ timestamp, GUID, thuộc tính tự sinh, `docProps` động) | 100% trên bộ golden |
| NFR-02 | Giới hạn tài nguyên mỗi lần gọi | File vào ≤ 50 MB; sau giải nén ≤ 500 MB; timeout 60 giây (gồm tính lại); RAM ≤ 2 GB |
| NFR-03 | Cách ly tiến trình Recalc Backend | Process riêng, profile riêng, không mạng, FS tối thiểu, tự dọn file khóa |
| NFR-04 | Quan sát được: trace, số liệu, mã lỗi ổn định | Mọi lần gọi có `request_id` |
| NFR-05 | Ranh giới module Render: giao tiếp qua `FileRef`; core không phụ thuộc thư viện render | LibreOffice chỉ dùng để tính lại bản sao |
| NFR-06 | Ma trận consumer có mức hỗ trợ rõ ràng, gồm khả năng **đọc giá trị cache** | Excel (Win/Mac/Web): đầy đủ; `pandas`, openpyxl `data_only`, Explorer Preview, QuickLook, mobile viewer, LibreOffice, Google Sheets import, WPS, Numbers: mức xác định trong Phase 0 (TC-39) |
| NFR-07 | Hiệu năng | Mutate bảng 5.000 dòng, không tính lại: p95 < 5 giây; tính lại: p95 < 30 giây |
| NFR-08 | Không phá hủy | 100% thao tác ghi sinh bản mới; file gốc không đổi (so `sha256`) |
| NFR-09 | An toàn song song | Nhiều job đồng thời không xung đột profile/khóa file của backend |
| NFR-10 | Mã thoát CI | `0` sạch, `1` cảnh báo, `2` lỗi nghiêm trọng |
| NFR-11 | Cache đúng kiểu và không phá công thức | 100% ô công thức được cache có `<v>` đúng kiểu; 0 công thức bị mất/vô hiệu; thời gian Cache Writer ≤ 20% thời gian build (không gồm recalc) `[ĐỀ XUẤT]` |

### 4.13. Yêu cầu bảo mật

| ID | Yêu cầu |
|---|---|
| SEC-01 | Parser ZIP/XML an toàn: giới hạn tỷ lệ giải nén, không phân giải entity ngoài (chống XXE), từ chối đường dẫn ZIP bất thường |
| SEC-02 | Từ chối `vbaProject` và `.xlsm` mặc định; không thực thi macro |
| SEC-03 | Không theo liên kết ngoài, OLE, DDE; không tải tài nguyên từ mạng |
| SEC-04 | Dữ liệu đầu vào được coi là không tin cậy: chặn chuỗi bắt đầu bằng `=` thành công thức ngoài ý muốn, loại ký tự điều khiển, kiểm vùng khóa |
| SEC-05 | Cách ly template, file và nhật ký theo tenant; `FileRef` ràng buộc tenant/session ở phía server (không thể hiện trong URI) và có TTL |
| SEC-06 | Audit log che dữ liệu nhạy cảm; mã hóa lưu trữ; chính sách retention |
| SEC-07 | Đầu vào `file://` chỉ chấp nhận trong roots do client khai báo, chống path traversal; URI `resource://` do server cấp là id mờ |
| SEC-08 | Recalc Backend chạy trong sandbox: tiến trình riêng, không mạng, timeout, giới hạn tài nguyên, dọn tiến trình treo |
| SEC-09 | Theo dõi advisory và giấy phép của phụ thuộc; ghim phiên bản (đặc biệt `lxml`, thư viện ZIP, `openpyxl`) |
| SEC-10 | Giá trị cache lấy từ backend là dữ liệu không tin cậy: escape XML tại một điểm, loại ký tự điều khiển, giới hạn độ dài 32.767 ký tự, chỉ nhận mã lỗi trong danh sách cho phép; ghi bằng parser XML an toàn (SEC-01) |

### 4.14. Quy tắc Template Lint (FR-03, FR-08)

1. **Chỉ đọc:** lint không sửa template; mọi sửa đổi đi qua `mutate_xlsx` hoặc `repair_xlsx` sinh bản mới (D-10).
2. **Anchor:** mỗi anchor phải tìm thấy **đúng một** kết quả trong vùng quét; trùng hoặc không thấy thì `E-TPL-ANCHOR-AMBIGUOUS` hoặc `E-TPL-ANCHOR-MISSING`, không tự chọn.
3. **Dòng mẫu:** Prototype Row phải nằm giữa dòng bắt đầu dữ liệu và dòng tổng (Semantic Sentinel); nếu dòng mẫu còn lại sau khi mở rộng, engine báo `W-TPL-SAMPLE-ROW` để quyết định xóa/giữ theo manifest, tránh nó bị tính vào tổng hợp.
4. **Placeholder:** liệt kê `{{...}}`, `<...>` còn lại; kiểm tra theo UG-10.
5. **Sheet tham chiếu:** sheet `Example`/`Template`/`Sample`/`Pattern` (hoặc khai báo trong manifest) phải tồn tại cho profile cần đối chiếu; không có thì dùng Design Tokens và báo `W-DEV-NO-REFERENCE`.
6. **Vùng khóa:** vùng khai báo phải nằm trong sheet hợp lệ; chồng lấn với vùng cần ghi thì báo `E-TPL-LOCK-CONFLICT`.
7. **Màu và kiểu:** lint ghi nhận kiểu dáng đã dùng dưới dạng token trích từ template (không hardcode ở mã), phục vụ UG-05.

### 4.15. Chính sách lệch template (D-18)

| Loại lệch | Ví dụ | Hành vi mặc định | Điều kiện áp dụng |
|---|---|---|---|
| Kiểu dáng | Đổi màu header, thêm badge, đổi viền | Không áp; phát `W-DEV-STYLE` kèm trước/sau | `approved_deviations` chứa mã tương ứng |
| Bố cục | Thêm freeze panes, đổi độ rộng cột | Không áp; phát `W-DEV-LAYOUT` | Như trên (ví dụ `W-DEV-LAYOUT:freeze_panes`) |
| Dữ liệu mẫu | Giữ/xóa dòng mẫu, thay dữ liệu giả lập | Theo manifest | Manifest hoặc phê duyệt |
| Miễn duyệt | Sửa lỗi hiển thị `###` do độ rộng quá hẹp; đồng bộ viền merge | Áp tự động, ghi `I-*` | Không cần duyệt (tương tự ngoại lệ trong rule E2) |

---
## 5. Actor & Feature

### 5.1. Actor

| Actor | Vai trò | Tương tác chính |
|---|---|---|
| Người dùng cuối (End User) | Yêu cầu cập nhật/tạo bảng tính, duyệt kết quả, mở trong Excel | Giao tiếp với AI; nhận file; quyết định các điểm AI không tự quyết (lệch template, thành phần có nguy cơ mất) |
| Antigravity AI (MCP Client) | Lập kế hoạch, lập MutationSpec/XlsxSpec, gọi công cụ, xử lý diagnostics | Gọi mọi công cụ MCP |
| Tác giả template (Template Author) | Thiết kế template trong Excel, khai báo manifest/profile | `preflight_xlsx`, `lint_template`, `register_template` |
| Quản trị/Kỹ sư nền tảng | Cấu hình giới hạn, tenant, backend tính lại, theo dõi audit, vận hành CI | Cấu hình; đọc audit/trace |
| Engine | Thực thi tất định, kiểm định, trả diagnostics | — |
| Recalc Backend | Tính lại công thức trên bản sao (LibreOffice hoặc Excel COM) | Nhận bản sao, trả giá trị và lỗi |
| Module PDF/Render (tương lai) | Chuyển `.xlsx` sang PDF, cung cấp số liệu hiển thị | Nhận/trả `FileRef` |
| Kiểm toán/Reviewer | Đối chiếu audit trail, chất lượng và bảo mật | Đọc audit log, báo cáo test |

### 5.2. Danh mục tính năng

| ID | Tính năng | Mô tả ngắn | Actor chính | Ưu tiên |
|---|---|---|---|---|
| FR-01 | Preflight và Package Inventory | Quét package chỉ đọc, lập Inventory (ảnh, chart, pivot, bảng, CF, DV, tên, merge, macro, liên kết ngoài, thành phần ẩn) | Template Author, AI | MVP |
| FR-02 | Fidelity Tier | Chọn T1/T2/T3 theo 4.6; T3 dừng và trả `fixable_by=human`; T2 vá XML bằng lxml | Engine | MVP (T1, T3); P1 (T2) |
| FR-03 | Template registry + manifest/profile | Lưu phiên bản, hash, anchor, dòng mẫu, vùng khóa, chính sách, profile cổng | Template Author, AI | MVP |
| FR-04 | Template lint | Kiểm tra chỉ đọc theo 4.14: anchor, dòng mẫu, placeholder, sheet tham chiếu, vùng khóa | Template Author, AI | MVP |
| FR-05 | Mutate template (Path A) | Sửa bản sao theo MutationSpec: `cell_updates`, `table_expansions`, `column_expansions`, `freeze_panes`, `sheet_ops`, `calc_policy` (MVP); thao tác xóa/gộp/DV/CF/tên xem FR-29 (P1) | AI | MVP |
| FR-06 | Clone kiểu dáng | Clone Prototype Row (font, fill, viền, canh lề, định dạng số, bảo vệ), đồng bộ viền merge | Engine | MVP |
| FR-07 | Shift Manager | Dịch mọi đối tượng phụ thuộc vị trí theo 4.7 và `range_policy` | Engine | MVP |
| FR-08 | Semantic Anchor Discovery | Tìm header, bắt đầu dữ liệu, dòng tổng bằng từ khóa/công thức; báo mơ hồ | Engine | MVP |
| FR-09 | Xác thực đầu vào | Schema MutationSpec/XlsxSpec, vùng khóa, chuỗi `=`, NFC, ký tự điều khiển | Engine | MVP |
| FR-10 | Recalc Backend | Tính lại trên bản sao, đọc giá trị, quét lỗi, báo hàm không hỗ trợ (4.8) | Engine, Recalc Backend | MVP |
| FR-11 | Trạng thái giá trị và cờ tính lại | `values_status` kèm `origin`; `fullCalcOnLoad` theo `calc_on_open`; ghi cache do FR-28 | Engine | MVP |
| FR-12 | Cổng chung (UG) | UG-01..UG-12 (4.9) | Engine | MVP |
| FR-13 | Cổng profile (PG) | Profile khai báo; profile `unit_test_matrix` chuyển từ 12 gate hiện có | Engine, Template Author | MVP |
| FR-14 | Structural Diff | Đối chiếu Inventory và kiểu dáng; phân loại `declared`/`undeclared` | AI, Kiểm toán | MVP |
| FR-15 | Diagnostics | Issues có `location`, `severity`, `evidence`, `fixable_by`, `suggested_action` | AI | MVP |
| FR-16 | Inspect cho AI | Snapshot có anchor và `values_status`; Snapshot Adapter tùy chọn (`excel-parser`) | AI | MVP |
| FR-17 | Chart relink | Relink series và dời anchor chart khi mở rộng bảng | Engine | MVP |
| FR-18 | Ước lượng hình thức | Chiều cao dòng, độ rộng cột, nguy cơ `###`, freeze panes; luôn gắn `estimated` | Engine | P1 |
| FR-19 | Build từ XlsxSpec (Path B) | Tạo workbook mới bằng XlsxWriter với Design Tokens | AI | P1 |
| FR-20 | Repair tất định | Sửa lỗi `fixable_by=engine`, sinh `_repaired`, giới hạn số vòng | AI, Engine | P1 |
| FR-21 | Chính sách lệch template | `W-DEV-*` và `approved_deviations` (4.15) | Engine, End User | MVP |
| FR-22 | Kho file `FileRef` | URI mờ kèm `sha256`; chiều vào qua roots; TTL; cách ly tenant | Engine | MVP |
| FR-23 | Audit log | Nhật ký thao tác, che dữ liệu nhạy cảm | Admin, Kiểm toán | MVP |
| FR-24 | Xử lý tiếng Việt và văn bản | NFC, cảnh báo font thiếu glyph, định danh `@` | Engine | MVP |
| FR-25 | Vệ sinh tài liệu | Báo/scrub sheet ẩn, tên ẩn, metadata, liên kết ngoài theo policy | Engine | P1 |
| FR-26 | Điểm mở rộng | Adapter cho định dạng/backend khác (ví dụ `.xlsm` giữ VBA, `.ods`, Excel COM) | Admin | P2 |
| FR-27 | Xuất `.xls` cũ | Chuyển `.xlsx` sang `.xls` qua LibreOffice (dual-delivery) | AI | P2 |
| FR-28 | Cache Writer (`write_cached`) | Ghi `<v>` và `t` (`n`/`str`/`b`/`e`) vào ô công thức của file giao bằng `lxml` từ giá trị Recalc Backend; `calc_policy`; tự kiểm UG-13 (4.8, D-12, D-22) | Engine | MVP |
| FR-29 | Thao tác xóa, gộp, DV/CF, tên | `delete_rows`, `delete_columns`, `merge`/`unmerge`, `set_validation`, `set_conditional_format`, `define_name` qua Shift Manager (D-23) | AI, Engine | P1 |

### 5.3. Ma trận Actor × Công cụ (rút gọn)

| Công cụ | End User | AI | Template Author | Admin | Kiểm toán |
|---|---|---|---|---|---|
| `preflight_xlsx`, `lint_template` | | ✓ | ✓ | ✓ | |
| `register_template`, `list_templates`, `get_template_manifest` | | ✓ | ✓ | ✓ | |
| `inspect_xlsx` | (qua AI) | ✓ | ✓ | ✓ | |
| `mutate_xlsx`, `build_xlsx`, `repair_xlsx`, `export_legacy_xls` | (qua AI) | ✓ | | | |
| `recalc_xlsx`, `validate_xlsx`, `diff_xlsx` | (qua AI) | ✓ | ✓ | ✓ | ✓ (đọc kết quả) |
| Duyệt `approved_deviations` | ✓ | (đề xuất) | | | |
| Audit log / trace | | | | ✓ | ✓ |

---

## 6. Demonstration

### 6.1. Quy trình nghiệp vụ tổng quan

```
[1] Template Author thiết kế template Excel + manifest/profile
        │
        ▼
[2] preflight_xlsx + lint_template ──► có lỗi / thành phần rủi ro? ──► sửa template / chọn Tier ──┐
        │ không                                                                                  │
        ▼                                                                                        │
[3] register_template (phiên bản, sha256) ◄──────────────────────────────────────────────────────┘
        │
        ▼
[4] Người dùng yêu cầu cập nhật/tạo bảng tính ───► AI
        │
        ▼
[5] AI chọn đường: Mutate template (MutationSpec) | Build mới (XlsxSpec) | Chỉ kiểm định/đối chiếu
        │   AI đọc inspect_xlsx (có values_status); không viết mã/XML
        ▼
[6] Engine: preflight ─► validate input ─► mutate (Shift Manager) ─► style/layout
            ─► recalc (bản sao) ─► write_cached ─► UG + PG + diff ──► file_ref + diagnostics
        │
        ▼
[7] AI đọc diagnostics:
        ├─ fixable_by=engine → gọi lại (repair/policy)
        ├─ fixable_by=ai     → sửa spec rồi gọi lại
        └─ fixable_by=human  → hỏi người dùng (lệch template, thành phần có thể mất, vùng khóa)
        │
        ▼
[8] Người dùng mở file trong Excel, duyệt (Excel tính lại khi mở nếu calc_on_open bật); consumer không tính vẫn thấy giá trị cache
        │
        ▼
[9] Audit log ghi toàn bộ chuỗi thao tác (hash, mã issue, phiên bản template)
```

### 6.2. Workflow chính

**WF-A. Nhập kho template**

```
Upload template -> preflight (Inventory, Tier) -> [T3 hoặc lỗi E-SEC?]
     |không                                         |có -> báo issues, dừng hoặc hỏi Template Author
     v
lint (anchor, dòng mẫu, placeholder, sheet tham chiếu, vùng khóa) -> OK?
     |có
     v
Đối chiếu manifest/profile (anchor, vùng khóa, required_package) -> register (version, sha256)
```

**WF-B. Mutate template (Path A)**

```
mutate_xlsx(template_id | file_ref, mutation_spec)
  -> giới hạn tài nguyên + xác thực tenant
  -> tạo bản sao làm việc (bản gốc giữ nguyên, sha256)
  -> preflight lại bản sao -> chọn Fidelity Tier (T3: dừng)
  -> validate MutationSpec (schema, vùng khóa, chuỗi '=', NFC) --[vi phạm]--> E-SPEC/E-LOCK, dừng
  -> tìm anchor ngữ nghĩa --[mơ hồ]--> E-TPL-ANCHOR-*, dừng
  -> Shift Manager: chèn dòng/cột, dịch công thức (toàn workbook), merge, CF, DV,
                    bảng, bộ lọc, vùng in, tên, chart, chiều cao dòng
  -> clone Prototype Row, ghi dữ liệu (định danh '@'), đồng bộ viền merge, freeze panes
  -> lưu file giao tạm (openpyxl)
  -> recalc trên bản sao riêng -> giá trị + lỗi (UG-04)
  -> Cache Writer: ghi <v>/t vào file giao theo calc_policy; đặt fullCalcOnLoad theo calc_on_open; đọc lại data_only (UG-13)
  -> UG + PG + Structural Diff --[error]--> trả lỗi kèm file_ref ở trạng thái 'không phát hành'
  -> lưu FileRef -> trả file_ref + diagnostics -> audit
```

**WF-C. Build mới (Path B)**

```
build_xlsx(xlsx_spec)
  -> validate XlsxSpec (schema, JSON path khi lỗi; chỉ nhận Design Tokens theo tên)
  -> dựng bằng XlsxWriter (CF dạng công thức cho zebra/màu điều kiện)
  -> recalc bản sao -> Cache Writer -> UG (không có PG nếu không có profile) -> trả kết quả
```

**WF-D. Kiểm định và đối chiếu file có sẵn**

```
preflight_xlsx(file_ref) -> inspect_xlsx -> validate_xlsx(profile?, reference?) -> diff_xlsx(trước, sau)
  -> báo cáo issues (UG/PG) + exit code 0/1/2
```

**WF-E. Tính lại và đọc giá trị cho AI**

```
inspect_xlsx(file_ref)
  -> có cache? --có--> values_status=cached (origin: source_file | engine_injected:<backend>)
  -> không --> recalc_xlsx (bản sao, LibreOffice) -> values_status=recalculated
  -> backend lỗi/không hỗ trợ hàm --> values_status=missing + W-CALC-*
```

### 6.3. Activity flow xử lý diagnostics (phía AI, dựa trên hợp đồng của engine)

```
Nhận diagnostics
  ├─ Có errors?
  │     ├─ E-PKG / E-TPL (package/template hỏng)      -> dừng, báo người dùng/Template Author
  │     ├─ E-SPEC (spec sai)                           -> sửa spec theo JSON path, gọi lại (tối đa N lần [ĐỀ XUẤT: 2])
  │     ├─ E-LOCK (ghi vào vùng khóa)                  -> không tự ghi; hỏi người dùng
  │     ├─ E-SHIFT (dịch sai/mồ côi/dạng chưa hỗ trợ)  -> dừng, không phát hành file; báo kèm evidence
  │     ├─ E-CACHE (cache sai kiểu/không an toàn)      -> dừng, không phát hành file; báo kèm evidence (lỗi của engine)
  │     └─ E-SEC                                       -> dừng, không thử lại với cùng đầu vào
  └─ Chỉ có warnings?
        ├─ W-PKG-UNSUPPORTED-* (fixable_by=human)      -> BẮT BUỘC hỏi người dùng: chấp nhận mất / dùng backend Excel / đổi template
        ├─ W-DEV-* (fixable_by=human)                  -> trình bày trước/sau, xin duyệt; chỉ gọi lại với approved_deviations
        ├─ W-CALC-NO-CACHE / W-CALC-VOLATILE / W-CALC-FUNC-UNSUPPORTED -> không tự sửa; nêu rõ nguồn số liệu (origin) khi bàn giao
        ├─ W-LAYOUT / W-STYLE (estimated)              -> gọi lại với policy phù hợp hoặc chấp nhận, ghi nhận 'estimated'
        └─ Không còn cảnh báo cần xử lý                -> bàn giao file
```

Quy tắc chặn vòng lặp: số lần gọi lại tối đa cố định; giữ phương án tốt nhất (ít lỗi nhất) và dừng ngay khi hai lần liên tiếp không cải thiện. Engine không tự lặp; vòng lặp thuộc về AI.

---

## 7. Test & Audit Planning

### 7.1. Chiến lược kiểm thử

| Tầng | Mục đích | Công cụ |
|---|---|---|
| Unit | Shift Manager (từng dạng công thức), Preflight, Tier, validator đầu vào, sinh issue | `pytest` |
| Integration | Pipeline Path A và Path B đầy đủ trên corpus template | `pytest` + corpus |
| Differential | So kết quả dịch chuyển của Shift Manager với LibreOffice (UNO) và Excel COM trên cùng file (D-16) | `pytest` + LibreOffice; runner Windows + Excel |
| Package Conformance | Hợp lệ package, content types, quan hệ, XSD; mở được không "Repair" | `lxml`, XSD ECMA-376; `OpenXmlValidator` (.NET) trong CI |
| Oracle / Compatibility | Mở file và tính lại trên Excel (Win/Mac/Web), LibreOffice; thủ công cho consumer còn lại | Excel COM trong CI; LibreOffice headless |
| Security | Zip bomb, XXE, path traversal, macro, liên kết ngoài, chuỗi `=` độc hại, cách ly backend | Payload corpus, fuzz |
| Property/Fuzz | MutationSpec ngẫu nhiên (vị trí chèn, số dòng, nhiều sheet) luôn cho file hợp lệ và Inventory parity | `hypothesis` |
| Regression/Golden | So khớp XML đã chuẩn hóa; các ca EV-01..EV-12 giữ làm regression vĩnh viễn | Golden files |
| Performance | Thời gian, bộ nhớ (kể cả tính lại) | Benchmark |
| UAT | Template và báo cáo nghiệp vụ thật | 20-30 file `[ĐỀ XUẤT]` |

Nguyên tắc: mọi test **độc lập** (không dùng thư mục scratch chung, không phụ thuộc thứ tự chạy), mỗi test tự tạo dữ liệu đầu vào (EV-09); mọi ca kiểm chứng ở Phụ lục E được chuyển thành test tự động trước khi sửa mã.

### 7.2. Danh mục ca kiểm thử

| ID | Ca kiểm thử | Kết quả mong đợi | Yêu cầu | Tự động hóa |
|---|---|---|---|---|
| TC-01 | Tên hàm có chữ + số khi chèn dòng sớm: `LOG10`, `ATAN2`, `BIN2DEC`, `DAYS360` (EV-01) | Tên hàm không đổi; chỉ toán hạng ô/dải được dịch | FR-07, D-03 | Tự động |
| TC-02 | Chuỗi và tên định danh trong công thức: `"TC001"`, `"TC020"`, `FY2024` (EV-02) | Giữ nguyên 100% (kể cả số 0 đầu) | FR-07, D-03 | Tự động |
| TC-03 | Công thức hai chiều giữa các sheet: sheet thống kê trỏ vào sheet được mở rộng; sheet được mở rộng trỏ sang sheet khác (EV-03, EV-04) | Chỉ tham chiếu trỏ vào sheet đích được dịch; công thức ở sheet khác được dịch; không dịch nhầm | FR-07, P-02 | Tự động + vi sai |
| TC-04 | Ngữ nghĩa biên theo `range_policy`: chèn tại dòng đầu dải, giữa dải, ngay dưới dòng cuối dải (EV-07) | Đúng bảng 4.7 cho từng policy; khớp Oracle ở `excel_native` | FR-07, D-04, D-16 | Tự động + vi sai |
| TC-05 | Dạng công thức: tuyệt đối, hỗn hợp, cả cột/dòng, tiền tố sheet có dấu nháy, tên đã định nghĩa, công thức mảng/chia sẻ; dạng chưa hỗ trợ (3D, tham chiếu cấu trúc, mảng động) | Dạng hỗ trợ dịch đúng; dạng chưa hỗ trợ báo `E-SHIFT-UNSUPPORTED-FORM`, không dịch đoán | FR-07 | Tự động |
| TC-06 | Đối tượng phụ thuộc vị trí: CF, DV, AutoFilter, bảng, vùng in, tên đã định nghĩa, chiều cao dòng, hyperlink, comment, ảnh neo (EV-05) | Mọi đối tượng dịch cùng lúc; UG-07 đạt; không tham chiếu mồ côi | FR-07, UG-07 | Tự động |
| TC-07 | Merge: dịch/mở rộng khi chèn, không chồng lấn, chỉ ghi ô Top-Left, đồng bộ viền | Đúng; không ngoại lệ ghi `MergedCell` | FR-06, UG-06 | Tự động |
| TC-08 | Chart: nhiều series, tham chiếu sheet khác, dời anchor dưới bảng | Series và anchor đúng; không chồng lên bảng | FR-17 | Tự động + soát mắt |
| TC-09 | Clone Prototype Row: font (gồm màu), fill (rgb/theme/indexed), viền, canh lề (gồm `wrap_text`), định dạng số, bảo vệ | Chữ ký dòng mới trùng dòng mẫu ở mọi cột | FR-06, UG-05 | Tự động |
| TC-10 | Preflight: file mẫu chứa từng loại thành phần (ảnh, chart, pivot, bảng, CF, DV, tên, macro, liên kết ngoài, ẩn) | Inventory và Tier đúng theo 4.6 | FR-01, FR-02 | Tự động |
| TC-11 | Fidelity thực của openpyxl: shape/text box, slicer, sparkline, form control, `x14` CF/DV, rich text, ảnh khi thiếu Pillow, pivot, bảng, hyperlink, comment | Ma trận hành vi được ghi nhận; các mục `[CẦN KIỂM CHỨNG]` ở 4.6 được chốt; thành phần mất phải bị bắt ở UG-02 | FR-02, UG-02 | Tự động (Phase 0) |
| TC-12 | Structural Diff: cố ý làm mất ảnh/chart/CF; thay đổi có khai báo trong spec | Mất không khai báo làm UG-02 thất bại; thay đổi khai báo đạt | FR-14, UG-02 | Tự động |
| TC-13 | Recalc: file chưa cache (EV-08); so giá trị LibreOffice với Excel COM trên corpus; hàm không được hỗ trợ | Giá trị khớp trên hàm phổ biến; hàm lệch/không hỗ trợ báo `W-CALC-FUNC-UNSUPPORTED` | FR-10 | Tự động (Excel: runner Windows) |
| TC-14 | Lỗi tính lại: `#REF!`, `#NAME?`, `#DIV/0!`, `#VALUE!` | Bị bắt ở UG-04 (trừ danh sách cho phép trong manifest) | FR-10, UG-04 | Tự động |
| TC-15 | Cache và `fullCalcOnLoad`: Excel, Protected View, trình xem trước, thư viện đọc; tổ hợp `calc_on_open` × cache | D-12 đã xác nhận bằng EV-13 (Excel COM + openpyxl); còn ghi nhận Protected View, hộp thoại lưu khi đóng, trình xem trước; `values_status` luôn đúng | FR-11, FR-28, D-12 | Thủ công + COM |
| TC-16 | Vùng khóa và chuỗi `=`: ghi vào vùng khóa; dữ liệu bắt đầu bằng `=` (EV-12) | `E-LOCK-001`; chuỗi `=` được lưu như văn bản trừ khi khai báo `formula` | FR-09, SEC-04 | Tự động |
| TC-17 | Định danh: mã có số 0 đầu, chuỗi số dài | `number_format='@'`; giá trị giữ chuỗi | FR-24, UG-09 | Tự động |
| TC-18 | Anchor và dòng mẫu: keyword trùng/thiếu; dòng mẫu còn lại sau mở rộng và bị tính vào tổng (EV-10) | `E-TPL-ANCHOR-AMBIGUOUS/MISSING`; `W-TPL-SAMPLE-ROW` đúng | FR-08, FR-04 | Tự động |
| TC-19 | Validator hai tầng: template ngoài ma trận kiểm thử (báo cáo tài chính, danh sách nhân sự); profile `unit_test_matrix` trên `Report5` | UG không fail vô nghĩa trên template khác; profile tái hiện đúng kết quả 12 gate hiện có | FR-12, FR-13, D-08 | Tự động |
| TC-20 | Chữ ký kiểu dáng: màu theme/indexed, `wrap_text`, màu chữ | Không còn "bằng nhau giả"; khác biệt bị bắt | UG-05, P-06 | Tự động |
| TC-21 | Path B: Design Tokens; zebra bằng CF công thức còn đúng sau chèn dòng; AI không đưa được mã màu tự do | Token hợp lệ được áp; mã tự do bị từ chối `E-SPEC-*` | FR-19, D-14 | Tự động |
| TC-22 | Lệch template: đổi màu/freeze panes khi chưa duyệt; khi có `approved_deviations`; sửa `###` | Chưa duyệt: không áp, `W-DEV-*`; có duyệt: áp; `###`: áp, `I-*` | FR-21, D-18 | Tự động |
| TC-23 | Không phá hủy và không fallback im lặng: `sha256` file gốc; template thiếu/sai đường dẫn | Gốc không đổi; lỗi rõ `E-TPL-*`, không tạo workbook rỗng | NFR-08, P-07 | Tự động |
| TC-24 | Bảo mật package: zip bomb, XXE, path traversal ZIP, `vbaProject`/`.xlsm`, liên kết ngoài, OLE | Bị từ chối với `E-SEC-*` | SEC-01..SEC-03 | Tự động |
| TC-25 | `FileRef` và roots: URI mờ không chứa tenant/session; id tenant khác; `file://` ngoài roots; path traversal; `sha256` | Từ chối truy cập chéo; chỉ đọc trong roots; toàn vẹn khớp | FR-22, SEC-05, SEC-07 | Tự động |
| TC-26 | Sandbox Recalc Backend: tiến trình treo, timeout, profile riêng, chạy song song N job, dọn `.~lock.*` (EV-08) | Dừng đúng; không xung đột; không rò tiến trình | NFR-03, NFR-09, SEC-08 | Tự động |
| TC-27 | Tất định: chạy lặp cùng đầu vào | XML chuẩn hóa trùng nhau | NFR-01 | Tự động |
| TC-28 | Tiếng Việt: NFD sang NFC, font thiếu glyph, ước lượng chiều cao/độ rộng, số hiển thị theo locale | Chữ đúng; cảnh báo font; mọi số đo hình thức gắn `estimated` | FR-24, UG-08 | Tự động + soát mắt |
| TC-29 | Snapshot cho AI: file có cache, không cache, bản đã tính lại; anchor ổn định; Snapshot Adapter (`excel-parser`) tương đương (nếu bật) | `values_status` đúng; round-trip `inspect` rồi dựng lại tương đương | FR-16, D-20 | Tự động |
| TC-30 | Chất lượng diagnostics: mỗi mã có tiêu chí kích hoạt đo được; mọi issue có `location`, `fixable_by`, `evidence` | Không có cảnh báo phỏng đoán không gắn `estimated` | FR-15 | Tự động |
| TC-31 | Hiệu năng | Đạt NFR-07 | NFR-07 | Tự động |
| TC-32 | Audit: đủ trường, che dữ liệu nhạy cảm | Đạt SEC-06 | FR-23, SEC-06 | Tự động |
| TC-33 | Bộ test độc lập và corpus golden: chạy ngẫu nhiên thứ tự, thư mục sạch (EV-09) | Luôn đạt hoặc luôn rớt như nhau, không phụ thuộc trạng thái | P-12 | Tự động (CI) |
| TC-34 | Fuzz/property: MutationSpec ngẫu nhiên | 100% file hợp lệ; Inventory parity; không tham chiếu mồ côi | FR-05, FR-07, UG-02, UG-07 | Tự động |
| TC-35 | UAT với template thật (Report5 Unit Test, báo cáo tài chính, danh sách nhân sự) | Đạt ngưỡng chấp nhận (7.3) | Tất cả MVP | Thủ công |
| TC-36 | Mở file trên Excel Win/Mac/Web, LibreOffice, Google Sheets import, WPS | Không báo "Repair"; ghi nhận chênh lệch theo NFR-06 | NFR-06, UG-01 | Một phần tự động |
| TC-37 | `repair_xlsx`: lỗi `fixable_by=engine`; giới hạn số vòng | Sửa tất định; sinh `_repaired`; gốc không đổi; dừng khi không cải thiện | FR-20 | Tự động |
| TC-38 | Cache bốn kiểu (tái hiện EV-13 tự động): `=SUM(A1:A2)`, `=IF(A1>5,"Pass","Fail")`, `=A1>5`, `=1/0`; thêm ngày/giờ và chuỗi rỗng; ghi cache bằng Cache Writer rồi đọc chéo | `data_only` cho `30`, `'Pass'`, `True`, `'#DIV/0!'`; Excel COM đọc đúng; không thông báo "recover"; UG-13 đạt | FR-28, UG-13, D-12 | Tự động (Excel COM: runner Windows) |
| TC-39 | Ma trận consumer đọc cache: `pandas.read_excel()`, openpyxl `data_only`, Excel Win/Mac/Web, Explorer Preview, QuickLook, iOS/Android viewer, LibreOffice, Google Sheets import, WPS | Mỗi consumer hiển thị đúng giá trị cache, không báo "Repair"; chênh lệch ghi vào ma trận NFR-06 (không khẳng định hỗ trợ trước khi có kết quả) | NFR-06, FR-28 | Một phần tự động + thủ công (Phase 0) |
| TC-40 | Công thức còn sống sau ghi cache: đổi `A1` rồi `Calculate()` (Excel COM) và tính lại bằng LibreOffice; `calc_on_open` bật/tắt; build lặp lại | Giá trị mới tính đúng (`A3` thành `120`); `<f>` trước/sau không đổi; kết quả tất định | FR-28, D-22, NFR-11 | Tự động (Excel COM: runner Windows) |
| TC-41 | Xóa dòng/cột có công thức, CF, DV, merge, chart, tên tham chiếu tới | Dịch/co đúng; vùng bị xóa hoàn toàn gây `E-SHIFT-ORPHAN`, không `#REF!` im lặng | FR-29, D-23 | Tự động + vi sai |
| TC-42 | Thao tác `merge`/`unmerge`, `set_validation`, `set_conditional_format`, `define_name` | Áp đúng; UG-06, UG-07 đạt; không chồng lấn merge | FR-29, D-23 | Tự động |
| TC-43 | Anchor `kind`/`scope` và cột theo tên header: đổi vị trí header, thêm/bớt cột, tên header trùng | Phân giải đúng; trùng/thiếu báo `E-TPL-ANCHOR-*`; không dựa số dòng/cột cứng | FR-08, D-24 | Tự động |
| TC-44 | Biên của Cache Writer: `<v/>` và `<v></v>` rỗng do openpyxl; ô đã có `t`; công thức chia sẻ/mảng; chuỗi > 32.767 ký tự; ký tự XML đặc biệt/điều khiển; hàm biến động; nhiều sheet, hàng chục nghìn ô | Ghi đúng hoặc bỏ qua kèm `W-CALC-NO-CACHE`; `W-CALC-VOLATILE`; không `E-CACHE-UNSAFE-VALUE` lọt; Inventory không đổi | FR-28, SEC-10, UG-13 | Tự động + fuzz |
| TC-45 | Vệ sinh tài liệu: sheet/tên ẩn, metadata `docProps`, liên kết ngoài theo policy | Báo hoặc scrub đúng; không rò rỉ | FR-25, UG-12 | Tự động |
| TC-46 | Giới hạn tài nguyên, timeout và mã thoát CI | Dừng đúng giới hạn NFR-02; exit code 0/1/2 đúng NFR-10 | NFR-02, NFR-10 | Tự động |

### 7.3. Tiêu chí chấp nhận `[ĐỀ XUẤT]`

| Tiêu chí | Ngưỡng |
|---|---|
| File báo "Repair" trên Excel (Win/Mac/Web) | 0 trên toàn bộ corpus |
| Khác biệt Inventory không khai báo (`undeclared`) | 0 |
| Token công thức (tên hàm, chuỗi, tên định danh) bị đổi | 0 |
| Dịch công thức đúng theo kiểm thử vi sai với Oracle, trên các dạng được hỗ trợ | 100% corpus |
| Công thức/đối tượng trỏ sai sau dịch (UG-07, `E-SHIFT-ORPHAN`) | 0 |
| Lỗi tính lại ngoài danh sách cho phép (UG-04) | 0 |
| Thành phần ngoài hỗ trợ bị mất mà không có cảnh báo | 0 |
| Ghi vào vùng khóa lọt qua | 0 |
| Ghi đè file gốc | 0 |
| Payload bảo mật được chặn | 100% trong corpus |
| Tất định (XML chuẩn hóa) | 100% |
| Tỷ lệ thành công "1-shot" trên corpus UAT | Ngưỡng do chủ sở hữu chốt (xem Q-11); tài liệu không ấn định số |
| UAT: file được người dùng duyệt | Ngưỡng do chủ sở hữu chốt (xem Q-05) |
| Ô công thức có cache sai kiểu, hoặc đọc `data_only` không khớp `values_summary` | 0 |
| Công thức bị mất hoặc vô hiệu hóa sau khi ghi cache (so `<f>` trước/sau) | 0 |

### 7.4. Kế hoạch Audit

**a) Audit runtime (vết thao tác)**

| Hạng mục | Nội dung |
|---|---|
| Ghi nhận | `request_id`, tenant, công cụ, hash đầu vào/đầu ra, phiên bản template/manifest/spec, Fidelity Tier, backend tính lại và phiên bản, `range_policy`, `calc_policy`, thống kê cache (written/skipped/types/origin), `approved_deviations`, danh sách issue (mã + vị trí), thời gian, kết quả |
| Không ghi nguyên văn | Nội dung ô, dữ liệu cá nhân/tài chính, văn bản prompt; chỉ ghi hash và thống kê |
| Lưu trữ | Mã hóa; cách ly theo tenant; retention theo chính sách `[ĐỀ XUẤT: xác định ở Q-06]` |
| Truy vết | Trace theo `request_id`; liên kết bản template ↔ file sinh ra ↔ giá trị `values_status` |

**b) Audit chất lượng kỹ thuật**

- Cổng chất lượng (release gate): toàn bộ TC của phạm vi MVP đạt (xem Phụ lục A); không có lỗi mức nghiêm trọng mở; mọi ca EV-01..EV-12 có test hồi quy.
- **Ma trận truy vết** (traceability, Phụ lục G): mỗi `FR/NFR/SEC` ↔ module mã ↔ `TC`; mục nào thiếu một trong ba cột là khoảng trống phải xử lý trước phát hành.
- Số liệu định kỳ, **đo được trên corpus**: tỷ lệ build thành công, tỷ lệ 1-shot, phân bố mã issue, tỷ lệ lỗi theo template, thời gian xử lý, tỷ lệ chênh lệch giá trị giữa LibreOffice và Excel.
- Quy tắc nằm trong tài liệu markdown (`E1..E14`, `ERR_XLSX_*`) chỉ có giá trị hướng dẫn cho AI; quy tắc nào cần được bảo đảm phải tồn tại dưới dạng gate hoặc test (R-13).

**c) Audit bảo mật**

- Rà soát phụ thuộc và advisory (đặc biệt `openpyxl`, `lxml`, thư viện ZIP, LibreOffice).
- Kiểm thử xâm nhập cho bề mặt file/ZIP/`FileRef`/tiến trình backend trước mỗi phiên bản lớn.
- Kiểm tra rò rỉ chéo tenant (template, file, log, profile của LibreOffice, thư mục tạm).
- Rà soát giấy phép trước khi phân phối: xác nhận lại từng phụ thuộc trong core; đặc biệt thư viện copyleft/AGPL không được vào core (D-17).

**d) Checklist phát hành**

1. Toàn bộ TC bắt buộc đạt trên CI (gồm kiểm thử vi sai và Oracle).
2. Bảng "Engine bảo đảm / không bảo đảm" (3.4) khớp hành vi thực tế.
3. Không có `[CẦN KIỂM CHỨNG]` nào còn mở trong phạm vi MVP.
4. Giấy phép phụ thuộc đã được rà soát và ghi lại.
5. Ma trận truy vết đầy đủ; audit log và masking đã kiểm tra.
6. Tài liệu hướng dẫn Template Author (anchor, dòng mẫu, vùng khóa, thành phần được hỗ trợ) đã phát hành.

---
## Phụ lục A. Lộ trình và phạm vi MVP

### A.1. Các giai đoạn

| Giai đoạn | Mục tiêu | Đầu ra | Điều kiện hoàn thành |
|---|---|---|---|
| **Phase 0 — Kiểm chứng** | Chốt mọi mục `[CẦN KIỂM CHỨNG]` trước khi viết engine | Ma trận fidelity của openpyxl (TC-11); ngữ nghĩa chèn dòng của Excel/LibreOffice (TC-04); chênh lệch LibreOffice-Excel (TC-13); hành vi `fullCalcOnLoad` cùng cache (TC-15; **D-12 đã xác nhận bằng EV-13**); ma trận consumer đọc cache và biên của Cache Writer (TC-39, TC-44); hành vi mặc định với chuỗi `=` (EV-12 đã có, cần chốt chính sách); giấy phép từng phụ thuộc; roots và `resource_link` của Antigravity (Q-10); font server; **corpus template** và **harness vi sai** | Danh sách `[CẦN KIỂM CHỨNG]` trong phạm vi MVP về 0; corpus tối thiểu 10-20 template; test độc lập (TC-33) |
| **Phase 1 — MVP** | Lõi an toàn: Preflight, Shift Manager mới, kiểm định hai tầng, recalc trên bản sao, ghi cache vào file giao | FR-01..FR-10, FR-11, FR-12..FR-17, FR-21..FR-24, FR-28; công cụ `preflight_xlsx`, `inspect_xlsx`, `lint_template`, `register_template`/`list_templates`/`get_template_manifest`, `mutate_xlsx`, `recalc_xlsx`, `validate_xlsx`, `diff_xlsx` | Toàn bộ TC trừ TC-21, TC-37, TC-41, TC-42 đạt (TC-11, TC-13, TC-15 đã hoàn thành ở Phase 0); tiêu chí 7.3 đạt trên corpus; UAT đạt ngưỡng Q-05. **MVP rộng có chủ đích; cắt lát theo A.3** |
| **Phase 2 — P1** | Mở rộng khả năng và độ bền | FR-02 (Tier T2, vá XML), FR-18, FR-19 (`build_xlsx`), FR-20 (`repair_xlsx`), FR-25, FR-29 | TC-21, TC-37, TC-41, TC-42, TC-45 đạt; ma trận consumer (NFR-06) hoàn chỉnh |
| **Phase 3 — P2** | Mở rộng hệ sinh thái | FR-26 (adapter: giữ VBA, `.ods`, Excel COM backend), FR-27 (`export_legacy_xls`) | Theo nhu cầu thương mại hóa (Q-14) |

### A.2. Thứ tự thực hiện khuyến nghị trong Phase 1

1. Chuyển các ca EV-01..EV-12 thành test hồi quy (độc lập, không dùng thư mục chung) **trước khi sửa mã**.
2. Viết lại bộ dịch công thức bằng bộ tách token, có tham số sheet đích và quét toàn workbook (D-03, FR-07).
3. Gom mọi đối tượng phụ thuộc vị trí vào Shift Manager (4.7).
4. Preflight Scanner và Structural Diff (D-06, D-07) — gate chung cho mọi template.
5. Tách validator thành UG và PG; chuyển 12 gate hiện có thành profile `unit_test_matrix` (D-08).
6. Recalc Backend LibreOffice trong sandbox; `values_status`; Cache Writer (`write_cached`) cùng TC-38..TC-40, TC-44 (D-05, D-12, D-20, D-22).
7. `mode="from_template" | "new"` và loại bỏ fallback im lặng; bỏ `xlwings` khỏi đường mặc định (D-19).
8. Manifest/profile, Template lint, vùng khóa, chính sách lệch template (D-09, D-18).

### A.3. Hướng dẫn cắt lát MVP (để chia lại nhanh)

MVP của tài liệu này rộng có chủ đích. Bảng dưới là các lát độc lập về ý nghĩa, kèm phụ thuộc, để chủ sở hữu chọn thứ tự mà không phải đọc lại toàn bộ spec.

| Lát | Nội dung | FR / NFR / SEC chính | Phụ thuộc | Giá trị khi đứng riêng |
|---|---|---|---|---|
| S0 — Nền an toàn | Test hồi quy EV-01..12; Shift Manager mới (tokenizer, sheet đích); mở rộng dòng/cột; anchor; không fallback im lặng | FR-07, FR-08, FR-09, FR-17, NFR-08 | (không) | Chặn lỗi sai công thức/CF/DV đang tồn tại |
| S1 — Preflight và Diff | Inventory, Fidelity Tier T1/T3, Structural Diff, UG-02 | FR-01, FR-02, FR-14 | S0 (để so trước/sau) | Không mất thành phần âm thầm |
| S2 — Mutate đầy đủ | Manifest, lint, clone kiểu dáng, vùng khóa, lệch template | FR-03, FR-04, FR-05, FR-06, FR-21, FR-24 | S0 | Dùng được trên template thật |
| S3 — Giá trị và cache | Recalc Backend, `values_status`, Cache Writer, `calc_policy` | FR-10, FR-11, FR-16, FR-28, NFR-11, SEC-08, SEC-10 | S0 (file giao ổn định) | Mọi consumer thấy số liệu; AI biết nguồn số liệu |
| S4 — Kiểm định | UG-01..13, PG và profile `unit_test_matrix` | FR-12, FR-13, FR-15 | S1, S3 | Cổng phát hành tự động |
| S5 — Hạ tầng | `FileRef`, audit, bảo mật package, giới hạn tài nguyên | FR-22, FR-23, SEC-01..07, NFR-02..04, NFR-09, NFR-10 | (độc lập) | Vận hành an toàn, đa tenant |
| Sau MVP | `build_xlsx`, `repair_xlsx`, ước lượng hình thức, vệ sinh, thao tác xóa/gộp, Tier T2 | FR-18..20, FR-25, FR-29 | S0..S4 | Mở rộng |
| P2 | Adapter, `.xls`, VBA, Excel COM backend | FR-26, FR-27 | — | Theo nhu cầu thương mại hóa |

Thứ tự cắt gọn gợi ý nếu cần phát hành sớm: S0 → S3 → S2 → S1 → S4 → S5. Mọi lát phải giữ nguyên các cổng của 7.3 liên quan tới chính nó.

---

## Phụ lục B. Rủi ro

| ID | Rủi ro | Mức | Giảm thiểu |
|---|---|---|---|
| R-01 | openpyxl đọc-sửa-ghi có mất mát; thành phần ngoài hỗ trợ bị mất | Cao | Preflight và Fidelity Tier; T2 vá XML; T3 dừng; UG-02 phát hiện sau thao tác (D-06, D-07) |
| R-02 | Shift Manager có "đuôi dài" dạng công thức hiếm (3D, tham chiếu cấu trúc, mảng động) | Cao | Bộ tách token; fail-closed `E-SHIFT-UNSUPPORTED-FORM`; kiểm thử vi sai với Oracle; fuzz (TC-05, TC-34) |
| R-03 | LibreOffice khác Excel ở hàm hiếm/mới; tính lại cho giá trị lệch | Trung bình | Danh sách hàm không hỗ trợ; `W-CALC-*`; kiểm tra vi sai trên corpus; Excel COM là backend tùy chọn |
| R-04 | Lỗi do tác giả template (anchor mơ hồ, dòng mẫu sai chỗ, placeholder sót) | Trung bình | Template lint chỉ đọc; từ chối thay vì đoán (FR-04, 4.14) |
| R-05 | Kỳ vọng "1-shot" hoặc "đúng pixel" không đo được | Trung bình | 3.4 phân định cam kết; đo bằng corpus; ngưỡng do chủ sở hữu chốt (Q-11) |
| R-06 | Giấy phép phụ thuộc cản trở thương mại hóa | Trung bình | D-17; rà soát trước phân phối; mọi thư viện ngoài lõi nằm sau interface |
| R-07 | Tiến trình LibreOffice treo, khóa profile, chạy song song không ổn định | Trung bình | Sandbox, profile riêng mỗi tiến trình, timeout, dọn khóa (SEC-08, NFR-09, TC-26) |
| R-08 | Font server thay thế làm lệch số đo hình thức | Thấp-Trung bình | Cài font tương thích; mọi số đo hình thức gắn `estimated` (UG-08) |
| R-09 | Chi phí và độ phức tạp của runner Windows + Excel cho CI | Thấp | Phase 0 chỉ cần chạy định kỳ; hằng ngày dùng LibreOffice |
| R-10 | Host/MCP client không hỗ trợ roots hoặc `resource_link` như kỳ vọng | Trung bình | Core chỉ định nghĩa hình dạng `FileRef`; chốt cách vận chuyển ở bước tích hợp (Q-10) |
| R-11 | Phụ thuộc vào thư viện còn non trẻ (`excel-parser`) | Thấp | Chỉ là Snapshot Adapter tùy chọn sau interface; pin phiên bản; có đường dự phòng bằng openpyxl |
| R-12 | AI tin giá trị tính lại của LibreOffice như giá trị của Excel | Trung bình | `values_status` và `backend_info` luôn đi kèm; bàn giao nêu nguồn số liệu |
| R-13 | Quy tắc nằm trong markdown chỉ là khuyến nghị cho AI, không được cưỡng chế | Trung bình | Chuyển quy tắc cần bảo đảm thành UG/PG/test (7.4.b); ma trận truy vết |
| R-14 | Rò rỉ chéo tenant (file, log, profile backend, thư mục tạm) | Cao | SEC-05, SEC-08; TC-25, TC-26; audit bảo mật định kỳ |
| R-15 | Giá trị cache do backend tính (LibreOffice) khác giá trị Excel sẽ tính; cache cũ so với dữ liệu sau khi người dùng chỉnh | Trung bình | `calc_on_open` bật khi nguồn không phải Excel; `origin` trong `values_status`/`stats`; hàm biến động báo `W-CALC-VOLATILE`; Excel COM là backend tùy chọn khi cần độ trung thực cao |
| R-16 | Cache Writer làm hỏng XML hoặc ô (sai kiểu, công thức chia sẻ/mảng, ký tự đặc biệt) | Trung bình | Chỉ sửa node có `<f>`; UG-13 tự kiểm; Package Integrity; TC-38, TC-40, TC-44; không phát hành khi `E-CACHE-*` |
| R-17 | MVP rộng khó kiểm soát tiến độ | Trung bình | Hướng dẫn cắt lát A.3; ma trận truy vết Phụ lục G; mỗi lát giữ cổng chất lượng riêng |

---

## Phụ lục C. Câu hỏi mở

| ID | Câu hỏi | Ảnh hưởng |
|---|---|---|
| Q-01 | Loại template ưu tiên cho MVP: ma trận kiểm thử (`Report5`), báo cáo tài chính, danh sách nhân sự, loại khác? | Phạm vi corpus, profile PG ban đầu |
| Q-02 | **[ĐÃ CHỐT quyết định 2026-10-06]** File giao có chèn cache: áp dụng `write_cached` bằng `lxml` (D-12, EV-13). **Còn mở:** mức hỗ trợ đọc cache của consumer ngoài Excel COM và openpyxl (Mac/Web, Google Sheets, LibreOffice, WPS, trình xem trước, mobile) được đo ở Phase 0 bằng TC-39 | NFR-06, D-12, TC-39 |
| Q-03 | Mô hình lưu trữ file và tenant (cục bộ, object store, đa tenant ngay từ đầu?) | FR-22, SEC-05 |
| Q-04 | Backend tính lại mặc định khi chạy cục bộ: LibreOffice hay Excel COM (máy dev Windows có Excel)? | D-05, độ trung thực giá trị |
| Q-05 | Ngưỡng UAT (số file, tỷ lệ được duyệt) | 7.3, cổng phát hành |
| Q-06 | Chính sách retention của audit log và file | SEC-06, 7.4.a |
| Q-07 | Có cấp runner Windows + Excel cho CI/vi sai không? | D-16, TC-04, TC-13 |
| Q-08 | Có cần định dạng mở rộng ngoài `.xlsx` (`.xlsm` giữ VBA, `.ods`) và khi nào? | FR-26, D-13 |
| Q-09 | Khi gặp thành phần ngoài hỗ trợ (shape, slicer...), mặc định từ chối (T3) hay cho phép tiếp tục kèm xác nhận của người dùng? | 4.6, 4.15, WF-B |
| Q-10 | Antigravity hỗ trợ roots và `resource_link`/`resources/read` đến đâu? | 4.3, SEC-07, R-10 |
| Q-11 | Ngưỡng "1-shot" chấp nhận được trên corpus UAT | 7.3 |
| Q-12 | Dual-delivery `.xlsx` và `.xls` (quy định trong kỹ năng hiện tại) là bắt buộc hay P2? | FR-27 |
| Q-13 | Chính sách dòng mẫu còn lại sau mở rộng: xóa hay giữ mặc định (ảnh hưởng tổng hợp)? | 4.14, `W-TPL-SAMPLE-ROW` |
| Q-14 | Mô hình thương mại hóa (SaaS, cài tại chỗ, mã nguồn mở) | D-17 (giấy phép), A.1 Phase 3 |
| Q-15 | `range_policy` mặc định cho từng loại thao tác có đúng như D-04 đề xuất không? | 4.7, TC-04 |
| Q-16 | `calc_on_open` mặc định khi đã có cache: `auto` như đề xuất (bật khi cache không do Excel tính) hay luôn tắt/luôn bật? Chấp nhận hộp thoại lưu khi đóng file? | D-21, 4.8, TC-15 |
| Q-17 | Khi cả LibreOffice và Excel COM đều có sẵn, backend nào cung cấp giá trị cache mặc định? | D-05, D-21, R-15 |

---

## Phụ lục D. Đối chiếu các nhận định trước đây

Bảng này ghi lại các nhận định từ bản đồ công cụ của Gemini, báo cáo audit của Antigravity và rà soát ban đầu, kèm kết luận sau khi kiểm chứng. Mục đích: không để các nhận định chưa đúng làm sai lệch triển khai.

| # | Nhận định | Nguồn | Kết luận | Tham chiếu |
|---|---|---|---|---|
| 1 | Regex `\\$?` làm tham chiếu tuyệt đối không được dịch | Antigravity | **Sai về hậu quả.** Đoạn đó là code chết (điều kiện `not startswith("=")` luôn `False` với công thức thật); `$F$10:$F$25` được dịch đúng | EV-06 |
| 2 | 12 Quality Gates chỉ phục vụ ma trận kiểm thử | Antigravity | **Đúng** | P-06, D-08 |
| 3 | `write_xlsx` còn tạo `Workbook()` rỗng | Antigravity | **Đúng, và nặng hơn:** còn xảy ra khi `template_path` sai đường dẫn | P-07, EV-10 |
| 4 | Conditional Formatting chưa xử lý; dòng mới "trắng" | Antigravity | **Đúng nhưng nặng hơn:** CF không được dịch nên áp sai lên dòng đã đẩy xuống | P-03, EV-05 |
| 5 | Pivot Table cache bị xóa, `#REF!` | Antigravity | **Phóng đại (chưa kiểm chứng):** vấn đề chính là nguồn không giãn khi chèn dòng và pivot không tự làm mới; cần xác nhận hành vi của openpyxl | 4.6, TC-11 |
| 6 | openpyxl "mù công thức" | Antigravity, Gemini | **Đúng nhưng thiếu:** sau khi lưu, **mọi** công thức mất giá trị cache, kể cả file khách vốn có cache. **Hướng xử lý đã kiểm chứng khả thi:** ghi `<v>` bằng `lxml` (Excel COM + openpyxl) | P-05, EV-08, EV-13 |
| 7 | "AST Regex Formula Shifter xử lý 80% trường hợp" | Antigravity | **Chưa đo.** Thực nghiệm cho thấy lỗi với tên hàm, chuỗi, tên định danh và cross-sheet | P-01, P-02, EV-01..EV-04 |
| 8 | Tỷ lệ 1-shot 55-65% (và các tỷ lệ khác) | Antigravity | **Không có cơ sở đo** | P-12 |
| 9 | Combo `formulas` rồi LibreOffice | Gemini | **Thừa.** Cả hai đều tính công thức; chọn LibreOffice làm Oracle; `formulas`/`pycel` có vấn đề giấy phép cần rà soát | D-05, D-17 |
| 10 | `pyfastexcel`/`fastexcel` giúp ghi nhanh file lớn | Gemini | **Không áp dụng:** `fastexcel` là thư viện đọc; luồng template không cần tầng này | — |
| 11 | Docling làm "mắt QA" cho Excel | Gemini | **Loại khỏi core:** nặng (mô hình ML), không cần cho XLSX; kiểm bằng Inventory, tính lại và ước lượng hình thức | UG-02, UG-04, UG-08; cùng hướng với D-03 của Docx Engine |
| 12 | PyMuPDF kiểm `###` | Gemini | **Loại khỏi core:** giấy phép AGPL; dùng UG-08; trích xuất PDF (nếu cần) thuộc module Render | D-17, NFR-05 |
| 13 | `excel-parser` là công cụ trọng yếu | Gemini | **Chỉ là Snapshot Adapter tùy chọn:** chỉ đọc, không tính lại, dự án còn non trẻ | D-17, EV-11 |
| 14 | ">95% hiệu quả với 5 mảnh ghép" | Gemini | **Không có cơ sở đo** | P-12 |
| 15 | Test hiện tại pass nghĩa là engine đúng | Hàm ý trong test suite | **Không đúng:** các ca nguy hiểm (EV-01..EV-05) không được test; test phụ thuộc trạng thái | EV-09, P-12 |
| 16 | Bộ quy tắc E1..E14, `ERR_XLSX_*` đủ để bảo đảm chất lượng | Rule/Skill hiện tại | **Chưa đủ:** là hướng dẫn cho AI, không được cưỡng chế; cần chuyển thành gate/test | R-13, 7.4.b |
| 17 | Ghi cache vào XML của file giao có làm hỏng file hoặc vô hiệu công thức không (D-12 bản 1.0 còn `[CẦN KIỂM CHỨNG khả thi]`) | Bản 1.0 | **Không**, trên phạm vi đã thử: bốn kiểu `n`/`str`/`b`/`e`, Excel 16.0 COM không báo lỗi, công thức tính lại đúng, openpyxl `data_only` đọc đúng. **Chưa suy rộng** sang consumer khác, ngày/giờ, công thức chia sẻ/mảng | D-12, EV-13, TC-38..TC-40, TC-44 |
| 18 | MVP quá nặng | Bản đối chiếu 2026-10-06 | **Ghi nhận; chủ sở hữu chấp nhận** (đây là SPEC tổng thể). Giảm rủi ro bằng cắt lát A.3 và ma trận truy vết Phụ lục G | A.3, Phụ lục G, R-17 |

---

## Phụ lục E. Nhật ký bằng chứng thực nghiệm

**Môi trường EV-01..EV-12:** sandbox Linux, Python 3.12.3, openpyxl 3.1.5, LibreOffice 24.2.7.2 (headless), Pillow 12.1.1. Chưa thử trên Excel thật cho nhóm này. Ngày thực hiện: 2026-10-05. Đối tượng thử: `xlsx_writer.py` do chủ sở hữu cung cấp. **Môi trường EV-13:** Windows, `openpyxl 3.1.5`, `lxml 6.0.2`, Microsoft Excel 16.0 (COM); ngày 2026-10-06; do chủ sở hữu thực hiện và báo cáo lại, chưa được tái chạy độc lập trong phiên soạn tài liệu.

**Phạm vi rà soát tài liệu:** đọc đầy đủ `xlsx_reader.py`, `xlsx_validator.py`, `test_excel_core.py`, `rule_enterprise_document_and_spreadsheet_qa.md`, `SKILL.md`; đọc có chọn lọc các hàm trọng yếu của `xlsx_writer.py` (bộ dịch công thức, mở rộng dòng, `mutate_template_excel`, `write_xlsx`); chỉ đọc lướt cấu trúc `GEMINI.md`, `rule_excel_template_preservation_and_ux.md`, `generate_enhanced_ux_excel.py`, `format_diff_excel.py`. Chưa có template thật `Report5_Unit Test-template.xlsx`, nên chưa chạy end-to-end trên template đó.

| ID | Thử nghiệm | Kết quả quan sát |
|---|---|---|
| EV-01 | `shift_formula_string(...)`, chèn tại dòng 2, +3 dòng | `=LOG10(A5)` thành `=LOG13(A8)`; `=ATAN2(A5,B5)` thành `=ATAN5(A8,B8)`; `=BIN2DEC(A5)` thành `=BIN5DEC(A8)`; `=DAYS360(A5,B5)` thành `=DAYS363(A8,B8)` |
| EV-02 | Chèn tại dòng 12, +3 dòng | `=COUNTIF(A:A,"TC001")` thành `"TC1"`; `=COUNTIF(B10:B30,"TC020")` thành `=COUNTIF(B10:B33,"TC23")`; `=FY2024*2` thành `=FY2027*2` |
| EV-03 | Mở rộng sheet `Data` (3 dòng tại dòng 5); sheet `Stat` trỏ vào `Data` | `Stat!A1 =Data!A11` và `Stat!A2 =SUM(Data!A1:A10)` **không đổi** (đáng lẽ `A14`, `A13`); `Stat!A3 =A1*2` (cục bộ) không đổi, đúng |
| EV-04 | Mở rộng sheet `Data` (5 dòng tại dòng 1); `Data` trỏ vào `Stat` | `=Stat!A20` thành `=Stat!A25`; `=SUM(Stat!A1:A30)` thành `=SUM(Stat!A1:A35)` (dịch nhầm sheet khác) |
| EV-05 | `expand_table_rows` 5 dòng tại dòng 5 trên sheet có CF `A1:A20`, DV `B5:B20`, chiều cao dòng 15 = 40, AutoFilter `A1:A20`, Print Area, Defined Name | Tất cả **không đổi**: CF vẫn `A1:A20`; DV vẫn `B5:B20`; chiều cao 40 vẫn ở dòng 15 (dòng 20 là `None`); AutoFilter, Print Area và Defined Name vẫn `A1:A20` |
| EV-06 | `=SUM($F$10:$F$25)`, chèn tại dòng 12, +3 dòng; đọc mã | Ra `=SUM($F$10:$F$28)` (đúng). Đoạn `r"\\$?..."` trong điều kiện early-exit là code chết |
| EV-07 | Biên dải ô, chèn tại dòng 12, +3 dòng | `=SUM(A5:A11)` không đổi (không mở rộng); `=SUM(A5:A12)` thành `=SUM(A5:A15)`; `=SUM(A12:A20)` thành `=SUM(A12:A23)` (mở rộng, không dịch cả dải như Excel) |
| EV-08 | Lưu bằng openpyxl rồi đọc `data_only=True`; chuyển bản sao qua LibreOffice | Giá trị cache của `=SUM(A1:A2)` là `None`; bản sao do LibreOffice tính lại cho `12`. Lần chạy đầu không chỉ định profile riêng không sinh file; chạy lại với `-env:UserInstallation=...` thì thành công |
| EV-09 | Chạy `test_excel_core.py` hai lần liên tiếp | Lần 1 (thư mục sạch): 7 test, 1 fail (`test_headless_openpyxl_reader`) và 1 error (`test_12_quality_gates_validator`). Lần 2 (đã có file do test khác tạo): 7 test đạt. Kết quả phụ thuộc trạng thái và thứ tự |
| EV-10 | Đọc mã | `write_xlsx` rơi về `Workbook()` rỗng khi `template_path` thiếu/sai; `read_xlsx(engine="auto")` thử `xlwings` trước và nuốt mọi ngoại lệ; `cell_sig` bỏ qua `wrap_text` và màu chữ, so màu fill chỉ khi kiểu `rgb`; test vòng đời xác nhận dòng mẫu bị đẩy xuống và còn trong file (được tính vào `SUM`) |
| EV-11 | Xem trang GitHub `knowledgestack/excel-parser` (trang tài liệu riêng chưa được xem) | Giấy phép MIT; thư viện **chỉ đọc**; phụ thuộc `openpyxl`, `pydantic`, `lxml`, `xxhash`, `tiktoken`; 74 sao, 32 commit khi xem; README nêu không tính lại công thức, pivot chỉ nhận diện, không trích sparkline, không chạy macro; benchmark tự báo cáo, đo khả năng truy xuất cho RAG, không đo độ trung thực khi sửa file |
| EV-12 | Gán chuỗi bắt đầu bằng `=` vào ô openpyxl | `data_type` là `f` (công thức), kể cả chuỗi như `=cmd|' /C calc'!A0` |
| EV-13 | Tiêm giá trị cache bằng `lxml` vào `xl/worksheets/sheet1.xml` của file do openpyxl lưu: `A3 =SUM(A1:A2)` (`<v>30</v>`), `B1 =IF(A1>5,"Pass","Fail")` (`t="str"`), `C1 =A1>5` (`t="b"`, `<v>1</v>`), `D1 =1/0` (`t="e"`, `<v>#DIV/0!</v>`) | `openpyxl data_only=True` đọc `30` (`int`), `'Pass'`, `True`, `'#DIV/0!'`. Excel 16.0 COM mở không báo lỗi, đọc `30.0`, `"Pass"`, `True`, `#DIV/0!`; đổi `A1` thành `100` rồi `Calculate()` thì `A3` thành `120.0` (công thức còn sống). **Chưa thử:** Excel Mac/Web, Google Sheets, LibreOffice, WPS, trình xem trước, mobile, `pandas`, ngày/giờ, công thức chia sẻ/mảng, `fullCalcOnLoad` kèm cache, file lớn |

---

## Phụ lục F. Khoảng cách giữa hiện trạng và đích

| Thành phần hiện có | Đích | Hành động |
|---|---|---|
| `clone_cell_style`, `sync_merged_borders` | FR-06 | Giữ; bổ sung `protection` và kiểm UG-05 |
| `shift_formula_string`, `shift_formulas_in_sheet` | FR-07 | **Viết lại** bằng bộ tách token; thêm sheet đích; quét toàn workbook (D-03) |
| `expand_table_rows`, `expand_table_columns` | FR-07 | Giữ phần merge/chart; chuyển phần dịch sang Shift Manager; thêm CF, DV, bảng, AutoFilter, vùng in, tên, chiều cao dòng |
| `find_anchor` | FR-08 | Giữ; thêm phát hiện mơ hồ/thiếu (`E-TPL-ANCHOR-*`) |
| `relink_and_reanchor_charts` | FR-17 | Giữ; mở rộng test (nhiều series, sheet khác) |
| `auto_fit_layout` | FR-18 | Giữ như ước lượng; gắn `estimated`; để Excel tự co dòng khi không merge `[CẦN KIỂM CHỨNG]` |
| `mutate_template_excel` | FR-05 | Bọc bằng Preflight, vùng khóa, `range_policy`, Structural Diff, recalc |
| `safe_set_cell` | FR-09 | Giữ; thêm vùng khóa và chính sách chuỗi `=` |
| `write_xlsx` | FR-05, FR-19 | Thay bằng `mode="from_template" \| "new"`; bỏ fallback im lặng (D-19) |
| `read_xlsx` | FR-16 | Bỏ `xlwings` khỏi `auto`; thêm `values_status` kèm `origin`; Snapshot Adapter tùy chọn |
| `validate_excel_sheet` (12 gate) | FR-12, FR-13 | Tách UG và profile `unit_test_matrix` (D-08); sửa `cell_sig` (P-06) |
| `test_excel_core.py` | TC-01..TC-37 | Làm test độc lập; thêm các ca EV-01..EV-12; thêm corpus và vi sai |
| `rule_*.md`, `SKILL.md` | 7.4.b, R-13 | Giữ làm hướng dẫn cho AI; quy tắc cần bảo đảm chuyển thành gate/test; cập nhật theo spec này |
| `generate_enhanced_ux_excel.py`, `format_diff_excel.py` | — | Chưa rà soát đầy đủ; xác định ở Phase 0 phần nào chuyển thành profile/tool |
| (chưa có) Cache Writer | FR-28, D-22 | **Viết mới** bằng `lxml`: ghi `<v>`/`t` cho ô công thức theo bảng ánh xạ kiểu (4.8); tự kiểm UG-13; chuyển các ca EV-13 thành TC-38..TC-40, TC-44 |
| (chưa có) thao tác xóa/gộp/DV/CF/tên | FR-29, D-23 | **Viết mới** trên Shift Manager; `E-SHIFT-ORPHAN`; TC-41, TC-42 |
| (chưa có) anchor `kind`/`scope`, cột theo tên header | D-24 | Mở rộng `find_anchor` và `id_columns`; giữ bí danh dạng cũ; TC-43 |


---

## Phụ lục G. Ma trận truy vết (FR / NFR / SEC ↔ module ↔ TC)

Quy tắc: mục nào thiếu một trong ba cột là khoảng trống phải xử lý trước phát hành (7.4.b). Mục P2 chưa có TC được đánh dấu rõ.

| Yêu cầu | Module (4.2) | Ca kiểm thử | Ghi chú |
|---|---|---|---|
| FR-01 Preflight/Inventory | Preflight Scanner | TC-10, TC-11, TC-12 | |
| FR-02 Fidelity Tier | Preflight Scanner, OOXML Package Helper | TC-10, TC-11 | T2 (P1) |
| FR-03 Registry + manifest | Template Service | TC-18, TC-19 | |
| FR-04 Template lint | Template Service | TC-18 | |
| FR-05 Mutate template | Dual-Path Builder | TC-16, TC-22, TC-23, TC-34, TC-35 | |
| FR-06 Clone kiểu dáng | Style & Layout | TC-07, TC-09, TC-20 | |
| FR-07 Shift Manager | Shift Manager | TC-01..TC-06, TC-34 | Vi sai: TC-03, TC-04 |
| FR-08 Semantic Anchor | Template Service, Shift Manager | TC-18, TC-43 | |
| FR-09 Xác thực đầu vào | Input Validation | TC-16, TC-17 | |
| FR-10 Recalc Backend | Recalc & Cache Writer, Sandbox | TC-13, TC-14, TC-26 | |
| FR-11 Trạng thái giá trị/cờ tính lại | Recalc & Cache Writer | TC-15, TC-29 | |
| FR-12 Cổng chung UG | Validators | TC-12, TC-19, TC-20, TC-38 | UG-13: TC-38, TC-44 |
| FR-13 Cổng profile PG | Validators | TC-19 | |
| FR-14 Structural Diff | Validators | TC-12 | |
| FR-15 Diagnostics | Diagnostics Builder | TC-30 | |
| FR-16 Inspect cho AI | Template Service / Inspect | TC-29 | |
| FR-17 Chart relink | Style & Layout, Shift Manager | TC-08 | |
| FR-18 Ước lượng hình thức | Style & Layout | TC-28 | P1 |
| FR-19 Path B | Dual-Path Builder | TC-21 | P1 |
| FR-20 Repair | Dual-Path Builder | TC-37 | P1 |
| FR-21 Chính sách lệch template | Input Validation, Style & Layout | TC-22 | |
| FR-22 `FileRef` | File Store | TC-25 | |
| FR-23 Audit log | Audit Log | TC-32 | |
| FR-24 Tiếng Việt, định danh | Input Validation | TC-17, TC-28 | |
| FR-25 Vệ sinh tài liệu | Preflight Scanner, Validators | TC-45 | P1 |
| FR-26 Điểm mở rộng | — | (P2: bổ sung TC khi triển khai) | Khoảng trống có chủ đích |
| FR-27 Xuất `.xls` | — | (P2: bổ sung TC khi triển khai) | Khoảng trống có chủ đích |
| FR-28 Cache Writer | Recalc & Cache Writer | TC-38, TC-39, TC-40, TC-44 | |
| FR-29 Xóa/gộp/DV/CF/tên | Shift Manager, Dual-Path Builder | TC-41, TC-42 | P1 |
| NFR-01 Tất định | Tất cả | TC-27 | |
| NFR-02 Giới hạn tài nguyên | API & Policy | TC-46 | |
| NFR-03 Cách ly Recalc | Sandbox | TC-26 | |
| NFR-04 Quan sát được | API & Policy, Audit Log | TC-32 | |
| NFR-05 Ranh giới Render | (kiến trúc) | Rà soát thiết kế | Không có TC chạy được |
| NFR-06 Ma trận consumer | Oracle/Compatibility | TC-36, TC-39 | |
| NFR-07 Hiệu năng | Tất cả | TC-31 | |
| NFR-08 Không phá hủy | Dual-Path Builder | TC-23 | |
| NFR-09 An toàn song song | Sandbox | TC-26 | |
| NFR-10 Mã thoát CI | API & Policy | TC-46 | |
| NFR-11 Cache đúng kiểu | Recalc & Cache Writer | TC-38, TC-40, TC-44 | |
| SEC-01 ZIP/XML an toàn | Preflight Scanner | TC-24 | |
| SEC-02 Macro | Preflight Scanner | TC-24 | |
| SEC-03 Liên kết ngoài/OLE | Preflight Scanner | TC-24 | |
| SEC-04 Đầu vào không tin cậy | Input Validation | TC-16 | |
| SEC-05 Cách ly tenant | File Store | TC-25 | |
| SEC-06 Audit che dữ liệu | Audit Log | TC-32 | |
| SEC-07 Roots / URI mờ | File Store | TC-25 | |
| SEC-08 Sandbox Recalc | Sandbox | TC-26 | |
| SEC-09 Advisory và giấy phép | (quy trình) | Audit bảo mật 7.4.c | Không có TC chạy được |
| SEC-10 Giá trị cache không tin cậy | Recalc & Cache Writer | TC-44 | |
