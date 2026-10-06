# Diagram Engine MCP — Kế hoạch Nền tảng (Foundation Plan)

| Thuộc tính | Giá trị |
|---|---|
| Tài liệu | Foundation Plan — Core Engine cho sơ đồ kỹ thuật (.drawio) thuộc Nhóm 4: Kiến trúc Hệ thống và Phần mềm |
| Phiên bản | 1.0 (Baseline để đối chiếu và triển khai) |
| Ngày | 2026-10-06 |
| Chủ sở hữu | MinMin |
| Trạng thái | Draft chờ phê duyệt baseline |
| Phạm vi tài liệu | Core engine (MCP Server) sinh, kiểm định, kiểm tra và render sơ đồ kỹ thuật Nhóm 4. Không bao gồm cách tích hợp vào Antigravity, không bao gồm biểu đồ số liệu (Chart), không bao gồm sơ đồ mạch điện/schematic |
| Tài liệu liên quan | Docx Engine MCP — Foundation Plan v1.1 và Xlsx Engine MCP — Foundation Plan v1.1 (dùng chung hợp đồng `FileRef`, phong bì kết quả, họ mã lỗi, nguyên tắc tất định) |

## Lịch sử thay đổi

| Phiên bản | Nội dung |
|---|---|
| 1.0 | Bản baseline đầu tiên. Tổng hợp từ: (1) định hướng kiến trúc 5 trụ cột và bản đồ công cụ (tài liệu định hướng Diagram & Chart); (2) đánh giá khoảng trống của bản định hướng (thiếu Gate ngữ nghĩa, thiếu các hạng mục của một Foundation Plan); (3) kết quả Phase 0 Spike S1-S4 chạy ngày 2026-10-06 trên Windows 11, Python 3.12, Node.js v22.12.0 (Phụ lục E); (4) đánh giá 6 điểm nghẽn kiến trúc (runtime, tách sinh XML/render, đo chữ, waypoint). **Đính chính quan trọng sau khi đọc lại mã spike:** kết luận của S3 (hệ số `K_adj = 0.78`) **không dùng được** vì lỗi đơn vị cỡ chữ trong script, kết luận của S2 mới xác nhận *cấu trúc XML*, chưa xác nhận hành vi trên draw.io thật, và S4 mới xác nhận tính tất định trong một tiến trình với 5 nút (Phụ lục D, E). Thêm Gate ngữ nghĩa DG-00 (4.8), bộ Gate DG-00..DG-08 (4.9), 5 spike bổ sung S5-S9 (Phụ lục A) |

## Cách đọc tài liệu này (dành cho người và AI)

- Mỗi yêu cầu có **mã định danh** để đối chiếu: `P-xx` (vấn đề), `D-xx` (quyết định thiết kế), `FR-xx` (chức năng), `NFR-xx` (phi chức năng), `SEC-xx` (bảo mật), `DG-xx` (cổng kiểm định chung), `PG-xx` (cổng kiểm định theo loại sơ đồ), `SEM-xx` (luật ngữ nghĩa), `TC-xx` (ca kiểm thử), `R-xx` (rủi ro), `Q-xx` (câu hỏi mở), `EV-xx` (bằng chứng thực nghiệm), `MX_INV_xx` (bất biến Draw.io đã có từ trước).
- Mức ưu tiên: **MVP** (bắt buộc cho bản đầu), **P1** (làm ngay sau MVP), **P2** (mở rộng).
- Nhãn `[ĐÃ KIỂM CHỨNG]`: nhận định đã được xác nhận bằng thực nghiệm (Phụ lục E, mã `EV-xx`). Phạm vi xác nhận luôn được nêu kèm.
- Nhãn `[CHƯA KẾT LUẬN]`: đã có thực nghiệm nhưng thiết kế thực nghiệm không đủ để rút kết luận; phải chạy lại.
- Nhãn `[CẦN KIỂM CHỨNG]`: nhận định kỹ thuật chưa được xác nhận bằng thực nghiệm; phải chốt trong Phase 0 (Phụ lục A).
- Nhãn `[ĐỀ XUẤT]`: con số hoặc lựa chọn do tài liệu này đề xuất, chưa được chủ sở hữu phê duyệt.
- Khi mâu thuẫn, thứ tự ưu tiên: Mục 3 (Nguyên tắc và Quyết định) > Mục 4 (Kiến trúc) > các mục còn lại.

## Tóm tắt điều hành

Diagram Engine là một **MCP Server tất định (deterministic)** chuyên sinh, kiểm định, kiểm tra và render sơ đồ kỹ thuật thuộc Nhóm 4 (ERD, UML, kiến trúc hệ thống/cloud, sơ đồ mạng) ra file `.drawio` sửa được. AI (Antigravity) là **client**: chỉ khai báo **DiagramSpec JSON** (nội dung, quan hệ, gợi ý bố cục), không viết XML và không đưa tọa độ. Engine **không tự gọi AI** và **không dựa vào AI để bảo đảm tính đúng đắn**. Engine:

1. **Kiểm tra schema** DiagramSpec, rồi chạy **Gate ngữ nghĩa DG-00** (khóa ngoại trỏ bảng không tồn tại, vòng kế thừa, thông điệp đi ngược thời gian, Subnet nằm ngoài VPC, CIDR chồng lấn...) **trước khi tính hình học**. Lỗi ngữ nghĩa dừng pipeline, không phát hành file.
2. **Đo chữ** bằng font được ghim và đóng gói, tính kích thước nút và nhãn.
3. **Tính bố cục** theo `diagram_type`: ELK (Node sidecar) cho đồ thị tự do và đồ thị lồng nhau; Python thuần cho bố cục có cấu trúc cứng (Sequence, DFD, hub-and-spoke).
4. **Định tuyến** dây Manhattan, sinh **waypoint tường minh** và cổng neo phân số theo dòng của bảng.
5. **Sinh XML** `mxGraphModel` bằng một bộ tuần tự hóa duy nhất (`lxml`), không cần trình duyệt, không cần mxGraph runtime.
6. **Kiểm định** bằng chuỗi cổng DG-00..DG-08 và cổng theo loại sơ đồ (PG), rồi trả file kèm **báo cáo chẩn đoán có cấu trúc** để AI tự quyết định bước tiếp theo.
7. **Render ảnh (Pha 2)** là công cụ riêng, chỉ chạy khi có yêu cầu; chèn vào Word/Excel đi qua `FileRef` sang Docx/Xlsx Engine, Diagram Engine không viết OOXML.

Engine cam kết **tính hợp lệ cấu trúc, tính hợp lệ ngữ nghĩa của spec, không node chồng nhau, không dây xuyên node không liên quan, và số điểm giao cắt được tối thiểu hóa và báo cáo**; engine **không cam kết** "zero-crossing" trên đồ thị dày hoặc không phẳng, không cam kết hình thức pixel giống hệt giữa draw.io và các trình đọc khác, và không cam kết số đo chữ chính xác tuyệt đối (xem 3.4).

---

## 1. Context

### 1.1. Bối cảnh

- Dự án Doc_Handler cung cấp cho AI Antigravity bộ công cụ làm việc với tài liệu văn phòng. Docx Engine và Xlsx Engine đã có Foundation Plan; Diagram Engine là hạng mục tiếp theo, hiện tập trung **Nhóm 4: Kiến trúc Hệ thống và Phần mềm**.
- Hiện trạng đã có lõi `mxgraph_engine.py` (nền tảng sinh draw.io), bộ bất biến `MX_INV_01..21`, kịch bản `validate_drawio.py` (4 cổng), tiêu chuẩn `rule_database_erd_standards.md`, bộ chạy ảnh `mxgraph_runner.html` + `mxClient.min.js` (headless Edge/Chrome). Các thành phần legacy (`spec_diagram_engine`, trình soạn thảo Tkinter) đã được loại bỏ hoàn toàn.
- Engine được đóng gói dưới dạng MCP, trong đó engine là server và AI là client, cùng mô hình với Docx/Xlsx Engine.
- Môi trường sử dụng chính là tiếng Việt; file `.drawio` được mở bằng Draw.io Desktop, diagrams.net hoặc tiện ích VS Code (xem NFR-07).
- Định hướng triển khai: chạy cục bộ trước (Windows), có khả năng đóng gói container Linux và thương mại hóa sau; vì vậy ưu tiên giấy phép dễ phân phối và không phụ thuộc phần mềm cài sẵn.

### 1.2. Phạm vi

| Trong phạm vi (In scope) | Ngoài phạm vi (Out of scope) |
|---|---|
| Sinh `.drawio` từ DiagramSpec cho Nhóm 4: ERD, Architecture/Cloud/Kubernetes, Network, Sequence (MVP); Class, Use Case, State, Component, Deployment, C4, DFD (P1) | Cách cắm vào Antigravity (cấu hình, transport MCP) |
| Kiểm tra ngữ nghĩa spec (DG-00), tính bố cục, định tuyến, đo chữ, tuần tự hóa XML | **Biểu đồ số liệu/Chart** (bar, line, pie, waterfall, DrawingML): chuyển sang kế hoạch riêng; phần chart relink thuộc Xlsx Engine (FR-17 của Xlsx Engine) |
| Chuỗi cổng kiểm định DG-00..DG-08 và cổng theo loại sơ đồ | **Schematic/sơ đồ mạch điện và hardware wiring** (không thuộc Nhóm 4; `MX_INV_10`, `MX_INV_13` giữ nguyên trong tài liệu cũ, chờ Q-01) |
| Đóng gói nhiều trang trong một file `.drawio`; tự chia trang theo module (P1) | Viết OOXML để chèn vào Word/Excel (thuộc Docx/Xlsx Engine) |
| Render PNG/SVG (Pha 2) qua công cụ riêng; kiểm chứng với Oracle | Bảo đảm hình thức pixel giống hệt giữa các trình đọc |
| Inspect, patch và bố cục ổn định khi sửa vòng hai (P1) | Soạn nội dung sơ đồ thay AI; engine không tự bịa quan hệ |
| Nhập từ nguồn có cấu trúc: SQL DDL, DBML, OpenAPI, docker-compose (P1) | Vòng lặp tự sửa dựa trên thị giác (OCR, mô hình thị giác) |
| Cưỡng chế bất biến `MX_INV_xx` bằng gate hoặc test | Mermaid/PlantUML như đường vào hoặc đường ra (không dùng dịch vụ ngoài) |
| Điểm mở rộng cho loại sơ đồ/adapter khác (FR-27) | Thực thi mã trong nhãn, macro, plugin draw.io |

### 1.3. Mối quan hệ với Docx Engine, Xlsx Engine và module Chart

- **Docx/Xlsx Engine:** dùng chung ba hợp đồng: `FileRef` (URI mờ kèm `sha256`), phong bì kết quả (`success`, `file_ref`, `diagnostics`, `guarantees_applied`, `stats`) và họ mã lỗi (`E-*`, `W-*`, `I-*`). Khác nhau ở mã lỗi theo miền (`E-SEM-*`, `E-LAYOUT-*`, `E-ROUTE-*`, `E-XML-*`, `E-RENDER-*`...).
- **Chèn sơ đồ vào tài liệu:** Diagram Engine xuất `FileRef` (PNG/SVG); Docx Engine nhận làm khối `image` của DocSpec hoặc `patch_docx`; Xlsx Engine nhận làm ảnh trong sheet. Diagram Engine **không** ghi OOXML (D-17), nên không có thành phần `docx`, `exceljs`, `xml-crypto` ở đây.
- **Chart:** đóng băng, có kế hoạch riêng (D-18). Lý do: chart nghiệp vụ phải sửa được số liệu gốc trong Office (DrawingML native), là bài toán thuộc ranh giới Docx/Xlsx Engine, không thuộc draw.io.

### 1.4. Thuật ngữ

| Thuật ngữ | Nghĩa |
|---|---|
| DiagramSpec | Mô tả sơ đồ dạng JSON có schema và phiên bản (AST khai báo), AI chỉ sinh cái này |
| `diagram_type` | Khóa phân biệt loại sơ đồ (`erd`, `architecture`, `sequence`...), quyết định schema, luật ngữ nghĩa, thuật toán bố cục |
| Layout Hints | Gợi ý bố cục AI được phép đưa: hướng, nhóm, hạng (rank), ghim; không phải tọa độ |
| Layout Oracle | Thành phần tính tọa độ: ELK (Node sidecar) hoặc bộ bố cục Python |
| Sidecar | Tiến trình Node (`elk_worker.mjs`) nhận JSON qua stdin, trả JSON tọa độ qua stdout |
| Router | Thành phần tính đường đi dây Manhattan, cổng neo và waypoint |
| Waypoint | Điểm gấp khúc tường minh `<mxPoint>` trong `<Array as="points">` |
| Fractional Port | Cổng neo phân số `exitX/exitY/entryX/entryY` trên cạnh của node, kèm `exitDy/entryDy` theo dòng |
| Corridor | Hành lang song song rời rạc dành cho các tuyến bus/dây dài |
| Snug Label | Nhãn có độ rộng ôm sát chữ, mặt nạ nền ôm khít |
| Gate | Một phép kiểm định có tiêu chí đo được: `DG` (chung mọi loại), `PG` (theo loại sơ đồ), DG-00 là Gate ngữ nghĩa |
| Semantic Gate | DG-00: kiểm tra ý nghĩa của sơ đồ trên spec, trước khi tính hình học |
| Stable Layout | Bố cục ổn định: sửa một phần không làm xáo các node không liên quan |
| Pha 1 / Pha 2 | Pha 1: sinh XML (không cần trình duyệt). Pha 2: render ảnh (cần trình duyệt headless hoặc CLI) |
| Renderer | Bộ chạy ảnh: headless Edge/Chrome + `mxgraph_runner.html`, hoặc draw.io CLI |
| Oracle | Phần mềm tham chiếu (draw.io thật) dùng trong CI để kiểm chứng, không dùng ở runtime |
| FileRef | Đối tượng `{uri, sha256, size, mime, expires_at}` với URI mờ, thay cho việc truyền byte |
| Diagnostics | Báo cáo lỗi/cảnh báo có cấu trúc do engine trả về |
| `MX_INV_xx` | Bất biến Draw.io đã được thống nhất từ trước (ví dụ `MX_INV_03` docking vào container) |

### 1.5. Giả định và ràng buộc

- Stack lõi (D-02): Python với `Pydantic v2`, `lxml`, `Pillow` (đo chữ), một chỉ mục không gian (R-tree) cho DG-03; **Node sidecar** với `elkjs` cho bố cục đồ thị; Renderer headless Edge/Chrome (S1) và draw.io CLI làm Oracle. `LibreOffice` không tham gia.
- Giấy phép phụ thuộc phải được kiểm tra trước khi phân phối `[CẦN KIỂM CHỨNG]`: `elkjs` (ghi nhận hiện tại EPL-2.0; chạy như tiến trình riêng, cần xác nhận pháp lý), `Pillow`, `lxml`, mxGraph/draw.io shapes (Apache-2.0), và **điều khoản dùng icon của từng nhà cung cấp cloud** (AWS/Azure/GCP/CNCF).
- Font: Windows có sẵn Arial/Segoe UI, nhưng container Linux thì không và không được giả định có sẵn "100% trên web". Font phải được ghim và đóng gói (D-08), với giấy phép cho phép phân phối.
- Thực nghiệm S1-S4 chạy trên Windows 11, Python 3.12, Node.js v22.12.0. **Draw.io Desktop/CLI chưa được cài** trên máy thử (EV-01), nên mọi nhận định về hành vi draw.io thật đều chưa được xác nhận.
- Người dùng doanh nghiệp tự chỉnh `.drawio` bằng tay sau khi nhận file; vì vậy bố cục ổn định và waypoint không bị draw.io tính lại là yêu cầu hạng nhất.

---

## 2. Problem

