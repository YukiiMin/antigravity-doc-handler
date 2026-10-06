# Reference: Activation Modes, Triggers & Frontmatter Parsing

> **Module**: `agent-context-architecture`
> **Mục tiêu**: Chuẩn hóa 4 chế độ kích hoạt Rule trong Antigravity IDE, giải mã cơ chế parser nội bộ của extension và phòng tránh lỗi giao diện GUI rỗng mẫu Glob (`0/250`).

---

## 1. Bốn Chế Độ Kích Hoạt Của Rule

Trong Antigravity IDE, mỗi file rule tại `.agents/rules/*.md` có thể được cấu hình với 1 trong 4 chế độ:

| Activation Mode | Thuộc tính `trigger:` | Trường đi kèm bắt buộc | Khi nào nên dùng? | Chi phí Token |
|---|---|---|---|---|
| **Glob** | `glob` | `globs: <pattern>` | Khi rule chỉ áp dụng cho nhóm file/thư mục cụ thể (vd: `*.docx`, `doctools/core/**`) | Tối ưu nhất (Chỉ tốn token khi chạm đúng file) |
| **Model Decision** | `model_decision` | `description: <text>` | Khi rule phụ thuộc ngữ cảnh bài toán (vd: QA, Refactoring, Git, Auth) | Rất tốt (Model tự cân nhắc nạp dựa trên description) |
| **Always-On** | `always_on` | *(không có)* | Bất biến tối quan trọng không thể bỏ qua ở bất kỳ bước nào | Đắt nhất (Chiếm dung lượng trong mọi prompt) |
| **Manual** | `manual` | *(không có)* | Chỉ nạp khi người dùng gõ tường minh `@rule_name` vào khung chat | Không tốn token tự động |

---

## 2. Giải Mã Cơ Chế Parser Nội Bộ Của Antigravity IDE

Trình soạn thảo quy tắc tùy biến trong extension Antigravity (module `extension.js`) không sử dụng một thư viện YAML đầy đủ mà duyệt theo từng dòng ký tự:

```javascript
// Trích xuất logic phân tích cú pháp từ extension.js
const lines = rawText.split('\n');
let trigger = 'always_on';
let globParam = '';
let modelDecisionParam = '';

for (const line of lines) {
  if (line.startsWith('trigger:')) {
    trigger = line.replace('trigger:', '').trim();
  } else if (line.startsWith('globs:')) {
    globParam = line.replace('globs:', '').trim();
  } else if (line.startsWith('description:')) {
    modelDecisionParam = line.replace('description:', '').trim();
  }
}
```

### 2.1. Phân tích nguyên nhân lỗi "Glob Pattern 0/250"
Khi người dùng hoặc Agent tạo file markdown có frontmatter:
```yaml
---
trigger: glob
---
```
Do thiếu dòng `globs: ...`, parser của IDE gán `globParam = ''`. Khi hiển thị lên giao diện Webview Custom Editor:
- Dropdown **Activation Mode** hiển thị là `Glob`.
- Ô nhập liệu **Glob Pattern** hiển thị rỗng: `Enter glob pattern... 0/250`.
- **Hậu quả**: Rule này **không bao giờ được kích hoạt** vì không có pattern nào khớp!

---

## 3. Cú Pháp Chuẩn Xác Cho Từng Chế Độ

### 3.1. Cấu hình Chế độ Glob (Chính xác 100%)
```yaml
---
trigger: glob
globs: doctools/**/docx/**, tests/test_docx/**, **/*.docx
---
```
> **Lưu ý**: Các pattern phân cách bằng dấu phẩy `,`. Sử dụng `**` để đệ quy thư mục con.

### 3.2. Cấu hình Chế độ Model Decision (Kèm mô tả súc tích)
```yaml
---
trigger: model_decision
description: Quy chuẩn kiểm toán chất lượng, bảo toàn DrawingML và sửa chữa tài liệu văn phòng
---
```
> **Lưu ý**: Dòng `description` phải nêu rõ **từ khóa kích hoạt** và **miền nghiệp vụ** để AI Agent có thể đánh giá chính xác khi nào nên tải rule vào ngữ cảnh.

### 3.3. Cấu hình Chế độ Always-On
```yaml
---
trigger: always_on
---
```
> **Khuyến nghị**: Chỉ sử dụng `always_on` cho các quy tắc phục hồi ngữ cảnh (`rule_context_recovery_protocol.md`) hoặc các bất biến an toàn dữ liệu khẩn cấp. Không dùng quá 2 file `always_on` trong một repo.

### 3.4. Cấu hình Chế độ Manual
```yaml
---
trigger: manual
---
```

---

## 4. Bảng Kiểm Tra Nhanh Trước Khi Hoàn Tất Rule (Checklist)

- [ ] File có chứa thẻ mở đầu `---` và kết thúc `---` cho frontmatter.
- [ ] Nếu `trigger: glob` $\rightarrow$ Đã có dòng `globs:` với pattern hợp lệ, không để trống.
- [ ] Nếu `trigger: model_decision` $\rightarrow$ Đã có dòng `description:` nêu rõ mục tiêu và miền tác vụ.
- [ ] Độ dài toàn bộ file rule không vượt quá 12,000 ký tự (giới hạn cảnh báo của IDE).
- [ ] Mở file trên Antigravity IDE UI kiểm tra: Ô input không hiển thị `0/250` khi chọn Glob.
