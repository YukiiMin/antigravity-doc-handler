# Docx Engine MCP — Kế hoạch Nền tảng (Foundation Plan)

| Thuộc tính | Giá trị |
|---|---|
| Tài liệu | Foundation Plan — Core Engine cho tài liệu Word (.docx) |
| Phiên bản | 1.1 (Baseline để đối chiếu và triển khai) |
| Ngày | 2026-10-05 |
| Chủ sở hữu | Minh |
| Trạng thái | Draft chờ phê duyệt baseline |
| Phạm vi tài liệu | Core engine (MCP Server). Không bao gồm cách tích hợp vào Antigravity và không bao gồm module PDF |

## Lịch sử thay đổi

| Phiên bản | Nội dung |
|---|---|
| 1.0 | Bản baseline đầu tiên |
| 1.1 | Tích hợp 5 đánh giá bổ sung: (1) quy tắc ghép run khi có `w:proofErr` (FR-02, mục 4.14); (2) `style_conflict_policy` khi ghép tài liệu (FR-06, mục 4.13, D-15); (3) Tag Order Registry sinh từ XSD và đính chính mức nghiêm ngặt theo container (D-06, mục 4.7); (4) `FileRef` là đối tượng URI mờ, tách chiều vào/ra (FR-15, mục 4.3, D-10); (5) chính sách trường động/TOC, engine tự phát hiện thay vì cờ khai báo (D-08, D-16, FR-12, mục 4.8). Thêm TC-25..TC-29, R-09, R-10, Q-09, Q-10 |

## Cách đọc tài liệu này (dành cho người và AI)

- Mỗi yêu cầu có **mã định danh** để đối chiếu: `FR-xx` (chức năng), `NFR-xx` (phi chức năng), `SEC-xx` (bảo mật), `TC-xx` (ca kiểm thử), `D-xx` (quyết định thiết kế), `R-xx` (rủi ro), `Q-xx` (câu hỏi mở).
- Mức ưu tiên: **MVP** (bắt buộc cho bản đầu), **P1** (làm ngay sau MVP), **P2** (mở rộng).
- Nhãn `[CẦN KIỂM CHỨNG]`: nhận định kỹ thuật chưa được xác nhận bằng thực nghiệm; phải chốt trong Phase 0 (xem Phụ lục A).
- Nhãn `[ĐỀ XUẤT]`: con số hoặc lựa chọn do tài liệu này đề xuất, chưa được chủ sở hữu phê duyệt.
- Khi mâu thuẫn, thứ tự ưu tiên: Mục 3 (Nguyên tắc và Quyết định) > Mục 4 (Kiến trúc) > các mục còn lại.

## Tóm tắt điều hành

Docx Engine là một **MCP Server tất định (deterministic)** chuyên tạo, sửa, kiểm tra tài liệu Word. AI (Antigravity) là **client**: quyết định nội dung và xử lý ngoại lệ. Engine **không tự gọi AI**, **không đo layout bằng render**. Thay vào đó, engine:

1. Dựng file qua hai đường: template (docxtpl) hoặc DocSpec JSON (tạo từ đầu).
2. Áp các ràng buộc ngữ nghĩa OOXML phòng ngừa lỗi layout (`keepNext`, `cantSplit`, `tblHeader`...).
3. Mọi thao tác ghi XML đi qua một **Schema Helper** duy nhất, sau đó kiểm tra hợp lệ OOXML.
4. Trả về file kèm **báo cáo chẩn đoán có cấu trúc** để AI tự quyết định bước tiếp theo.
5. Cưỡng chế tính bất biến của nội dung pháp lý/số liệu ở phía engine, không dựa vào prompt.

Engine cam kết **tính hợp lệ cấu trúc**, không cam kết số trang hay hình thức cuối cùng trong Word (xem 3.4).

---

## 1. Context

### 1.1. Bối cảnh

- Cần một bộ công cụ để AI Antigravity làm việc với tài liệu văn phòng, trọng tâm là Word `.docx` (hợp đồng, biên bản, báo cáo, biểu mẫu).
- Bộ công cụ được đóng gói dưới dạng MCP, trong đó engine là server và AI là client.
- Môi trường sử dụng chính là tiếng Việt, mở file bằng Word (và các trình đọc khác ở mức hỗ trợ khác nhau, xem NFR-06).

### 1.2. Phạm vi

| Trong phạm vi (In scope) | Ngoài phạm vi (Out of scope) |
|---|---|
| Tạo, sửa, ghép, kiểm tra, kiểm định `.docx` | Cách cắm vào Antigravity (cấu hình, transport MCP) |
| Template Word dùng Jinja (docxtpl) và DocSpec JSON | Module PDF (có core engine riêng, phát triển sau) |
| Ràng buộc layout bằng thuộc tính OOXML | Bảo đảm số trang/vị trí ngắt trang trong Word |
| Cưỡng chế nội dung bất biến, vệ sinh tài liệu, audit | Vòng lặp tự sửa dựa trên render, sensor thị giác (Docling) |
| Điểm mở rộng cho định dạng khác (FR-18) | Triển khai các định dạng khác ngoài `.docx` trong bản đầu |

### 1.3. Mối quan hệ với PDF

PDF chỉ là **chức năng chuyển đổi hỗ trợ từ `.docx`**, thuộc module riêng. Core chỉ định nghĩa **ranh giới giao tiếp** (NFR-05): module PDF nhận tham chiếu file `.docx` và trả về tham chiếu file PDF kèm số liệu layout (nếu có). Core không phụ thuộc dxpdf/Skia/Rust.

### 1.4. Thuật ngữ

| Thuật ngữ | Nghĩa |
|---|---|
| OOXML | Định dạng XML của `.docx` (ECMA-376 / ISO/IEC 29500) |
| DocSpec | Mô tả tài liệu dạng JSON có schema, để AI tạo tài liệu từ đầu |
| Manifest | Tệp mô tả kèm mỗi template: biến, kiểu, trường bất biến, chính sách layout |
| Guard | Thuộc tính OOXML ép Word xử lý ngắt trang/dòng/bảng đúng ý |
| Schema Helper | Lớp duy nhất được phép ghi XML, bảo đảm đúng thứ tự phần tử theo schema |
| FileRef | Đối tượng tham chiếu file `{uri, sha256, size, mime, expires_at}` với URI mờ, thay cho việc truyền byte |
| Anchor | Định danh ổn định của một đoạn/bảng để AI trỏ lại giữa các lần gọi |
| Diagnostics | Báo cáo lỗi/cảnh báo có cấu trúc do engine trả về |
| Oracle | Phần mềm tham chiếu (Word thật, LibreOffice) dùng trong CI để kiểm chứng, không dùng ở runtime |

### 1.5. Giả định và ràng buộc

- Stack lõi: Python với `python-docx`, `docxtpl` (Jinja2), `docxcompose`, `Pydantic v2`, `lxml`.
- Người dùng doanh nghiệp tự sửa template trong Word, không có kiến thức lập trình (cần linter, xem FR-01).
- Nội dung có thể gồm văn bản pháp lý và dữ liệu tài chính (cần cưỡng chế bất biến, xem FR-13).
- Giấy phép các phụ thuộc phải được kiểm tra trước khi phân phối `[CẦN KIỂM CHỨNG]` (theo ghi nhận hiện tại, `docxtpl` là LGPL).

---

## 2. Problem

| ID | Vấn đề | Hệ quả nếu không giải quyết |
|---|---|---|
| P-01 | Đầu ra của LLM không tất định, trong khi Word rất nghiêm ngặt về cấu trúc XML (thứ tự phần tử con, id duy nhất) | File mở lên báo "Repair"/"unreadable content", mất niềm tin |
| P-02 | Template do người dùng sửa trong Word làm thẻ Jinja bị băm thành nhiều run | Render lỗi hoặc im lặng cho kết quả sai |
| P-03 | Template và dữ liệu là bề mặt tấn công: SSTI trong Jinja, chèn XML, zip bomb, XXE, rò rỉ metadata/nội dung cũ | Thực thi mã, hỏng file, lộ thông tin giữa khách hàng |
| P-04 | AI có xu hướng "cắt/tóm tắt" để vừa trang, kể cả điều khoản pháp lý và số liệu | Sai lệch nội dung có hiệu lực pháp lý |
| P-05 | Lỗi layout phổ biến: heading mồ côi cuối trang, dòng bảng bị cắt, header bảng không lặp, khối chữ ký tách trang | Tài liệu thiếu chuyên nghiệp |
| P-06 | Layout cuối cùng do Word quyết định (phụ thuộc phiên bản, font, máy); không engine nào khác tái tạo chính xác tuyệt đối | Không thể bảo đảm số trang; mọi cam kết "đúng 100%" là sai |
| P-07 | Trường động (TOC, PAGEREF, tham chiếu chéo) cần số trang thật mà phía Python không tính được; tắt `updateFields` thì số trang sai/trống, bật thì Word hiện hộp thoại | Mục lục sai/trống, hoặc trải nghiệm mở file bị gián đoạn |
| P-08 | Tạo từ đầu và sửa tài liệu có sẵn thiếu API an toàn; `python-docx` không phủ numbering nhiều cấp, footnote, trường, tracked changes | Phải viết OXML thủ công, dễ hỏng file |
| P-09 | Tiếng Việt: dạng tổ hợp dấu (NFD), font không đủ dấu, slot font (`ascii/hAnsi/cs/eastAsia`) | Chữ lỗi/đổi font bất ngờ |
| P-10 | Giao tiếp AI-engine: truyền byte `.docx` qua JSON-RPC làm phình context; AI không có cách trỏ lại đúng đoạn bị lỗi | Tốn token, vòng sửa không chính xác |