| ID | Vấn đề | Hệ quả nếu không giải quyết |
|---|---|---|
| P-01 | LLM không tất định và "ảo tưởng không gian 2D": viết hàng nghìn ký tự XML với tọa độ và thẻ đóng dễ sai | File hỏng, dây lệch, mất niềm tin |
| P-02 | Edge chỉ khai báo `source`/`target` với `edgeStyle=orthogonalEdgeStyle` thì draw.io tự định tuyến khi mở/di chuyển node. S2 chỉ mới tạo hai file thử, **chưa mở trên draw.io thật** nên chưa biết các điểm `mxPoint` có thực sự đóng băng hay chỉ là gợi ý cho bộ định tuyến trực giao `[CẦN KIỂM CHỨNG: EV-02, S5]` | Toàn bộ công sức corridor/waterfall routing có thể bị xóa khi người dùng mở file |
| P-03 | Một thuật toán bố cục không phù hợp mọi loại sơ đồ: Sugiyama tốt cho luồng, kém cho ERD lớn và topology mạng; Sequence cần bố cục lifeline riêng; sơ đồ cloud cần bố cục lồng nhau | ERD kéo dài sọc khó đọc; container phình; Sequence sai trục thời gian |
| P-04 | Đo chữ chưa có số liệu đáng tin: S3 so hai **ước lượng** với nhau (heuristic ký tự và Pillow), không so với draw.io; và script quy đổi `14px` thành `10pt` rồi truyền vào `ImageFont.truetype(size=...)`, tham số này tính bằng **pixel**, nên đo ở cỡ 10px thay vì 14px; ngoài ra dùng `getbbox` (ink bounds) thay vì độ dài advance `[CHƯA KẾT LUẬN: EV-03, EV-05]` | Sai số nhãn không biết chiều nào: mặt nạ phình (che dây) hoặc quá chật (chữ bị wrap/cắt) |
| P-05 | Renderer hiện tại là `mxClient.min.js` trong headless browser. S1 chứng minh nó **lặp lại ổn định** (5/5, cùng 1416×1244 px, 47.797 byte) nhưng không chứng minh nó **giống draw.io thật**: `shape=table`, `childLayout=tableLayout` là thành phần của lớp `Graph` trong draw.io, không chắc có trong mxGraph lõi `[CẦN KIỂM CHỨNG: S9]`. Cold start 7,20 s, trung bình 2,80 s; phụ thuộc `msedge.exe`/`chrome.exe` | Ảnh xuất khác file mở trong draw.io; chi phí và độ ổn định trên Linux/đồng thời chưa rõ |
| P-06 | Các cổng hiện tại (và bản định hướng 6 cổng) đều là hình học và định dạng; không bắt lỗi ngữ nghĩa: khóa ngoại trỏ bảng không tồn tại, vòng kế thừa, thông điệp Sequence đi ngược thời gian, Subnet ngoài VPC, CIDR chồng lấn | Sơ đồ đẹp nhưng sai nghĩa, nguy hiểm hơn lỗi hình học |
| P-07 | Hệ thống lớn (50 microservice, hàng trăm bảng): spec khổng lồ, AI quên quy tắc ở giữa/cuối, sinh cạnh mồ côi; sơ đồ một trang không đọc được | Mất kết nối, thiếu thuộc tính, sơ đồ phình vô hạn |
| P-08 | Cổng neo ở mức cạnh của node không đủ cho ERD: dây One-to-Many phải cắm vào **dòng** chứa khóa ngoại, nhưng `MX_INV_03` cấm trỏ vào cell con | Dây đè chữ của chính bảng hoặc cắm sai dòng |
| P-09 | Người dùng sửa tay trong draw.io rồi nhờ AI sửa tiếp; bố cục tính lại từ đầu làm xáo toàn bộ | Mất công sức chỉnh tay, không dùng được ở vòng hai |
| P-10 | Bất biến `MX_INV_xx` hiện là văn bản, chưa chắc là mã (bài học R-13 của Xlsx Engine) | Quy tắc không được cưỡng chế, trôi dần |
| P-11 | Bề mặt tấn công: nhãn `html=1` (script, `onerror`, `javascript:`), liên kết trong `UserObject`, ảnh `data:`/URL ngoài trong style, XXE và nén khi nhập `.drawio`, SVG đầu ra | Thực thi mã khi mở file/ảnh, rò rỉ |
| P-12 | Tên style/icon sai (ví dụ `mxgraph.aws4.*` gõ sai) cho ra hình trống mà không có lỗi | Sơ đồ thiếu icon âm thầm |
| P-13 | Cam kết "Zero-Collision", "Zero-Zigzag", "đồng nhất 100%" quá tuyệt đối: đồ thị dày/không phẳng (K5) không thể không giao cắt | Cam kết sai; không có thước đo chất lượng |
| P-14 | Tiếng Việt: NFD/NFC, font server thiếu glyph dấu, chuỗi tổ hợp đo sai | Chữ lỗi, tràn nhãn |
| P-15 | ELK là Node/Java-gốc, không có tương đương Python đạt chuẩn; tính tất định mới chứng minh trong **một tiến trình**, 10 lần chạy, 5 nút, không port, không phân cấp, chỉ so tọa độ nút (không so điểm gấp khúc của dây); tọa độ phân số (`105,17`) cần quy về lưới `[ĐÃ KIỂM CHỨNG có giới hạn: EV-04]` | Phụ thuộc Node và giấy phép; rủi ro tất định ở phạm vi rộng hơn chưa biết |
| P-16 | Chưa có đường vào tự động từ nguồn thật (SQL DDL, OpenAPI, docker-compose, Terraform): AI phải tự khai báo mọi thứ | Spec lớn, dễ sai; bỏ lỡ cách tất định nhất để sinh ERD/kiến trúc |
| P-17 | Phạm vi bị trộn: schematic, chart, DrawingML và bộ thư viện Node ghi OOXML nằm cùng tài liệu định hướng | Trùng lặp với Docx/Xlsx Engine; kế hoạch loãng |
| P-18 | Giao tiếp AI-engine: truyền byte file làm phình context; AI không có cách trỏ lại đúng node/dây/trang bị lỗi | Tốn token, vòng sửa không chính xác |

---

## 3. Solution

### 3.1. Nguyên tắc thiết kế

1. **Engine tất định, AI quyết định.** Engine không chứa logic tự trị, không gọi ngược AI. "Tất định" được hiểu là tương đương về ngữ nghĩa (so sánh XML đã chuẩn hóa), không phải trùng byte (NFR-01).
2. **AI khai báo, engine tính.** AI chỉ đưa DiagramSpec và gợi ý bố cục. Toàn bộ tọa độ, định tuyến, đo chữ thuộc engine.
3. **Ngữ nghĩa trước hình học.** Spec sai nghĩa bị chặn ở DG-00 trước khi tốn công tính bố cục (fail-closed).
4. **Tách sinh XML khỏi render.** Pha 1 không cần trình duyệt; Pha 2 là công cụ riêng.
5. **Waypoint tường minh.** Mọi dây không phải đoạn thẳng đều mang điểm gấp khúc tường minh; không giao cho draw.io tự quyết.
6. **Đo được thay cho đoán.** Mọi cam kết gắn với phép đo (cổng, số giao cắt, quality score). Điều chỉ ước lượng được (đo chữ) mang nhãn `estimated`.
7. **Một đường ghi XML duy nhất.** Mọi phần tử đi qua XML Serializer; cấm nối chuỗi tay.
8. **Bất biến là mã.** Mỗi `MX_INV_xx` phải có gate hoặc test tương ứng (D-10).
9. **Bố cục ổn định.** ID tất định, ghim vị trí, bố cục tăng dần; sửa một phần không xáo phần còn lại.
10. **Handle thay cho byte.** File đi qua `FileRef`; không truyền base64 nội tuyến.
11. **Cam kết tường minh.** Tài liệu liệt kê rõ engine bảo đảm gì và không bảo đảm gì (3.4).
12. **Phụ thuộc có kỷ luật.** Thư viện ngoài nằm sau interface, ghim phiên bản, rà giấy phép; sidecar cách ly.

### 3.2. Nhật ký quyết định

| ID | Quyết định | Lý do | Phương án đã loại |
|---|---|---|---|
| D-01 | Engine là MCP tool server tất định; AI là client | Nhất quán với Docx/Xlsx Engine; server không gọi ngược client | Engine gọi AI để tự sửa sơ đồ |
| D-02 | **Runtime: Python lõi + Node sidecar** (`elk_worker.mjs` qua stdin/stdout JSON). Python là chủ quản (MCP, validate, FileRef, gate); Node chỉ tính tọa độ. Sơ đồ có cấu trúc cứng (Sequence, DFD 5 cột, hub-and-spoke) do Python tính 100%, không gọi Node | Cùng stack MCP với Docx/Xlsx; ELK là lựa chọn mạnh duy nhất cho layered + cổng cố định + lồng nhau mà không cần cài phần mềm thứ ba; Node chỉ là worker | Node độc lập (lệch hệ sinh thái); Pure Python tự viết Sugiyama/orthogonal (tốn tháng, kém); Graphviz binary (ngoài C++, kém port/lồng) |
| D-03 | Tách **Pha 1 (sinh XML, không trình duyệt)** và **Pha 2 (`render_diagram`, chỉ khi có yêu cầu)** | `.drawio` là XML; tọa độ đã có thì tuần tự hóa không cần đồ họa; giảm tài nguyên | Sinh XML qua mxGraph trong trình duyệt |
| D-04 | Không dùng `jsdom` + `mxClient.min.js` để tính bố cục hay đo chữ | `jsdom` không có layout/`getBBox` thật; mxGraph đã ngừng phát triển; không có lợi ích so với Pha 1 thuần Python. *Đây là quyết định loại bỏ dựa trên lý do kỹ thuật, không dựa trên thực nghiệm* | Mock hàng trăm API trình duyệt |
| D-05 | **Bố cục chọn theo `diagram_type`** (bảng 4.5); mỗi loại có thuật toán, luật ngữ nghĩa và PG riêng | Loại P-03; tránh một thuật toán cho mọi thứ | Sugiyama cho tất cả |
| D-06 | **Waypoint tường minh bắt buộc**; `routing_mode` chọn theo kết quả S5 (draw.io thật): `orthogonal_with_points`, `polyline_with_points` hoặc `segment_style`. Mặc định tạm thời: `orthogonal_with_points` cho đến khi S5 chốt | Loại P-02; S2 mới xác nhận cấu trúc XML | Để draw.io tự định tuyến |
| D-07 | **Docking ở mức container** (`MX_INV_03`): `source`/`target` của edge luôn trỏ vào node/bảng cha, vị trí dòng điều khiển bằng `exitY/entryY` phân số và `exitDy/entryDy` | Giải P-08 mà không vi phạm bất biến | Nối vào cell con |
| D-08 | **Đo chữ bằng font ghim và đóng gói**, `Pillow.ImageFont.truetype(path, size=PIXEL)` và `font.getlength(text)` (độ dài advance, không dùng `getbbox`), chuẩn hóa NFC trước khi đo, có cache. Hủy hệ số `K_adj = 0.78` (EV-05). Số đo luôn gắn `estimated`; biên an toàn là tham số theo font, chốt bằng ground truth từ draw.io (S6) | Loại P-04, P-14 | Heuristic `len(text)*k`; hệ số thực nghiệm từ S3 |
| D-09 | **Gate ngữ nghĩa DG-00** chạy trước bố cục, fail-closed, luật theo `diagram_type` (4.8); lỗi ngữ nghĩa `fixable_by=ai`, engine không tự sửa nghĩa | Loại P-06 | Chỉ kiểm hình học |
| D-10 | Chuỗi cổng **DG-00..DG-08** + **PG** theo loại; mỗi `MX_INV_xx` ánh xạ về một gate hoặc test (bảng 4.9); có meta-test (TC-43) | Loại P-10 | Bất biến chỉ là tài liệu |
| D-11 | **Bố cục ổn định:** ID do spec cung cấp (không sinh ngẫu nhiên), ghim vị trí khi vá, bố cục tăng dần, toạ độ quy về lưới | Loại P-09 | Tính lại bố cục toàn bộ mỗi lần |
| D-12 | AI chỉ truyền **gợi ý** (`direction`, `groups`, `rank`, `pin_to_side`, `importance`), không truyền tọa độ. Tọa độ chỉ xuất hiện khi vá từ file có sẵn (đọc ra từ file, không do AI bịa) | Loại P-01; bố cục là việc của engine | AI đưa tọa độ |
| D-13 | **Registry style và icon dạng allow-list**; tên không có trong registry là `E-STYLE-UNKNOWN`; mỗi mục registry có test render không trống | Loại P-12, P-11 | Cho AI viết style tự do |
| D-14 | **Một điểm ghi XML:** XML Serializer (`lxml`), thứ tự thuộc tính và phần tử cố định, escape tại một điểm | Tất định, sạch XML | Nối chuỗi |
| D-15 | **Một file, nhiều trang** (`MX_INV_09`); tự chia trang theo module khi vượt ngưỡng (P1), có trang tổng quan | Loại P-07 | Một trang khổng lồ |
| D-16 | **Renderer là Strategy:** headless browser + runner (S1) | draw.io CLI | (P1) SVG→PNG thuần cho Linux tối giản. Kiểm chứng độ giống draw.io thật bằng Oracle trong CI (DG-08, S9) | Chỉ một renderer cố định |
| D-17 | Không viết OOXML trong Diagram Engine; chèn vào Word/Excel qua `FileRef` sang Docx/Xlsx Engine. Loại `docx`, `exceljs`, `xml-crypto`, `archiver` | Tránh OOXML writer thứ hai | Nhúng DrawingML từ Diagram Engine |
| D-18 | Chart và Schematic **ngoài phạm vi** bản này; sẽ có kế hoạch riêng (Q-01, Q-02) | Loại P-17; tập trung Nhóm 4 | Gộp chung |
| D-19 | **Importer tất định** (SQL DDL, DBML trước; OpenAPI, docker-compose, Terraform/K8s sau) sinh DiagramSpec, là đường vào ưu tiên (P1) | Loại P-16; giảm spec do AI sinh | Chỉ AI khai báo |
| D-20 | **Chất lượng đo được:** `quality_score` gồm số giao cắt, số điểm gấp, tổng độ dài dây, tỷ lệ khung; cam kết "không chồng node, không dây xuyên node không liên quan", **không** cam kết zero-crossing | Loại P-13 | Cam kết tuyệt đối |
| D-21 | `elkjs` chạy **như tiến trình riêng**, ghim phiên bản; rà giấy phép trước khi phân phối; có đường lùi (fallback) bố cục Python đơn giản kèm `W-LAYOUT-FALLBACK` khi Node vắng (P1) | Loại P-15 | Gắn cứng vào ELK |
| D-22 | Phase 0 **mở lại** S3 và **mở rộng** S2, S4 (Phụ lục A) | Kết luận hiện có không đủ | Coi S1-S4 là đã đóng |

### 3.3. Tổng quan giải pháp

```
AI (client) --MCP--> [ Diagram Engine:
      validate schema -> DG-00 ngữ nghĩa -> style/icon registry -> đo chữ
      -> bố cục (ELK sidecar | Python) -> router (waypoint, cổng phân số)
      -> XML Serializer -> DG-01..DG-07 + PG ]
                                      |
                       FileRef(.drawio) + Diagnostics (anchor, fixable_by, evidence, quality)
                                      |
AI quyết định: chấp nhận / sửa spec / đổi gợi ý bố cục / hỏi người dùng
                                      |
                  (tùy chọn) render_diagram -> PNG/SVG -> FileRef -> Docx/Xlsx Engine
```

### 3.4. Ranh giới cam kết

| Engine bảo đảm | Engine KHÔNG bảo đảm |
|---|---|
| File `.drawio` là XML `mxGraphModel` hợp lệ, ID duy nhất, cây parent đúng, edge không mồ côi | Hình thức pixel giống hệt giữa draw.io Desktop, diagrams.net, VS Code extension và trình xem khác |
| Spec đã qua DG-00: không có lỗi ngữ nghĩa mức `error` (khóa ngoại hợp lệ, không vòng kế thừa, thời gian Sequence đơn điệu, lồng nhau/CIDR hợp lệ...) | Sơ đồ phản ánh đúng *ý đồ nghiệp vụ* của người dùng (engine chỉ kiểm nhất quán nội tại) |
| Không node nào chồng nhau; khoảng cách tối thiểu theo tham số; không dây xuyên node không phải đầu mút | Zero-crossing: số giao cắt được tối thiểu hóa, **báo cáo**, không hứa bằng 0 |
| Waypoint tường minh được ghi đúng; hành vi giữ nguyên của chúng sau khi mở trên draw.io là điều **cần kiểm chứng** theo `routing_mode` (S5) | Draw.io không tự định tuyến lại khi người dùng "Reset Edge", di chuyển node hoặc đổi kiểu dây |
| Kích thước nhãn tính từ font ghim, gắn `estimated`; kiểm tra nhãn nằm trong giới hạn đã tính | Số đo chữ khớp pixel với mọi trình đọc/font thay thế |
| Mọi `MX_INV_xx` đã ánh xạ được kiểm bằng gate hoặc test | Bất biến chưa ánh xạ (ghi trong 4.9) cho đến khi được rà soát |
| Cùng đầu vào cho cùng XML sau chuẩn hóa (cùng phiên bản engine, ELK, font) | Trùng byte; tất định giữa **phiên bản ELK/font khác nhau** |
| Diagnostics chỉ dựa trên tiêu chí đo được; điều ước lượng mang nhãn `estimated` | Chẩn đoán thẩm mỹ chủ quan |
| Ảnh Pha 2 lặp lại được (cùng renderer, cùng đầu vào, cùng kích thước) | Ảnh Pha 2 giống hệt ảnh xuất từ draw.io thật (đo ở S9, ghi trong NFR-07) |

---

## 4. Architecture

### 4.1. Sơ đồ logic

