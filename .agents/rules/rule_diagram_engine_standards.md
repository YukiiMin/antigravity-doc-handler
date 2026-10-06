---
trigger: glob
globs: doctools/**/diagram/**, tests/test_diagram/**, **/*.drawio*
---

# Rule: DIAGRAM Engine & Technical Diagram Standards

> **Module**: DIAGRAM (Technical Diagram & Architecture Visualization)
> **Căn cứ**: Diagram Foundation Plan v1.0, Master Architecture Plan v6, 21 bất biến `MX_INV_01..21`.
> **Scope**: Bắt buộc áp dụng cho mọi tác vụ sinh, kiểm định, vá, import và render sơ đồ kỹ thuật (`.drawio`, PNG/SVG) trong `doctools` / `pdf_to_docx_converter`.

---

## 1. Triết Lý Thiết Kế Cốt Lõi (Core Philosophy)

1. **Engine tất định, AI quyết định**:
   - Engine là MCP Server tất định 100%, không tự gọi AI.
   - AI (Client) chịu trách nhiệm nội dung nghiệp vụ, phát sinh `DiagramSpec` JSON kèm `layout_hints` (hướng, nhóm, rank, importance).
   - **Tuyệt đối CẤM AI tự viết XML hoặc tự đưa tọa độ ($X, Y$)**. Toàn bộ việc đo chữ, tính toán bố cục, bẻ góc dây trực giao và tuần tự hóa XML thuộc thẩm quyền của engine.
2. **Ngữ nghĩa trước hình học (Semantic-First, DGM-D-09)**:
   - **Gate Ngữ nghĩa DG-00** chạy trực tiếp trên spec trước khi tính hình học (fail-closed).
   - Lỗi vi phạm ngữ nghĩa (FK trỏ bảng không tồn tại, chu trình kế thừa, Sequence nghịch đảo thời gian) dừng pipeline ngay lập tức.
3. **Tách biệt Pha 1 và Pha 2 (DGM-D-03)**:
   - **Pha 1 (`diagram.build`)**: Sinh XML `mxGraphModel` tất định thuần túy bằng `lxml`, không cần trình duyệt, thời gian xử lý $< 1$s cho 50 nodes.
   - **Pha 2 (`diagram.render`)**: Render ảnh PNG/SVG qua headless browser runner hoặc Draw.io CLI; chỉ kích hoạt khi có yêu cầu xuất bản.
4. **Waypoint Tường Minh & Docking Container (DGM-D-06, DGM-D-07)**:
   - Đoạn dây gấp khúc bắt buộc mang danh sách điểm tường minh trong `<Array as="points">`.
   - Đường nối chỉ gắn `source`/`target` vào ID của node/bảng cha (`MX_INV_03`), cấm nối vào cell con. Vị trí dòng FK điều khiển bằng `entryDy`/`exitDy`.
5. **Đo Chữ Advance Length Bằng Font Ghim (DGM-D-08)**:
   - Đo độ dài nhãn bằng `Pillow font.getlength(text)` với font ghim đóng gói (Liberation Sans, Be Vietnam Pro), chuẩn hóa Unicode NFC.
   - **Hủy bỏ hoàn toàn hệ số `K_adj = 0.78` và công thức thô $N_{\text{chars}} \times 6.1$** do sai lệch đơn vị.
6. **Ranh giới ngoài**: Diagram Engine **không ghi OOXML**; chèn sơ đồ vào Word/Excel qua `FileRef` ảnh + `render_info`. Sơ đồ Schematic quy hoạch vào **Phase 3b (P2)** đi kèm Diagram Spec v1.1.

---

## 2. Bảng 21 Bất Biến Kỹ Thuật Draw.io & mxGraphModel (`MX_INV_01..21`)