---

## 3. Solution

### 3.1. Nguyên tắc thiết kế

1. **Engine tất định, AI quyết định.** Engine không chứa logic tự trị, không gọi ngược AI. "Tất định" được hiểu là tương đương về ngữ nghĩa (so sánh XML đã chuẩn hóa), không phải trùng byte (NFR-01).
2. **Phòng ngừa thay vì đo đạc.** Dùng ràng buộc ngữ nghĩa OOXML; không render để đo layout trong core.
3. **Một đường ghi XML duy nhất.** Mọi thay đổi XML đi qua Schema Helper; cấm `append()` tùy tiện.
4. **An toàn mặc định.** Sandbox, autoescape, parser an toàn, giới hạn tài nguyên.
5. **Cam kết tường minh.** Tài liệu liệt kê rõ engine bảo đảm gì và không bảo đảm gì (3.4).
6. **Handle thay cho byte.** File đi qua `FileRef`; không truyền base64 nội tuyến.
7. **Bất biến do engine cưỡng chế.** Không dựa vào quy ước trong prompt.
8. **Không làm thay đổi thiết kế của con người ngoài ý muốn.** Với đường template, guard mặc định chỉ báo cáo; áp guard là tùy chọn.

### 3.2. Nhật ký quyết định

| ID | Quyết định | Lý do | Phương án đã loại |
|---|---|---|---|
| D-01 | Engine là MCP tool server tất định; AI là client | MCP: server không gọi ngược client; loại phụ thuộc vòng tròn | Engine gọi AI để tóm tắt/cắt gọn |
| D-02 | Không có vòng tự phục hồi dựa trên render trong core | Cảm biến render (dxpdf/LibreOffice) không phải Word; đo sai nơi dùng | Vòng PID/Docling/Heuristic dựa trên PDF |
| D-03 | Bỏ Docling khỏi core | Công cụ phân tích cấu trúc, nặng, xác suất; PDF vector đã có tọa độ chính xác | Docling làm "mắt thần" |
| D-04 | Dùng guard OOXML phòng ngừa | Buộc Word tự xử lý đúng ở máy người dùng | Đo pixel và vi chỉnh khoảng cách dòng |
| D-05 | Hai đường dựng: Template và DocSpec | Phục vụ cả biểu mẫu chuẩn và tài liệu tự do | Chỉ template |
| D-06 | Schema Helper là lõi ghi XML, dùng Tag Order Registry sinh từ XSD; validator chạy sau mỗi build | Word chặt về thứ tự phần tử; registry chỉ lo thứ tự, XSD + id duy nhất bắt các lỗi còn lại | Ghi `lxml` trực tiếp; registry gõ tay |
| D-07 | Bất biến cưỡng chế bằng tham chiếu hoặc hash khóa trước | `Field(frozen=True)` của Pydantic chỉ chặn gán lại, không chặn AI truyền nội dung đã sửa | Quy ước trong prompt hoặc `frozen=True` |
| D-08 | Chính sách trường động tường minh (`field_update: auto/none/update_on_open`, `toc_mode`); mặc định `auto`: tài liệu có TOC kèm số trang thì `update_on_open` và luôn kèm `W-FIELD-UPDATE-REQUIRED`, tài liệu khác thì `none`; TOC luôn ghi nội dung cached | Tắt hẳn làm số trang sai/trống; bật hẳn gây hộp thoại cho mọi file; chỉ bật khi thật sự cần và luôn báo | Tắt `updateFields` cho mọi file; bật cho mọi file; cờ `has_toc` khai báo trong manifest |
| D-09 | Tách `lint` (chỉ đọc) và `normalize` (sinh bản mới có phiên bản) | Linter không được âm thầm đổi template | Linter tự sửa |
| D-10 | `FileRef` là đối tượng URI mờ (`resource://...`) kèm `sha256`; công cụ trả về diagnostics có anchor | Tránh phình context; AI định vị được lỗi; tương thích mô hình Resources của MCP mà không lộ tenant trong URI | `template_bytes`/`docx_bytes` nội tuyến; URI chứa `tenant_id`/`session_id` |
| D-11 | Template đi kèm manifest; model Pydantic sinh động từ manifest | Một nguồn sự thật cho biến, kiểu, bất biến, policy | Lớp Python cứng cho từng loại tài liệu |
| D-12 | Guard đặt ở **style** khi có thể; trên đoạn chỉ khi cần | Giữ khả năng người dùng chỉnh trong Word, tránh "direct formatting" tràn lan | Gắn thuộc tính trực tiếp lên mọi đoạn |
| D-13 | Word là Oracle trong CI (Windows + COM), LibreOffice là Oracle thứ hai | Kiểm chứng guard bằng ground truth thật | Kiểm thủ công |
| D-14 | PDF tách thành module riêng, giao tiếp qua `FileRef` | Tránh kéo Rust/Skia/clang vào core; vòng đời độc lập | Nhúng dxpdf trong core |
| D-15 | `style_conflict_policy` (`master_wins` / `isolate_styles` / `flatten_styles`) khi ghép | Style trùng tên khác định nghĩa làm phụ lục đổi hình thức; cần lựa chọn tường minh | Mặc định im lặng theo hành vi của docxcompose |
| D-16 | Sự thật về tài liệu (có TOC, có PAGEREF...) do engine **phát hiện**; manifest chỉ khai báo **chính sách** | Cờ khai báo có thể lệch thực tế (template sửa sau, AI chèn TOC qua DocSpec/patch) | Cờ `has_toc` trong manifest |

### 3.3. Tổng quan giải pháp

```
AI (client) --MCP--> [ Docx Engine: validate -> build -> guards -> fields -> scrub -> validate OOXML ]
                                      |
                       FileRef + Diagnostics (có anchor, có "fixable_by")
                                      |
AI quyết định: chấp nhận / sửa trường co giãn / chèn ngắt trang chủ động / hỏi người dùng
```

### 3.4. Ranh giới cam kết

| Engine bảo đảm | Engine KHÔNG bảo đảm |
|---|---|
| File hợp lệ OOXML (thứ tự phần tử, id duy nhất) | Số trang, vị trí ngắt trang cuối cùng trong Word |
| Dữ liệu điền đúng template; thẻ không vỡ; không chèn XML | "Trông giống hệt" giữa các trình đọc (Word, WPS, LibreOffice, Google Docs) |
| Nội dung bất biến không bị thay đổi (so với nguồn/hash) | Số trang trong mục lục: chỉ đúng sau khi Word cập nhật trường hoặc nhờ module render; engine luôn báo trạng thái bằng `W-FIELD-UPDATE-REQUIRED` |
| Guard được áp đúng theo policy và có thể kiểm chứng bằng Word-oracle | Ràng buộc kiểu "tối đa N trang" (thuộc module render) |
| Diagnostics chỉ dựa trên tiêu chí đo được | Chẩn đoán thẩm mỹ mang tính phỏng đoán (nếu có phải gắn nhãn `estimated`) |

---

## 4. Architecture