```
┌────────────────────────────────────────────────────────────────────────┐
│                     ANTIGRAVITY AI (MCP Client)                        │
│ - Sinh DiagramSpec + Layout Hints (không tọa độ, không XML)            │
│ - Đọc Diagnostics, quyết định sửa spec / chấp nhận / hỏi người dùng    │
└───────────────────────────────┬────────────────────────────────────────┘
                                │ MCP tool calls (FileRef, JSON)
┌───────────────────────────────▼────────────────────────────────────────┐
│                  DIAGRAM ENGINE (MCP Server, tất định, Python)         │
│                                                                        │
│ [A] API & Policy: xác thực tenant, giới hạn tài nguyên, audit          │
│ [B] Spec Registry & Validation: schema theo diagram_type (Pydantic)    │
│ [C] Source Importers (P1): SQL DDL | DBML | OpenAPI | compose          │
│ [D] Semantic Linter  DG-00: luật SEM-* theo diagram_type               │
│ [E] Style & Icon Registry (allow-list) + Text Measurer (font ghim)     │
│ [F] Layout Dispatcher:                                                 │
│       ELK Client ──stdin/stdout──► Node sidecar (elk_worker.mjs)       │
│       Python layouts: Sequence | DFD 5 cột | Radial hub-and-spoke      │
│ [G] Router: cổng phân số, waypoint, corridor, bundling (P1)            │
│ [H] Page Splitter (P1) + XML Serializer (lxml, một đường ghi)          │
│ [I] Gate Runner: DG-01..DG-07 + PG theo loại; Quality Metrics          │
│ [J] Diagnostics Builder: issues có anchor, severity, fixable_by        │
│ [K] Inspect / Patch (P1): anchor ổn định, bố cục ổn định               │
│                                                                        │
│ Cross-cutting: Sandbox (Node, browser), File Store (FileRef), Audit    │
└───────┬───────────────────────────────────────────────┬────────────────┘
        │ FileRef(.drawio)                              │ (Pha 2, công cụ riêng)
        ▼                                               ▼
 [Người dùng mở trong draw.io]            [Render Service: headless browser | draw.io CLI]
                                                        │ FileRef(PNG/SVG)
                                                        ▼
                                         [Docx Engine / Xlsx Engine chèn ảnh]
```

### 4.2. Thành phần và trách nhiệm

| Thành phần | Trách nhiệm | Công nghệ | Yêu cầu liên quan |
|---|---|---|---|
| API & Policy | Xác thực, giới hạn kích thước/thời gian, định tuyến công cụ, ghi audit | MCP SDK (Python) | NFR-02, SEC-05, FR-23 |
| Spec Registry & Validation | JSON Schema/Pydantic theo `diagram_type` (discriminated union), phiên bản schema, lỗi có JSON path | Pydantic v2 | FR-01, FR-02 |
| Source Importers | Chuyển nguồn có cấu trúc thành DiagramSpec tất định | Parser Python | FR-21, D-19 |
| Semantic Linter | Chạy luật SEM-* trên spec, trả `E-SEM-*`/`W-SEM-*` | Python (đồ thị thuần) | FR-03, D-09 |
| Style & Icon Registry | Allow-list style token và icon; kiểm tra tồn tại | YAML/JSON + test render | FR-04, D-13 |
| Text Measurer | Đo độ rộng/cao nhãn, quyết định wrap, cache | `Pillow`, font ghim | FR-05, FR-24, D-08 |
| Layout Dispatcher | Chọn thuật toán theo `diagram_type` và mật độ; gọi ELK hoặc bộ Python | Python + `elkjs` | FR-06, FR-07, FR-10, FR-29 |
| Router | Cổng phân số, waypoint, corridor, bundling | Python | FR-08, FR-09 |
| Page Splitter | Chia trang theo module/bounded context; trang tổng quan | Python | FR-15, FR-16 |
| XML Serializer | Tuần tự hóa `mxGraphModel`, thứ tự cố định, escape một điểm | `lxml` | FR-11, D-14 |
| Gate Runner | Chạy DG-01..DG-07 + PG; tính quality metrics | `lxml`, R-tree | FR-12, FR-13, FR-25 |
| Diagnostics Builder | Chuẩn hóa lỗi thành `issues` | Pydantic | FR-14 |
| Render Service | Render PNG/SVG từ `.drawio` (Pha 2) | Headless Edge/Chrome + `mxgraph_runner.html`; draw.io CLI | FR-17, D-16 |
| Render Oracle | Mở file bằng draw.io thật trong CI, so ảnh/kích thước (DG-08) | draw.io CLI | FR-18 |
| Inspect/Patch | Cây cấu trúc có anchor, sửa khai báo, bố cục ổn định | `lxml` | FR-19, FR-20 |
| Sandbox | Chạy Node sidecar và trình duyệt trong tiến trình cách ly, timeout, không mạng | OS/container | SEC-04, NFR-03 |
| File Store | Cấp và giải `FileRef`, TTL, cách ly theo tenant | Cục bộ hoặc object store | FR-22, SEC-05 |
| Audit Log | Nhật ký thao tác che dữ liệu nhạy cảm | JSONL/OpenTelemetry | FR-23, SEC-06 |

### 4.3. Hợp đồng công cụ MCP (v1)

| Công cụ | Mục đích | Đầu vào chính | Đầu ra chính | Ưu tiên |
|---|---|---|---|---|
| `get_diagram_schema` | Trả JSON Schema và ví dụ theo `diagram_type` cho AI | `diagram_type` | `schema`, `examples`, `limits` | MVP |
| `validate_diagram_spec` | Kiểm tra schema và DG-00 (chỉ đọc, chưa tính hình học) | `spec` | `valid`, `issues` | MVP |
| `build_diagram` | DiagramSpec → `.drawio` (Pha 1) | `spec`, `layout_policy` | `file_ref`, `diagnostics`, `quality` | MVP |
| `validate_drawio` | Chạy DG-01..DG-07 và PG trên file có sẵn | `file_ref`, `profile` | `issues`, `gates` | MVP |
| `inspect_drawio` | Đọc cấu trúc cho AI: trang, node, edge, anchor ổn định | `file_ref` | cây cấu trúc có `anchor` | MVP |
| `render_diagram` | Render PNG/SVG (Pha 2) | `file_ref`, `format`, `dpi`, `page` | `file_ref`, `render_info` | MVP |
| `patch_diagram` | Sửa file có sẵn bằng thao tác khai báo, giữ bố cục | `file_ref`, `operations[]` | `file_ref`, `diagnostics` | P1 |
| `import_source` | Nguồn có cấu trúc → DiagramSpec | `source_ref`, `source_type` | `spec`, `issues` | P1 |
| `list_style_registry` | Liệt kê token style/icon được phép | `diagram_type` | `tokens`, `icons` | P1 |

Quy ước chung:

- Tất cả tệp vào/ra là `FileRef` (không truyền byte): `{uri, sha256, size, mime, expires_at}`.
- **Chiều ra:** `uri` dạng `resource://diagram-engine/files/{opaque_id}`; id mờ, không chứa tenant/session; quyền truy cập kiểm tra ở phía server (SEC-05).
- **Chiều vào:** tệp người dùng truyền bằng `file://` nằm trong **roots** do client khai báo (SEC-07), hoặc bằng `FileRef` do engine cấp. Việc client đọc được `resources/read` hoặc `resource_link` `[CẦN KIỂM CHỨNG]` (Q-09).
- Mọi công cụ trả về cùng một phong bì kết quả. Công cụ ghi **không bao giờ ghi đè** file gốc; luôn trả `file_ref` của bản mới.
- Spec lớn dùng `modules[]` và `$ref` nội bộ (4.4); công cụ từ chối spec vượt giới hạn NFR-02.

**Phong bì kết quả**

```json
{
  "success": true,
  "file_ref": {
    "uri": "resource://diagram-engine/files/b71d...",
    "sha256": "...", "size": 18342,
    "mime": "application/vnd.jgraph.mxfile",
    "expires_at": "2026-10-07T00:00:00Z"
  },
  "diagnostics": { "errors": [], "warnings": [], "info": [] },
  "guarantees_applied": ["semantic_valid", "xml_wellformed", "ids_unique", "no_node_overlap", "waypoints_explicit"],
  "stats": {
    "pages": 2, "nodes": 38, "edges": 61, "duration_ms": 410,
    "layout": { "engine": "elk-layered", "elk_version": "x.y.z", "sidecar_ms": 62, "fallback": false },
    "text": { "metrics_source": "pillow_truetype", "font": "Liberation Sans 11px", "estimated": true },
    "quality": { "crossings": 3, "avg_bends": 1.4, "edge_length_total": 9120, "aspect_ratio": 1.52 }
  }
}
```

**Cấu trúc một issue**

```json
{
  "code": "E-SEM-ERD-001",
  "severity": "error",
  "location": { "page": "core", "anchor": "tbl_order", "json_path": "$.entities[2].columns[4].references" },
  "message": "Khóa ngoại 'customer_id' trỏ tới bảng 'customer' không tồn tại trong spec.",
  "evidence": { "column": "order.customer_id", "references": "customer.id", "known_tables": ["orders", "users", "products"] },
  "fixable_by": "ai",
  "suggested_action": "fix_reference_or_add_entity"
}
```

Họ mã lỗi: `E-SPEC-*` (schema/giới hạn spec), `E-SEM-*` (vi phạm ngữ nghĩa, theo loại: `E-SEM-ERD-*`, `E-SEM-CLS-*`, `E-SEM-SEQ-*`, `E-SEM-ARC-*`, `E-SEM-DFD-*`, `E-SEM-UC-*`, `E-SEM-ST-*`), `E-STYLE-*` (style/icon không có trong registry), `E-LAYOUT-*` (bố cục thất bại, ví dụ `E-LAYOUT-SIDECAR` khi sidecar lỗi, `E-LAYOUT-OVERLAP`), `E-ROUTE-*` (dây xuyên node, cổng ngoài cạnh, waypoint không trực giao), `E-XML-*` (XML/ID/parent/docking sai, gồm `E-XML-INV-nn` cho từng `MX_INV`), `E-RENDER-*` (render lỗi/hết thời gian), `E-SEC-*` (an ninh), `W-SEM-*` (cảnh báo ngữ nghĩa), `W-LAYOUT-*` (ví dụ `W-LAYOUT-FALLBACK`, `W-LAYOUT-QUALITY`, `W-LAYOUT-DENSE`), `W-ROUTE-*` (ví dụ `W-ROUTE-CROSSINGS`), `W-TEXT-*` (ví dụ `W-TEXT-ESTIMATED`, `W-TEXT-NO-GLYPH`), `W-RENDER-*` (ví dụ `W-RENDER-DIVERGENCE`), `I-*` (thông tin).

Quy ước mức độ: một issue cần **người dùng làm thêm một hành động** để kết quả đúng (duyệt rút gọn sơ đồ, chấp nhận bố cục dày) là `warning` với `fixable_by=human`, không hạ xuống `info`. Mã thoát khi chạy CLI/CI: `0` sạch; `1` chỉ có cảnh báo; `2` có lỗi (ngữ nghĩa, cấu trúc XML, mất kết nối).

### 4.4. DiagramSpec (FR-01, FR-02)

**Khóa phân loại.** `diagram_type` ∈ `erd` | `architecture` | `network` | `sequence` (MVP); `class` | `use_case` | `state` | `component` | `deployment` | `c4` | `dfd` (P1). Mỗi loại có schema, luật SEM, thuật toán bố cục và PG riêng.

**Quy tắc chung.**

- Mọi phần tử có `id` do spec cung cấp, duy nhất trong spec; ID này đi thẳng vào `mxCell/@id` (D-11).
- Spec **không chứa tọa độ, XML, style tự do**. Style chọn bằng **token** trong registry; icon chọn bằng khóa registry.
- `layout_hints` được phép: `direction` (`RIGHT`/`DOWN`), `groups`, `rank` (số nguyên tương đối), `pin_to_side`, `importance` (để chọn Core Hub), `max_width`.
- Spec lớn chia `modules[]` (mỗi module có thể thành một trang) và liên kết chéo module bằng `$ref`/`external_ref`; engine kiểm tra tham chiếu chéo ở DG-00.
- Giới hạn `[ĐỀ XUẤT]` (NFR-02): spec ≤ 2 MB; ≤ 300 node và ≤ 800 edge mỗi trang; ≤ 40 trang; độ sâu lồng ≤ 6; nhãn ≤ 500 ký tự.

**Ví dụ ERD:**

```json
{
  "diagram_spec_version": "1.0",
  "diagram_type": "erd",
  "title": "Đơn hàng",
  "layout_hints": { "direction": "RIGHT", "importance": { "orders": 3 } },
  "entities": [
    { "id": "users", "name": "users",
      "columns": [
        { "name": "id", "type": "bigint", "key": "PK" },
        { "name": "email", "type": "varchar(255)", "key": "UK" }
      ] },
    { "id": "orders", "name": "orders",
      "columns": [
        { "name": "id", "type": "bigint", "key": "PK" },
        { "name": "user_id", "type": "bigint", "key": "FK" },
        { "name": "ordered_at", "type": "timestamp" }
      ] }
  ],
  "relationships": [
    { "id": "rel_user_orders", "from": { "entity": "users", "column": "id", "cardinality": "one" },
      "to": { "entity": "orders", "column": "user_id", "cardinality": "many" }, "label": "đặt" }
  ]
}
```

**Ví dụ Architecture (lồng nhau):**

```json
{
  "diagram_spec_version": "1.0",
  "diagram_type": "architecture",
  "nodes": [
    { "id": "vpc1", "kind": "container", "icon": "aws.vpc", "name": "VPC", "attrs": { "cidr": "10.0.0.0/16" } },
    { "id": "sn_pub", "kind": "container", "parent": "vpc1", "icon": "aws.subnet_public", "name": "Public", "attrs": { "cidr": "10.0.1.0/24" } },
    { "id": "alb", "parent": "sn_pub", "icon": "aws.alb", "name": "ALB" },
    { "id": "api", "parent": "sn_pub", "icon": "generic.service", "name": "API Gateway" }
  ],
  "edges": [ { "id": "e1", "from": "alb", "to": "api", "protocol": "HTTPS", "port": 443 } ]
}
```

**Mapping từ nguồn (P1, D-19):** SQL DDL, DBML → `erd`; OpenAPI → `component` hoặc `sequence` (khung); docker-compose → `architecture`/`deployment`; Terraform/K8s manifest → `architecture`. Importer là tất định; chỗ mơ hồ phát `W-SEM-*` thay vì đoán.

### 4.5. Chọn bố cục theo `diagram_type` (D-05, FR-06, FR-07, FR-10)

| `diagram_type` | Thuật toán | Ai tính | Cổng (port) | Ghi chú |
|---|---|---|---|---|
| `erd` | ELK (layered/orthogonal; với đồ thị lớn hoặc dày thì chọn `stress`/`radial`/cụm theo thành phần liên thông; chốt ở S8) | Node sidecar | Cổng cố định theo dòng khóa ngoại (`FIXED_POS`) `[CẦN KIỂM CHỨNG: S8]` | Bảng không quan hệ xếp lưới; Core Hub (bậc cao nhất) đặt giữa khi dùng radial |
| `architecture` / `deployment` / `c4` | ELK phân cấp (`hierarchyHandling=INCLUDE_CHILDREN`), layered | Node sidecar | Cổng theo hướng | Container tự giãn theo con + padding; kiểm DG-04 |
| `network` | Hybrid: ELK `stress` cho topology; hub-and-spoke Python khi có Core Hub rõ | Sidecar hoặc Python | Theo cạnh | Chọn theo tỷ lệ bậc cao nhất/bậc trung bình |
| `class` | ELK layered, hướng DOWN, kế thừa hướng lên | Node sidecar | Theo cạnh | Dây kế thừa/hiện thực dùng ký hiệu riêng |
| `use_case` | ELK layered hoặc lưới; ranh giới hệ thống là container | Node sidecar | Theo cạnh | Actor ngoài biên |
| `state` | ELK layered; trạng thái hợp thành lồng nhau | Node sidecar | Theo cạnh | Một trạng thái đầu |
| `component` | ELK layered phân cấp | Node sidecar | Theo cạnh | Giao diện provided/required |
| `sequence` | **Bố cục lifeline Python**: cột theo thứ tự khai báo, trục y theo chỉ số thông điệp | Python | Không dùng ELK | Activation, fragment (`alt`/`loop`) lồng nhau |
| `dfd` | **Lưới 5 cột Python** (`MX_INV_14`) | Python | Hướng cố định | Không gọi ELK |
| (Hub-and-spoke) | **Bố cục bán kính Python** (`importance`) | Python | Cổng phân số | Hỗ trợ nhánh Bắc/Nam/Đông/Tây |

Quy tắc chung: tọa độ ELK quy về lưới (bội của 10 px `[ĐỀ XUẤT]`); mọi bố cục chạy với **hạt giống và tùy chọn ghim cố định**; kích thước đầu vào cho ELK lấy từ Text Measurer, không từ trình duyệt.

### 4.6. Định tuyến và cổng neo (FR-08, FR-09)

**Nguyên tắc.**