| Mã Bất Biến | Tên Bất Biến | Quy Chuẩn Cưỡng Chế Bắt Buộc | Cổng / Test |
|---|---|---|---|
| `MX_INV_01` | **Pure Native Hierarchy** | CẤM thẻ `<UserObject mermaidData/plantUmlData>`. Node/edge là `<mxCell>` trực tiếp dưới `<root><mxCell id="1" parent="0"/>`. | `DG-01` / `DGM-TC-19` |
| `MX_INV_02` | **Minimalist & Clean XML** | Loại bỏ metadata rác (`mermaidBaseStyle`, `alternateBounds`). File $< 300\text{KB}$, well-formed 100%. | `DG-01` / `DGM-TC-19` |
| `MX_INV_03` | **Container-Level Docking** | Edge chỉ nối vào ID của bảng/node cha (`table_<NAME>`), cấm nối vào cell con (`tableRow`). | `DG-04` / `DGM-TC-17` |
| `MX_INV_04` | **Orthogonal Perimeter Routing**| Đường nối vuông góc 90°: `edgeStyle=orthogonalEdgeStyle;`. Cổng chu vi chuẩn: Top `(0.5, 0.0)`, Bottom `(0.5, 1.0)`, Left `(0.0, 0.5)`, Right `(1.0, 0.5)`. | `DG-07` / `DGM-TC-15` |
| `MX_INV_05` | **Dynamic Geometry Scaling** | Chiều cao bảng tự co giãn: $H = 43 \times (N_{\text{fields}} + 1)$. Hành lang an toàn $\ge 60\text{px}$ giữa 2 bảng. | `DG-03` / `DGM-TC-12` |
| `MX_INV_06` | **Dual Delivery** | Xuất song song file vector gốc `.drawio` và ảnh render chất lượng cao (PNG/SVG theo DPI chuẩn). | Render / `DGM-TC-22` |
| `MX_INV_07` | **Monochrome Line-Art** | Sơ đồ kỹ thuật ưu tiên Monochrome: nền trắng `#ffffff`, viền đen `#000000`, nét đứt xám `#888888` cho quan hệ phụ. | `DG-01` / `DGM-TC-28` |
| `MX_INV_08` | **Collision-Free Masks** | Nhãn trên dây có `labelBackgroundColor=#ffffff;` chống đè chữ; hành lang chạy dây $\ge 40\text{px}$. | `DG-05` / `DGM-TC-09` |
| `MX_INV_09` | **Multi-Page Single-File** | Đóng gói nhiều sơ đồ liên quan trong 1 file `.drawio` duy nhất với nhiều tab `<diagram name="...">`. | `DG-01` / `DGM-TC-24` |
| `MX_INV_10` | **Schematic Direct Taps** | [Phase 3b] Dây nguồn màu (+12V Đỏ, +5V Cam, +3V3 Xanh, GND Đen) đi thẳng từ rail vào IC/MCU. | `PG-SCH-01` / `DGM-TC-SCH-01` |
| `MX_INV_11` | **Fractional Port Anchoring** | Cổng neo phân số theo dòng FK: `exitY = clamp((y - y_top) / H, 0.05, 0.95)` kèm offset `entryDy` để mũi tên đi thẳng. | `DG-07` / `DGM-TC-15` |
| `MX_INV_12` | **Discrete Highway Corridors** | Tuyến bus song song đi qua các trục tọa độ rời rạc cách nhau $\ge 30\text{px}$–$50\text{px}$. Nhãn tự động wrap. | `DG-07` / `DGM-TC-18` |
| `MX_INV_13` | **Schematic Strip Layout** | [Phase 3b] IC xếp dải ngang 1 hàng (L-to-R), Rails nguồn trên đỉnh, GND dưới đáy cắm thẳng đứng. | `PG-SCH-02` / `DGM-TC-SCH-02` |
| `MX_INV_14` | **DFD 5-Column Flow** | [Phase 3b] Sơ đồ DFD tuân thủ 5 cột: $C_1$ External $\rightarrow$ $C_2$ Ingestion $\rightarrow$ $C_3$ Processing/Store $\rightarrow$ $C_4$ Comm $\rightarrow$ $C_5$ Cloud. | `PG-DFD-01` / `DGM-TC-06` |
| `MX_INV_15` | **Dynamic Edge Label Width** | CẤM `\n`, `<br>` trong nhãn dây. Bắt buộc dùng `labelWidth=<W>;html=1;whiteSpace=wrap;` để Draw.io tự wrap. | `DG-05` / `DGM-TC-09` |
| `MX_INV_16` | **4-Tier Stroke Depth** | Tier 1 (Khung/Rail: 2.5–3.0px) > Tier 2 (MCU/IC: 1.8–2.0px) > Tier 3 (Ngoại vi: 1.2px) > Tier 4 (Line dây: 1.0px). | `PG-ARC-01` / `DGM-TC-13` |
| `MX_INV_17` | **Rail Header Legend** | [Phase 3b] Tên rail nguồn tách thành cột Header riêng ($x < x_{\text{first\_ic}}$), thân rail để `value=""` chống đè chữ. | `PG-SCH-02` / `DGM-TC-SCH-03` |
| `MX_INV_18` | **MCU Egress Waterfall** | Tuyến bus từ MCU không đâm xuyên hộp linh kiện phụ; đi vào hành lang dọc riêng ($\ge 80\text{px}$) rồi đổ thác xuống bus. | `DG-07` / `DGM-TC-18` |
| `MX_INV_19` | **4-Sided Data Store** | [Phase 3b] Kho dữ liệu (D1, D2) trong DFD bắt buộc có đủ 4 cạnh viền (`top=1;bottom=1;left=1;right=1;`) chống mất viền. | `PG-DFD-01` / `DGM-TC-06` |
| `MX_INV_20` | **Snug Mask Bounding** | CẤM gán cứng `labelWidth` quá lớn. `labelWidth` tính động ôm khít chữ đo được để mặt nạ không che lấp dây lân cận. | `DG-05` / `DGM-TC-09` |
| `MX_INV_21` | **Zero-Clipping Viewport** | Headless render quét $(\max_X, \max_Y)$ động. Viewport $\ge \max + 160\text{px}$, PIL auto-crop với 25px uniform padding. | `DG-06` / `DGM-TC-21` |