### 4.1. Sơ đồ logic

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ANTIGRAVITY AI (MCP Client)                       │
│ - Phân loại nội dung: Bất biến / Co giãn                             │
│ - Đọc Diagnostics, quyết định sửa / chấp nhận / hỏi người dùng       │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ MCP tool calls (FileRef, JSON)
┌───────────────────────────────▼──────────────────────────────────────┐
│                    DOCX ENGINE (MCP Server, tất định)                │
│                                                                      │
│ [A] API & Policy Layer: xác thực tenant, giới hạn tài nguyên, audit  │
│ [B] Template Service: registry, manifest, lint, normalize            │
│ [C] Input Validation: Pydantic động (từ manifest), NFC, control chars│
│                       kiểm tra bất biến (hash / tham chiếu)          │
│ [D] Dual-Path Builder:                                               │
│       Path A: docxtpl (sandbox, autoescape) [+ docxcompose]          │
│       Path B: DocSpec Builder (python-docx + Schema Helper)          │
│ [E] Semantic Guards (theo layout_policy, ưu tiên ở style)            │
│ [F] Field & Hygiene: TOC cached, tùy chọn updateFields, scrub metadata│
│ [G] OOXML Validator: XSD, thứ tự phần tử, id duy nhất, đo tĩnh       │
│ [H] Diagnostics Builder: issues có anchor, severity, fixable_by      │
│                                                                      │
│ Cross-cutting: Schema Helper (đường ghi XML duy nhất), Sandbox       │
│                process, File Store (FileRef), Audit Log              │
└───────────────┬──────────────────────────────────────┬───────────────┘
                │ FileRef(.docx)                       │ (tùy chọn, tương lai)
                ▼                                      ▼
        [Người dùng mở trong Word]       [Module PDF / Render (tách riêng)]
```

### 4.2. Thành phần và trách nhiệm

| Thành phần | Trách nhiệm | Công nghệ | Yêu cầu liên quan |
|---|---|---|---|
| API & Policy | Xác thực, giới hạn kích thước/thời gian, định tuyến công cụ, ghi audit | MCP SDK | NFR-02, SEC-05, FR-16 |
| Template Service | Lưu template theo phiên bản, manifest, lint (thuần đọc), normalize (sinh bản mới + diff) | `lxml`, `jinja2.meta` | FR-01, FR-02, FR-03 |
| Input Validation | Sinh model Pydantic từ manifest; NFC; loại ký tự điều khiển; kiểm bất biến | Pydantic v2 | FR-13, FR-17, SEC-02 |
| Dual-Path Builder | Dựng `.docx` từ template hoặc DocSpec; ghép phụ lục | `docxtpl`, `python-docx`, `docxcompose` | FR-04, FR-05, FR-06 |
| Semantic Guards | Áp guard theo policy | Schema Helper | FR-07 |
| Field & Hygiene | TOC cached, tùy chọn cập nhật trường, scrub metadata/tracked changes/comment | Schema Helper | FR-12, FR-14 |
| OOXML Validator | XSD, thứ tự phần tử mọi phần quan trọng, id duy nhất, kiểm tra tĩnh | XSD ECMA-376 qua `lxml`; `OpenXmlValidator` (.NET) trong CI | FR-08 |
| Diagnostics Builder | Chuẩn hóa lỗi thành `issues` | Pydantic | FR-09 |
| Schema Helper | Chèn/sửa phần tử đúng thứ tự bằng Tag Order Registry (sinh từ XSD) cho `pPr`, `rPr`, `tblPr`, `trPr`, `tcPr`, `sectPr`, `settings.xml` | `lxml` | D-06 |
| Sandbox | Chạy render template trong process cách ly, có timeout, giới hạn CPU/RAM | OS/container | SEC-01, NFR-03 |
| File Store | Cấp và giải `FileRef`, TTL, cách ly theo tenant | Cục bộ hoặc object store | FR-15, SEC-05 |
| Audit Log | Nhật ký thao tác có che dữ liệu nhạy cảm | JSONL/OpenTelemetry | FR-16, SEC-06 |

### 4.3. Hợp đồng công cụ MCP (v1)

| Công cụ | Mục đích | Đầu vào chính | Đầu ra chính | Ưu tiên |
|---|---|---|---|---|
| `lint_template` | Kiểm tra template (thuần đọc) | `template_ref` | `valid`, `variables`, `fields_detected`, `issues` | MVP |
| `normalize_template` | Ghép run vỡ, sinh phiên bản mới | `template_ref` | `new_template_ref`, `diff` | MVP |
| `register_template` / `list_templates` / `get_template_manifest` | Quản lý template và manifest | `template_ref`, `manifest` | `template_id`, `version`, `manifest` | MVP |
| `build_document` | Dựng tài liệu | `source_type`, `template_id` hoặc `docspec`, `context_data`, `layout_policy` | `file_ref`, `diagnostics` | MVP |
| `inspect_docx_structure` | Đọc cấu trúc cho AI | `file_ref` | cây cấu trúc có `anchor` | MVP |
| `validate_docx` | Kiểm tra hợp lệ độc lập | `file_ref` | `issues` | MVP |
| `merge_docx` | Ghép nhiều file | `base_ref`, `parts[]`, `style_conflict_policy` | `file_ref`, `diagnostics` | P1 |
| `patch_docx` | Sửa file có sẵn bằng thao tác khai báo | `file_ref`, `operations[]` | `file_ref`, `diagnostics` | P1 |

Quy ước chung:

- Tất cả tệp vào/ra là `FileRef` (không truyền byte): đối tượng `{uri, sha256, size, mime, expires_at}`.
- **Chiều ra (server sang client):** `uri` có dạng `resource://docx-engine/files/{opaque_id}`; id là mờ, không chứa tenant hay session; quyền truy cập được kiểm tra ở phía server (SEC-05). `sha256` phục vụ toàn vẹn và FR-13.
- **Chiều vào (client sang server):** tệp của người dùng truyền bằng `file://` nằm trong các **roots** mà client khai báo (SEC-07), hoặc bằng `FileRef` do chính engine cấp.
- Việc client đọc được `resources/read` hoặc `resource_link` phụ thuộc host và phiên bản spec MCP `[CẦN KIỂM CHỨNG]`. Core chỉ định nghĩa hình dạng `FileRef`; cách vận chuyển cuối cùng chốt ở bước tích hợp (ngoài phạm vi).
- Mọi công cụ trả về cùng một phong bì kết quả.

**Phong bì kết quả**

```json
{
  "success": true,
  "file_ref": {
    "uri": "resource://docx-engine/files/8f3a...",
    "sha256": "...", "size": 48213,
    "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "expires_at": "2026-10-06T00:00:00Z"
  },
  "diagnostics": {
    "errors": [], "warnings": [], "info": []
  },
  "guarantees_applied": ["ooxml_valid", "guards:keepNext,cantSplit,tblHeader"],
  "stats": { "paragraphs": 120, "tables": 4, "duration_ms": 640,
             "fields": { "toc": true, "pageref": 12, "update_applied": "update_on_open" } }
}
```

**Cấu trúc một issue**

```json
{
  "code": "W-LAYOUT-TBL-001",
  "severity": "warning",
  "location": { "anchor": "tbl_03", "part": "word/document.xml" },
  "message": "Tổng độ rộng cột (17.2 cm) vượt vùng in (16.0 cm).",
  "evidence": { "sum_cols_cm": 17.2, "printable_cm": 16.0 },
  "fixable_by": "engine | ai | human",
  "suggested_action": "reduce_column_widths"
}
```

Họ mã lỗi (ví dụ): `E-SCHEMA-*` (vi phạm cấu trúc OOXML), `E-TPL-*` (template/thẻ Jinja, ví dụ `E-TPL-UNMERGEABLE`), `E-IMMUT-*` (vi phạm bất biến), `E-SEC-*` (an ninh), `W-LAYOUT-*` (rủi ro layout đo được), `W-TPL-*` (cảnh báo template, ví dụ `W-TPL-MIXED-FORMAT`), `W-FIELD-*` (trạng thái trường động, ví dụ `W-FIELD-UPDATE-REQUIRED`), `W-MERGE-*` (ví dụ `W-MERGE-STYLE-CONFLICT`), `I-*` (thông tin).

Quy ước mức độ: một issue cần **người dùng làm thêm một hành động** để tài liệu đúng (ví dụ cập nhật trường) là `warning` với `fixable_by=human`, không hạ xuống `info`.

### 4.4. Hai đường dựng

**Path A — Template-driven (`docxtpl` + `docxcompose`)**

- Template đã qua `lint` và `normalize`, có manifest.
- Render trong `SandboxedEnvironment`, `autoescape=True`; chỉ cho phép tag/filter trong allow-list (kiểm tra AST bằng `jinja2.meta` lúc lint).
- Ghép phụ lục bằng `docxcompose`; thứ tự "render từng phần rồi ghép" là mặc định `[ĐỀ XUẤT]`; `Subdoc` của docxtpl chỉ dùng cho chèn nội tuyến nhỏ; xung đột style xử lý theo `style_conflict_policy` (4.13).

**Path B — DocSpec-driven**