- **Waypoint tường minh:** mọi edge có ≥ 1 góc gấp mang `<Array as="points">` đầy đủ; edge thẳng một đoạn thì không cần. Kiểu dây (`routing_mode`) quyết định bởi S5 (D-06).
- **Docking ở container (D-07):** `source`/`target` luôn là node cha; vị trí dòng điều khiển bằng `exitY/entryY` phân số, `exitDy/entryDy` theo dòng.
- **Cổng phân số theo dòng:** với bảng có `header_h` và `row_h`, dòng thứ `i` có tâm tại `y = header_h + (i + 0.5)·row_h`; `exitY = clamp(y / h_table, 0.05, 0.95)`. Chiều cao dòng lấy từ Text Measurer/Serializer, không từ hằng số tách rời.
- **Dây ngang phẳng:** `exitY = clamp((y_target_center − y_source_top) / h_source, 0.05, 0.95)` chỉ cho dây **thẳng một đoạn** khi hai cạnh quay vào nhau và tâm đích nằm trong khoảng cao của nguồn; ngoài điều kiện đó dùng tuyến hai gấp khúc trên hành lang. Công thức này là thiết kế `[CẦN KIỂM CHỨNG: S5, TC-15]`.
- **Hành lang song song:** các tuyến bus chạy theo trục rời rạc cách nhau ≥ `corridor_spacing` (mặc định 30-50 px, tham số hóa theo loại và mật độ, xem 4.9) và đi ngoài hộp, không đâm xuyên node không phải đầu mút (DG-07).
- **Edge bundling (P1):** gộp các dây song song cùng hướng vào một bó có điểm tách/nhập rõ ràng, có quy tắc tránh nhầm quan hệ.
- **Nhãn trên dây:** vị trí nhãn xác định bởi Router; mặt nạ ôm khít (4.7); DG-05 kiểm nhãn không che dây/thực thể khác.

**Chỉ số chất lượng (D-20, FR-25).** `crossings`, `avg_bends`, `edge_length_total`, `aspect_ratio`, `min_node_gap`. Ngưỡng báo `W-LAYOUT-QUALITY` là tham số theo `diagram_type` `[ĐỀ XUẤT]`; đồ thị dày phát `W-LAYOUT-DENSE` kèm gợi ý tách trang.

### 4.7. Đo chữ và nhãn (FR-05, FR-24)

- **Font ghim và đóng gói:** họ font mặc định tương thích số đo (ví dụ Liberation Sans cho Arial/Helvetica; Noto Sans hoặc Be Vietnam Pro nếu cần đủ glyph dấu Việt) được phân phối cùng engine; không giả định font hệ thống. Khai báo `fontFamily` trong style để draw.io chọn đúng họ; font thay thế ở máy người dùng là nguồn lệch còn lại và phải được ghi nhận (S6).
- **Cách đo:** `ImageFont.truetype(font_path, size=<PIXEL>)`; độ rộng bằng `font.getlength(text)` (advance); chuẩn hóa **NFC** trước khi đo; đo từng dòng sau khi wrap theo `max_width`; có cache theo (font, cỡ, chuỗi).
- **Không dùng:** `len(text) * k` (heuristic ký tự), `getbbox` (ink bounds), hệ số `K_adj = 0.78` (EV-05).
- **Nhãn ôm khít:** `snug_width = advance + 2·pad` (`pad` mặc định 4 px `[ĐỀ XUẤT]`); cấm ngắt dòng thủ công (`\n`, `<br>`) trong nhãn, để draw.io tự wrap với `whiteSpace=wrap` (`MX_INV_15`, `MX_INV_20`). Hiệu lực của `labelWidth` trên nhãn của edge `[CẦN KIỂM CHỨNG: S6]`.
- **Biên an toàn** là hằng số theo font đo từ ground truth draw.io (S6), không phải con số cố định ± 20%. Mọi số đo gắn `estimated` và phát `W-TEXT-ESTIMATED` (`I-*` nếu chỉ để thông tin).
- **Glyph:** font khai báo thiếu glyph tiếng Việt → `W-TEXT-NO-GLYPH`.

### 4.8. Gate ngữ nghĩa DG-00 (FR-03, D-09)

DG-00 chạy trên **spec** trước khi tính bố cục. `error` dừng pipeline (không phát hành file); `warning` đi kèm file. `fixable_by` mặc định `ai` (AI sửa spec) trừ khi nêu khác. Mỗi luật có tiêu chí đo được, mã ổn định và có TC.

**ERD (`SEM-ERD-*`, MVP)**

| ID | Luật | Mức |
|---|---|---|
| SEM-ERD-01 | Khóa ngoại trỏ tới (bảng, cột) tồn tại trong spec hoặc trong `external_ref` hợp lệ | error |
| SEM-ERD-02 | Kiểu cột FK tương thích kiểu cột được trỏ tới (cùng họ kiểu; bảng tương thích khai báo trong registry) | error (khác họ), warning (cùng họ khác độ dài) |
| SEM-ERD-03 | Mỗi bảng có khóa chính (hoặc khai báo `no_pk: true`) | warning |
| SEM-ERD-04 | Không trùng tên bảng; không trùng tên cột trong một bảng | error |
| SEM-ERD-05 | Cardinality hợp lệ (`one`, `zero_or_one`, `many`, `one_or_many`); FK có dòng tương ứng trong bảng "nhiều" | error |
| SEM-ERD-06 | Quan hệ N-N không qua bảng trung gian | warning |
| SEM-ERD-07 | FK tự tham chiếu được cho phép nhưng phải gắn cờ `self_reference` | info |
| SEM-ERD-08 | Cột `key=PK` không được `nullable`; khóa chính ghép khai báo đủ cột | error |

**Class (`SEM-CLS-*`, P1)**

| ID | Luật | Mức |
|---|---|---|
| SEM-CLS-01 | Không có vòng kế thừa (`extends`) | error |
| SEM-CLS-02 | Một lớp không đồng thời `extends` và `implements` cùng một kiểu | error |
| SEM-CLS-03 | `implements` chỉ trỏ tới interface; `extends` giữa lớp-lớp hoặc interface-interface | error |
| SEM-CLS-04 | Multiplicity hợp lệ và quan hệ trỏ tới lớp tồn tại | error |
| SEM-CLS-05 | Lớp trừu tượng không được là đích của `instantiates`/`creates` | warning |
| SEM-CLS-06 | Phạm vi truy cập (`visibility`) thuộc tập cho phép | error |

**Sequence (`SEM-SEQ-*`, MVP)**

| ID | Luật | Mức |
|---|---|---|
| SEM-SEQ-01 | Mọi thông điệp có `from`/`to` là lifeline đã khai báo | error |
| SEM-SEQ-02 | Chỉ số thông điệp tăng đơn điệu; thông điệp `reply` phải sau `call` tương ứng (không "trả về" trước "gọi") | error |
| SEM-SEQ-03 | Thông điệp `create` phải là thông điệp đầu tiên tới lifeline đó; lifeline chưa được tạo không nhận thông điệp trước `create` | error |
| SEM-SEQ-04 | Sau `destroy` không có thông điệp nào tới/từ lifeline đó | error |
| SEM-SEQ-05 | Activation cân bằng (mở/đóng khớp) và lồng đúng | error |
| SEM-SEQ-06 | Fragment (`alt`, `opt`, `loop`, `par`) mở/đóng khớp, lồng đúng; `alt` có ≥ 2 nhánh hoặc `else` | error |
| SEM-SEQ-07 | Thông điệp tự gọi có độ sâu activation hợp lệ | warning |
| SEM-SEQ-08 | Thông điệp bất đồng bộ không có `reply` bắt buộc | info |

**Architecture / Cloud / Network (`SEM-ARC-*`, MVP)**

| ID | Luật | Mức |
|---|---|---|
| SEM-ARC-01 | Mỗi node có tối đa một `parent`; cây lồng nhau không có vòng; `parent` tồn tại | error |
| SEM-ARC-02 | Bảng hợp lệ lồng nhau theo loại (ví dụ Subnet phải nằm trong VPC/VNet; VPC trong Region/Account; Pod trong Node/Namespace) theo registry | error |
| SEM-ARC-03 | CIDR của con nằm hoàn toàn trong CIDR của cha | error |
| SEM-ARC-04 | Các CIDR anh em trong cùng cha không chồng lấn | error |
| SEM-ARC-05 | Mọi `edge` có `from`/`to` tồn tại; không cạnh tự vòng trừ khi khai báo `self_loop` | error |
| SEM-ARC-06 | Giao thức/cổng hợp lệ (`port` trong 1..65535, `protocol` thuộc tập) | error |
| SEM-ARC-07 | Dịch vụ cần thành phần tiền đề (ví dụ ALB cần ≥ 1 Subnet công cộng) theo registry | warning |
| SEM-ARC-08 | Node cô lập (không edge, không phải container) | warning |

**DFD (`SEM-DFD-*`, P1)**

| ID | Luật | Mức |
|---|---|---|
| SEM-DFD-01 | Không có luồng trực tiếp Data Store ↔ Data Store hoặc External ↔ External | error |
| SEM-DFD-02 | Mỗi Process có ≥ 1 luồng vào và ≥ 1 luồng ra | error |
| SEM-DFD-03 | Mọi luồng dữ liệu có nhãn (tên dữ liệu) | warning |
| SEM-DFD-04 | Cân bằng giữa các mức (luồng vào/ra của process cha khớp sơ đồ con) | error |

**Use Case (`SEM-UC-*`) và State (`SEM-ST-*`) (P1)**

| ID | Luật | Mức |
|---|---|---|
| SEM-UC-01 | Không có kết nối Actor-Actor trừ khi khai báo `generalization` | error |
| SEM-UC-02 | `include`/`extend` nối use case với use case, đúng chiều | error |
| SEM-ST-01 | Có đúng một trạng thái đầu mỗi vùng; không có chuyển ra từ trạng thái cuối | error |
| SEM-ST-02 | Trạng thái không tới được từ trạng thái đầu | warning |

**Luật xuyên loại (`SEM-X-*`, MVP)**

| ID | Luật | Mức |
|---|---|---|
| SEM-X-01 | ID duy nhất; mọi tham chiếu (`from`, `to`, `parent`, `$ref`) tồn tại: không cạnh mồ côi | error |
| SEM-X-02 | Tham chiếu chéo module/trang hợp lệ; không vòng `$ref` | error |
| SEM-X-03 | Style token và icon có trong registry | error (`E-STYLE-UNKNOWN`) |
| SEM-X-04 | Nhãn không chứa chuỗi bị cấm (SEC-01) | error |
| SEM-X-05 | Quy mô trong giới hạn NFR-02; vượt giới hạn trang → gợi ý chia module (`W-LAYOUT-DENSE`) | error/warning |

### 4.9. Chuỗi cổng kiểm định DG-00..DG-08, PG và ánh xạ bất biến (FR-12, FR-13)

**Cổng chung (áp cho mọi `diagram_type`)**

| ID | Cổng | Tiêu chí đo được | Nguồn |
|---|---|---|---|
| DG-00 | Semantic Validity | Mọi luật SEM mức `error` đều đạt (4.8); chạy **trước** bố cục | Mới |
| DG-01 | XML Well-formedness và Invariants | File kết thúc bằng `</root></mxGraphModel>`; không có `<UserObject>` chứa mã Mermaid/PlantUML thô | Gate 1 cũ; `MX_INV_01`, `MX_INV_02` |
| DG-02 | Unique IDs và Parent Hierarchy | 100% ID duy nhất; mọi `mxCell` có `parent` tồn tại trong cây | Gate 2 cũ |
| DG-03 | AABB Collision và Spacing | R-tree: không hai node chồng nhau; khoảng cách tối thiểu `min_node_gap` (mặc định 60 px, tham số hóa) | Gate 3 cũ; `MX_INV_05` |
| DG-04 | Container-level Docking | `source`/`target` luôn là node cha, cấm cell con; không edge mồ côi; con nằm trong biên container + padding | Gate 4 cũ; `MX_INV_03` |
| DG-05 | Snug Label và Text Bounds | `labelWidth` khớp độ rộng đo (`estimated`, trong biên đã hiệu chỉnh); không ngắt dòng thủ công; nhãn dây không đè thực thể khác hay dây song song gần hơn `corridor_spacing` | Gate 5 cũ; `MX_INV_15`, `MX_INV_20` |
| DG-06 | Zero-Clipping Viewport | Tính `(max_x, max_y)` từ mọi `mxGeometry` và waypoint; kích thước trang/viewport `≥ max + viewport_margin` (mặc định 160 px); khi xuất ảnh: tự cắt biên với padding đều (mặc định 25 px). *Hai ngưỡng áp lên hai đối tượng khác nhau: trang trong `mxGraphModel` và ảnh xuất* | Gate 6 cũ; `MX_INV_21` |
| DG-07 | Edge Routing Integrity | Mọi đoạn dây trực giao; không dây xuyên node không phải đầu mút; điểm cổng nằm trên chu vi; khoảng cách giữa các hành lang ≥ `corridor_spacing`; số giao cắt, số điểm gấp được **đo và báo cáo** (không có ngưỡng "0") | Mới; `MX_INV_11`, `MX_INV_12`, `MX_INV_18` |
| DG-08 | Render Oracle (CI) | File mở được bằng draw.io thật không lỗi; số trang, kích thước và hộp bao khớp trong dung sai; so ảnh với golden có dung sai | Mới; chạy trong CI, không ở runtime |

**Cổng theo loại sơ đồ (PG)** — khai báo theo `diagram_type`:

| ID | Loại | Nội dung |
|---|---|---|
| PG-ERD-01 | `erd` | Bảng ba cột Type/Name/Key; ký hiệu Crow's foot đúng theo `rule_database_erd_standards.md`; dòng FK có cổng neo tương ứng |
| PG-ERD-02 | `erd` | Dây không đè lên chữ của chính bảng; dây vào đúng dòng FK (kiểm `entryDy`) |
| PG-ARC-01 | `architecture` | Phân tầng nét vẽ theo `MX_INV_16`; container chứa trọn con |
| PG-ARC-02 | `architecture` | Icon thuộc registry; nhãn dịch vụ đủ rõ (không rỗng) |
| PG-SEQ-01 | `sequence` | Lifeline thẳng đứng, thông điệp nằm ngang đúng thứ tự; activation nằm trong lifeline |
| PG-DFD-01 | `dfd` | Lưới 5 cột đúng thứ tự theo `MX_INV_14` |

**Ánh xạ `MX_INV_xx` → gate/test (D-10).** Chỉ liệt kê các bất biến đã có trong đầu vào của tài liệu này; mục "chưa có trong đầu vào" phải được rà soát ở Phase 0 trước khi MVP đóng.

| Bất biến | Nội dung | Cưỡng chế bởi |
|---|---|---|
| `MX_INV_01`, `MX_INV_02` | XML đóng đúng; không chứa mã Mermaid/PlantUML thô | DG-01 |
| `MX_INV_03` | Docking vào container, không vào cell con | DG-04 |
| `MX_INV_05` | Khoảng cách an toàn giữa các khối | DG-03 |
| `MX_INV_09` | Một file nhiều tab `<diagram name="...">` | TC-24, DG-01 |
| `MX_INV_11` | Cổng neo phân số theo tâm đích | DG-07, TC-15 |
| `MX_INV_12`, `MX_INV_18` | Hành lang song song rời rạc; bus bậc thang | DG-07, TC-18 |
| `MX_INV_14` | DFD 5 cột | PG-DFD-01 |
| `MX_INV_15`, `MX_INV_20` | Không ngắt dòng thủ công; `labelWidth` ôm khít; nền trắng | DG-05, TC-09 |
| `MX_INV_16` | Phân tầng nét vẽ kiến trúc | PG-ARC-01 |
| `MX_INV_21` | Viewport và cắt biên đều | DG-06, TC-21 |
| `MX_INV_10`, `MX_INV_13` | Schematic (rail nguồn, không text trên dây nguồn) | **Ngoài phạm vi** (D-18, Q-01) |
| `MX_INV_04`, `06`, `07`, `08`, `17`, `19` | (chưa có trong đầu vào của tài liệu này) | Rà soát ở Phase 0 |

### 4.10. Render (Pha 2) và Dual Delivery (FR-17, FR-18, FR-28)

- **Công cụ riêng `render_diagram`:** nhận `file_ref` `.drawio`, trả `file_ref` PNG/SVG (PDF ở P1). Pha 1 hoàn toàn độc lập với Pha 2.
- **Renderer (D-16):** (1) headless Edge/Chrome + `mxgraph_runner.html` + `mxClient.min.js` (hiện có, S1); (2) draw.io CLI nếu có; (3) fallback SVG→PNG thuần cho Linux tối giản (P1). Số đo S1 trên Windows: thành công 5/5, ảnh 1416×1244 px, 47.797 byte mỗi lần; cold start 7,20 s; warm 1,35-2,55 s (trung bình 2,80 s gồm cold) `[ĐÃ KIỂM CHỨNG có giới hạn: EV-01]`.
- **Bể trình duyệt (browser pool):** tái sử dụng tiến trình trình duyệt để tránh cold start 7 s; số tiến trình đồng thời giới hạn (NFR-10); dọn tiến trình treo (SEC-04).
- **Độ giống draw.io:** hai thứ cần đo tách biệt — *lặp lại* (S1, đã có) và *độ giống draw.io thật* (S9, chưa có). Đến khi S9 xong, mọi ảnh Pha 2 mang `render_info.renderer` và `W-RENDER-DIVERGENCE` nếu CI phát hiện lệch.
- **Dual Delivery:** file vector gốc `.drawio` (mở trên draw.io Desktop/VS Code extension) và ảnh PNG độ phân giải cao theo `dpi`. Kích thước và tỷ lệ khung của ảnh được trả trong `render_info` (`width_px`, `height_px`, `dpi`) để Docx/Xlsx Engine đặt đúng placeholder mà không méo tỷ lệ.
- **Chèn vào Office:** do Docx/Xlsx Engine thực hiện từ `FileRef` (D-17). Diagram Engine không ghi OOXML.

