# Rule: DIAGRAM Engine & Technical Diagram Standards

> **Module**: DIAGRAM (Technical Diagram & Architecture Visualization)
> **Companion Spec**: [Diagram Foundation Plan v1.0](docs/update-spec/diagram-engine-mcp-plan.md) & [Master Architecture Plan v6](brain/97336993-346b-4633-a7c7-6988a7a212ae/ai_native_toolkit_modular_architecture_plan.md)
> **Scope**: Bắt buộc áp dụng cho mọi tác vụ sinh, kiểm tra, kiểm định, vá, import và render sơ đồ kỹ thuật (.drawio, PNG/SVG) trong bộ công cụ AI-Native `doctools` / `pdf_to_docx_converter`.

---

## 1. Triết Lý Thiết Kế Cốt Lõi (Core Philosophy)

1. **Engine tất định, AI quyết định**:
   - Engine là MCP Server tất định 100%, không chứa logic phỏng đoán, không tự gọi AI.
   - AI (Client) chịu trách nhiệm nội dung nghiệp vụ, phát sinh `DiagramSpec` JSON kèm `layout_hints` (hướng, nhóm, rank, importance).
   - **Tuyệt đối CẤM AI tự viết XML hoặc tự đưa tọa độ ($X, Y$)**. Toàn bộ việc đo chữ, tính toán bố cục, bẻ góc dây trực giao và tuần tự hóa XML thuộc thẩm quyền của engine.
2. **Ngữ nghĩa trước hình học (Semantic-First, DGM-D-09)**:
   - **Gate Ngữ nghĩa DG-00** chạy trực tiếp trên spec trước khi tính hình học (fail-closed).
   - Mọi lỗi vi phạm ngữ nghĩa (FK trỏ bảng không tồn tại, chu trình kế thừa, Sequence nghịch đảo thời gian, Subnet ngoài VPC, CIDR chồng lấn) dừng pipeline ngay lập tức, không phát hành file.
3. **Tách biệt Pha 1 và Pha 2 (DGM-D-03)**:
   - **Pha 1 (`diagram.build`)**: Sinh XML `mxGraphModel` tất định thuần túy bằng `lxml`, không cần trình duyệt, không cần mxGraph runtime, thời gian xử lý $< 1$s cho 50 nodes.
   - **Pha 2 (`diagram.render`)**: Render ảnh PNG/SVG chất lượng cao qua headless browser runner hoặc Draw.io CLI; chỉ kích hoạt khi có yêu cầu xuất bản tài liệu.
4. **Waypoint Tường Minh & Docking Container (DGM-D-06, DGM-D-07)**:
   - Mọi đoạn dây không phải đoạn thẳng trực tiếp bắt buộc mang danh sách điểm gấp khúc tường minh trong `<Array as="points">`.
   - Đường nối chỉ được gắn `source`/`target` vào ID của node/bảng cha (`MX_INV_03`), cấm nối vào cell con. Vị trí dòng FK điều khiển bằng tọa độ phân số chu vi `exitY/entryY` và offset `exitDy/entryDy`.
5. **Đo Chữ Advance Length Bằng Font Ghim (DGM-D-08)**:
   - Đo độ dài nhãn bằng `Pillow font.getlength(text)` với font ghim đóng gói (Liberation Sans, Be Vietnam Pro) ở đúng kích thước pixel, chuẩn hóa Unicode NFC.
   - **Hủy bỏ hoàn toàn hệ số `K_adj = 0.78` và công thức thô $N_{\text{chars}} \times 6.1$** do sai lệch đơn vị cỡ chữ trong các script cũ. Mọi kích thước đo gắn nhãn `estimated`.
6. **Ranh giới Cam kết**:
   - **Bảo đảm**: File `.drawio` là XML hợp lệ, ID duy nhất, không node chồng nhau, không dây xuyên node không liên quan, số giao cắt được tối thiểu hóa và báo cáo.
   - **KHÔNG bảo đảm**: "Zero-crossing" trên đồ thị dày hoặc không phẳng; không bảo đảm trùng khớp pixel 100% giữa các trình đọc Draw.io khác nhau.
   - **Ranh giới ngoài**: Diagram Engine **không ghi OOXML**; chèn sơ đồ vào Word/Excel chuyển giao qua `FileRef` ảnh + `render_info`. Sơ đồ Mạch điện Schematic quy hoạch vào **Phase 3b (P2)** đi kèm Diagram Spec v1.1.