- DocSpec là JSON có schema và phiên bản, tham chiếu **named style** của một base template/theme.
- Nút chính: `heading`, `paragraph`, `list`, `table`, `image`, `page_setup`, `header_footer`, `toc`, `page_break` (tường minh).
- DocSpec **không lộ thuộc tính OOXML**; ràng buộc layout do `layout_policy` quyết định.
- Cấu trúc python-docx không có API (numbering nhiều cấp, trường, footnote, tracked changes) được dựng bằng builder OXML riêng, đi qua Schema Helper.

```json
{
  "docspec_version": "1.0",
  "base_template": "tpl_report_vi@3",
  "blocks": [
    { "type": "heading", "level": 1, "text": "1. Biên bản họp" },
    { "type": "table", "style": "TableGrid",
      "headers": ["STT", "Hạng mục", "Ghi chú"],
      "rows": [["1", "Nghiệm thu phần mềm", "Đạt"]] }
  ]
}
```

### 4.5. Manifest của template

```yaml
template_id: tpl_contract_vi
version: 3
sha256: "<hash của file .docx>"
variables:
  contract_number: { type: string, immutable: true }
  total_amount:    { type: number, immutable: true }
  legal_clauses:   { type: list[string], immutable: true, source_ref_required: true }
  executive_summary: { type: string, immutable: false, max_chars: 1500 }
layout_policy_default:
  apply_guards: report_only      # report_only | apply
  allow_page_break_before_heading: true
  field_update: auto                # auto | none | update_on_open
  toc_mode: with_page_numbers       # with_page_numbers | no_page_numbers
  style_conflict_policy: master_wins   # master_wins | isolate_styles | flatten_styles
guards_allowed: [keepNext, keepLines, cantSplit, tblHeader, pageBreakBefore]
```

Manifest **không** khai báo `has_toc` hay các sự thật tương tự: engine tự phát hiện (D-16). Manifest chỉ khai báo chính sách mặc định; tham số của từng lần gọi (`layout_policy`) ghi đè manifest.

### 4.6. Cưỡng chế bất biến (FR-13)

Với trường `immutable: true`, engine chấp nhận một trong hai dạng và từ chối mọi dạng khác với mã `E-IMMUT-001`:

1. **Tham chiếu:** AI truyền `clause_id`/`source_ref`; engine tự lấy văn bản từ kho tin cậy.
2. **Hash khóa trước:** người dùng/hệ thống khóa hash của giá trị gốc; `build_document` so khớp hash trước khi dựng.

Trường co giãn (`immutable: false`) được AI viết lại, trong giới hạn `max_chars` nếu có.

### 4.7. Semantic Guards (FR-07)

| Mục tiêu | Thuộc tính | Vị trí | Ghi chú |
|---|---|---|---|
| Heading không mồ côi cuối trang | `w:keepNext` | `pPr` / style Heading | Ưu tiên đặt ở style; chuỗi `keepNext` dài hơn một trang bị Word bỏ qua |
| Không cắt dòng bảng | `w:cantSplit` | `trPr` | Dòng cao hơn một trang vẫn bị cắt |
| Lặp header bảng | `w:tblHeader` | `trPr` | Chỉ cho các dòng đầu liên tiếp; bảng nổi (text wrapping) `[CẦN KIỂM CHỨNG]` |
| Không tách đoạn quan trọng | `w:keepLines` | `pPr` | Chỉ giữ các dòng trong **một** đoạn |
| Khối nhiều đoạn đi cùng nhau (chữ ký) | `keepNext` trên mọi đoạn trừ đoạn cuối; nếu chữ ký nằm trong bảng: `cantSplit` + `keepNext` trong ô | `pPr`, `trPr` | `keepLines` một mình không đủ |
| Ngắt trang chủ động | `w:pageBreakBefore` | `pPr` | Ưu tiên hơn `<w:br w:type="page"/>`; chỉ dùng khi AI/người dùng yêu cầu tường minh |
| Kiểm soát dòng góa/mồ côi | `w:widowControl` | `pPr` / style | Khai báo tường minh |
| Bảng ổn định | `tblLayout`, `tblW`, `tblGrid` nhất quán với `tcW` | `tblPr`, `tblGrid` | Nguồn lỗi bảng phổ biến |
| Ngôn ngữ | `w:lang` (`vi-VN`) | `rPr` / style | Xem FR-17 |

**Thứ tự ưu tiên khi có xung đột:** style của template < `layout_policy` < ghi đè tường minh của AI. Mọi ghi đè được liệt kê trong diagnostics (`I-POLICY-OVERRIDE`).

**Thứ tự phần tử: Tag Order Registry (D-06).** Schema Helper dùng một chỉ mục thứ tự tĩnh cho từng container (`pPr`, `rPr`, `tblPr`, `trPr`, `tcPr`, `sectPr`, `settings`...), **sinh tự động từ XSD ECMA-376 lúc build**, không gõ tay (có test so khớp, TC-28). Ví dụ `pPr`: `pStyle, keepNext, keepLines, pageBreakBefore, framePr, widowControl, numPr, suppressLineNumbers, pBdr, shd, tabs, ... spacing, ind, ... jc, ..., outlineLvl, ..., rPr, sectPr, pPrChange`.

- Thuật toán chèn: tìm phần tử con đầu tiên có thứ hạng lớn hơn phần tử mới rồi chèn ngay trước nó; nếu đã có phần tử cùng loại thì thay thế, không tạo trùng; phần tử ngoài registry (`w14:*`, `mc:AlternateContent`) được giữ nguyên vị trí.
- Phạm vi cam kết: registry chỉ bảo đảm **thứ tự**. Nó không bảo đảm thuộc tính/nội dung hợp lệ, nên vẫn cần validator XSD (FR-08).
- Mức nghiêm ngặt theo container: `pPr`, `tblPr`, `tcPr`, `sectPr`, `settings.xml` là sequence; `trPr` là choice; `rPr` tùy phiên bản XSD (Transitional/Strict) `[CẦN KIỂM CHỨNG]`. Quy tắc an toàn: **luôn ghi theo thứ tự chuẩn** cho mọi container, kể cả khi schema cho phép tự do.

### 4.8. Trường động và Mục lục (FR-12)

**Bản chất vấn đề.** Số trang thật chỉ có khi Word dàn trang. Các trường cần nó: TOC, `PAGEREF`, tham chiếu chéo có số trang, `NUMPAGES` trong thân văn bản. `PAGE`/`NUMPAGES` trong header/footer do Word tự tính khi dàn trang `[CẦN KIỂM CHỨNG]`. Tắt `updateFields` thì TOC có số trang sẽ sai hoặc trống; bật thì Word hiện hộp thoại khi mở, và không cập nhật trong Protected View cho đến khi người dùng bật chỉnh sửa. Đây là đánh đổi thật, không có lựa chọn không tốn gì.

**Nguyên tắc.**

1. Engine **phát hiện** trường (D-16): TOC dạng field hoặc SDT, `PAGEREF`, `NUMPAGES` ngoài header/footer. Không dựa vào cờ khai báo.
2. Hành vi do `field_update` và `toc_mode` quyết định; mọi quyết định được ghi vào `stats.fields` và diagnostics.
3. Không có thay đổi cờ toàn cục nào diễn ra âm thầm.

| Tham số | Giá trị | Hành vi |
|---|---|---|
| `field_update` | `auto` (mặc định) | Nếu phát hiện TOC kèm số trang (hoặc `PAGEREF`/`NUMPAGES` trong thân): áp `update_on_open` và phát `W-FIELD-UPDATE-REQUIRED`. Ngược lại: `none` |
| | `none` | Không ghi cờ. Nếu có trường cần số trang: phát `W-FIELD-UPDATE-REQUIRED` (`evidence.update_applied = none`) |
| | `update_on_open` | Ghi `w:updateFields` đúng vị trí trong `settings.xml`; phát `W-FIELD-UPDATE-REQUIRED` (`evidence.dialog_expected = true`) |
| `toc_mode` | `with_page_numbers` (mặc định) | TOC có số trang; phụ thuộc cập nhật trường |
| | `no_page_numbers` | TOC chỉ có liên kết đến heading (bỏ số trang), nên không có số trang sai và không cần cập nhật; không phát cảnh báo |
| (P2) | `oracle_estimate` | Module render tính số trang và ghi vào nội dung cached, gắn nhãn `estimated`; thuộc module PDF/render, ngoài core |

**Nội dung cached của TOC.** Tiêu đề lấy từ heading; liên kết tới bookmark `_Toc*` có id duy nhất; số trang để trống hoặc ghi chú ngắn. Nội dung cached phải khớp heading thực tế (TC-26).