### 4.11. Sơ đồ lớn và nhiều trang (FR-15, FR-16)

- Spec chia `modules[]`; mỗi module có thể là một `<diagram>` (một tab) trong **một file** (`MX_INV_09`).
- **Trang tổng quan + drill-down:** trang đầu hiển thị module dưới dạng khối thu gọn và dây giữa module; mỗi module có trang chi tiết; liên kết chéo giữa trang bằng `link=data:page/id,...` chuẩn của draw.io `[CẦN KIỂM CHỨNG: S5]`.
- **Tự chia trang (P1):** theo `groups`/bounded context; nếu không có, theo thành phần liên thông và cắt cạnh ít nhất; luôn cảnh báo `W-LAYOUT-DENSE` kèm chỉ số.
- **Giới hạn mỗi trang (NFR-02)** và chiến lược khi vượt: từ chối `E-SPEC-TOO-LARGE` với gợi ý chia module, hoặc chia tự động nếu `auto_split: true`.

### 4.12. Inspect, Patch và bố cục ổn định (FR-19, FR-20)

- `inspect_drawio` trả cây trang → node → edge với **anchor ổn định** (dựa trên `id` từ spec; file ngoài engine được gán anchor theo `id` có sẵn trong XML).
- `patch_diagram` nhận thao tác khai báo (`add_node`, `remove_node`, `rename`, `add_edge`, `move_to_group`, `set_hint`), tính bố cục **tăng dần**: các node không bị ảnh hưởng và đã ghim giữ nguyên tọa độ và waypoint; chỉ vùng bị ảnh hưởng được tính lại.
- Thay đổi do người dùng chỉnh tay (tọa độ lệch so với bố cục engine) được nhận diện và **bảo toàn** (`pinned_by_user`) theo mặc định.
- Chỉ tiêu (NFR-08): sau `patch` thêm/xóa một node, số node không liên quan bị dịch chuyển = 0 khi chúng được ghim `[ĐỀ XUẤT]`.

### 4.13. Yêu cầu phi chức năng

| ID | Yêu cầu | Chỉ tiêu `[ĐỀ XUẤT]` |
|---|---|---|
| NFR-01 | Tất định theo ngữ nghĩa: cùng đầu vào, cùng phiên bản engine/ELK/font cho cùng XML sau chuẩn hóa | 100% trên bộ golden, kể cả giữa các tiến trình và hệ điều hành (TC-10, TC-32) |
| NFR-02 | Giới hạn tài nguyên mỗi lần gọi | Spec ≤ 2 MB; ≤ 300 node và ≤ 800 edge/trang; ≤ 40 trang; độ sâu lồng ≤ 6; timeout build 30 giây; RAM ≤ 1 GB |
| NFR-03 | Cách ly Node sidecar và trình duyệt | Tiến trình riêng, không mạng, FS tối thiểu, tự dọn |
| NFR-04 | Quan sát được: trace, số liệu, mã lỗi ổn định | Mọi lần gọi có `request_id` |
| NFR-05 | Ranh giới với Docx/Xlsx Engine: giao tiếp qua `FileRef`; Diagram Engine không ghi OOXML | Không phụ thuộc `docx`, `exceljs` |
| NFR-06 | Hiệu năng Pha 1 (không gồm render) | Sơ đồ 50 node: p95 < 1 giây; 300 node: p95 < 5 giây; Pha 2: warm p95 < 5 giây, cold start được ghi nhận riêng (S1: 7,2 s) |
| NFR-07 | Ma trận consumer có mức hỗ trợ rõ ràng | draw.io Desktop (Win/Mac), diagrams.net (web), VS Code extension: hỗ trợ đầy đủ mục tiêu; mức xác định trong Phase 0 (TC-44) |
| NFR-08 | Bố cục ổn định khi vá | 0 node không liên quan bị dịch (ghim) |
| NFR-09 | Di động | Chạy được trên Windows và container Linux (font đóng gói, Node ghim, renderer fallback) |
| NFR-10 | An toàn song song | Nhiều job đồng thời không xung đột tiến trình/ổ khóa; số trình duyệt đồng thời giới hạn |
| NFR-11 | Mã thoát CI | `0` sạch, `1` cảnh báo, `2` lỗi |

### 4.14. Yêu cầu bảo mật

| ID | Yêu cầu |
|---|---|
| SEC-01 | Nhãn: chỉ cho phép tập thẻ/thuộc tính HTML trong allow-list khi `html=1`; chặn `<script>`, `on*=`, `javascript:`, `<iframe>`, `<style>` ngoài allow-list; escape tại một điểm duy nhất |
| SEC-02 | Cấm liên kết ngoài và tài nguyên mạng trong style/`UserObject` (URL ảnh, `link=`), cấm ảnh `data:` không thuộc registry icon đã kiểm; liên kết nội bộ giữa trang theo allow-list |
| SEC-03 | Nhập `.drawio`: parser XML an toàn (không phân giải entity ngoài, chống XXE), giới hạn tỷ lệ giải nén cho `<diagram>` nén (base64/deflate), từ chối đường dẫn/ZIP bất thường |
| SEC-04 | Node sidecar và trình duyệt chạy trong sandbox: tiến trình riêng, không mạng, timeout, giới hạn tài nguyên, dọn tiến trình/file tạm; cờ trình duyệt hạn chế (tắt tiện ích, tắt truy cập mạng) |
| SEC-05 | Cách ly template, file, nhật ký theo tenant; `FileRef` ràng buộc tenant/session ở phía server (không thể hiện trong URI) và có TTL |
| SEC-06 | Audit log che dữ liệu nhạy cảm (tên bảng/cột, IP/CIDR là dữ liệu nhạy cảm); mã hóa lưu trữ; retention |
| SEC-07 | `file://` chỉ chấp nhận trong roots do client khai báo, chống path traversal; `resource://` là id mờ |
| SEC-08 | SVG/ảnh đầu ra được làm sạch: không `<script>`, không `foreignObject` trỏ tài nguyên ngoài, không tham chiếu `href` ra ngoài |
| SEC-09 | Theo dõi advisory và giấy phép của phụ thuộc; ghim phiên bản (`elkjs`, Node, `Pillow`, `lxml`, trình duyệt); rà điều khoản icon cloud |
| SEC-10 | Giới hạn spec để chống tấn công tài nguyên: độ sâu lồng, kích thước nhãn, số node/edge, vòng `$ref` |

---

## 5. Actor & Feature

### 5.1. Actor

| Actor | Vai trò | Tương tác chính |
|---|---|---|
| Người dùng cuối (End User) | Yêu cầu sơ đồ, duyệt kết quả, mở/chỉnh trong draw.io | Giao tiếp với AI; nhận file; quyết định các điểm AI không tự quyết |
| Antigravity AI (MCP Client) | Lập DiagramSpec và gợi ý bố cục, gọi công cụ, xử lý diagnostics | Gọi mọi công cụ MCP |
| Tác giả đặc tả/Registry Author | Duy trì registry style/icon, luật SEM, PG | Cập nhật registry, chạy `list_style_registry` |
| Quản trị/Kỹ sư nền tảng | Cấu hình giới hạn, tenant, sandbox, theo dõi audit, vận hành CI | Cấu hình; đọc audit/trace |
| Engine | Thực thi tất định, kiểm định, trả diagnostics | — |
| Node sidecar (ELK) | Tính tọa độ cho đồ thị | Nhận/trả JSON qua stdin/stdout |
| Render Service | Render PNG/SVG từ `.drawio` | Nhận/trả `FileRef` |
| Docx/Xlsx Engine | Chèn ảnh sơ đồ vào tài liệu | Nhận `FileRef` ảnh |
| Kiểm toán/Reviewer | Đối chiếu audit trail, chất lượng và bảo mật | Đọc audit log, báo cáo test |

### 5.2. Danh mục tính năng

| ID | Tính năng | Mô tả ngắn | Actor chính | Ưu tiên |
|---|---|---|---|---|
| FR-01 | Spec Registry và schema | JSON Schema theo `diagram_type`, phiên bản; `get_diagram_schema` | AI | MVP |
| FR-02 | Kiểm tra spec | Schema, giới hạn, lỗi kèm JSON path | Engine, AI | MVP |
| FR-03 | Gate ngữ nghĩa DG-00 | Luật SEM theo loại (4.8): ERD, Architecture, Sequence ở MVP; Class, Use Case, State, DFD ở P1 | Engine | MVP (ERD, ARC, SEQ); P1 (còn lại) |
| FR-04 | Style và Icon Registry | Allow-list token/icon; từ chối tên lạ | Engine, Registry Author | MVP |
| FR-05 | Text Measurer | Font ghim, `getlength`, NFC, cache, nhãn `estimated` (4.7) | Engine | MVP |
| FR-06 | Layout Dispatcher và ELK sidecar | Chọn thuật toán theo `diagram_type`; gọi Node qua stdin/stdout; quy lưới | Engine | MVP |
| FR-07 | Bố cục theo loại | ERD, Architecture/Network (lồng nhau), Sequence ở MVP; Class, Use Case, State, Component, Deployment, C4, DFD ở P1 | Engine | MVP/P1 |
| FR-08 | Router | Waypoint tường minh, cổng phân số theo dòng, docking container (4.6) | Engine | MVP |
| FR-09 | Corridor và Edge Bundling | Hành lang song song, bó dây | Engine | P1 |
| FR-10 | Bố cục bán kính (hub-and-spoke) | Core Hub ở giữa, vệ tinh theo 4 hướng | Engine | P1 |
| FR-11 | XML Serializer và bất biến | Một đường ghi XML; thứ tự cố định; escape một điểm | Engine | MVP |
| FR-12 | Chuỗi cổng DG-01..DG-07 | Kiểm định file/XML/hình học (4.9) | Engine | MVP |
| FR-13 | Cổng theo loại PG | PG-ERD, PG-ARC, PG-SEQ ở MVP; PG-DFD ở P1 | Engine | MVP/P1 |
| FR-14 | Diagnostics | Issues có `location`, `severity`, `evidence`, `fixable_by`, `suggested_action` | AI | MVP |
| FR-15 | Một file nhiều trang | `<diagram name=...>` nhiều tab (`MX_INV_09`) | Engine | MVP |
| FR-16 | Tự chia trang và trang tổng quan | Theo module/bounded context, drill-down | Engine | P1 |
| FR-17 | Render Service (Pha 2) | PNG/SVG (PDF ở P1), `render_info`, bể trình duyệt | AI, Engine | MVP |
| FR-18 | Render Oracle và DG-08 | draw.io thật trong CI; so kích thước và ảnh | Admin, Kiểm toán | MVP |
| FR-19 | Inspect | Cây cấu trúc có anchor ổn định | AI | MVP |
| FR-20 | Patch và bố cục ổn định | Thao tác khai báo, bố cục tăng dần, ghim | AI, Engine | P1 |
| FR-21 | Source Importers | SQL DDL, DBML trước; OpenAPI, docker-compose, Terraform/K8s sau | AI | P1 |
| FR-22 | Kho file `FileRef` | URI mờ kèm `sha256`; roots; TTL; cách ly tenant | Engine | MVP |
| FR-23 | Audit log | Nhật ký thao tác, che dữ liệu nhạy cảm | Admin, Kiểm toán | MVP |
| FR-24 | Xử lý tiếng Việt | NFC, font đủ glyph, cảnh báo thiếu glyph | Engine | MVP |
| FR-25 | Quality Metrics | `crossings`, `avg_bends`, `edge_length_total`, `aspect_ratio`, `min_node_gap`; `W-LAYOUT-QUALITY`, `W-LAYOUT-DENSE` | Engine | MVP |
| FR-26 | Làm sạch bảo mật | Nhãn, liên kết, ảnh, XXE, SVG đầu ra (4.14) | Engine | MVP |
| FR-27 | Điểm mở rộng | Thêm loại sơ đồ/adapter; sau này gắn module Chart/Schematic | Admin | P2 |
| FR-28 | Hợp đồng chuyển giao sang Docx/Xlsx Engine | `render_info` (kích thước, DPI, tỷ lệ) để chèn đúng placeholder | AI | P1 |
| FR-29 | Bố cục dự phòng không Node | Bố cục Python đơn giản khi Node vắng; `W-LAYOUT-FALLBACK` | Engine | P1 |

### 5.3. Ma trận Actor × Công cụ (rút gọn)

| Công cụ | End User | AI | Registry Author | Admin | Kiểm toán |
|---|---|---|---|---|---|
| `get_diagram_schema`, `list_style_registry` | | ✓ | ✓ | ✓ | |
| `validate_diagram_spec` | (qua AI) | ✓ | ✓ | ✓ | |
| `build_diagram`, `patch_diagram`, `import_source` | (qua AI) | ✓ | | | |
| `validate_drawio`, `inspect_drawio` | (qua AI) | ✓ | ✓ | ✓ | ✓ (đọc kết quả) |
| `render_diagram` | (qua AI) | ✓ | | ✓ | |
| Audit log / trace | | | | ✓ | ✓ |

---

## 6. Demonstration

### 6.1. Quy trình nghiệp vụ tổng quan

```
[1] Registry Author duy trì registry style/icon, luật SEM, PG
        │
        ▼
[2] Người dùng yêu cầu sơ đồ (hoặc đưa nguồn: SQL DDL, docker-compose) ───► AI
        │
        ▼
[3] AI: get_diagram_schema -> (tùy chọn) import_source -> lập DiagramSpec + layout_hints
        │   AI không viết XML, không đưa tọa độ
        ▼
[4] validate_diagram_spec ──► E-SEM / E-SPEC? ──► AI sửa spec theo json_path ──┐
        │ sạch                                                                   │
        ▼                                                                        │
[5] build_diagram: đo chữ -> bố cục -> router -> serializer -> DG-01..07 + PG ◄──┘
        │
        ▼
[6] AI đọc diagnostics và quality:
        ├─ fixable_by=ai     → sửa spec/gợi ý rồi gọi lại
        ├─ fixable_by=engine → gọi lại với policy phù hợp
        └─ fixable_by=human  → hỏi người dùng (rút gọn sơ đồ, chấp nhận bố cục dày)
        │
        ▼
[7] Người dùng mở .drawio để duyệt/chỉnh; hoặc render_diagram -> PNG -> Docx/Xlsx Engine
        │
        ▼
[8] (Vòng hai) inspect_drawio -> patch_diagram giữ bố cục ổn định
        │
        ▼
[9] Audit log ghi toàn bộ chuỗi thao tác
```

### 6.2. Workflow chính

**WF-A. Build sơ đồ từ DiagramSpec**

```
build_diagram(spec, layout_policy)
  -> giới hạn tài nguyên + xác thực tenant
  -> validate schema (JSON path khi lỗi) --[E-SPEC]--> dừng
  -> DG-00 ngữ nghĩa --[E-SEM]--> dừng, không phát hành file
  -> style/icon registry --[E-STYLE-UNKNOWN]--> dừng
  -> Text Measurer (NFC, font ghim) -> kích thước node/nhãn
  -> Layout Dispatcher: ELK sidecar | bố cục Python theo diagram_type
       (sidecar lỗi/hết giờ --> E-LAYOUT-SIDECAR, hoặc fallback có W-LAYOUT-FALLBACK)
  -> Router: cổng phân số, waypoint, corridor
  -> Page Splitter (nếu vượt ngưỡng) -> XML Serializer
  -> DG-01..DG-07 + PG --[error]--> trả lỗi, không phát hành file
  -> quality metrics -> lưu FileRef -> trả file_ref + diagnostics -> audit
```

**WF-B. Render và chèn vào tài liệu**

```
render_diagram(file_ref, format=png, dpi=300, page=...)
  -> lấy Renderer từ bể (headless browser | draw.io CLI)
  -> render -> làm sạch SVG (nếu có) -> lưu FileRef ảnh + render_info(width_px, height_px, dpi)
AI -> Docx Engine: build_document/patch_docx (khối image, FileRef ảnh)  |  Xlsx Engine: chèn ảnh
```

**WF-C. Sửa sơ đồ có sẵn (vòng hai)**

