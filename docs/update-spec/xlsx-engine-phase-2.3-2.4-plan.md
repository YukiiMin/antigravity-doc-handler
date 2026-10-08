# Xlsx Engine MCP — Kế Hoạch Thực Thi Phase 2.3 & 2.4 (Execution Slice)

| Thuộc tính | Giá trị |
|---|---|
| Tài liệu | Kế hoạch thực thi chi tiết (Execution Slice) — Phase 2.3 & Phase 2.4 |
| Phiên bản | 1.0 (Bản trích kỹ thuật, đồng bộ v1.2) |
| Ngày | 2026-10-08 |
| Nguồn sự thật (SSOT) | [xlsx-engine-mcp-plan-v1.2.md](xlsx-engine-mcp-plan-v1.2.md) |
| Master Plan đồng bộ | [ai_native_toolkit_modular_architecture_plan.md](../ai_native_toolkit_modular_architecture_plan.md) |
| Trạng thái | Approved Baseline (Sẵn sàng triển khai mã nguồn) |

---

## 1. Nguyên Tắc Nền Tảng & Thứ Bậc Nguồn Sự Thật (SSOT)

1. **Thứ bậc ưu tiên tuyệt đối**:
   - [xlsx-engine-mcp-plan-v1.2.md](xlsx-engine-mcp-plan-v1.2.md) là **Nguồn Sự Thật Duy Nhất (SSOT)** về quyết định kỹ thuật (`D-*`), yêu cầu chức năng (`FR-*`), cổng kiểm định (`UG-*`), và ca kiểm thử (`TC-*`).
   - Tài liệu này là **Execution Slice** (bản trích lát cắt thực thi): Ánh xạ nhiệm vụ cụ thể của Phase 2.3 và Phase 2.4 sang các mã định danh của `v1.2`. Tuyệt đối không tự định nghĩa lại khái niệm. Nếu có bất kỳ mâu thuẫn nào: **v1.2 THẮNG**.
2. **Kỷ luật Tool-First (Nguyên tắc 11-12, D-25)**:
   - Mọi thao tác đọc/ghi `.xlsx` của AI phải đi qua tool MCP. Mã Python do agent tự chạy chỉ ở mức phụ trợ (tính toán, thống kê trên dữ liệu đã trích xuất).
   - Mọi trường hợp agent thay thế một thao tác `.xlsx` bằng Python được tính là một **Tool Gap** và ghi vào **Tool Gap Register**.
   - Chỉ số **Escape Rate** = (số bước xlsx làm ngoài tool) / (tổng số bước xlsx).
   - Ca nào chỉ đạt ở chế độ `tool_plus_shell` mà không đạt ở `tool_only` được tính là **FAIL của tool**, không phải PASS.
3. **Quy tắc đường dẫn tương đối**:
   - Toàn bộ liên kết trong tài liệu sử dụng đường dẫn tương đối chuẩn repo; không dùng đường dẫn tuyệt đối.

---

## 2. Bằng Chứng Thực Nghiệm Mới: EV-15 (Phiên Test Report5 ngày 2026-10-07)

* **Môi trường đo**: Windows 11, Python 3.13, `openpyxl 3.1.5`, `lxml 6.0.2`, Microsoft Excel 16.0 COM (test trên `Report5_Unit-Test-1.xlsx` và `Report5_Unit-Test-1_tested.xlsx`).
* **Các phát hiện thực nghiệm ghi nhận**:
  1. `openpyxl.copy_worksheet()` **làm rơi hoàn toàn Data Validation** (`len(ws.data_validations) = 0`), khiến các ô chọn dropdown (như dấu tích `O`, `N,A,B`, `P,F`) biến thành text thường không có mũi tên sổ xuống.
  2. Bảng `Statistics` của template gốc vốn dĩ đã bị đứt gãy viền (dòng 12 có đủ viền `hair`, dòng 13..18 khuyết viền cột B, C; dòng 19..21 mất sạch viền B..I). Khi AI xóa chuỗi `#REF!`, các khoảng trống không viền lộ diện.
  3. Sheet mẫu `Return(Staff)` trong dataset gốc chứa lỗi gõ nhầm công thức: `-AA7` (ô rỗng = 0) thay vì `-O7` (ô chứa tổng số test cases), khiến chỉ số `Lack of test cases` tính sai thành số dương (+12, +15) dù đã viết đủ 22 test cases.

---

## 3. Lộ Trình Chi Tiết Phase 2.3: Comprehensive Inspect & Knowledge Catalog