**Hoàn tất ở phía người dùng.** `W-FIELD-UPDATE-REQUIRED` có `fixable_by=human`. AI **bắt buộc** nêu rõ cho người dùng khi bàn giao file (6.3): mở bằng Word, chọn Yes ở hộp thoại cập nhật, hoặc chọn toàn bộ rồi nhấn F9.

**Cần kiểm chứng (Phase 0).** `w:dirty="true"` trên từng trường như phương án thay thế `updateFields`; việc Word có xóa cờ `updateFields` sau khi lưu hay không; hành vi ở các consumer khác (TC-08).

### 4.9. Vệ sinh tài liệu (FR-14)

Cảnh báo hoặc loại bỏ (theo policy): tracked changes còn sót (`w:del`/`w:ins`), comment, văn bản ẩn (`w:vanish`), metadata `docProps` (tác giả, `lastModifiedBy`, thời gian chỉnh sửa, đường dẫn), quan hệ ngoài (`TargetMode="External"`), `vbaProject`.

### 4.10. Tiếng Việt (FR-17)

- Chuẩn hóa văn bản về **NFC** ở bước validate input.
- Khi đặt font, đồng bộ các slot `ascii`, `hAnsi`, `cs`, `eastAsia`; đặt `w:lang=vi-VN`.
- Cảnh báo khi font được chỉ định không có đủ glyph dấu Việt.

### 4.11. Yêu cầu phi chức năng

| ID | Yêu cầu | Chỉ tiêu `[ĐỀ XUẤT]` |
|---|---|---|
| NFR-01 | Tất định theo ngữ nghĩa: cùng đầu vào cho cùng XML sau khi chuẩn hóa (bỏ timestamp, GUID, rsid, `docProps` động) | 100% trên bộ golden |
| NFR-02 | Giới hạn tài nguyên mỗi lần gọi | File vào ≤ 25 MB; sau giải nén ≤ 200 MB; timeout 30 giây; RAM ≤ 1 GB |
| NFR-03 | Cách ly thực thi bước render template | Process riêng, không mạng, FS tối thiểu |
| NFR-04 | Quan sát được: trace, số liệu, mã lỗi ổn định | Mọi lần gọi có `request_id` |
| NFR-05 | Ranh giới module PDF: giao tiếp qua `FileRef`; core không phụ thuộc Rust/Skia | Không có phụ thuộc biên dịch ngoài Python trong core |
| NFR-06 | Ma trận consumer có mức hỗ trợ rõ ràng | Word (Win/Mac/Web): hỗ trợ đầy đủ; LibreOffice, WPS, Google Docs import, Pages: mức xác định trong Phase 0 |
| NFR-07 | Hiệu năng | Dựng tài liệu ~20 trang: p95 < 3 giây (không gồm render PDF) |

### 4.12. Yêu cầu bảo mật

| ID | Yêu cầu |
|---|---|
| SEC-01 | Render Jinja trong `SandboxedEnvironment`; allow-list tag/filter/thuộc tính kiểm tra bằng AST lúc lint; ghim phiên bản Jinja và theo dõi advisory (sandbox không phải ranh giới tuyệt đối); process cách ly + timeout |
| SEC-02 | `autoescape=True` (mặc định của docxtpl là `False`); escape tại một điểm duy nhất, tránh escape hai lần; loại ký tự điều khiển XML 1.0 (`U+0000-0008`, `0B`, `0C`, `0E-1F`, `U+FFFE`, `U+FFFF`, surrogate lẻ) khỏi **dữ liệu** |
| SEC-03 | Parser ZIP/XML an toàn: giới hạn tỷ lệ giải nén, không phân giải entity ngoài (chống XXE), từ chối đường dẫn ZIP bất thường |
| SEC-04 | Từ chối `vbaProject`; không theo quan hệ ngoài; không tải tài nguyên từ mạng |
| SEC-05 | Cách ly template, file và nhật ký theo tenant; `FileRef` được ràng buộc tenant/session ở phía server (không thể hiện trong URI) và có TTL |
| SEC-06 | Audit log che dữ liệu nhạy cảm; mã hóa lưu trữ; chính sách retention |
| SEC-07 | Đầu vào `file://` chỉ chấp nhận trong roots do client khai báo (allow-list), chống path traversal; URI `resource://` do server cấp là id mờ, không chứa tenant/session; phân quyền kiểm tra phía server |

### 4.13. Xung đột style khi ghép (FR-06)

Khi ghép phụ lục từ nguồn khác (ví dụ `Normal`: Aptos 11pt ở tài liệu chính, Times New Roman 12pt ở phụ lục), theo hành vi đã biết `docxcompose` giữ style của tài liệu chính khi trùng tên, nên phụ lục đổi hình thức `[CẦN KIỂM CHỨNG]` (TC-27).

| `style_conflict_policy` | Hành vi |
|---|---|
| `master_wins` (mặc định) | Phụ lục theo style của tài liệu chính; báo `W-MERGE-STYLE-CONFLICT` liệt kê style khác định nghĩa |
| `isolate_styles` | Đổi `styleId` các style của phụ lục (ví dụ `Normal` thành `Normal_Annex1`) trước khi nối, rồi ánh xạ lại mọi tham chiếu |
| `flatten_styles` | Chuyển định dạng hiệu lực của phụ lục thành định dạng trực tiếp: giữ nguyên hình thức, mất khả năng chỉnh theo style |

Quy tắc cho `isolate_styles`:

- Phải cập nhật đồng thời mọi tham chiếu: `pStyle`, `rStyle`, `tblStyle`, `basedOn`, `next`, `link`, và các tham chiếu style bên trong numbering, header/footer, footnote của phụ lục.
- Không đổi `w:name` của style built-in (Heading n, Normal...) vì Word nhận diện theo tên. Với các style này, tạo style mới có tên tiền tố dựa trên định nghĩa của phụ lục; hệ quả là heading phụ lục có thể không vào TOC theo `\o`, cần kiểm tra thêm `\u`/`\t` `[CẦN KIỂM CHỨNG]`.
- Nguồn hình thức nằm ngoài style: `docDefaults` và font theme (ví dụ `asciiTheme`). Đổi tên style không giải quyết được; phải so sánh và cảnh báo hoặc chuyển thành định dạng trực tiếp.

### 4.14. Quy tắc Template Normalizer (FR-02)

Mục tiêu: sửa thẻ Jinja bị vỡ do cách Word lưu XML, bảo toàn tối đa nội dung.

1. **Phạm vi:** chỉ các đoạn `w:p` có dấu mở Jinja (`{{`, `{%`, `{#`) chưa khép trong cùng chuỗi văn bản; đoạn khác giữ nguyên để diff nhỏ.
2. **Phần tử bị loại** khi chen giữa các run của cụm thẻ: `w:proofErr` (đánh dấu kiểm tra chính tả/ngữ pháp) và `w:lastRenderedPageBreak`. Cả hai không có ngữ nghĩa hiển thị.
3. **Không xóa** `w:noProof`, `w:lang`, `rsid*`: chúng là thuộc tính trong `rPr` của run (không phải thẻ chen giữa), và `lang` phục vụ FR-17. Khi so sánh `rPr` để quyết định gộp run, bỏ qua `noProof`, `lang` và `rsid*`.
4. **Định dạng sau gộp:** lấy `rPr` của run đầu tiên; nếu các run còn lại khác `rPr` (sau khi bỏ qua mục 3) thì phát `W-TPL-MIXED-FORMAT`.
5. **Khoảng trắng:** khi nối `w:t`, đặt `xml:space="preserve"` nếu có khoảng trắng đầu/cuối.
6. **Ca khó:** thẻ vắt qua nhiều đoạn, trong text box (`w:txbxContent`), SDT, hyperlink, hoặc bị chen bởi bookmark/tracked change: xử lý theo từng ca đã được test (TC-02); ca không xử lý an toàn được thì phát `E-TPL-UNMERGEABLE` kèm anchor, không tự đoán.
7. **Đầu ra:** luôn là bản mới có phiên bản kèm diff; không ghi đè bản gốc (D-09).

---

## 5. Actor & Feature

### 5.1. Actor