```
inspect_drawio(file_ref) -> AI nhận cây + anchors (kèm node ghim/người dùng đã chỉnh)
patch_diagram(file_ref, operations[anchor, op, payload])
  -> DG-00 trên spec suy ra -> bố cục tăng dần (giữ node ghim)
  -> DG-01..07 -> file_ref mới + diagnostics
```

**WF-D. Nhập từ nguồn có cấu trúc (P1)**

```
import_source(source_ref, source_type=sql_ddl)
  -> parser tất định -> DiagramSpec (+ W-SEM-* cho chỗ mơ hồ)
  -> AI bổ sung gợi ý/nhóm -> build_diagram như WF-A
```

### 6.3. Activity flow xử lý diagnostics (phía AI, dựa trên hợp đồng của engine)

```
Nhận diagnostics
  ├─ Có errors?
  │     ├─ E-SPEC (schema/giới hạn)        -> sửa spec theo json_path, gọi lại (tối đa N lần [ĐỀ XUẤT: 2])
  │     ├─ E-SEM (ngữ nghĩa)               -> sửa spec theo evidence (thêm bảng, đổi tham chiếu, đảo thứ tự); không hỏi người dùng trừ khi mơ hồ nghiệp vụ
  │     ├─ E-STYLE-UNKNOWN                 -> gọi list_style_registry, chọn token/icon hợp lệ
  │     ├─ E-LAYOUT / E-ROUTE              -> đổi layout_hints (hướng, nhóm) hoặc chia module; nếu lặp lại thì báo người dùng
  │     ├─ E-XML (lỗi engine)              -> dừng, không phát hành file; báo kèm evidence (lỗi của engine)
  │     └─ E-SEC                           -> dừng, không thử lại với cùng đầu vào
  └─ Chỉ có warnings?
        ├─ W-SEM (fixable_by=ai)           -> sửa nếu rõ ràng, hoặc ghi nhận khi bàn giao
        ├─ W-LAYOUT-DENSE / W-LAYOUT-QUALITY -> đề xuất chia module/tách trang; hỏi người dùng nếu cần giữ một trang (fixable_by=human)
        ├─ W-ROUTE-CROSSINGS               -> chấp nhận kèm số giao cắt hoặc đổi gợi ý bố cục
        ├─ W-TEXT-ESTIMATED / W-RENDER-DIVERGENCE -> nêu rõ số đo/ảnh chỉ ước lượng khi bàn giao
        ├─ W-LAYOUT-FALLBACK               -> báo bố cục dự phòng, chất lượng thấp hơn
        └─ Không còn cảnh báo cần xử lý    -> bàn giao file
```

Quy tắc chặn vòng lặp: số lần gọi lại tối đa cố định; giữ phương án tốt nhất (ít lỗi nhất, `quality` tốt nhất) và dừng ngay khi hai lần liên tiếp không cải thiện. Engine không tự lặp; vòng lặp thuộc về AI.

---

## 7. Test & Audit Planning

### 7.1. Chiến lược kiểm thử

| Tầng | Mục đích | Công cụ |
|---|---|---|
| Unit | Luật SEM, Text Measurer, Router, Serializer, từng gate, sinh issue | `pytest` |
| Integration | Pipeline build đầy đủ theo từng `diagram_type` | `pytest` + corpus |
| Golden/Regression | So khớp XML chuẩn hóa; các ca EV-01..EV-05 giữ làm hồi quy | Golden files |
| Differential/Oracle | Mở file bằng draw.io thật (CLI, desktop, web); so kích thước, hộp bao, ảnh có dung sai | draw.io CLI; runner Windows |
| Ground truth chữ | Đo độ rộng nhãn thực tế trên draw.io và so với Text Measurer | Script + draw.io |
| Determinism | Chạy lặp: cùng tiến trình, khác tiến trình, khác OS, ELK ghim vs nâng cấp | `pytest`, CI đa nền |
| Security | XML/HTML injection trong nhãn, URL/`data:`, XXE, nén, `$ref` vòng | Payload corpus, fuzz |
| Property/Fuzz | Spec ngẫu nhiên luôn cho XML hợp lệ hoặc từ chối có mã | `hypothesis` |
| Quality/Visual | Chỉ số giao cắt/điểm gấp trên corpus; visual regression có dung sai | Benchmark, so ảnh |
| Performance | Thời gian, bộ nhớ (kể cả sidecar và render) | Benchmark |
| UAT | Sơ đồ nghiệp vụ thật | 20-30 sơ đồ `[ĐỀ XUẤT]` |

Nguyên tắc: mọi test **độc lập** (không dùng thư mục scratch chung, không phụ thuộc thứ tự chạy); mọi ca thực nghiệm ở Phụ lục E được chuyển thành test tự động trước khi viết mã; mọi `MX_INV_xx` có test (TC-43).

### 7.2. Danh mục ca kiểm thử

| ID | Ca kiểm thử | Kết quả mong đợi | Yêu cầu | Tự động hóa |
|---|---|---|---|---|
| TC-01 | Spec sai schema: thiếu trường, sai kiểu, `diagram_type` lạ, vượt giới hạn | `E-SPEC-*` kèm JSON path; không phát hành file | FR-01, FR-02 | Tự động |
| TC-02 | DG-00 ERD: FK trỏ bảng/cột không tồn tại, kiểu lệch, trùng tên, PK nullable, N-N không trung gian | Mỗi luật SEM-ERD-01..08 bắt đúng, đúng mức `error`/`warning` | FR-03 | Tự động |
| TC-03 | DG-00 Class: vòng kế thừa, `extends`+`implements` cùng kiểu, `implements` trỏ lớp | SEM-CLS-01..06 bắt đúng | FR-03 | Tự động (P1) |
| TC-04 | DG-00 Sequence: thông điệp tới lifeline lạ; reply trước call; message trước `create`; sau `destroy`; activation/fragment lệch | SEM-SEQ-01..08 bắt đúng | FR-03 | Tự động |
| TC-05 | DG-00 Architecture: Subnet ngoài VPC; CIDR con ngoài CIDR cha; CIDR anh em chồng lấn; vòng lồng; ALB không có subnet công cộng | SEM-ARC-01..08 bắt đúng | FR-03 | Tự động |
| TC-06 | DG-00 DFD/Use Case/State: store↔store, process thiếu vào/ra, actor↔actor, nhiều trạng thái đầu, trạng thái không tới được | SEM-DFD/UC/ST bắt đúng | FR-03 | Tự động (P1) |
| TC-07 | Luật xuyên loại: ID trùng, tham chiếu mồ côi, `$ref` vòng, token/icon lạ, nhãn cấm | `E-SEM-X-*`/`E-STYLE-UNKNOWN`/`E-SEC-*` đúng | FR-03, FR-04, SEC-01 | Tự động |
| TC-08 | **Text Measurer đối chiếu ground truth:** chạy lại S3 đúng cách (cỡ chữ tính bằng pixel, `getlength`, NFC), đo trên draw.io thật cho ASCII và tiếng Việt, nhiều cỡ chữ | Sai số được ghi thành hằng số theo font; không còn `K_adj` tùy tiện; mọi số đo `estimated` | FR-05, FR-24, D-08 | Tự động + thủ công (S6) |
| TC-09 | Snug Label: mặt nạ nền nhãn có che dây song song cách 30-50 px không | Không che dây/thực thể khác (DG-05) | FR-05, FR-12 | Tự động + soát mắt |
| TC-10 | **Tính tất định ELK:** 100 lần/tiến trình, khác tiến trình, khác OS, cổng cố định, đồ thị phân cấp, so cả tọa độ và đường dây; đổi phiên bản ELK | XML chuẩn hóa trùng; khác phiên bản ELK được phát hiện (ghim) | NFR-01, FR-06, D-02 | Tự động (CI đa nền) |
| TC-11 | Dispatcher chọn đúng thuật toán theo `diagram_type`; Node vắng/hết giờ/lỗi | Đúng bảng 4.5; `E-LAYOUT-SIDECAR` hoặc `W-LAYOUT-FALLBACK` | FR-06, FR-29 | Tự động |
| TC-12 | Chất lượng ERD: corpus 10/50/100 bảng | 0 node chồng; 0 dây xuyên node; giao cắt/điểm gấp được báo cáo; không kéo dài sọc | FR-07, FR-25, DG-03, DG-07 | Tự động + soát mắt |
| TC-13 | Architecture lồng nhau: nhiều tầng container | Con nằm trọn trong container + padding; container giãn đúng | FR-07, DG-04 | Tự động |
| TC-14 | Bố cục Sequence: thứ tự lifeline, trục y đơn điệu, activation, fragment | Đúng PG-SEQ-01 | FR-07, PG-SEQ-01 | Tự động |
| TC-15 | Router: dây trực giao, cổng phân số theo dòng, `entryDy` khớp dòng FK, dây ngang phẳng khi thẳng hàng, dây vào đúng dòng và không đè chữ bảng | Đúng 4.6; DG-07 đạt; PG-ERD-02 đạt | FR-08, MX_INV_11 | Tự động + soát mắt |
| TC-16 | **Waypoint trên draw.io thật (S5):** mở file, di chuyển node, đổi zoom, "Reset Edge", với từng `routing_mode`; trên Desktop và web | Ghi nhận mode nào giữ waypoint; chốt `routing_mode` mặc định; ghi vào NFR-07 | D-06, P-02 | Thủ công + CLI (Phase 0) |
| TC-17 | Docking: `source`/`target` luôn là node cha; dòng chọn bằng offset | Không edge nào trỏ cell con; DG-04 đạt | D-07, MX_INV_03 | Tự động |
| TC-18 | Corridor và bundling: khoảng cách hành lang; không xuyên node | ≥ `corridor_spacing`; DG-07 đạt | FR-09, MX_INV_12, MX_INV_18 | Tự động (P1) |
| TC-19 | XML Serializer: thứ tự thuộc tính, escape, ID duy nhất, kết thúc đúng, không chứa Mermaid/PlantUML | DG-01, DG-02 đạt; XML tất định | FR-11, MX_INV_01 | Tự động |
| TC-20 | Mỗi cổng DG-01..DG-07 có fixture lỗi cố ý | Mỗi cổng bắt đúng lỗi của nó, không bắt nhầm | FR-12 | Tự động |
| TC-21 | Viewport: tọa độ lớn; waypoint ngoài biên; cắt biên 25 px đều | Không clipping; DG-06 đạt | FR-12, MX_INV_21 | Tự động |
| TC-22 | Render Service: 5/5 lặp lại, kích thước, DPI; cold/warm; đồng thời N job; bể trình duyệt | Lặp lại 100%; cold start được ghi; không rò tiến trình | FR-17, NFR-06, NFR-10 | Tự động |
| TC-23 | **Độ giống draw.io (S9):** render bằng runner vs draw.io thật; riêng `shape=table`, `childLayout=tableLayout`, icon, nhãn HTML | Lệch được đo; `W-RENDER-DIVERGENCE`; quyết định giữ hay thay Renderer | FR-17, FR-18, DG-08 | Tự động + thủ công (Phase 0) |
| TC-24 | Một file nhiều trang; liên kết giữa trang; (P1) tự chia trang | Đúng `MX_INV_09`; liên kết hoạt động | FR-15, FR-16 | Tự động |
| TC-25 | Inspect: anchor ổn định; round-trip `build` rồi `inspect` rồi dựng lại | Cấu trúc tương đương | FR-19 | Tự động |
| TC-26 | Patch và bố cục ổn định: thêm/xóa/đổi tên một node; node ghim; chỉnh tay của người dùng | 0 node không liên quan dịch; chỉnh tay được bảo toàn | FR-20, NFR-08 | Tự động (P1) |
| TC-27 | Importer: SQL DDL, DBML (rồi OpenAPI, compose) so với golden DiagramSpec | Spec khớp golden; chỗ mơ hồ có `W-SEM-*` | FR-21 | Tự động (P1) |
| TC-28 | Registry: tên lạ bị từ chối; mỗi icon/token trong registry render không trống | `E-STYLE-UNKNOWN`; 0 icon trống | FR-04, D-13 | Tự động |
| TC-29 | Bảo mật nội dung: nhãn có `<script>`, `onerror`, `javascript:`, `<iframe>`; `data:`; URL ngoài; XXE, nén bomb khi nhập; `$ref` vòng; lồng sâu | Bị chặn với `E-SEC-*`/`E-SPEC-*` | SEC-01, SEC-02, SEC-03, SEC-10 | Tự động |
| TC-30 | Cách ly Node và trình duyệt: treo, timeout, không mạng, dọn file tạm, chạy song song | Dừng đúng; không rò tiến trình | NFR-03, SEC-04, NFR-10 | Tự động |
| TC-31 | `FileRef` và roots: URI mờ; tenant khác; `file://` ngoài roots; path traversal; `sha256` | Từ chối truy cập chéo; toàn vẹn khớp | FR-22, SEC-05, SEC-07 | Tự động |
| TC-32 | Tất định toàn pipeline: chạy lặp, đa tiến trình, đa OS | XML chuẩn hóa trùng | NFR-01 | Tự động |
| TC-33 | Giới hạn tài nguyên và timeout; mã thoát CI | Dừng đúng NFR-02; exit code 0/1/2 đúng NFR-11 | NFR-02, NFR-11 | Tự động |
| TC-34 | Chất lượng diagnostics: mỗi mã có tiêu chí đo được; mọi issue có `location`, `fixable_by`, `evidence`; điều ước lượng gắn `estimated` | Không có cảnh báo phỏng đoán không gắn nhãn | FR-14 | Tự động |
| TC-35 | Hiệu năng Pha 1 và Pha 2 | Đạt NFR-06 | NFR-06 | Tự động |
| TC-36 | Audit: đủ trường, che dữ liệu nhạy cảm | Đạt SEC-06 | FR-23, SEC-06 | Tự động |
| TC-37 | Tiếng Việt đầu-cuối: nhãn có dấu, NFD→NFC, font thiếu glyph, wrap, trong ERD và Architecture | Chữ đúng; `W-TEXT-NO-GLYPH`; không tràn nhãn | FR-24 | Tự động + soát mắt |
| TC-38 | Đồ thị dày/không phẳng (K5, lưới dày, 300 node): quality score trung thực | Báo giao cắt thật; `W-LAYOUT-DENSE`; không tuyên bố zero-crossing | FR-25, D-20 | Tự động |
| TC-39 | Tích hợp: PNG vào Docx Engine và Xlsx Engine qua `FileRef` | Đúng kích thước/tỷ lệ/DPI; không méo | FR-28, NFR-05 | Tự động + soát mắt |
| TC-40 | UAT với sơ đồ nghiệp vụ thật (ERD từ DB thật, microservices, sequence luồng đăng nhập/thanh toán) | Đạt ngưỡng chấp nhận (7.3) | Tất cả MVP | Thủ công |
| TC-41 | Property/Fuzz: spec ngẫu nhiên | XML luôn hợp lệ hoặc từ chối có mã; DG-01..DG-04 đạt | FR-02, FR-11, FR-12 | Tự động |
| TC-42 | Spec lớn: 50 service/100+ bảng; `modules[]`, `$ref`, nhiều trang, giới hạn | Chia trang đúng; không vượt giới hạn trang; không cạnh mồ côi | FR-15, FR-16, NFR-02 | Tự động |
| TC-43 | Meta-test bất biến: mỗi `MX_INV_xx` trong bảng 4.9 có gate/test; bất biến chưa ánh xạ bị liệt kê | Không có bất biến "chỉ là tài liệu" | D-10, P-10 | Tự động (CI) |
| TC-44 | Ma trận consumer: draw.io Desktop (Win/Mac), diagrams.net, VS Code extension mở file | Không lỗi/cảnh báo; chênh lệch ghi vào NFR-07 | NFR-07 | Một phần tự động + thủ công |

### 7.3. Tiêu chí chấp nhận `[ĐỀ XUẤT]`

| Tiêu chí | Ngưỡng |
|---|---|
| Spec có lỗi ngữ nghĩa mức `error` mà vẫn phát hành file | 0 |
| Lỗi XML well-formed, ID trùng, parent sai, edge mồ côi | 0 |
| Node chồng nhau; dây xuyên node không phải đầu mút | 0 |
| Edge trỏ cell con (vi phạm `MX_INV_03`) | 0 |
| Bất biến `MX_INV` đã ánh xạ không có gate/test | 0 |
| Waypoint bị draw.io tính lại ở `routing_mode` mặc định (đo ở S5) | 0 trên tập kiểm thử đã định nghĩa; kết quả ghi vào NFR-07 |
| Tất định (XML chuẩn hóa), trong tiến trình, giữa tiến trình và giữa OS | 100% trên bộ golden |
| Sai số đo chữ so ground truth draw.io | Đạt biên do chủ sở hữu chốt sau S6 (Q-04); mọi số đo gắn `estimated` |
| Payload bảo mật được chặn | 100% trong corpus |
| Ghi đè file gốc | 0 |
| Hiệu năng (NFR-06) | Đạt |
| UAT: sơ đồ được người dùng duyệt | Ngưỡng do chủ sở hữu chốt (Q-05) |
| Cam kết "zero-crossing" trong tài liệu hoặc diagnostics | Không xuất hiện; chỉ báo số giao cắt đo được |