Phase 2.3 tập trung vào năng lực "nhìn và hiểu toàn diện" bảng tính mà không can thiệp sửa file, phân rã thành 4 lát cắt độc lập để tối ưu token:

```
[2.3a Inspect Lõi & Coverage] ──► [2.3b Formula Analyzer] ──► [2.3c Format Describer] ──► [2.3d Function Registry & Fx]
```

### 2.3a. Inspect Lõi & Coverage Report
* **Công cụ**: `xlsx.inspect(level)` mở rộng + `xlsx.coverage_report`.
* **Nhiệm vụ**:
  - Hỗ trợ 4 cấp độ ban đầu: `summary`, `structure`, `objects`, `cells`.
  - Gom nhóm đối tượng (merged cells, shapes, images, comments) kèm dải RLE và phân trang. Cờ `truncated: true` bắt buộc khi dữ liệu bị cắt.
  - Xuất **Coverage Matrix** hiện hành theo 5 trạng thái chuẩn: `READ_WRITE`, `READ_ONLY`, `PRESERVE_ONLY`, `DETECT_ONLY`, `UNSUPPORTED` (Phụ lục I của `v1.2`).
* **Ánh xạ v1.2**: `FR-30`, `FR-36`, `D-26`, `D-28`.
* **Ca kiểm thử**: `TC-47` (inspect phân tầng), `TC-54` (coverage matrix), `TC-58` (token efficiency).

### 2.3b. Formula Analyzer
* **Công cụ**: `xlsx.analyze_formulas`.
* **Nhiệm vụ**:
  - Gom nhóm công thức theo **mẫu R1C1 chuẩn hóa** (1.000 công thức cùng logic gom thành 1 dòng; chỉ liệt kê các ô phá mẫu `W-FORMULA-PATTERN-BREAK`).
  - Phân loại hàm, rủi ro, đồ thị phụ thuộc chéo sheet, phát hiện chu trình (`W-FORMULA-CIRCULAR`).
  - Cảnh báo xác định: `W-FORMULA-EMPTY-CELL-REF` khi công thức tham chiếu ô rỗng tại thời điểm build (bài học EV-15).
* **Ánh xạ v1.2**: `FR-31`, `D-26`.
* **Ca kiểm thử**: `TC-48` (gom nhóm R1C1), `TC-49` (chu trình), `TC-61` (hồi quy tham chiếu ô rỗng).

### 2.3c. Format Describer
* **Công cụ**: `xlsx.describe_formats`.
* **Nhiệm vụ**:
  - Phân loại toàn bộ định dạng theo 12 lớp số (General, Number, Currency, Accounting, Date, Time, Percentage, Fraction, Scientific, Text `@`, Special, Custom).
  - Phân tích Font phân vùng, Fill, 4 cạnh Border, Alignment, CF (18 loại), DV (7 loại).
  - Bảng style duy nhất (mỗi `xfId` một lần) + ánh xạ RLE style-id. Phân giải màu theme/indexed kèm tint.
* **Ánh xạ v1.2**: `FR-33`, `D-26`.
* **Ca kiểm thử**: `TC-52` (format describer toàn diện), `TC-53` (phân giải theme color), `TC-60` (hồi quy lủng viền).

### 2.3d. Function Registry & Ma Trận Fx Vi Sai
* **Công cụ**: `xlsx.function_catalog`.
* **Nhiệm vụ**:
  - Xây dựng Function Registry riêng có phiên bản (độc lập `openpyxl.utils.FORMULAE` cũ theo EV-14), có bản ghi cho các hàm hiện đại: `XLOOKUP`, `FILTER`, `TEXTJOIN`, `IFS`, `SWITCH`, `LET`, `LAMBDA`, `STDEV.S`, `AGGREGATE`...
  - Chỉ ghi nhận trạng thái là "có bản ghi registry". Trạng thái "hỗ trợ" chỉ công bố khi có kết quả đo ma trận vi sai qua runner Excel COM / LibreOffice (`MATCH`, `DIFF`, `UNSUPPORTED_BACKEND`, `NOT_TESTED`).
* **Ánh xạ v1.2**: `FR-32`, `D-27`.
* **Ca kiểm thử**: `TC-50` (ma trận vi sai Fx), `TC-51` (cảnh báo hàm ngoài registry `W-FX-UNKNOWN`).

---

## 4. Lộ Trình Chi Tiết Phase 2.4: Enforcement, Parity Cloner & Controlled Mutation

