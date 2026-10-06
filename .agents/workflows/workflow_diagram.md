# Workflow: Module DIAGRAM (Diagram & Visual Architecture Engine)

> **Mô-đun**: DIAGRAM Engine (`diagram.*`)  
> **Căn cứ**: Diagram Foundation Plan v1.0, [rule_diagram_engine_standards.md](../rules/rule_diagram_engine_standards.md), 21 bất biến `MX_INV_01..21`.  
> **Phạm vi**: 5 quy trình tác nghiệp chuẩn: Dựng sơ đồ từ JSON Spec, chuyển đổi từ cú pháp text DSL, vòng lặp kiểm định thị giác tự sửa, đóng gói đa trang, và đối chiếu khác biệt.

---

## 1. Danh Mục Workflows Cho Module DIAGRAM

```
                                 [Tác Vụ DIAGRAM]
                                        │
      ┌──────────────────┬──────────────┴──────────────┬──────────────────┐
      ▼                  ▼                             ▼                  ▼
[WF-DIAG-01: Spec Path] [WF-DIAG-02: Text DSL]       [WF-DIAG-03: QA Loop] [WF-DIAG-04/05]
plan_layout & build    parse Mermaid/PlantUML/DDL    inspect & auto-repair multi-page & diff
```

---

## 2. Chi Tiết Từng Quy Trình Tác Nghiệp

### WF-DIAG-01: Dựng Sơ Đồ Kiến Trúc & ERD Từ Đặc Tả (Path B: Spec-Driven Generation)
Quy trình chuẩn mực để AI tạo sơ đồ khối kỹ thuật, ERD, DFD, hoặc kiến trúc hệ thống đạt chuẩn xuất bản.

1. **Lập DiagramSpec JSON thuần**: Khai báo `topology`, `theme`, `nodes` (id, label, kind, fields[] cho ERD), `edges` (id, source, target, relationship, label).
2. **Hoạch định Bố cục Tất định**: Gọi `diagram.plan_layout(diagram_spec)` nhận `LayoutPlan` (tọa độ $x, y$, kích thước, waypoints cho edge). Cấm AI tự đoán tọa độ pixel bằng tay.
3. **Biên dịch XML Native**: Gọi `diagram.build(diagram_spec, layout_plan)` sinh file `.drawio` pure native mxGraphModel XML (`MX_INV_01..05`, `16`, `20`).
4. **Headless Render**: Gọi `diagram.render_raster(file_ref, format="png")` qua Playwright sidecar / Draw.io CLI, áp dụng `MX_INV_21` (viewport $\ge \max + 160\text{px}$, PIL auto-crop 25px uniform padding).
5. **Kiểm tra Thị giác**: Gọi `diagram.inspect_visual(png_ref)`. Nếu sạch 100% $\rightarrow$ bàn giao; nếu có lỗi $\rightarrow$ chuyển sang WF-DIAG-03.

---

### WF-DIAG-02: Chuyển Đổi Từ Cú Pháp Văn Bản (Path A: Text DSL Ingestion)
Quy trình tiếp nhận sơ đồ từ cú pháp phổ biến (Mermaid, PlantUML, SQL DDL) sang Draw.io native chất lượng cao.

1. **Bóc tách cú pháp**: Gọi `diagram.parse(text_content, format="mermaid"|"plantuml"|"ddl")` trích xuất `DiagramSpec` chuẩn hóa, loại bỏ hoàn toàn metadata rác (`MX_INV_01`).
2. **Kế thừa luồng dựng**: Tiếp tục chạy theo Bước 2..5 của WF-DIAG-01 (`plan_layout` $\rightarrow$ `build` $\rightarrow$ `render` $\rightarrow$ `inspect`).

---

### WF-DIAG-03: Kiểm Định Cổng & Chẩn Đoán Thị Giác Khép Kín (Visual QA & Auto-Repair Loop)
Quy trình đảm bảo sơ đồ không bị lỗi kỹ thuật hình thức, chống từ chối Apply và chống méo mó.

1. **Kiểm định Cú pháp & Cấu trúc**: Chạy bộ cổng `DG-00..08` (XML hợp lệ, ID duy nhất, không va chạm AABB qua R-tree, docking vỏ bảng `MX_INV_03`, nhãn snug mask `MX_INV_20`).
2. **Phân tích Thị giác Khép kín**: Gọi `diagram.inspect_visual(png_ref)` quét bounding boxes: phát hiện va chạm nhãn-dây (Collision Detection), phát hiện dây đâm xuyên hộp linh kiện (`MX_INV_18`).
3. **Xử lý & Tự Sửa Bố cục**:
   - Không có lỗi: Bàn giao file `.drawio` và `.png`.
   - Có lỗi hình học: Gọi `diagram.repair_layout(file_ref, diagnostics)` để engine tự căn chỉnh lại khoảng cách bus ($\ge 30$–$50$px) và nắn lại cổng viền. Re-render và inspect lần 2.
   - Nguyên tắc Fail-Fast: Tối đa 2 lần thử sửa tự động; nếu không đạt $\rightarrow$ Dừng và báo cáo bằng chứng cho người dùng.

---

### WF-DIAG-04: Đóng Gói Đa Trang Độc Lập (Multi-Page Packaging & Export)
Quy trình đóng gói bộ tài liệu kiến trúc nhiều góc nhìn (Context, Container, Component, Data Model) vào một file duy nhất.

1. **Soạn thảo Bộ DiagramSpec**: Mỗi góc nhìn kiến trúc tương ứng với một trang `<diagram name="...">` (`MX_INV_09`).
2. **Build Multi-Page**: Gọi `diagram.build` với danh sách specs để nhúng chung vào một container XML duy nhất.
3. **Xuất bản Đa định dạng**: Gọi `diagram.export_pages(file_ref, format="png"|"svg"|"pdf")` để xuất đồng thời file tổng `.drawio` và ảnh từng trang độ nét cao.

---

### WF-DIAG-05: So Sánh Khác Biệt Sơ Đồ (Visual & Structural Diff)
Dành cho CI/CD hoặc quy trình Review Kiến trúc khi cập nhật phiên bản sơ đồ.

1. **Structural Diff**: Gọi `diagram.diff_layout(file_ref_before, file_ref_after)` đối chiếu danh sách node/edge thêm mới, xóa bỏ, sửa đổi thuộc tính và waypoints.
2. **Visual Diff**: So sánh ảnh raster trước và sau, đánh dấu vùng biến đổi (Bounding Box Highlight) để kỹ sư nhận biết trực quan thay đổi kiến trúc.