---

## 2. Bảng 21 Bất Biến Kỹ Thuật Draw.io & mxGraphModel (`MX_INV_01..21`)

Mọi sơ đồ kỹ thuật và mã sinh Draw.io bắt buộc phải tuân thủ nghiêm ngặt 21 bất biến cốt lõi:

| Mã Bất Biến | Tên Bất Biến | Mô Tả & Quy Chuẩn Cưỡng Chế | Cưỡng Chế Bởi Gate / Test |
|---|---|---|---|
| `MX_INV_01` | **Pure Native Hierarchy** | **CẤM** bọc sơ đồ trong `<UserObject mermaidData="..." plantUmlData="...">`. Toàn bộ node và edge bắt buộc là `<mxCell>` trực tiếp dưới `<root><mxCell id="1" parent="0"/>`. | `DG-01` (XML Gate) / `DGM-TC-19` |
| `MX_INV_02` | **Minimalist & Well-Formed XML** | Loại bỏ metadata rác (`mermaidBaseStyle`, `mermaidId`, `alternateBounds`). File $< 300\text{KB}$, kết thúc đầy đủ bằng `</root></mxGraphModel>`. | `DG-01` (XML Gate) / `DGM-TC-19` |
| `MX_INV_03` | **Container-Level Docking** | Edge chỉ được nối `source`/`target` vào ID của bảng/node cha (`table_<NAME>`), **nghiêm cấm** nối vào cell con (`tableRow`/`partialRectangle`). | `DG-04` (Docking Gate) / `DGM-TC-17` |
| `MX_INV_04` | **Orthogonal Perimeter Routing** | Đường nối vuông góc 90°: `edgeStyle=orthogonalEdgeStyle;`. Khai báo cổng chu vi chuẩn: Top `(0.5, 0.0)`, Bottom `(0.5, 1.0)`, Left `(0.0, 0.5)`, Right `(1.0, 0.5)`. | `DG-07` (Routing Gate) / `DGM-TC-15` |
| `MX_INV_05` | **Dynamic Geometry Scaling** | Chiều cao bảng tự co giãn: $H = \text{header\_h} + N_{\text{fields}} \times \text{row\_h}$. Duy trì hành lang giao thông an toàn $\ge 60\text{px}$ giữa 2 bảng liền kề. | `DG-03` (Collision Gate) / `DGM-TC-12` |
| `MX_INV_06` | **Dual Delivery** | Xuất song song file vector gốc `.drawio` và ảnh render độ nét cao (PNG/SVG theo DPI chuẩn) để tích hợp vào tài liệu. | Quy trình Render / `DGM-TC-22` |
| `MX_INV_07` | **Monochrome Academic Line-Art** | Sơ đồ học thuật/kỹ thuật ưu tiên Monochrome: nền trắng `#ffffff`, viền đen `#000000`, nét đứt xám `#888888` cho quan hệ phụ. | `DG-01` & Token Registry / `DGM-TC-28` |
| `MX_INV_08` | **Collision-Free Labels & Masks** | Nhãn trên dây có `labelBackgroundColor=#ffffff;labelBorderColor=none;` chống đè chữ; hành lang chạy dây $\ge 40\text{px}$. | `DG-05` & `DG-07` / `DGM-TC-09` |
| `MX_INV_09` | **Multi-Page Single-File** | Đóng gói toàn bộ các sơ đồ liên quan trong 1 file `.drawio` duy nhất với nhiều tab `<diagram name="...">`. | `DG-01` & Page Manager / `DGM-TC-24` |
| `MX_INV_10` | **Schematic Direct Taps** | [Phase 3b] Dây nguồn màu (+12V Đỏ, +5V Cam, +3V3 Xanh, GND Đen) đi thẳng từ rail vào IC/MCU. Không gắn nhãn text đè dây nguồn. | `PG-SCH-01` / `DGM-TC-SCH-01` |
| `MX_INV_11` | **Fractional Port Anchoring** | Cổng neo phân số theo dòng FK: `exitY = clamp((y - y_top) / H, 0.05, 0.95)` kèm offset `entryDy` để mũi tên đi thẳng vào đúng dòng. | `DG-07` (Routing Gate) / `DGM-TC-15` |
| `MX_INV_12` | **Discrete Highway Corridors** | Tuyến bus song song đi qua các trục tọa độ rời rạc cách nhau $\ge 30\text{px}$–$50\text{px}$. Nhãn dài tự động wrap theo hành lang. | `DG-07` (Routing Gate) / `DGM-TC-18` |
| `MX_INV_13` | **Schematic Horizontal Strip** | [Phase 3b] IC/Module xếp dải ngang 1 hàng (L-to-R), Rails nguồn trên đỉnh, GND dưới đáy cắm thẳng đứng. GPIO đi qua bus tầng dưới. | `PG-SCH-02` / `DGM-TC-SCH-02` |
| `MX_INV_14` | **DFD 5-Column Orthogonal Flow** | [Phase 3b] Sơ đồ DFD tuân thủ 5 cột: $C_1$ External $\rightarrow$ $C_2$ Ingestion $\rightarrow$ $C_3$ Processing/Store $\rightarrow$ $C_4$ Comm $\rightarrow$ $C_5$ Cloud. | `PG-DFD-01` / `DGM-TC-06` |
| `MX_INV_15` | **Dynamic Edge Label Width** | **CẤM** chèn `\n`, `<br>` vào nhãn của dây. Bắt buộc dùng `labelWidth=<W>;html=1;whiteSpace=wrap;` để Draw.io tự động xuống hàng. | `DG-05` (Label Gate) / `DGM-TC-09` |
| `MX_INV_16` | **4-Tier Stroke Depth Hierarchy** | 4 cấp độ đậm nét: Tier 1 (Khung lớn/Rail: 2.5–3.0px) > Tier 2 (MCU/IC: 1.8–2.0px) > Tier 3 (Ngoại vi: 1.2px) > Tier 4 (Line dây: 1.0px). | `PG-ARC-01` / `DGM-TC-13` |
| `MX_INV_17` | **Dedicated Rail Header Legend** | [Phase 3b] Tên rail nguồn tách thành cột Header riêng ($x < x_{\text{first\_ic}}$), thân rail để `value=""` chống dây cắt đè lên chữ. | `PG-SCH-02` / `DGM-TC-SCH-03` |
| `MX_INV_18` | **MCU Egress Waterfall Routing** | Tuyến bus từ MCU không đâm xuyên hộp linh kiện phụ; đi vào hành lang dọc riêng ($\ge 80\text{px}$) rồi đổ thác xuống bus $y \ge 475$. | `DG-07` (Routing Gate) / `DGM-TC-18` |
| `MX_INV_19` | **Complete 4-Sided Data Store** | [Phase 3b] Kho dữ liệu (D1, D2) trong DFD bắt buộc có đủ 4 cạnh viền (`top=1;bottom=1;left=1;right=1;`) chống mất viền trái/phải. | `PG-DFD-01` / `DGM-TC-06` |
| `MX_INV_20` | **Snug Mask Bounding** | CẤM gán cứng `labelWidth` quá lớn. `labelWidth` tính động ôm khít chữ đo được để mặt nạ trắng không che lấp dây lân cận. | `DG-05` (Label Gate) / `DGM-TC-09` |
| `MX_INV_21` | **Zero-Clipping Viewport** | Headless render quét toàn bộ geometry tính $(\max_X, \max_Y)$ động. Viewport $\ge \max + 160\text{px}$, PIL auto-crop với 25px uniform padding. | `DG-06` (Viewport Gate) / `DGM-TC-21` |