Tuân thủ nghiêm ngặt thứ tự kỹ thuật: Viết test hồi quy trước $\rightarrow$ sửa cloner $\rightarrow$ cổng kiểm định chỉ phát hiện $\rightarrow$ vá viền theo policy $\rightarrow$ write catalog $\rightarrow$ benchmark A/B.

```
[2.4.1 Test Hồi Quy EV-15] ──► [2.4.2 Sheet Cloner Parity] ──► [2.4.3 Cổng UG-14/15/16 (Chỉ Phát Hiện)]
                                                                           │
[2.4.6 Benchmark A/B]  ◄────── [2.4.5 Write Catalog] ◄──────── [2.4.4 Border Auto-Repair Policy]
```

### 2.4.1. Bộ Test Hồi Quy Cho 3 Lỗi Thật EV-15
* **Nhiệm vụ**: Viết trước các ca kiểm thử tự động thất bại (failing tests) để khóa chặt 3 lỗi phát hiện từ phiên test Report5:
  - `TC-59`: Kiểm tra rơi Data Validation và các đối tượng khi clone sheet.
  - `TC-60`: Kiểm tra phát hiện bảng bị khuyết viền `hair` ở các dòng dữ liệu dưới.
  - `TC-61`: Kiểm tra phát hiện công thức tham chiếu ô rỗng (`-AA7`).
* **Ánh xạ v1.2**: `EV-15`.

### 2.4.2. Sheet Cloner Parity Engine
* **Nhiệm vụ**:
  - Sửa lỗi ở nguồn: Khắc phục triệt để lỗ hổng của `openpyxl.copy_worksheet()` bằng cách sao chép độc lập toàn bộ các họ đối tượng: Data Validation, Conditional Formatting, ảnh, chart, bảng, freeze panes, print area.
  - Tự động trỏ lại công thức tự tham chiếu sheet nguồn sang sheet mới (ví dụ: `'Return(Staff)'!A1` $\rightarrow$ `'NewSheet'!A1`).
* **Ánh xạ v1.2**: `D-23`, `FR-29`, `FR-35`.
* **Ca kiểm thử**: `TC-59` (PASS sau khi sửa), `TC-41`.

### 2.4.3. Bộ Cổng Kiểm Định Mở Rộng (Chỉ Phát Hiện, Không Sửa Ngầm)
* **Nhiệm vụ**:
  - **UG-14 (Validation & Object Parity Gate)**: Phát hiện nếu sheet mới bị rơi mất Data Validation/CF so với sheet tham chiếu (`E-XLSX-UG14-VALIDATION-DROPPED`).
  - **UG-15 (Table Border Consistency Gate)**: Quét dải bảng biểu, phát hiện các ô bị khuyết viền so với dòng mẫu (`W-XLSX-UG15-INCONSISTENT-BORDERS`).
  - **UG-16 (Formula Deterministic Anomaly Gate)**: Chỉ bắt quy tắc xác định `W-FORMULA-EMPTY-CELL-REF` (công thức toán học tham chiếu vào ô rỗng tại thời điểm build). Các quy tắc suy đoán ngữ nghĩa khác gắn nhãn `estimated` và không được phép chặn build.
* **Ánh xạ v1.2**: `UG-14`, `UG-15`, `UG-16`.
* **Ca kiểm thử**: `TC-59`, `TC-60`, `TC-61`.

### 2.4.4. Table Border Repair Bằng Policy Tường Minh
* **Nhiệm vụ**:
  - Tôn trọng tuyệt đối nguyên tắc "Template là chân lý" (Mục 3.1, 4.15 của `v1.2`).
  - Tuyệt đối không tự ý vá ngầm viền ô. Chỉ vá khi: (1) Được bật bằng policy tường minh trong spec (`border_policy: inherit_prototype`); (2) Suy ra xác định được từ Prototype Row hoặc sheet anh em; (3) Ghi nhận vào diff cấu trúc là thay đổi được khai báo (`declared`).
* **Ánh xạ v1.2**: `D-04`, `FR-06`, `FR-14`.
* **Ca kiểm thử**: `TC-60`, `TC-44`.

### 2.4.5. Extended Write Catalog
* **Nhiệm vụ**:
  - Mở rộng các thao tác ghi có schema và token Pydantic: `set_format`, `set_validation`, `set_conditional_format`, `table_resize`, `copy_sheet`.
  - Mọi thao tác đều có round-trip test (ghi rồi inspect lại khớp 100%).