| Actor | Vai trò | Tương tác chính |
|---|---|---|
| Người dùng cuối (End User) | Yêu cầu tài liệu, duyệt kết quả, mở trong Word | Giao tiếp với AI; nhận file; quyết định các điểm AI không tự quyết |
| Antigravity AI (MCP Client) | Lập kế hoạch, phân loại nội dung, gọi công cụ, xử lý diagnostics | Gọi mọi công cụ MCP |
| Tác giả template (Template Author) | Soạn template trong Word, khai báo manifest | `lint_template`, `normalize_template`, `register_template` |
| Quản trị/Kỹ sư nền tảng | Cấu hình giới hạn, tenant, theo dõi audit, vận hành CI | Cấu hình; đọc audit/trace |
| Engine | Thực thi tất định, kiểm định, trả diagnostics | — |
| Module PDF (tương lai) | Chuyển `.docx` sang PDF, cung cấp số liệu layout | Nhận/trả `FileRef` |
| Kiểm toán/Reviewer | Đối chiếu audit trail, chất lượng và bảo mật | Đọc audit log, báo cáo test |

### 5.2. Danh mục tính năng

| ID | Tính năng | Mô tả ngắn | Actor chính | Ưu tiên |
|---|---|---|---|---|
| FR-01 | Template lint | Kiểm tra thuần đọc: thẻ Jinja, biến, tag không an toàn, `w:del`/comment/văn bản ẩn; phát hiện trường động (TOC, PAGEREF, NUMPAGES) | Template Author, AI | MVP |
| FR-02 | Template normalize | Ghép thẻ Jinja bị vỡ run theo quy tắc 4.14 (loại `proofErr`, không xóa `noProof`/`lang`, giữ `xml:space`), sinh phiên bản mới kèm diff | Template Author | MVP |
| FR-03 | Template registry + manifest | Lưu phiên bản, hash, biến, bất biến, policy | Template Author, AI | MVP |
| FR-04 | Build từ template | docxtpl trong sandbox, autoescape, validate input | AI | MVP |
| FR-05 | Build từ DocSpec | Dựng tài liệu từ JSON có schema; builder OXML cho cấu trúc ngoài python-docx | AI | MVP |
| FR-06 | Ghép tài liệu | docxcompose; `style_conflict_policy` (4.13); kiểm tra numbering, header/section, id trùng | AI | P1 |
| FR-07 | Semantic guards | Áp guard theo policy và thứ tự ưu tiên (4.7) | Engine | MVP |
| FR-08 | OOXML validation | XSD, thứ tự phần tử, id duy nhất, kiểm tra tĩnh | Engine | MVP |
| FR-09 | Diagnostics | Issues có anchor, severity, `fixable_by`, `evidence` | AI | MVP |
| FR-10 | Inspect cấu trúc | Cây cấu trúc, heading, bảng, ngắt trang cứng, anchor ổn định | AI | MVP |
| FR-11 | Patch tài liệu có sẵn | Thay chữ giữ định dạng, chèn/xóa đoạn, sửa bảng, tracked changes/comment | AI | P1 |
| FR-12 | Trường động | `field_update`, `toc_mode`, TOC cached, `W-FIELD-UPDATE-REQUIRED`, tùy chọn `dirty` (4.8). MVP chưa có FR-12: DocSpec không hỗ trợ khối `toc`; TOC có sẵn trong template chỉ được phát hiện và báo | AI, Engine | P1 |
| FR-13 | Cưỡng chế bất biến | Tham chiếu hoặc hash khóa trước; mã `E-IMMUT-*` | Engine | MVP |
| FR-14 | Vệ sinh tài liệu | Scrub metadata, tracked changes, comment, văn bản ẩn, quan hệ ngoài | Engine | P1 |
| FR-15 | Kho file `FileRef` | Cấp/giải `FileRef` dạng URI mờ kèm `sha256`; chiều vào qua roots; TTL; cách ly tenant | Engine | MVP |
| FR-16 | Audit log | Nhật ký thao tác, che dữ liệu nhạy cảm | Admin, Kiểm toán | MVP |
| FR-17 | Xử lý tiếng Việt | NFC, slot font, `w:lang`, cảnh báo font thiếu glyph | Engine | MVP |
| FR-18 | Điểm mở rộng định dạng | Giao diện adapter cho định dạng khác (ví dụ `.xlsx`, `.pptx`) | Admin | P2 |

### 5.3. Ma trận Actor × Công cụ (rút gọn)

| Công cụ | End User | AI | Template Author | Admin | Kiểm toán |
|---|---|---|---|---|---|
| `lint_template`, `normalize_template`, `register_template` | | ✓ | ✓ | ✓ | |
| `list_templates`, `get_template_manifest` | | ✓ | ✓ | ✓ | |
| `build_document`, `merge_docx`, `patch_docx` | (qua AI) | ✓ | | | |
| `inspect_docx_structure`, `validate_docx` | (qua AI) | ✓ | ✓ | ✓ | |
| Audit log / trace | | | | ✓ | ✓ |

---

## 6. Demonstration

### 6.1. Quy trình nghiệp vụ tổng quan

```
[1] Template Author soạn template Word + manifest
        │
        ▼
[2] lint_template ──► có lỗi? ──► sửa template ──┐
        │ không                                  │
        ▼                                        │
[3] normalize_template ──► register_template ◄───┘
        │
        ▼
[4] Người dùng yêu cầu tạo/sửa tài liệu ───► AI
        │
        ▼
[5] AI chọn đường: Template (build) | DocSpec | Patch file có sẵn
        │   AI phân loại dữ liệu: bất biến (tham chiếu/hash) | co giãn
        ▼
[6] Engine dựng + guard + kiểm định ──► file_ref + diagnostics
        │
        ▼
[7] AI đọc diagnostics:
        ├─ fixable_by=engine → gọi lại với policy phù hợp
        ├─ fixable_by=ai     → sửa trường co giãn rồi gọi lại
        └─ fixable_by=human  → hỏi người dùng
        │
        ▼
[8] Người dùng mở file trong Word; nếu có W-FIELD-UPDATE-REQUIRED thì cập nhật trường
        theo hướng dẫn AI đưa ra; duyệt
        │
        ▼
[9] Audit log ghi toàn bộ chuỗi thao tác
```

### 6.2. Workflow chính

**WF-A. Nhập kho template**

```
Upload template -> lint (thuần đọc) -> [lỗi?]
     |no                                  |yes -> báo issues, dừng
     v
normalize (sinh phiên bản mới + diff) -> lint lại -> OK?
     |yes
     v
Đối chiếu manifest (biến, kiểu, bất biến) -> register (version, sha256)
```

**WF-B. Build từ template**

```
build_document(template_id, context_data, layout_policy)
  -> giới hạn tài nguyên + xác thực tenant
  -> validate input (Pydantic động, NFC, loại control chars)
  -> kiểm bất biến (tham chiếu/hash) --[vi phạm]--> E-IMMUT-001, dừng
  -> render docxtpl (sandbox, autoescape)
  -> (tùy chọn) merge phụ lục
  -> áp guards theo policy (report_only | apply)
  -> phát hiện trường, áp field_update/toc_mode (TOC cached), vệ sinh (scrub)
  -> validate OOXML (XSD, id duy nhất) --[lỗi E-SCHEMA]--> trả lỗi, không phát hành file
  -> lưu FileRef -> trả file_ref + diagnostics -> audit
```

**WF-C. Build từ DocSpec**

```
build_document(source_type=docspec, docspec, layout_policy)
  -> validate DocSpec theo JSON Schema (lỗi có JSON path)
  -> dựng bằng builder (python-docx + Schema Helper)
  -> áp guards theo style/policy -> trường & vệ sinh -> validate OOXML -> trả kết quả
```

**WF-D. Sửa tài liệu có sẵn**

```
inspect_docx_structure(file_ref) -> AI nhận cây + anchors
patch_docx(file_ref, operations[anchor, op, payload])
  -> áp thao tác (giữ định dạng) -> validate OOXML -> file_ref mới + diagnostics
```

### 6.3. Activity flow xử lý diagnostics (phía AI, dựa trên hợp đồng của engine)

```
Nhận diagnostics
  ├─ Có errors?
  │     ├─ E-SCHEMA / E-TPL (lỗi hệ thống/template) -> dừng, báo người dùng/Template Author
  │     ├─ E-IMMUT -> không tự sửa nội dung bất biến; dùng tham chiếu/hash đúng hoặc hỏi người dùng
  │     └─ E-SEC -> dừng, không thử lại với cùng đầu vào
  └─ Chỉ có warnings?
        ├─ W-LAYOUT (đo được, fixable_by=engine) -> gọi lại với policy phù hợp
        ├─ W-LAYOUT liên quan trường co giãn -> AI rút gọn/sửa rồi build lại (tối đa N lần [ĐỀ XUẤT: 2])
        ├─ Liên quan trường bất biến -> giữ nguyên chữ; có thể chèn ngắt trang chủ động
        │                                hoặc chấp nhận tăng số trang
        ├─ W-FIELD-UPDATE-REQUIRED (fixable_by=human) -> không tự sửa; BẮT BUỘC nêu rõ với
        │                      người dùng cách cập nhật trường khi bàn giao file
        └─ Không còn cảnh báo cần xử lý -> bàn giao file
```