### 7.4. Kế hoạch Audit

**a) Audit runtime (vết thao tác)**

| Hạng mục | Nội dung |
|---|---|
| Ghi nhận | `request_id`, tenant, công cụ, hash đầu vào/đầu ra, phiên bản schema/registry, `diagram_type`, thuật toán bố cục và phiên bản ELK/font, `routing_mode`, thống kê quality, danh sách issue (mã + vị trí), thời gian, kết quả |
| Không ghi nguyên văn | Tên bảng/cột/dịch vụ, IP/CIDR, nhãn, văn bản prompt; chỉ ghi hash và thống kê |
| Lưu trữ | Mã hóa; cách ly theo tenant; retention theo chính sách `[ĐỀ XUẤT: xác định ở Q-07]` |
| Truy vết | Trace theo `request_id`; liên kết spec ↔ file `.drawio` ↔ ảnh render |

**b) Audit chất lượng kỹ thuật**

- Cổng chất lượng (release gate): toàn bộ TC của phạm vi MVP đạt (Phụ lục A); không lỗi mức nghiêm trọng mở; mọi ca EV có test hồi quy.
- **Ma trận truy vết** (Phụ lục G): mỗi `FR/NFR/SEC` ↔ module ↔ `TC`; mục nào thiếu một trong ba cột là khoảng trống phải xử lý trước phát hành.
- Số liệu định kỳ, **đo được trên corpus**: tỷ lệ build thành công, phân bố mã issue, phân bố quality score, tỷ lệ sơ đồ phải chia trang, thời gian xử lý, độ lệch Renderer với draw.io thật, độ lệch số đo chữ.
- Quy tắc nằm trong tài liệu markdown (`MX_INV_xx`, `rule_database_erd_standards.md`) chỉ có giá trị hướng dẫn; quy tắc nào cần được bảo đảm phải tồn tại dưới dạng gate hoặc test (D-10, TC-43).

**c) Audit bảo mật**

- Rà soát phụ thuộc và advisory (`elkjs`, Node, `Pillow`, `lxml`, trình duyệt headless).
- Kiểm thử xâm nhập cho bề mặt nhãn/XML nhập/`FileRef`/tiến trình sidecar và trình duyệt trước mỗi phiên bản lớn.
- Kiểm tra rò rỉ chéo tenant (file, log, profile trình duyệt, thư mục tạm).
- Rà giấy phép trước khi phân phối, kể cả điều khoản icon cloud.

**d) Checklist phát hành**

1. Toàn bộ TC bắt buộc đạt trên CI (gồm Oracle draw.io thật và kiểm thử tất định đa nền).
2. Bảng "Engine bảo đảm / không bảo đảm" (3.4) khớp hành vi thực tế.
3. Không có `[CẦN KIỂM CHỨNG]` hoặc `[CHƯA KẾT LUẬN]` nào còn mở trong phạm vi MVP.
4. Giấy phép phụ thuộc và icon đã được rà soát và ghi lại.
5. Ma trận truy vết đầy đủ; audit log và masking đã kiểm tra.
6. Tài liệu hướng dẫn cho AI (cách lập DiagramSpec, gợi ý bố cục, xử lý diagnostics) đã phát hành.

---

## Phụ lục A. Lộ trình và phạm vi MVP

### A.1. Các giai đoạn

| Giai đoạn | Mục tiêu | Đầu ra | Điều kiện hoàn thành |
|---|---|---|---|
| **Phase 0 — Kiểm chứng (đang thực hiện)** | Chốt mọi mục `[CẦN KIỂM CHỨNG]`/`[CHƯA KẾT LUẬN]` trước khi viết engine | S1-S4 (đã chạy, xem Phụ lục E) và **S5-S9** (bên dưới); corpus mẫu; ma trận consumer | Danh sách `[CẦN KIỂM CHỨNG]`/`[CHƯA KẾT LUẬN]` trong phạm vi MVP về 0 |
| **Phase 1 — MVP** | Lõi an toàn: schema, DG-00 (ERD, ARC, SEQ), đo chữ, bố cục ELK + Python, router, serializer, DG-01..07, render, inspect | FR-01, 02, 03 (MVP), 04-08, 11-15, 17-19, 22-26; công cụ `get_diagram_schema`, `validate_diagram_spec`, `build_diagram`, `validate_drawio`, `inspect_drawio`, `render_diagram` | Toàn bộ TC MVP đạt (trừ TC-03, 06, 18, 26, 27 thuộc P1); tiêu chí 7.3 đạt trên corpus; UAT đạt ngưỡng Q-05. **MVP rộng có chủ đích; cắt lát theo A.3** |
| **Phase 2 — P1** | Mở rộng loại sơ đồ và độ bền | Class, Use Case, State, Component, Deployment, C4, DFD; FR-09, 10, 16, 20, 21, 28, 29; `patch_diagram`, `import_source` | TC-03, 06, 18, 26, 27 đạt; ma trận consumer hoàn chỉnh |
| **Phase 3 — P2** | Mở rộng hệ sinh thái | FR-27; kế hoạch riêng cho Chart và Schematic | Theo nhu cầu (Q-01, Q-02) |

### A.2. Spike Phase 0

Các spike S1-S4 đã chạy ngày 2026-10-06. Spike S5-S9 là **điều kiện để chốt các quyết định D-06, D-08, D-16**.

| Spike | Câu hỏi | Trạng thái | Việc còn lại |
|---|---|---|---|
| S1 | Render offline hoạt động ra sao khi không có draw.io CLI? | **Đã chạy, có giới hạn** (EV-01) | Đo trên Linux; đo đồng thời; đo cả `shape=table` (nối với S9) |
| S2 | Waypoint `mxPoint` có đóng băng routing không? | **Mới xác nhận cấu trúc XML** (EV-02) | **S5**: mở trên draw.io thật |
| S3 | Sai lệch `labelWidth` heuristic vs font thật? | **[CHƯA KẾT LUẬN]** (EV-03, EV-05) | **S6**: chạy lại đúng cách và đo ground truth |
| S4 | ELK có tất định không? | **Đã chạy, có giới hạn** (EV-04) | **S7, S8**: cross-process/OS/phiên bản; cổng và phân cấp |
| **S5** | draw.io thật có giữ waypoint khi mở/di chuyển node/zoom/"Reset Edge" với từng `routing_mode`? `exitY` phân số + `exitDy` hoạt động ra sao? Liên kết giữa trang? | Chưa chạy | Cài draw.io Desktop/CLI; kịch bản kiểm thử TC-16 |
| **S6** | Độ rộng nhãn thật trên draw.io so với `Pillow getlength` ở đúng px, với font ghim, ASCII và tiếng Việt, nhiều cỡ; `labelWidth` có hiệu lực trên nhãn edge không? | Chưa chạy | TC-08 |
| **S7** | ELK tất định: 100 lần, khác tiến trình, khác OS, khác phiên bản; so cả đường dây | Chưa chạy | TC-10 |
| **S8** | ELK với cổng cố định theo dòng bảng, phân cấp (VPC>Subnet>Node), đồ thị ERD 50-100 bảng: chất lượng và thời gian; so với Router tự viết | Chưa chạy | Chốt thuật toán ERD lớn (bảng 4.5) và phân vai ELK/Router |
| **S9** | Runner `mxClient.min.js` vs draw.io thật: `shape=table`, `childLayout=tableLayout`, icon, nhãn HTML, kích thước ảnh | Chưa chạy | TC-23; quyết định giữ hay thay Renderer |

Ngoài ra Phase 0 phải: chốt giấy phép (`elkjs`, icon cloud), rà các `MX_INV` chưa có trong đầu vào, và chốt font ghim.

### A.3. Hướng dẫn cắt lát MVP

| Lát | Nội dung | FR / NFR / SEC chính | Phụ thuộc | Giá trị khi đứng riêng |
|---|---|---|---|---|
| S0 — Nền spec và ngữ nghĩa | Schema, DG-00 (ERD, ARC, SEQ), registry style/icon, diagnostics | FR-01..04, FR-14 | (không) | Chặn spec sai nghĩa ngay từ đầu |
| S1 — Hình học lõi | Text Measurer, Layout Dispatcher + ELK, Router, Serializer, DG-01..07 | FR-05..08, FR-11, FR-12, FR-25 | S0, Phase 0 (S5-S8) | Ra được `.drawio` đúng và ổn định |
| S2 — Loại sơ đồ MVP | ERD, Architecture/Network, Sequence, PG | FR-07, FR-13, FR-15 | S1 | Phủ ba loại có giá trị nhất |
| S3 — Render và giao hàng | `render_diagram`, bể trình duyệt, DG-08, `FileRef`, tích hợp Docx/Xlsx | FR-17, FR-18, FR-22, FR-28 | S1, S9 | Ảnh chèn vào tài liệu |
| S4 — Inspect | `inspect_drawio`, anchor | FR-19 | S1 | AI trỏ lại được lỗi |
| S5 — Hạ tầng và bảo mật | Audit, sandbox, làm sạch, giới hạn, tiếng Việt | FR-23, FR-24, FR-26, SEC-01..10, NFR-02..04, NFR-10 | (độc lập) | Vận hành an toàn |
| Sau MVP (P1) | Patch ổn định, Importer, Class/Use Case/State/Component/Deployment/C4/DFD, Corridor/bundling, radial, tự chia trang, fallback | FR-03 (P1), FR-09, 10, 16, 20, 21, 28, 29 | S0..S4 | Mở rộng |
| P2 | Điểm mở rộng; Chart, Schematic | FR-27 | — | Theo nhu cầu |

Thứ tự cắt gọn gợi ý nếu cần phát hành sớm: S0 → S1 → S2 (chỉ ERD) → S5 → S3 → S4. Phase 0 (S5-S9) **chặn** S1 và S3.

---

## Phụ lục B. Rủi ro

| ID | Rủi ro | Mức | Giảm thiểu |
|---|---|---|---|
| R-01 | Draw.io tính lại đường nối dù có waypoint (S2 chưa xác nhận trên draw.io thật) | Cao | S5 trước khi viết Router; `routing_mode`; TC-16; DG-08 |
| R-02 | Phụ thuộc ELK/Node: giấy phép (EPL-2.0), đóng gói, tất định chưa chứng minh rộng | Cao | Tiến trình riêng; ghim phiên bản; S7, S8; fallback Python (FR-29); rà giấy phép |
| R-03 | Renderer `mxClient.min.js` khác draw.io thật (đặc biệt `shape=table`) | Cao | S9; DG-08; có thể chuyển sang draw.io CLI hoặc renderer khác (D-16) |
| R-04 | Sai số đo chữ; kết luận S3 sai; font server khác máy người dùng | Cao | S6; font ghim và đóng gói; nhãn `estimated`; hằng số theo font |
| R-05 | Cam kết chất lượng bố cục quá tuyệt đối với đồ thị dày | Trung bình | D-20; quality score; `W-LAYOUT-DENSE`; TC-38 |
| R-06 | Spec lớn làm AI quên quy tắc hoặc vượt giới hạn | Trung bình | `modules[]`/`$ref`; importer (FR-21); giới hạn NFR-02; chia trang |
| R-07 | Luật ngữ nghĩa thiếu/sai theo từng loại sơ đồ; registry phụ thuộc nhà cung cấp cloud | Trung bình | Luật theo loại có TC; registry có test; mở rộng dần; luật không chắc chắn là `warning` |
| R-08 | Bất biến `MX_INV_xx` trôi hoặc chỉ là tài liệu | Trung bình | D-10; TC-43; rà các bất biến chưa ánh xạ |
| R-09 | Rò rỉ chéo tenant (file, log, profile trình duyệt, thư mục tạm) | Cao | SEC-05, SEC-04; TC-30, TC-31 |
| R-10 | Bảo mật nhãn HTML/SVG/XML nhập | Cao | SEC-01..03, SEC-08; TC-29 |
| R-11 | Điều khoản icon của nhà cung cấp cloud hạn chế phân phối lại | Trung bình | Rà điều khoản; dùng icon sẵn có trong draw.io thay vì tự đóng gói (Q-10) |
| R-12 | Trình duyệt headless nặng/treo/cold start 7 s khi đồng thời | Trung bình | Bể trình duyệt; timeout; giới hạn đồng thời (NFR-10); fallback SVG→PNG |
| R-13 | Bố cục không ổn định khi vá | Trung bình | D-11; ghim; TC-26 |
| R-14 | Host/MCP client không hỗ trợ roots hoặc `resource_link` | Trung bình | Core chỉ định nghĩa `FileRef`; kiểm chứng ở bước tích hợp (Q-09) |
| R-15 | MVP rộng khó kiểm soát tiến độ | Trung bình | A.3; ma trận truy vết; Phase 0 chặn đúng chỗ |
| R-16 | Phạm vi trượt (Chart, Schematic) kéo kế hoạch | Thấp-Trung bình | D-18; Q-01, Q-02 |

---

## Phụ lục C. Câu hỏi mở

| ID | Câu hỏi | Ảnh hưởng |
|---|---|---|
| Q-01 | Schematic/hardware wiring (`MX_INV_10`, `MX_INV_13`) có thuộc kế hoạch Diagram Engine riêng, hay thuộc module khác? | D-18, 1.2 |
| Q-02 | Chart nghiệp vụ: giữ kế hoạch riêng, hay hợp nhất vào Xlsx/Docx Engine? | D-18, 1.3 |
| Q-03 | Thứ tự ưu tiên các loại sơ đồ MVP: có đồng ý ERD, Architecture/Network, Sequence? DFD đưa vào P1 hay MVP? | 4.5, A.1 |
| Q-04 | Biên sai số đo chữ chấp nhận được (sau S6)? | D-08, 7.3 |
| Q-05 | Ngưỡng UAT: số sơ đồ, tỷ lệ được duyệt | 7.3 |
| Q-06 | `routing_mode` mặc định nếu S5 cho thấy `orthogonal_with_points` không giữ waypoint? | D-06 |
| Q-07 | Chính sách retention của audit log và file | SEC-06, 7.4.a |
| Q-08 | Mô hình lưu trữ file và tenant (cục bộ, object store, đa tenant ngay từ đầu?) | FR-22, SEC-05 |
| Q-09 | Antigravity hỗ trợ roots và `resource_link`/`resources/read` đến đâu? | 4.3, SEC-07, R-14 |
| Q-10 | Dùng icon cloud: chỉ icon có sẵn trong draw.io, hay đóng gói icon chính thức của nhà cung cấp (điều khoản)? | D-13, R-11 |
| Q-11 | Ngưỡng tham số theo loại sơ đồ: `min_node_gap`, `corridor_spacing`, `viewport_margin`, giới hạn node/trang | 4.9, NFR-02 |
| Q-12 | Có cần Linux container ngay từ đầu (ảnh hưởng font, renderer, Node)? | NFR-09, D-16 |
| Q-13 | Mô hình thương mại hóa (SaaS, tại chỗ, mã nguồn mở) — ảnh hưởng chọn `elkjs` | D-21, giấy phép |
| Q-14 | Danh sách `MX_INV_04`, `06`, `07`, `08`, `17`, `19` (chưa có trong đầu vào) để hoàn tất bảng ánh xạ | 4.9, TC-43 |
| Q-15 | Có cấp runner có draw.io Desktop/CLI cho CI (Windows) không? | DG-08, FR-18, TC-16, TC-23 |

---

## Phụ lục D. Đối chiếu các nhận định trước đây

Bảng này ghi lại các nhận định từ bản định hướng ban đầu, bản bổ sung công cụ, bản đánh giá và báo cáo Phase 0 Spike, kèm kết luận sau khi đối chiếu. Mục đích: không để nhận định chưa đúng làm sai lệch triển khai.