---

## 3. Quy Chuẩn Thực Thể Bảng ERD (Native 3-Column Entity & Crow's Foot)

### 3.1. Cấu Trúc Khối Bảng Native 3 Cột (Type | Field Name | Key)
- Mọi bảng trong Physical ERD bắt buộc cấu trúc theo khối 3 cột:
  - Cột 1: Kiểu dữ liệu (`int`, `varchar(255)`, `timestamp`, `bigint`).
  - Cột 2: Tên trường dữ liệu (`id`, `user_id`, `created_at`).
  - Cột 3: Định danh khóa (`PK`, `FK`, `UK`, hoặc để trống).
- Chiều cao dòng chuẩn 43px, `startSize=43` cho tiêu đề bảng. Căn lề trái cho text, căn giữa cho khóa.

### 3.2. Quy Tắc Đầu Nối Chuẩn Crow's Foot & Loại Bỏ Nhãn Động Từ Dư Thừa
1. **Physical ERD KHÔNG dùng nhãn động từ (No Verb Labels)**:
   - Trong Physical ERD (Database Schema), **tuyệt đối KHÔNG hiển thị nhãn chữ động từ quan hệ** (`authenticates`, `holds`, `creates`, `purchases`).
   - Bản chất Physical ERD đã thể hiện trọn vẹn quan hệ qua tên trường khóa ngoại `<<FK>>` và ký hiệu Crow's Foot. Nhãn động từ chỉ dành cho Conceptual Diagram.