Quy tắc chặn vòng lặp: số lần build lại tối đa cố định, giữ phương án tốt nhất (ít lỗi nhất) và dừng ngay khi hai lần liên tiếp không cải thiện.

---

## 7. Test & Audit Planning

### 7.1. Chiến lược kiểm thử

| Tầng | Mục đích | Công cụ |
|---|---|---|
| Unit | Schema Helper, normalizer, validator input, sinh issue | `pytest` |
| Integration | Pipeline build đầy đủ cho cả hai đường | `pytest` + corpus |
| Conformance OOXML | Hợp lệ theo schema, id duy nhất, không báo "Repair" | XSD ECMA-376 (lxml); `OpenXmlValidator` (.NET) |
| Oracle / Compatibility | Kiểm chứng guard và khả năng mở file | Word (Windows + COM) trong CI; LibreOffice headless; kiểm tra thủ công cho consumer còn lại |
| Security | SSTI, XML injection, zip bomb, XXE, path traversal | Payload corpus, fuzz |
| Property/Fuzz | DocSpec ngẫu nhiên luôn cho file hợp lệ | `hypothesis` |
| Regression/Golden | So khớp XML đã chuẩn hóa | Golden files |
| Performance | Thời gian, bộ nhớ | Benchmark |
| UAT | Tài liệu nghiệp vụ thật | 30-50 tài liệu `[ĐỀ XUẤT]` |

### 7.2. Danh mục ca kiểm thử

| ID | Ca kiểm thử | Kết quả mong đợi | Yêu cầu | Tự động hóa |
|---|---|---|---|---|
| TC-01 | Template có `{{ item.name }}` bị tách run (đổi màu/đậm một nửa), có `w:proofErr` và `w:lastRenderedPageBreak` chen giữa, khoảng trắng đầu/cuối run | Nối đúng theo 4.14; `xml:space="preserve"` được giữ; `noProof`/`lang` không bị xóa; định dạng theo run đầu và `W-TPL-MIXED-FORMAT` khi khác; render không vỡ | FR-02 | Tự động |
| TC-02 | Thẻ Jinja trong header/footer, text box, dòng bảng, content control, hyperlink, có tracked change/bookmark chen giữa | Lint nhận diện; normalize xử lý hoặc báo lỗi rõ ràng | FR-01, FR-02 | Tự động |
| TC-03 | docxcompose: ghép 3 file có numbering lặp, section Landscape/Portrait, header khác nhau, style trùng tên khác định nghĩa | Numbering không nhảy; header theo đúng section; xung đột style được báo `W-MERGE-STYLE-CONFLICT` (kiểm theo từng chế độ ở TC-27) | FR-06 | Tự động + soát mắt |
| TC-04 | Conformance: XSD + `OpenXmlValidator`, thứ tự phần tử trong `pPr`, `rPr`, `tblPr`, `tcPr`, `sectPr`, `settings.xml` | 0 lỗi | FR-08 | Tự động (CI) |
| TC-05 | Id duy nhất sau ghép: `wp:docPr/@id`, `bookmarkStart/@id`, id numbering/comment | Không trùng | FR-06, FR-08 | Tự động |
| TC-06 | Word-oracle cho guard: `keepNext`, `cantSplit`, `tblHeader`, khối chữ ký (vị trí trang từng đoạn qua COM) | Đúng kỳ vọng trên tập tài liệu thử | FR-07 | Tự động (runner Windows) |
| TC-07 | Mở file trên Word Win/Mac/Web, LibreOffice, WPS, Google Docs import, Pages | Không báo "Repair"; ghi nhận chênh lệch theo NFR-06 | NFR-06 | Một phần tự động |
| TC-08 | Trường/TOC: hành vi với `updateFields`, `dirty`, Protected View, trình xem trước; cờ `updateFields` có bị Word xóa sau khi lưu không; `PAGE`/`NUMPAGES` trong header/footer so với trong thân | Khớp mô tả ở 4.8; cảnh báo hộp thoại đúng; ghi nhận kết quả để chốt các mục `[CẦN KIỂM CHỨNG]` | FR-12 | Thủ công + COM |
| TC-09 | Tiếng Việt: NFD→NFC, slot font, `w:lang`, font thiếu dấu | Chữ hiển thị đúng; cảnh báo font thiếu glyph | FR-17 | Tự động + soát mắt |
| TC-10 | Bất biến: sửa chữ điều khoản; sai hash; dùng tham chiếu đúng | Sửa chữ/sai hash bị từ chối (`E-IMMUT-001`); tham chiếu đúng được chấp nhận | FR-13 | Tự động |
| TC-11 | Payload SSTI (`__class__`, `|attr`, `format`, lặp lớn) | Bị chặn hoặc hết thời gian; không thực thi mã | SEC-01 | Tự động |
| TC-12 | Dữ liệu có `<`, `&`, ký tự điều khiển, chuỗi giống XML | Không hỏng file; không escape hai lần | SEC-02 | Tự động |
| TC-13 | Zip bomb, XXE, quan hệ ngoài, `vbaProject`, đường dẫn ZIP bất thường | Bị từ chối với `E-SEC-*` | SEC-03, SEC-04 | Tự động |
| TC-14 | Vệ sinh: `w:del`/comment/`w:vanish`/metadata trong template | Cảnh báo hoặc loại bỏ theo policy; không còn rò rỉ | FR-14 | Tự động |
| TC-15 | Fuzz/property: DocSpec ngẫu nhiên | 100% file hợp lệ OOXML | FR-05, FR-08 | Tự động |
| TC-16 | Round-trip: `inspect` rồi dựng lại | Cấu trúc tương đương | FR-10 | Tự động |
| TC-17 | `patch_docx`: thay chữ giữ định dạng, chèn/xóa đoạn, sửa ô bảng | Định dạng giữ nguyên; file hợp lệ | FR-11 | Tự động |
| TC-18 | Tất định: chạy lặp cùng đầu vào | XML chuẩn hóa trùng nhau | NFR-01 | Tự động |
| TC-19 | `FileRef`: cách ly tenant, TTL, path traversal | Không truy cập chéo tenant; hết hạn đúng | FR-15, SEC-05, SEC-07 | Tự động |
| TC-20 | Giới hạn tài nguyên và timeout | Dừng đúng, mã lỗi rõ ràng | NFR-02, NFR-03 | Tự động |
| TC-21 | Chất lượng diagnostics: mỗi mã có tiêu chí kích hoạt đo được; mọi issue có `location`, `fixable_by`, `evidence` | Không có cảnh báo phỏng đoán không gắn nhãn | FR-09 | Tự động |
| TC-22 | Hiệu năng | Đạt NFR-07 | NFR-07 | Tự động |
| TC-23 | Audit: đầy đủ trường, che dữ liệu nhạy cảm | Đạt SEC-06 | FR-16, SEC-06 | Tự động |
| TC-24 | UAT với tài liệu nghiệp vụ thật (hợp đồng, biên bản, báo cáo) | Đạt ngưỡng chấp nhận (7.3) | Tất cả MVP | Thủ công |
| TC-25 | Phát hiện trường: TOC dạng field và SDT, `PAGEREF`, `NUMPAGES` trong thân và header/footer; phân giải `field_update: auto` | Phát hiện đủ; `auto` thành `update_on_open` chỉ khi có TOC kèm số trang; `W-FIELD-UPDATE-REQUIRED` có evidence đúng; không có thay đổi cờ nào không được báo | FR-01, FR-12, D-16 | Tự động |
| TC-26 | TOC cached và `toc_mode`: nội dung cached khớp heading; bookmark `_Toc*` có id duy nhất; `no_page_numbers` không có số trang và không phát cảnh báo; hiển thị ở Word, trình xem trước, Protected View | Đúng mô tả 4.8 | FR-12 | Tự động + thủ công |
| TC-27 | Style khi ghép: phụ lục Times New Roman 12pt vào tài liệu chính Aptos 11pt; từng chế độ `master_wins`/`isolate_styles`/`flatten_styles`; kiểm tra tham chiếu chéo (`basedOn`, `next`, `link`, numbering, header/footer, footnote), `docDefaults`/font theme, heading phụ lục trong TOC | Hình thức đúng theo từng chế độ; không còn tham chiếu mồ côi; báo `W-MERGE-STYLE-CONFLICT` | FR-06 | Tự động + soát mắt |
| TC-28 | Tag Order Registry: bản sinh từ XSD khớp danh sách mong đợi (gồm `suppressLineNumbers`); chèn vào mọi vị trí; trùng loại; phần tử ngoài registry (`w14:*`, `mc:AlternateContent`) | Luôn đúng thứ tự; không tạo trùng; giữ nguyên phần tử lạ; XSD hợp lệ | D-06, FR-08 | Tự động |
| TC-29 | `FileRef`: URI mờ không chứa tenant/session; thử dùng id của tenant khác; `file://` ngoài roots; path traversal; `sha256` khớp | Từ chối truy cập chéo; chỉ đọc trong roots; toàn vẹn khớp | FR-15, SEC-05, SEC-07 | Tự động |

