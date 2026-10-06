---
name: mxgraph-diagram-engineering
description: AI-Native Diagram Engineering Skill for Draw.io (mxGraphModel). Professional generation, topology layout, orthogonal routing, headless rendering, visual inspection, and layout auto-repair without manual coordinate guesswork.
---

# Skill: mxGraphModel & Draw.io Diagram Engineering (AI-Native Engine)

> **Mục tiêu**: Chuẩn hóa toàn bộ quy trình thiết kế, sinh mã, kiểm định và tối ưu hóa sơ đồ kỹ thuật chất lượng cao trên Draw.io (`mxGraphModel`).  
> **Nguyên tắc nền tảng**: Tuân thủ 100% tài liệu [`.agents/rules/rule_diagram_engine_standards.md`](file:///d:/Minh/For_myself/ZSCORT_GSU26_SAP05/tool/pdf_to_docx_converter/.agents/rules/rule_diagram_engine_standards.md) và Quy trình Chuẩn `WF-DIAG-01..05` tại skill `doctools-delivery`.

---

## 1. Mental Model Vận Hành AI-Native (Cốt Lõi)

1. **AI KHÔNG Tự Viết XML Draw.io**: AI tuyệt đối không tự chắp vá hàng ngàn dòng XML bằng tay. Rủi ro hỏng tag, rách cấu trúc hoặc Draw.io từ chối Apply là cực kỳ cao.
2. **AI KHÔNG Tự Đoán Tọa Độ Pixel Bằng Tay**: Bố cục không gian $(x, y)$, chiều rộng/cao, và đường đi của dây nối (orthogonal waypoints) phải do layout planner tất định (`Sugiyama`, `Force-Directed`, `Radial`) tính toán.
3. **Giao Tiếp Bằng JSON Spec Chuẩn (`DiagramSpec`)**: AI tập trung vào logic hệ thống (danh sách `nodes`, `edges`, `groups`, `topology`, `theme`), trao đổi với Engine qua các công cụ MCP.
4. **Kiểm Định Thị Giác Khép Kín (Visual Closed-Loop Inspection)**: Bản vẽ sinh ra bắt buộc phải được render headless sang PNG/SVG và kiểm tra trực quan tự động bằng `diagram.inspect_visual` trước khi bàn giao.

---

## 2. Bảng Tra Cứu 21 Bất Biến Cốt Lõi (MX_INV_01–21)

| Mã | Tên Bất Biến | Nguyên Tắc Kỹ Thuật Bắt Buộc |
|---|---|---|
| `MX_INV_01` | **Pure Native Hierarchy** | Cấm thẻ `<UserObject mermaidData/plantUmlData>`. Mọi node và edge phải là `<mxCell>` trực tiếp dưới `parent="1"`. |
| `MX_INV_02` | **Minimalist & Well-Formed XML** | Xóa metadata rác (`mermaidBaseStyle`, `mermaidId`, `alternateBounds`). XML well-formed 100%, dung lượng gọn nhẹ. |
| `MX_INV_03` | **Container-Level Docking** | Dây nối ERD chỉ kết nối vào vỏ bảng (`table_X`), nghiêm cấm nối vào cell con (`tableRow`/`partialRectangle`). |
| `MX_INV_04` | **Orthogonal Perimeter Routing** | `edgeStyle=orthogonalEdgeStyle;` kèm cổng viền chuẩn (`exitX, exitY, entryX, entryY` là `0.0`, `0.5`, `1.0`). |
| `MX_INV_05` | **Dynamic Geometry Scaling** | Chiều cao bảng ERD: $H = 43 \times (N_{\text{fields}} + 1)$; hành lang giao thông giữa các khối $\ge 60$px. |
| `MX_INV_06` | **Dual Delivery** | Xuất theo định dạng yêu cầu (`.drawio` và `.png`/`.svg` đi kèm; không tạo file rác trùng lặp). |
| `MX_INV_07` | **Academic Line-Art First** | Ưu tiên Monochrome học thuật: `#ffffff` fill, `#000000` text/viền, nét đứt `#888888` cho liên kết tùy chọn. |
| `MX_INV_08` | **Collision-Free Labels & Masks** | Nhãn trên dây phải có `labelBackgroundColor=#ffffff;` chống đè nét; hành lang chạy dây $\ge 40$px. |
| `MX_INV_09` | **Multi-Page Single-File** | Hỗ trợ đóng gói đa sơ đồ trong 1 file `.drawio` duy nhất với nhiều tab `<diagram name="...">`. |
| `MX_INV_10` | **Schematic Direct Taps** | Dây nguồn màu (+12V Red, +5V Orange, +3V3 Blue, GND Black) đi thẳng từ rail vào IC/MCU. Không gắn ô text thừa trên dây nguồn. |
| `MX_INV_11` | **Fractional Port Anchoring** | Nối Hub sang vệ tinh dùng toạ độ vi phân chu vi (`exitY = 0.05..1.0`) khớp $y_{\text{center}}$ đích để tạo đường ngang phẳng 100% (Zero-Zigzag). |
| `MX_INV_12` | **Discrete Highway Corridors** | Tuyến bus song song đi qua các trục tọa độ rời rạc cách $\ge 30$–$50$px. Nhãn dài bọc thẻ HTML chống tràn. |
| `MX_INV_13` | **Schematic Horizontal Strip** | Module chính xếp dải ngang 1 hàng (L-to-R), Rails nguồn trên đỉnh, GND dưới đáy cắm thẳng đứng. GPIO đi qua bus tầng dưới. |
| `MX_INV_14` | **DFD 5-Column Flow** | DFD tuân thủ 5 cột ($C_1$ External $\rightarrow$ $C_2$ Ingestion $\rightarrow$ $C_3$ Processing/Store $\rightarrow$ $C_4$ Comm $\rightarrow$ $C_5$ Cloud). Nhãn dùng `offset` mask trắng. |
| `MX_INV_15` | **Dynamic Edge Label Width** | Cấm `\n`/`<br>` trong label; bắt buộc `labelWidth=<W>;html=1;whiteSpace=wrap;labelBackgroundColor=#FFFFFF;` để Draw.io auto-wrap. |
| `MX_INV_16` | **4-Tier Stroke Hierarchy** | Tier 1 (Khung lớn/Rail: 2.5–3.0px) > Tier 2 (MCU/IC: 1.8–2.0px, `#F8F9FA`) > Tier 3 (Ngoại vi: 1.2px) > Tier 4 (Line dây: 1.0px). |
| `MX_INV_17` | **Dedicated Rail Header Legend** | Sơ đồ Schematic nhiều rail: text tên rail tách thành cột Header riêng ($x < x_{\text{first\_ic}}$), thân rail để `value=""` chống đè chữ. |
| `MX_INV_18` | **MCU Egress Waterfall** | Tuyến bus GPIO từ MCU không đâm xuyên hộp linh kiện phụ; xuất phát từ mép phải (`exitX=1.0`), đi vào hành lang dọc ($\ge 80\text{px}$) rồi đổ waterfall xuống bus. |
| `MX_INV_19` | **4-Sided Data Store Enclosure** | Kho Dữ Liệu (D1, D2) trong DFD bắt buộc có đủ 4 cạnh viền (`top=1;bottom=1;left=1;right=1;` hoặc `shape=rectangle;`) chống mất viền. |
| `MX_INV_20` | **Snug Mask Bounding** | CẤM gán cứng `labelWidth` lớn cho nhãn ngắn. `labelWidth` phải tính động theo độ dài text để mask trắng ôm khít chữ, không che lấp dây lân cận. |
| `MX_INV_21` | **Dynamic Viewport Bounds** | Headless render PNG: viewport $\ge \max(X, Y) + 160\text{px}$, PIL auto-crop 25px uniform padding chống cắt cụt đồ hoạ. |

---

## 3. Danh Mục Công Cụ MCP Diagram Engine (`diagram.*`)

| Tên Công Cụ MCP | Phân Lớp | Mô Tả Chức Năng Chính |
|---|---|---|
| `diagram.parse` | MVP | Bóc tách Mermaid, PlantUML, SQL DDL thành `DiagramSpec` chuẩn hóa, loại bỏ hoàn toàn metadata rác. |
| `diagram.plan_layout` | MVP | Tính toán bố cục tất định (Sugiyama, Force, Radial), phân tầng, chống va chạm, trả về `LayoutPlan`. |
| `diagram.build` | MVP | Biên dịch `DiagramSpec` + `LayoutPlan` thành pure native `mxGraphModel` XML (`.drawio`). |
| `diagram.render_raster`| MVP | Render headless sang ảnh raster PNG chất lượng cao (300 DPI) qua Playwright sidecar hoặc Draw.io CLI. |
| `diagram.render_svg` | MVP | Xuất sơ đồ ra file vector SVG trong suốt, sắc nét cho in ấn. |
| `diagram.inspect_visual`| MVP | Kiểm tra thị giác khép kín: phát hiện va chạm nhãn-dây, cắt cụt chữ, dây đâm xuyên hộp linh kiện. |
| `diagram.repair_layout`| P1 | Tự động căn chỉnh lại hành lang bus, cổng viền và khoảng cách khi phát hiện va chạm hình học. |
| `diagram.diff_layout` | P1 | So sánh sự khác biệt cấu trúc và thị giác giữa 2 phiên bản sơ đồ (`.drawio` trước và sau). |
| `diagram.export_pages` | P1 | Tách và xuất từng trang độc lập từ file `.drawio` chứa nhiều tab trang. |

---

## 4. Quy Trình Vận Hành Chuẩn 5 Bước Cho AI

### Bước 1 — Lập Đặc Tả DiagramSpec JSON
AI chuẩn hóa mô tả bài toán thành cấu trúc `DiagramSpec`:
```json
{
  "title": "Authentication Microservice Architecture",
  "topology": "layered_arch",
  "theme": "academic_monochrome",
  "nodes": [
    { "id": "client", "label": "Client App", "kind": "boundary", "group": "frontend" },
    { "id": "gateway", "label": "API Gateway", "kind": "service", "group": "backend" },
    { "id": "auth_svc", "label": "Auth Service", "kind": "service", "group": "backend" },
    { "id": "redis", "label": "Session Cache", "kind": "datastore", "group": "data" }
  ],
  "edges": [
    { "id": "e1", "source": "client", "target": "gateway", "label": "HTTPS POST /login" },
    { "id": "e2", "source": "gateway", "target": "auth_svc", "label": "gRPC VerifyToken" },
    { "id": "e3", "source": "auth_svc", "target": "redis", "label": "GetSession(Token)" }
  ]
}
```

### Bước 2 — Hoạch Định Bố Cục Tất Định (`diagram.plan_layout`)
Gọi `diagram.plan_layout(spec=diagram_spec)` để nhận `LayoutPlan`:
- Tự động gán tọa độ $(x, y)$, chiều dài/rộng từng node.
- Tự động tính toán đường rẽ nhánh orthogonal cho từng edge, bảo đảm không đè nhau.

### Bước 3 — Biên Dịch XML Native (`diagram.build`)
Gọi `diagram.build(spec=diagram_spec, layout_plan=layout_plan)`:
- Tạo ra file `.drawio` hoàn toàn sạch, tuân thủ `MX_INV_01..05`.
- Nhận về `file_ref_drawio`.

### Bước 4 — Headless Render & Soi Thị Giác
1. Gọi `diagram.render_raster(file_ref=file_ref_drawio, format="png")` $\rightarrow$ Nhận `png_ref`.
2. Gọi `diagram.inspect_visual(file_ref=png_ref)` $\rightarrow$ Nhận báo cáo thị giác:
   - Danh sách vi phạm (nếu có): `collisions`, `pierced_boxes`, `clipped_labels`.

### Bước 5 — Triage Kết Quả & Bàn Giao
- Nếu báo cáo `diagnostics` sạch 100%: Bàn giao cả 2 file `.drawio` và `.png` cho người dùng.
- Nếu có lỗi hình học: Xem Mục 5 để xử lý tự động qua `diagram.repair_layout` hoặc điều chỉnh spec.

---

## 5. Triage & Xử Lý Sự Cố (Troubleshooting & Auto-Repair)

### Bảng Mã Lỗi Diagram Engine (`E-DGM-*`)

| Mã Lỗi | Nhóm Lỗi | Nguyên Nhân Kỹ Thuật | Phương Án Khắc Phục Chuẩn |
|---|---|---|---|
| `E-DGM-SPEC-SCHEMA` | Schema | Cấu trúc `DiagramSpec` thiếu trường bắt buộc hoặc sai kiểu | AI tự sửa JSON Spec theo đường dẫn báo lỗi. |
| `E-DGM-SEC-INJECTION` | Security | Label chứa thẻ script độc hại hoặc injection XML | Loại bỏ mã độc, escape chuỗi XML an toàn. |
| `E-DGM-TOPOLOGY-PORT` | Topology | Cổng viền docking không hợp lệ (ngoài khoảng 0.0–1.0) | Kích hoạt Auto-Repair đưa về cổng viền chuẩn. |
| `E-DGM-XML-USEROBJECT` | XML | Phát hiện thẻ cấm `<UserObject mermaidData>` (`MX_INV_01`) | Chuyển đổi thành `<mxCell>` thuần túy. |
| `E-DGM-XML-CORRUPT` | XML | Cắt cụt thẻ XML hoặc thiếu thẻ đóng `<root>` | Re-serialize qua `xml_serializer.py`. |
| `E-DGM-FONT-METRICS` | Layout | Thiếu font file hệ thống, không tính được text width | Kích hoạt bộ fallback Pillow font metrics. |
| `E-DGM-ROUTING-PIERCE` | Routing | Dây nối đâm xuyên qua hộp linh kiện phụ (`MX_INV_18`) | Nắn tuyến dây vào hành lang Waterfall ($x \ge 80\text{px}$). |
| `E-DGM-RENDER-CRASH` | Render | Tiến trình headless render bị timeout hoặc crash | Khởi động lại Chromium sidecar sandbox. |
| `W-LAYOUT-COLLISION` | Warning | Hai nhãn dây nằm quá gần nhau ($\Delta d < 20\text{px}$) | Giãn khoảng cách trục bus $\ge 30$–$50$px. |

### Nguyên Tắc Chặn Vòng Lặp Vô Tận (Fail-Fast)
- Tối đa **2 lần gọi sửa tự động** (`diagram.repair_layout`).
- Nếu sau 1 lần sửa mà số lượng lỗi không giảm hoặc xuất hiện lỗi mới: **DỪNG LẠI NGAY**, in nguyên nhân và hình ảnh chẩn đoán ra để người dùng quyết định.

---

## 6. Lưu Ý Trong Giai Đoạn Chuyển Tiếp (Transitional Fallback)

Trong thời gian hoàn thiện khung sườn Phase 0 và Phase 3 theo Master Plan v6:
- Nếu môi trường chưa nạp runtime MCP `diagram.*`, Agent có thể sử dụng các script phụ trợ khẩn cấp tại `.agents/skills/mxgraph-diagram-engineering/scripts/`:
  - `build_drawio.py`: Sinh XML thuần cơ bản cho ERD.
  - `validate_drawio.py`: Kiểm định 4 cổng cú pháp.
- Mọi sơ đồ sinh ra bằng script phụ trợ đều phải được đối chiếu thủ công nghiêm ngặt với 21 bất biến `MX_INV_01..21` trước khi bàn giao!