* **Ánh xạ v1.2**: `FR-35`.
* **Ca kiểm thử**: `TC-55`.

### 2.4.6. Benchmark A/B Framework & Thoát Khỏi Tool (Escape Rate)
* **Nhiệm vụ**:
  - **Chốt Q-18 & Q-19**: Định nghĩa bộ tác vụ mẫu và cơ chế đọc log phiên để đo Escape Rate.
  - Chạy so sánh hai chế độ trên cùng bộ tác vụ: `tool_only` (AI chỉ dùng tool MCP) vs `tool_plus_shell`.
  - Mỗi tác vụ chạy lặp lại $N \ge 3$ lần trên môi trường sạch, báo cáo cả giá trị trung bình và phương sai (do tính không tất định của LLM).
  - Xuất báo cáo kiểm thử trung thực theo đúng mẫu Phụ lục H của `v1.2`.
* **Ánh xạ v1.2**: `D-25`, `D-30`, `FR-37`, `Q-18`, `Q-19`.
* **Ca kiểm thử**: `TC-56`, `TC-57`.

---

## 5. Bảng Ánh Xạ Truy Vết Đầy Đủ (Traceability Matrix)

| Tiểu bước | Thành phần triển khai trong `doctools/` | Yêu cầu `v1.2` | Quyết định `v1.2` | Cổng kiểm định | Ca kiểm thử |
|---|---|---|---|---|---|
| **2.3a** | `operations/xlsx/inspect_ops.py`, `core/xlsx/inspect/` | `FR-30`, `FR-36` | `D-26`, `D-28` | — | `TC-47`, `TC-54`, `TC-58` |
| **2.3b** | `core/xlsx/inspect/formula_profiler.py` | `FR-31` | `D-26` | — | `TC-48`, `TC-49`, `TC-61` |
| **2.3c** | `core/xlsx/inspect/format_profiler.py` | `FR-33` | `D-26` | — | `TC-52`, `TC-53`, `TC-60` |
| **2.3d** | `core/xlsx/template/function_registry.py` | `FR-32` | `D-27` | — | `TC-50`, `TC-51` |
| **2.4.1** | `tests/test_xlsx/test_regression_ev15.py` | `EV-15` | — | — | `TC-59`, `TC-60`, `TC-61` |
| **2.4.2** | `core/xlsx/mutate/style_cloner.py` | `FR-29`, `FR-35` | `D-23` | — | `TC-59`, `TC-41` |
| **2.4.3** | `gates/xlsx/universal_gates.py` | `FR-12` | — | `UG-14`, `UG-15`, `UG-16` | `TC-59`, `TC-60`, `TC-61` |
| **2.4.4** | `core/xlsx/mutate/mutator.py` | `FR-06`, `FR-14` | `D-04` | `UG-15` | `TC-60`, `TC-44` |
| **2.4.5** | `operations/xlsx/mutate_ops.py` | `FR-35` | `D-14` | — | `TC-55` |
| **2.4.6** | `tests/benchmark/test_ab_benchmark.py` | `FR-37` | `D-25`, `D-30` | — | `TC-56`, `TC-57` |

---

## 6. Phụ Lục: Mẫu Báo Cáo Kiểm Thử Trung Thực (Theo Phụ Lục H của v1.2)

Mỗi lần chạy nghiệm thu hoặc kiểm thử cùng AI Antigravity, báo cáo bắt buộc phải tuân theo mẫu:

```markdown
### Báo Cáo Kiểm Thử Trung Thực — [Tên Bộ Tác Vụ]

1. Môi trường: OS, Python, openpyxl, lxml, LibreOffice/Excel COM, Commit hash.
2. Chế độ: tool_only / tool_plus_shell (Model: Gemini / Claude / GPT).
3. Phạm vi: Danh sách TC đã chạy.
4. Kết quả theo ca: PASS / FAIL / SKIPPED kèm bằng chứng diff / hash.
   *Lưu ý: Ca nào đạt ở tool_plus_shell mà không đạt ở tool_only ghi là FAIL của tool.*
5. Mục CHƯA THỬ: Liệt kê rõ các tính năng, hàm Fx hoặc consumer chưa đo.
6. Đo lường: Độ chính xác, Token tiêu thụ, Thời gian thực thi, Escape Rate.
7. Tool Gap mới: Danh sách tính năng agent phải thoát ra ngoài tool để làm.
8. Kết luận: Tuyên bố trung thực trong phạm vi bằng chứng, không suy rộng.
```