### 7.3. Tiêu chí chấp nhận `[ĐỀ XUẤT]`

| Tiêu chí | Ngưỡng |
|---|---|
| File báo "Repair" trên Word (Win/Mac/Web) | 0 trên toàn bộ corpus |
| Lỗi XSD/OpenXmlValidator | 0 |
| Guard đúng theo Word-oracle | 100% trên tập tài liệu thử đã định nghĩa |
| Vi phạm bất biến lọt qua | 0 |
| Payload bảo mật được chặn | 100% trong corpus |
| Tất định (XML chuẩn hóa) | 100% |
| UAT: tài liệu đạt duyệt của người dùng | Ngưỡng do chủ sở hữu chốt (xem Q-05) |
| Tài liệu có TOC kèm số trang mà chưa được cập nhật: `W-FIELD-UPDATE-REQUIRED` luôn xuất hiện | 100% |

### 7.4. Kế hoạch Audit

**a) Audit runtime (vết thao tác)**

| Hạng mục | Nội dung |
|---|---|
| Ghi nhận | `request_id`, tenant, công cụ, hash đầu vào/đầu ra, phiên bản template/DocSpec, policy áp dụng, danh sách issue (mã + vị trí), thời gian, kết quả |
| Không ghi nguyên văn | Nội dung tài liệu, dữ liệu cá nhân, văn bản prompt; chỉ ghi hash và thống kê |
| Lưu trữ | Mã hóa; cách ly theo tenant; retention theo chính sách `[ĐỀ XUẤT: xác định ở Q-06]` |
| Truy vết | Trace theo `request_id`; liên kết bản template ↔ tài liệu sinh ra |

**b) Audit chất lượng kỹ thuật**

- Cổng chất lượng (release gate): TC-01 đến TC-23 đạt; coverage mã lõi theo ngưỡng chủ sở hữu quy định; không có lỗi mức nghiêm trọng mở.
- Báo cáo định kỳ: tỷ lệ build thành công, phân bố mã issue, tỷ lệ lỗi theo template, thời gian xử lý.

**c) Audit bảo mật**

- Rà soát phụ thuộc và advisory (đặc biệt Jinja, lxml, thư viện ZIP).
- Kiểm thử xâm nhập cho bề mặt template/ZIP/FileRef trước mỗi phiên bản lớn.
- Kiểm tra rò rỉ chéo tenant (template, file, log, metadata).

**d) Checklist phát hành**

1. Toàn bộ TC bắt buộc đạt trên CI (gồm Word-oracle).
2. Tài liệu "Engine bảo đảm / không bảo đảm" (3.4) khớp hành vi thực tế.
3. Không có `[CẦN KIỂM CHỨNG]` nào còn mở trong phạm vi MVP.
4. Giấy phép phụ thuộc đã được rà soát.
5. Audit log và masking đã kiểm tra.

---

## Phụ lục A. Roadmap đề xuất

| Phase | Mục tiêu | Đầu ra | Điều kiện qua cổng |
|---|---|---|---|
| 0 — Kiểm chứng (spike) | Chốt các điểm `[CẦN KIỂM CHỨNG]`; dựng Word-oracle trong CI | Báo cáo kiểm chứng; corpus mẫu; ma trận consumer | Trả lời được: `updateFields`/`dirty`/`PAGE`/`NUMPAGES`, `tblHeader` ở bảng nổi, hành vi style của docxcompose, mức nghiêm ngặt thứ tự `rPr`/`trPr` theo XSD và Word, corpus `proofErr`, hỗ trợ roots/`resource_link` của client MCP, giấy phép |
| 1 — MVP | FR-01..05, 07..10, 13, 15..17; hợp đồng công cụ; Schema Helper và validator | Engine chạy được hai đường dựng; bộ test TC-01, 02, 04, 06, 09..13, 15, 16, 18..21, 23 | Đạt 7.3 trên corpus |
| 2 — P1 | FR-06, 11, 12, 14 | Ghép, sửa file có sẵn, trường động, vệ sinh | TC-03, 05, 08, 14, 17 đạt |
| 3 — P2 và PDF | FR-18; module PDF (core engine riêng) | Adapter định dạng khác; module PDF qua `FileRef` | Hợp đồng NFR-05 giữ nguyên |

## Phụ lục B. Rủi ro

| ID | Rủi ro | Mức | Giảm thiểu |
|---|---|---|---|
| R-01 | `python-docx` thiếu API cho numbering/footnote/trường/tracked changes, khối lượng OXML thủ công lớn | Cao | Đầu tư Schema Helper sớm; cân nhắc sidecar (ví dụ thư viện Node `docx`) `[CẦN KIỂM CHỨNG]` |
| R-02 | Hành vi khác nhau giữa các phiên bản Word và trình đọc khác | Trung bình | Ma trận consumer, Word-oracle, ghi rõ mức hỗ trợ |
| R-03 | Người soạn template làm hỏng thẻ Jinja trong Word | Trung bình | Lint bắt buộc khi nhập kho; hướng dẫn soạn template; manifest đối chiếu |
| R-04 | Sandbox Jinja bị vượt | Cao | Process cách ly, timeout, ghim phiên bản, allow-list AST |
| R-05 | Kỳ vọng sai về "đúng số trang/đúng 100%" | Trung bình | Mục 3.4; diagnostics chỉ dựa trên đo được |
| R-06 | Rò rỉ nội dung/metadata giữa tenant hoặc từ template cũ | Cao | FR-14, SEC-05, SEC-06 |
| R-07 | Giấy phép phụ thuộc (docxtpl LGPL, PyMuPDF AGPL nếu dùng ở module PDF) | Trung bình | Rà soát trước khi phân phối |
| R-08 | Chi phí runner Windows + Word cho CI | Thấp | Chạy theo lịch/nhánh chính; giữ corpus nhỏ nhưng đại diện |
| R-09 | Số trang mục lục sai/trống, hoặc hộp thoại cập nhật gây phiền cho người dùng | Trung bình | `field_update`/`toc_mode`, `W-FIELD-UPDATE-REQUIRED`, AI thông báo khi bàn giao; chốt mặc định ở Q-09 |
| R-10 | Client MCP không hỗ trợ roots/`resource_link` như giả định | Trung bình | Core chỉ định nghĩa `FileRef`; kiểm chứng ở Phase 0; chốt cách vận chuyển ở bước tích hợp |

## Phụ lục C. Câu hỏi mở

| ID | Câu hỏi | Ảnh hưởng |
|---|---|---|
| Q-01 | Loại tài liệu ưu tiên cho MVP (đề xuất: hợp đồng, biên bản, báo cáo)? | Phạm vi DocSpec/template |
| Q-02 | Consumer nào bắt buộc hỗ trợ ngoài Word (WPS, Google Docs, LibreOffice)? | NFR-06, TC-07 |
| Q-03 | Template và file lưu ở đâu (cục bộ hay object store) và mô hình tenant? | FR-03, FR-15, SEC-05 |
| Q-04 | Có yêu cầu "tối đa N trang" cho loại tài liệu nào? (nếu có, thuộc module render) | Ranh giới 3.4 |
| Q-05 | Ngưỡng chấp nhận UAT và số tài liệu mẫu? | 7.3 |
| Q-06 | Chính sách retention và che dữ liệu cho audit log? | FR-16, SEC-06 |
| Q-07 | Có runner Windows + giấy phép Word cho CI không? | D-13, TC-06 |
| Q-08 | Phạm vi định dạng mở rộng sau `.docx` và thứ tự ưu tiên? | FR-18 |
| Q-09 | Mặc định nghiệp vụ cho tài liệu có TOC: chấp nhận hộp thoại cập nhật (`update_on_open`), bỏ số trang (`no_page_numbers`), hay chờ module render tính số trang (`oracle_estimate`)? | D-08, FR-12 |
| Q-10 | Client MCP của Antigravity hỗ trợ roots, `resources/read`, `resource_link` đến mức nào? | FR-15, SEC-07 |
