---
name: agent-context-architecture
description: Kiến trúc chuẩn hóa phân tầng ngữ cảnh (Hierarchical Context + Progressive Disclosure) cho AI Agent: GEMINI.md, Rules, Skills, Specs và Scripts. Dùng khi thiết kế, tái cấu trúc hoặc bảo trì bộ Customization cho Solo Dev cộng tác với AI.
---

# Skill: Agent Context Architecture (AI-Native System)

> **Mục tiêu**: Định hình kiến trúc phân tầng ngữ cảnh chuẩn xác nhất (Hierarchical Context Architecture) cho Antigravity IDE / Cursor / Claude, triệt tiêu 100% tình trạng "Context Bloat" (tràn bộ nhớ) và "Lost in the Middle" (quên chỉ thị giữa chừng).

---

## 1. When to Use
Kích hoạt skill này khi:
- Khởi tạo dự án mới cần thiết lập bộ quy chuẩn làm việc cho AI Agent (`GEMINI.md`, `.agents/rules/`, `.agents/skills/`).
- Tái cấu trúc hoặc tối ưu hóa dự án hiện hữu đang bị phình to context hoặc cảnh báo đỏ (vượt 12,000 ký tự / 20,000 tokens rule budget).
- Phân định một yêu cầu kỹ thuật nên viết vào **GEMINI.md**, **Rule**, **Skill**, hay **Spec**.
- Chuyển đổi các quy trình cũ (Workflows monolithic) sang kiến trúc đóng gói module hóa (Skills).

---

## 2. Mô Hình 5 Tầng Ngữ Cảnh (The 5-Layer Context Model)

Tuyệt đối không coi mọi file markdown đều là "context file". Mỗi thành phần có vai trò và vòng đời kích hoạt độc lập:

| Thành Phần | Định Nghĩa Bản Chất | Cơ Chế Kích Hoạt | Vai Trò & Ngân Sách |
|---|---|---|---|
| **GEMINI.md / AGENTS.md** | Context nền tảng theo thư mục (Walk-up Scoping) | **Always On** (trong scope) | Bản đồ dự án, danh mục module, bất biến tối thượng. **Root $\le 100$ dòng**, **Module $\le 40$ dòng**. Không dùng frontmatter. |
| **.agents/rules/*.md** | Rào chắn, coding standards, ràng buộc kiến trúc | **glob**, **model_decision**, **always_on**, **manual** | Quy định "Phải làm / Không được làm". Ngân sách tối đa 20,000 tokens active rules; tối đa 12,000 ký tự/file. |
| **.agents/skills/** | Năng lực chuyên môn, quy trình đa bước | **Progressive Disclosure** (Khám phá qua name + description) | Đóng gói trọn vẹn: `SKILL.md` (hướng dẫn) + `references/` (kiến thức sâu) + `scripts/` (công cụ thực thi). |
| **SPEC / DOCS** | Nguồn chân lý kỹ thuật (Source of Truth) | **On-Demand / Reference** | Đặc tả kiến trúc, hợp đồng dữ liệu, bảng ánh xạ. Chỉ đọc khi Agent/Skill yêu cầu tường minh. |
| **SCRIPTS** | Công cụ xác định, thuật toán tính toán nặng | **Execution as Black Box** | Để máy tính thực thi các việc phức tạp (đo pixel, tính layout, format diff), không bắt Agent đoán mò. |

---

## 3. Decision Tree: Phân Loại Thông Tin Vào Đâu?

Khi bạn muốn đưa một thông tin/quy tắc vào dự án, đối chiếu cây quyết định:

```
                            [Tôi muốn đưa thông tin này vào hệ thống]
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
     [Ràng Buộc Bắt Buộc / Invariant]                              [Năng Lực / Hướng Dẫn Tác Vụ]
                 │                                                             │
     ┌───────────┴───────────┐                                                 ▼
     ▼                       ▼                                        [Tạo Thư Mục Skill Mới]
[Toàn cục / Dự án]     [Theo Module Cụ Thể]                        .agents/skills/<name>/SKILL.md
     │                       │                                                 │
     ▼                       ▼                                   ┌─────────────┴─────────────┐
[GEMINI.md (Root)]     [Chọn Cơ Chế Rule]                        ▼                           ▼
(Ngắn gọn ≤ 100 dòng)        │                            [Quy Trình Chính]          [Tài Liệu Chi Tiết]
                             ├─ Chạm file cụ thể? ──► trigger: glob                 references/<topic>.md
                             ├─ Tùy ngữ cảnh task? ──► trigger: model_decision
                             └─ Chỉ khi user gọi?  ──► trigger: manual
```

---

## 4. Bảng Quy Chuẩn Trình Bày Frontmatter Cho Rules

Trong Antigravity IDE, frontmatter của Rules bắt buộc theo đúng cấu trúc:

```yaml
# 1. Kích hoạt theo đường dẫn file (Tất định 100%):
---
trigger: glob
globs: doctools/**/docx/**, tests/test_docx/**, **/*.docx
---

# 2. Kích hoạt theo đánh giá ngữ nghĩa của AI Model (Kèm mô tả):
---
trigger: model_decision
description: Quy chuẩn kiểm toán chất lượng và chẩn đoán lỗi tài liệu văn phòng
---

# 3. Kích hoạt luôn luôn (Thận trọng, tốn context):
---
trigger: always_on
---

# 4. Kích hoạt thủ công khi user gõ @ten-rule:
---
trigger: manual
---
```

---

## 5. Danh Mục References Chuyên Sâu Đi Kèm

- [references/5_layer_context_model.md](references/5_layer_context_model.md): Phân tích chi tiết 5 tầng ngữ cảnh và cơ chế Walk-up Scoping.
- [references/activation_modes_and_triggers.md](references/activation_modes_and_triggers.md): So sánh chi tiết 4 chế độ kích hoạt Rule và kỹ thuật viết `globs` không bị rỗng.
- [references/progressive_disclosure_and_budgets.md](references/progressive_disclosure_and_budgets.md): Quản lý ngân sách 20,000 token active rules và kỹ thuật lazy-load kiến thức.
- [references/templates_and_boilerplates.md](references/templates_and_boilerplates.md): Bộ template mẫu sẵn dùng (Root GEMINI, Module GEMINI, Glob Rule, Model-decision Rule, SKILL package).