---

## 3. Quy Chuẩn Physical ERD & Crow's Foot

1. **Khối Bảng 3 Cột**: Cột 1 kiểu dữ liệu, Cột 2 tên trường, Cột 3 định danh khóa (`PK`, `FK`, `UK`). Chiều cao dòng chuẩn 43px.
2. **Không Dùng Nhãn Động Từ**: Trong Physical ERD, tuyệt đối KHÔNG hiển thị nhãn chữ động từ (`authenticates`, `creates`). Quan hệ thể hiện qua tên trường `<<FK>>` và Crow's Foot.
3. **Ký Hiệu Crow's Foot Chuẩn**:
   - `Mandatory 1` ($||$): `startArrow=ERmandOne; endArrow=ERmandOne;`
   - `Zero or 1` ($o|$): `startArrow=ERzeroToOne; endArrow=ERzeroToOne;`
   - `Zero or Many` ($o\{$): `startArrow=ERzeroToMany; endArrow=ERzeroToMany;`
   - `One or Many` ($|\{$): `startArrow=ERoneToMany; endArrow=ERoneToMany;`
4. Dây quan hệ cắm chính xác vào dòng chứa trường FK qua `entryDy` tương ứng (`PG-ERD-02`).

---

## 4. Chuỗi Cổng Kiểm Định `DG-00..DG-08` & PG Profiles

- `DG-00` (**Semantic Validity**): 100% luật `SEM-*` mức error đạt trên DiagramSpec JSON trước khi tính bố cục.
- `DG-01` (**XML Well-Formedness**): XML hợp lệ, kết thúc `</root></mxGraphModel>`, không chứa thẻ rác UserObject.
- `DG-02` (**Unique IDs & Hierarchy**): 100% ID duy nhất; mọi `mxCell` có parent tồn tại trong cây DOM.
- `DG-03` (**AABB Collision & Spacing**): 0 node chồng lấn qua R-tree; khoảng cách `min_node_gap >= 60px`.
- `DG-04` (**Container Docking**): 100% edge chỉ trỏ vào node cha, cấm edge trỏ vào cell con.
- `DG-05` (**Snug Label & Bounds**): `labelWidth` khớp kích thước đo advance length; nhãn không che dây lân cận.
- `DG-06` (**Zero-Clipping Viewport**): Viewport $\ge \max + 160\text{px}$; ảnh render tự cắt với 25px uniform padding.
- `DG-07` (**Edge Routing Integrity**): 100% trực giao; không dây xuyên node không liên quan; báo cáo số giao cắt.
- `DG-08` (**Render Oracle Gate**): File `.drawio` mở được trên Draw.io Desktop/CLI không lỗi.
- **PG Profiles**: `PG-ERD-*` (3 cột, Crow's foot, dòng FK), `PG-ARC-*` (4 tier stroke, container), `PG-SEQ-*` (lifeline, thứ tự thời gian), `PG-DFD-*` [P1] (5 cột, kho 4 cạnh), `PG-SCH-*` [P2] (rails, dải ngang).

---

## 5. Danh Mục Công Cụ MCP `diagram.*` & Bảng Mã Lỗi

1. `diagram.get_schema`: Trả JSON Schema và ví dụ theo `diagram_type`.
2. `diagram.validate_spec`: Kiểm tra schema và chạy Gate Ngữ nghĩa DG-00 (fail-closed, chỉ đọc).
3. `diagram.build`: DiagramSpec $\rightarrow$ file `.drawio` (Pha 1: đo chữ, bố cục ELK/Python, router, serializer).
4. `diagram.validate_drawio`: Chạy DG-01..DG-07 và PG profiles trên file `.drawio`.
5. `diagram.inspect`: Đọc cấu trúc sơ đồ: trang, node, edge, anchor ổn định.
6. `diagram.render`: Pha 2: Render PNG/SVG từ `.drawio` qua headless browser / Draw.io CLI.
7. `diagram.patch` [P1]: Sửa file có sẵn theo thao tác khai báo, bố cục tăng dần.
8. `diagram.import_source` [P1]: Nhập từ SQL DDL, DBML $\rightarrow$ DiagramSpec tất định.
9. `diagram.list_style_registry` [P1]: Liệt kê token kiểu dáng và icon cloud hợp lệ.

### Bảng Mã Lỗi Chuẩn:
`E-DGM-SPEC-*` (sai schema/vượt giới hạn); `E-DGM-SEM-*` (vi phạm ngữ nghĩa ERD/ARC/SEQ); `E-DGM-STYLE-*` (token ngoài allow-list); `E-DGM-LAYOUT-*` (sidecar/overlap); `E-DGM-ROUTE-*` (xuyên node/sai trực giao); `E-DGM-XML-*` (lỗi XML/docking cell con); `E-DGM-RENDER-*` (timeout/crash render); `E-DGM-SEC-*` (XSS trong nhãn, XXE); `W-DGM-*` (cảnh báo độ dày layout, số giao cắt, advance length ước lượng).