| # | Nhận định | Nguồn | Kết luận | Tham chiếu |
|---|---|---|---|---|
| 1 | "Heuristic đo dư 16,7%-26,9% (trung bình ~23% với tiếng Việt); bắt buộc nhân `K_adj = 0.78`" | Báo cáo S3 | **Không dùng được.** Script đổi `14px` thành `int(14·72/96) = 10` rồi truyền vào `ImageFont.truetype(size=…)`, tham số này là **pixel**, nên Pillow đo ở 10 px thay vì 14 px; ngoài ra dùng `getbbox` (ink bounds) và mới chỉ so hai ước lượng với nhau. Tính lại thô từ số liệu trong report (không chạy lại), quy phần chữ từ 10 px lên 14 px (nhân 1,4) cho thấy heuristic có thể **đo thiếu** khoảng 0-11% (ví dụ `CustomerOrderHistory`: ≈147 px thay vì 107 px, so với heuristic 130 px), tức là chiều sai lệch có thể **đảo ngược**. Cần chạy lại | P-04, EV-03, EV-05, D-08 |
| 2 | "Đo bằng `ImageDraw.textbbox()`/`getbbox()` là đủ" | Bản đánh giá, ví dụ `measure_snug_label` | **Chưa đúng cách:** `getbbox` trả hộp mực (ink), không phải độ dài advance; dùng `font.getlength()` và cỡ **pixel** | 4.7, D-08 |
| 3 | "Ghim Arial/Segoe UI vì có sẵn 100% trên Windows và web" | Bản đánh giá | **Sai về phạm vi:** không có sẵn trên container Linux/trình duyệt mọi nơi; phải đóng gói font có giấy phép phân phối | 1.5, D-08, NFR-09 |
| 4 | "Spike S2 xác nhận draw.io đóng băng waypoint, không bao giờ tự bẻ lại dây" | Báo cáo S2, bản đánh giá | **Chưa xác nhận.** S2 sinh hai file XML (có/không `Array as="points"`) nhưng draw.io không được cài (`drawio.exe` không tìm thấy) nên không mở thử. Ghi chú: với `edgeStyle=orthogonalEdgeStyle`, các điểm trong `Array as="points"` có thể chỉ là *gợi ý* cho bộ định tuyến trực giao `[CẦN KIỂM CHỨNG]` | P-02, EV-02, S5, D-06 |
| 5 | "ELK layered hoàn toàn tất định (10 lần, sai số 0,00 px)" | Báo cáo S4 | **Đúng trong phạm vi:** một tiến trình, 10 lần, 5 node, không cổng, không phân cấp, chỉ so tọa độ node (không so đường dây). Chưa kiểm khác tiến trình/OS/phiên bản. Phát biểu "an toàn tuyệt đối" cần hạ xuống thành "được phép tiếp tục thử nghiệm" | P-15, EV-04, S7, S8 |
| 6 | "Subprocess Node chỉ mất ~40 ms" | Bản đánh giá | **Không có số liệu:** script S4 không đo thời gian | EV-04, NFR-06 |
| 7 | "Pha 1 hoàn tất < 50 ms, 100% tất định" | Bản đánh giá | **Chưa đo**; là mục tiêu, không phải kết quả; NFR-06 đặt ngưỡng mới | NFR-06 |
| 8 | "Render offline 100% tất định (5/5, 1416×1244 px)" | Báo cáo S1 | **Đúng về độ lặp lại**; chưa chứng minh giống draw.io thật (`shape=table`, `tableLayout`) | P-05, EV-01, S9 |
| 9 | "Không cần cài draw.io Desktop vì pipeline nội bộ chạy ổn" | Báo cáo S1 | **Đúng để chạy Pha 2**, nhưng **cần draw.io thật làm Oracle** trong CI (DG-08) và để chốt S5, S9 | D-16, FR-18 |
| 10 | "`jsdom` + mxGraph là ngõ cụt" | Bản đánh giá | **Đồng ý, là quyết định loại bỏ** (không dựa trên thực nghiệm): không cần mxGraph để sinh XML | D-03, D-04 |
| 11 | "Chọn Phương án C: Python lõi + Node sidecar" | Bản đánh giá | **Chấp nhận có điều kiện:** kèm S7, S8, fallback Python (FR-29), rà giấy phép `elkjs` | D-02, D-21, R-02 |
| 12 | "Zero-Collision, Zero-Zigzag, đồng nhất 100% mỗi lần chạy" | Bản định hướng | **Quá tuyệt đối** với đồ thị dày/không phẳng; thay bằng không chồng node, không xuyên node, giao cắt được tối thiểu hóa và báo cáo | P-13, D-20, 3.4 |
| 13 | "6 cổng kiểm định (Gate 1-6) đủ cho Nhóm 4" | Bản định hướng | **Chưa đủ:** thiếu cổng ngữ nghĩa (DG-00), kiểm định routing (DG-07) và Oracle render (DG-08) | P-06, 4.9 |
| 14 | "Tích hợp `docx`, `exceljs`, `xml-crypto`, `archiver` để inject DrawingML" | Bản bổ sung công cụ | **Loại:** trùng Docx/Xlsx Engine (Python); `xml-crypto` (chữ ký XML) không liên quan | D-17, P-17 |
| 15 | "Dùng `rbush` (Node) cho AABB" | Bản bổ sung công cụ | **Đổi sang R-tree phía Python** (lõi là Python); `rbush` chỉ hợp lý nếu kiểm tra nằm trong Node | 4.2, DG-03 |
| 16 | "Chuyển SVG icon của cloud provider sang stencil XML" | Bản bổ sung công cụ | **Không cần mặc định:** draw.io đã có thư viện shape; chỉ dùng registry allow-list; điều khoản icon cần rà | D-13, R-11, Q-10 |
| 17 | "Schematic, Chart, DrawingML nằm trong cùng module Diagram" | Bản định hướng | **Tách ra:** ngoài phạm vi Nhóm 4 | D-18, P-17 |
| 18 | "`MX_INV_xx` là đủ để bảo đảm chất lượng" | Bản định hướng | **Chưa đủ:** là tài liệu; phải thành gate/test | D-10, P-10, TC-43 |

---

## Phụ lục E. Nhật ký bằng chứng thực nghiệm

**Môi trường EV-01..EV-04:** Windows 11, Python 3.12, Node.js v22.12.0; ngày 2026-10-06; do chủ sở hữu thực hiện và báo cáo lại qua Antigravity, chưa được tái chạy độc lập trong phiên soạn tài liệu này. Draw.io Desktop/CLI **chưa được cài** trên máy thử. **EV-05** là kết quả đọc mã script S3 trong phiên soạn tài liệu (không chạy lại).

| ID | Thử nghiệm | Kết quả quan sát | Phạm vi xác nhận |
|---|---|---|---|
| EV-01 | **S1.** Quét `drawio.exe` trong `PATH`, `Program Files`, `%LOCALAPPDATA%`; chạy 5 lần liên tiếp renderer nội bộ (headless Edge + `mxgraph_runner.html` + `mxClient.min.js`) | Không có `drawio.exe`. 5/5 thành công; mọi lần ra 1416×1244 px, 47.797 byte. Thời gian: cold 7,20 s; warm 1,35 s, 1,48 s, 1,42 s, 2,55 s; trung bình 2,80 s | `[ĐÃ KIỂM CHỨNG có giới hạn]` Chỉ chứng minh **lặp lại**, trên Windows, một sơ đồ. Chưa chứng minh giống draw.io thật, chưa đo Linux, chưa đo đồng thời. Runner không báo thành phần `shape=table` có được vẽ đúng không |
| EV-02 | **S2.** Sinh `spike_s2_WITH_waypoints.drawio` (edge có `<Array as="points">` với 2 `mxPoint`) và `spike_s2_WITHOUT_waypoints.drawio` (không có) cho bảng `TABLE_A` → `TABLE_B` | Đọc lại hai file: khác nhau duy nhất ở khối `Array as="points"` trong `mxGeometry` của edge; cả hai dùng `orthogonalEdgeStyle`, `exitX=1.0, exitY=0.5, entryX=0.0, entryY=0.5` | `[ĐÃ KIỂM CHỨNG]` về **cấu trúc XML**; `[CẦN KIỂM CHỨNG]` về hành vi trên draw.io thật (mở, di chuyển node, zoom, "Reset Edge") |
| EV-03 | **S3.** `spike_s3_labelwidth.py`: 10 nhãn (ASCII và tiếng Việt), so heuristic `len·6.1+8` với Pillow `getbbox` + 8 | Drift báo cáo từ −12,6% đến −26,9%; ví dụ `UserID`: 44,6 vs 36,0; `Lịch sử đơn hàng của khách`: 166,6 vs 128,0 | `[CHƯA KẾT LUẬN]` Xem EV-05: so hai ước lượng, không phải ground truth; lỗi đơn vị cỡ chữ |
| EV-04 | **S4.** `spike_s4_elk_determinism.mjs`: 10 lần `elk.layout` trên cùng đồ thị 5 bảng/5 cạnh (`layered`, `RIGHT`, `nodeNode=60`, `nodeNodeBetweenLayers=100`), so tọa độ làm tròn 2 chữ số | 10/10 giống hệt. Ví dụ: `TABLE_USER` (12; 105,17), `TABLE_ORDER` (352; 62,17), `TABLE_PRODUCT` (1032; 76,5), `TABLE_INVOICE` (692; 12), `TABLE_MEMBER` (352; 294,17) | `[ĐÃ KIỂM CHỨNG có giới hạn]` Một tiến trình; 5 node; không cổng; không phân cấp; chỉ tọa độ node; không đo thời gian; tọa độ phân số cần quy lưới |
| EV-05 | **Đọc mã S3.** `pt_size = int(14*72/96)` → 10, truyền `ImageFont.truetype(font_path, size=pt_size)`; `getbbox` rồi `+ PADDING`; danh sách font thử `trebuc.ttf`, `arial.ttf`, `segoeui.ttf` theo thứ tự; báo cáo không ghi font đã nạp; docstring của script tự ghi chú "ground truth requires opening draw.io" | Đo ở 10 px thay vì 14 px (tham số của Pillow là pixel); đo ink bounds thay vì advance; không có ground truth; font thực dùng không được ghi lại | `[ĐÃ KIỂM CHỨNG]` bằng đọc mã (không chạy lại). Hệ quả: kết luận S3 và `K_adj` bị hủy (Phụ lục D #1) |

---

## Phụ lục F. Khoảng cách giữa hiện trạng và đích

| Thành phần hiện có | Đích | Hành động |
|---|---|---|
| `mxgraph_engine.py` (nền tảng sinh draw.io) | FR-06..08, FR-11 | Tách thành: Layout Dispatcher, Router, XML Serializer; bỏ phần nối chuỗi XML tay (D-14); bỏ mọi heuristic đo chữ `len·k` |
| Bộ bất biến `MX_INV_01..21` | DG-01..DG-08, PG | Ánh xạ từng bất biến vào gate/test (bảng 4.9); rà các bất biến còn thiếu (Q-14) |
| `validate_drawio.py` (4 cổng) | FR-12, FR-13 | Nâng thành DG-01..DG-07 + PG; thêm DG-00 ở tầng spec và DG-08 ở CI |
| `rule_database_erd_standards.md` | PG-ERD-01, PG-ERD-02, SEM-ERD-* | Chuyển quy tắc thành luật SEM và PG có test |
| `mxgraph_runner.html` + `mxClient.min.js` | FR-17, D-16 | Giữ làm Renderer thứ nhất cho Pha 2; kiểm độ giống draw.io (S9); không dùng để tính bố cục/đo chữ |
| Heuristic `len(text)·k + pad` | FR-05 | **Thay** bằng Text Measurer (font ghim, `getlength`, NFC) |
| (chưa có) Spec Registry và schema | FR-01, FR-02 | **Viết mới** (Pydantic discriminated union); thêm `get_diagram_schema` |
| (chưa có) Semantic Linter DG-00 | FR-03 | **Viết mới** theo 4.8 |
| (chưa có) Style và Icon Registry | FR-04 | **Viết mới**; test render không trống |
| (chưa có) Node sidecar `elk_worker.mjs` | FR-06 | **Viết mới** (~50 dòng), stdin/stdout JSON; ghim phiên bản; sandbox |
| (chưa có) Router có waypoint tường minh và cổng theo dòng | FR-08 | **Viết mới**, sau S5 |
| (chưa có) Quality Metrics | FR-25 | **Viết mới** |
| (chưa có) Inspect/Patch, bố cục ổn định | FR-19, FR-20 | **Viết mới** |
| (chưa có) Importer SQL DDL/DBML | FR-21 | **Viết mới** (P1) |
| (chưa có) `FileRef`, audit, sandbox, giới hạn tài nguyên | FR-22, FR-23, SEC-04, NFR-02 | Dùng chung hạ tầng với Docx/Xlsx Engine |
| `spec_diagram_engine`, trình soạn Tkinter | — | Đã loại bỏ; không quay lại |
| Spike S1-S4 | EV-01..EV-05, TC | Chuyển thành test hồi quy độc lập; chạy lại S3; mở rộng S2, S4 (S5-S9) |

---

## Phụ lục G. Ma trận truy vết (FR / NFR / SEC ↔ module ↔ TC)

Quy tắc: mục nào thiếu một trong ba cột là khoảng trống phải xử lý trước phát hành (7.4.b). Mục P2 chưa có TC được đánh dấu rõ.

| Yêu cầu | Module (4.2) | Ca kiểm thử | Ghi chú |
|---|---|---|---|
| FR-01 Spec Registry và schema | Spec Registry & Validation | TC-01 | |
| FR-02 Kiểm tra spec | Spec Registry & Validation | TC-01, TC-41 | |
| FR-03 Gate ngữ nghĩa DG-00 | Semantic Linter | TC-02, TC-03, TC-04, TC-05, TC-06, TC-07 | TC-03, TC-06: P1 |
| FR-04 Style và Icon Registry | Style & Icon Registry | TC-07, TC-28 | |
| FR-05 Text Measurer | Text Measurer | TC-08, TC-09, TC-37 | Ground truth: S6 |
| FR-06 Layout Dispatcher và ELK | Layout Dispatcher, Sandbox | TC-10, TC-11 | |
| FR-07 Bố cục theo loại | Layout Dispatcher | TC-12, TC-13, TC-14 | Loại còn lại: P1 |
| FR-08 Router | Router | TC-15, TC-16, TC-17 | S5 |
| FR-09 Corridor và Bundling | Router | TC-18 | P1 |
| FR-10 Bố cục bán kính | Layout Dispatcher | TC-12 | P1; bổ sung ca radial khi triển khai |
| FR-11 XML Serializer | XML Serializer | TC-19, TC-32, TC-41 | |
| FR-12 DG-01..DG-07 | Gate Runner | TC-20, TC-21 | |
| FR-13 Cổng PG | Gate Runner | TC-12, TC-14, TC-15 | PG-DFD: P1 |
| FR-14 Diagnostics | Diagnostics Builder | TC-34 | |
| FR-15 Một file nhiều trang | Page Splitter, XML Serializer | TC-24, TC-42 | |
| FR-16 Tự chia trang | Page Splitter | TC-24, TC-42 | P1 |
| FR-17 Render Service | Render Service | TC-22, TC-23 | |
| FR-18 Render Oracle (DG-08) | Render Oracle | TC-16, TC-23, TC-44 | Cần runner draw.io (Q-15) |
| FR-19 Inspect | Inspect/Patch | TC-25 | |
| FR-20 Patch và bố cục ổn định | Inspect/Patch | TC-26 | P1 |
| FR-21 Source Importers | Source Importers | TC-27 | P1 |
| FR-22 `FileRef` | File Store | TC-31 | |
| FR-23 Audit log | Audit Log | TC-36 | |
| FR-24 Tiếng Việt | Text Measurer | TC-08, TC-37 | |
| FR-25 Quality Metrics | Gate Runner | TC-12, TC-38 | |
| FR-26 Làm sạch bảo mật | Gate Runner, Serializer | TC-29 | |
| FR-27 Điểm mở rộng | — | (P2: bổ sung TC khi triển khai) | Khoảng trống có chủ đích |
| FR-28 Chuyển giao Docx/Xlsx | Render Service | TC-39 | P1 |
| FR-29 Bố cục dự phòng không Node | Layout Dispatcher | TC-11 | P1 |
| NFR-01 Tất định | Tất cả | TC-10, TC-32 | |
| NFR-02 Giới hạn tài nguyên | API & Policy | TC-33, TC-42 | |
| NFR-03 Cách ly sidecar/trình duyệt | Sandbox | TC-30 | |
| NFR-04 Quan sát được | API & Policy, Audit Log | TC-36 | |
| NFR-05 Ranh giới Docx/Xlsx | (kiến trúc) | TC-39 | Rà soát thiết kế |
| NFR-06 Hiệu năng | Tất cả | TC-22, TC-35 | |
| NFR-07 Ma trận consumer | Oracle/Compatibility | TC-16, TC-44 | |
| NFR-08 Bố cục ổn định | Inspect/Patch | TC-26 | P1 |
| NFR-09 Di động | Render Service, Text Measurer | TC-22, TC-37 | Linux: bổ sung khi triển khai container |
| NFR-10 An toàn song song | Sandbox, Render Service | TC-22, TC-30 | |
| NFR-11 Mã thoát CI | API & Policy | TC-33 | |
| SEC-01 Làm sạch nhãn | Gate Runner, Serializer | TC-07, TC-29 | |
| SEC-02 Liên kết/ảnh ngoài | Gate Runner | TC-29 | |
| SEC-03 Nhập XML an toàn | Inspect/Patch, Importers | TC-29 | |
| SEC-04 Sandbox sidecar/trình duyệt | Sandbox | TC-30 | |
| SEC-05 Cách ly tenant | File Store | TC-31 | |
| SEC-06 Audit che dữ liệu | Audit Log | TC-36 | |
| SEC-07 Roots / URI mờ | File Store | TC-31 | |
| SEC-08 SVG đầu ra | Render Service | TC-29 | |
| SEC-09 Advisory và giấy phép | (quy trình) | Audit bảo mật 7.4.c | Không có TC chạy được |
| SEC-10 Giới hạn spec | Spec Registry & Validation | TC-29, TC-33 | |