2. **Ký hiệu Crow's Foot Native Chuẩn**:
   - `Mandatory 1` ($||$): `startArrow=ERmandOne; endArrow=ERmandOne;`
   - `Zero or 1` ($o|$): `startArrow=ERzeroToOne; endArrow=ERzeroToOne;`
   - `Zero or Many` ($o\{$): `startArrow=ERzeroToMany; endArrow=ERzeroToMany;`
   - `One or Many` ($|\{$): `startArrow=ERoneToMany; endArrow=ERoneToMany;`
3. **Cổng Neo Vào Đúng Dòng Khóa Ngoại**:
   - Dây quan hệ nối sang bảng "nhiều" bắt buộc phải cắm chính xác vào dòng chứa trường FK thông qua `entryDy` tương ứng với vị trí dòng của trường đó (`PG-ERD-02`).

---

## 4. Chuỗi Cổng Kiểm Định `DG-00..DG-08` & `PG Profiles`

Mọi sơ đồ trước khi phát hành phải vượt qua chuỗi cổng kiểm định tự động:

| Cổng | Tên Cổng Kiểm Định | Tiêu Chí Đo Lường Cụ Thể |
|---|---|---|
| **DG-00** | **Semantic Validity Gate** | 100% luật `SEM-*` mức `error` đều đạt trên DiagramSpec JSON trước khi tính bố cục. |
| **DG-01** | **XML Well-Formedness** | XML đóng thẻ hoàn chỉnh, kết thúc bằng `</root></mxGraphModel>`, không chứa thẻ rác UserObject Mermaid/PlantUML. |
| **DG-02** | **Unique IDs & Parent Hierarchy** | 100% ID duy nhất trong toàn file; mọi `mxCell` có `parent` thực sự tồn tại trong cây DOM. |
| **DG-03** | **AABB Collision & Spacing** | Kiểm tra va chạm hộp bao qua R-tree: 0 node nào chồng lấn nhau; khoảng cách `min_node_gap >= 60px`. |
| **DG-04** | **Container-Level Docking** | 100% edge chỉ trỏ vào node cha, cấm edge trỏ vào cell con; các phần tử con nằm trọn trong container cha. |
| **DG-05** | **Snug Label & Bounds** | `labelWidth` khớp kích thước đo advance length; không ngắt dòng thủ công; nhãn không che dây song song lân cận. |
| **DG-06** | **Zero-Clipping Viewport** | Kích thước viewport $\ge \max + 160\text{px}$; ảnh render xuất bản tự cắt biên với 25px uniform padding. |
| **DG-07** | **Edge Routing Integrity** | 100% đoạn dây trực giao; không dây đâm xuyên qua node không liên quan; số giao cắt được đo lường và báo cáo. |
| **DG-08** | **Render Oracle Gate (CI)** | File `.drawio` mở được trên Draw.io Desktop/CLI thật mà không phát sinh lỗi hoặc cảnh báo. |

### Các Profile Kiểm Định Chuyên Biệt (PG Profiles)
- `PG-ERD-01/02`: Bảng 3 cột Type/Name/Key, ký hiệu Crow's foot chuẩn, dây cắm đúng dòng FK, không đè chữ bảng.
- `PG-ARC-01/02`: Phân tầng nét vẽ 4 tier (`MX_INV_16`), container bao trọn con, icon thuộc allow-list.
- `PG-SEQ-01`: Lifeline thẳng đứng, thông điệp nằm ngang đúng thứ tự thời gian đơn điệu, activation cân bằng.
- `PG-DFD-01` [Phase 3b]: Lưới 5 cột đúng thứ tự (`MX_INV_14`), kho dữ liệu đóng kín 4 cạnh (`MX_INV_19`).
- `PG-SCH-01/02` [Phase 3b]: Dây nguồn cắm đúng rail, module xếp dải ngang 1 hàng (`MX_INV_10, 13, 17`).

---

## 5. Danh Mục 9 Công Cụ MCP `diagram.*` & Bảng Mã Lỗi

### Danh Mục Công Cụ MCP
1. `diagram.get_schema`: Trả JSON Schema và ví dụ theo `diagram_type` (`erd`, `architecture`, `sequence`, `dfd`, `class`, `radial`, `schematic`).
2. `diagram.validate_spec`: Kiểm tra schema và chạy Gate Ngữ nghĩa DG-00 (fail-closed, chỉ đọc).
3. `diagram.build`: DiagramSpec $\rightarrow$ file `.drawio` (Pha 1: đo chữ, bố cục ELK/Python, router, serializer).
4. `diagram.validate_drawio`: Chạy DG-01..DG-07 và PG profiles trên file `.drawio` có sẵn.
5. `diagram.inspect`: Đọc cấu trúc sơ đồ cho AI: trang, node, edge, anchor ổn định.
6. `diagram.render`: Pha 2: Render PNG/SVG từ `.drawio` qua headless browser / Draw.io CLI.
7. `diagram.patch` [P1]: Sửa file có sẵn theo thao tác khai báo, bố cục tăng dần giữ nguyên node ghim.
8. `diagram.import_source` [P1]: Nhập từ nguồn có cấu trúc (SQL DDL, DBML) $\rightarrow$ DiagramSpec tất định.
9. `diagram.list_style_registry` [P1]: Liệt kê token kiểu dáng và icon cloud hợp lệ.

### Bảng Mã Lỗi Chuẩn
- `E-DGM-SPEC-*`: Lỗi cấu trúc JSON Spec hoặc vượt giới hạn dung lượng/kích thước sơ đồ.
- `E-DGM-SEM-*`: Lỗi vi phạm ngữ nghĩa spec (`E-DGM-SEM-ERD-*`, `E-DGM-SEM-ARC-*`, `E-DGM-SEM-SEQ-*`).
- `E-DGM-STYLE-*`: Token kiểu dáng hoặc icon không có trong allow-list (`E-DGM-STYLE-UNKNOWN`).
- `E-DGM-LAYOUT-*`: Bố cục thất bại (`E-DGM-LAYOUT-SIDECAR`, `E-DGM-LAYOUT-OVERLAP`).
- `E-DGM-ROUTE-*`: Dây xuyên node không liên quan, cổng neo ngoài chu vi, lỗi định tuyến trực giao.
- `E-DGM-XML-*`: Vi phạm tính toàn vẹn XML, ID trùng, docking vào cell con (`E-DGM-XML-INV-*`).
- `E-DGM-RENDER-*`: Render ảnh thất bại hoặc timeout trong headless browser.
- `E-DGM-SEC-*`: Vi phạm bảo mật (payload XSS trong nhãn, XXE, liên kết mạng ngoài).
- `W-DGM-LAYOUT-DENSE`: Sơ đồ quá dày, vượt ngưỡng khuyến nghị $\rightarrow$ gợi ý chia trang.
- `W-DGM-ROUTE-CROSSINGS`: Cảnh báo số giao cắt đo được trên đồ thị không phẳng.
- `W-DGM-TEXT-ESTIMATED`: Thông báo độ rộng nhãn là ước lượng advance length từ font ghim.
