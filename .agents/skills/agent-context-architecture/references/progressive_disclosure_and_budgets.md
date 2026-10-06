# Reference: Progressive Disclosure, Budgets & Workflow Deprecation

> **Module**: `agent-context-architecture`
> **Mục tiêu**: Hướng dẫn quản trị ngân sách ngữ cảnh (Token Budgeting), áp dụng mô hình Progressive Disclosure để tải kiến thức theo yêu cầu, và lộ trình thay thế hoàn toàn Workflows cũ bằng Skills.

---

## 1. Ngân Sách Ngữ Cảnh & Các Giới Hạn Cứng (Hard Limits)

Khi xây dựng hệ thống rules và customizations cho AI, có 3 giới hạn vật lý bắt buộc ghi nhớ:

| Chỉ Số Giới Hạn | Giá Trị Ngưỡng | Hậu Quả Khi Vượt Quá |
|---|---|---|
| **Active Rules Budget** | **20,000 tokens** | Khi tổng các rule đang kích hoạt vượt ngưỡng, hệ thống sẽ cảnh báo đỏ hoặc cắt bớt context, dẫn đến AI vi phạm quy chuẩn. |
| **Kích thước 1 file Rule** | **12,000 ký tự** (~2,500 từ) | IDE hiển thị thanh đếm `XXXX/12000` màu đỏ. AI dễ bị quá tải thông tin cục bộ. |
| **Kích thước file GEMINI.md** | **$\le 100$ dòng** (Root) / **$\le 40$ dòng** (Sub) | GEMINI.md luôn nằm trong prompt khởi động; nếu dài, nó sẽ làm loãng lệnh của user ngay từ turn 1. |

---

## 2. Mô Hình Phơi Bày Tiến Bộ (Progressive Disclosure)

Để cung cấp lượng kiến thức chuyên môn đồ sộ (hàng trăm trang tài liệu chuẩn) cho AI mà không làm tràn ngân sách 20,000 tokens, ta áp dụng mô hình **Progressive Disclosure**:

```
[Level 0: Skill Metadata - Tốn ~50 tokens]
  AI quét qua danh mục: name + description của tất cả skills
            │
            ▼ (Khi phát hiện bài toán phù hợp)
[Level 1: SKILL.md - Tốn ~500–1,000 tokens]
  AI đọc quy trình cốt lõi, bảng tóm tắt, checklist hành động
            │
            ▼ (Khi cần tra cứu kỹ thuật chuyên sâu)
[Level 2: references/<topic>.md - Tốn ~500 tokens mỗi file]
  AI chỉ đọc đúng file tài liệu liên quan đến lỗi/chủ đề hiện tại
            │
            ▼ (Khi cần xử lý tính toán)
[Level 3: scripts/ - Tốn 0 token ngữ cảnh]
  AI gọi lệnh chạy script độc lập qua terminal hoặc MCP tool
```

### 2.1. Lợi ích so với cấu trúc cũ
- Không bao giờ nạp toàn bộ tài liệu cùng lúc.
- AI đọc hiểu có mục tiêu rõ ràng (`view_file` có định hướng).
- Giảm thiểu 80% chi phí token và độ trễ phản hồi (latency).

---

## 3. Lộ Trình Khai Tử Workflows Cũ (Workflows Deprecation)

### 3.1. Thông báo chính thức từ Google Antigravity
> **Official Notice**: Hệ thống **Workflows** (`.agents/workflows/` và file `WORKFLOW.md`) chính thức bị **deprecated** và sẽ bị ngừng hỗ trợ hoàn toàn vào ngày **01/11/2026**. Tất cả các quy trình đa bước phải được chuyển đổi thành **Skills** có cấu trúc phân tầng.

### 3.2. Vì sao Workflows bị khai tử?
1. **Tính nguyên khối (Monolithic)**: Workflows cũ thường gom tất cả các bước vào một file dài hàng trăm dòng, vi phạm ngân sách context.
2. **Thiếu khả năng tự khám phá (Lack of Discovery)**: AI không thể đánh giá ngữ nghĩa khi nào nên kích hoạt từng phần của workflow.
3. **Không hỗ trợ công cụ thực thi đính kèm**: Workflows chỉ là văn bản hướng dẫn thụ động, không có thư mục `scripts/` hay `references/` độc lập.

### 3.3. Bảng ánh xạ chuyển đổi (Migration Matrix)

| Trước đây (Workflows cũ - Xóa bỏ) | Hiện tại & Tương lai (Skills chuẩn hóa) |
|---|---|
| `.agents/workflows/workflow_docx.md` | `.agents/skills/docx-handler/SKILL.md` + `references/` |
| `.agents/workflows/workflow_xlsx.md` | `.agents/skills/excel-handler/SKILL.md` + `references/` |
| `.agents/workflows/workflow_diagram.md` | `.agents/skills/mxgraph-diagram-engineering/SKILL.md` |
| `.agents/workflows/WORKFLOW.md` (Gốc) | `.agents/skills/doctools-delivery/SKILL.md` + `references/` |

---

## 4. Công Thức Tính Toán Sức Khỏe Ngữ Cảnh (Context Health Score)

Trước khi đóng một giai đoạn (Phase) hoặc bàn giao hệ thống, kiểm tra công thức:

$$\text{Health Score} = \frac{\text{Tokens của Always-On Rules} + \text{Tokens của GEMINI.md}}{\text{Ngân Sách 20,000 Tokens}} \times 100\%$$

- **Xuất sắc**: $< 15\%$ (Ngữ cảnh nền tảng dưới 3,000 tokens, chừa $85\%$ cho suy luận và tác vụ).
- **Cảnh báo**: $15\% - 30\%$. Cần chuyển bớt rule từ `always_on` sang `glob` hoặc `model_decision`.
- **Nguy hiểm**: $> 30\%$. Cần tái cấu trúc ngay lập tức theo mô hình Progressive Disclosure.
