# Reference: Micro-Commit Cadence & Git Workflow Protocol

## 1. Nguyên Tắc Cốt Lõi
- **Tất định & Nhỏ gọn**: Mỗi commit giải quyết trọn vẹn một tiểu bước `X.Y.Z`. Không gộp nhiều sub-step vào một commit lớn.
- **Fail-Closed**: Không bao giờ commit khi có test thất bại hoặc linter báo lỗi.
- **Quyền Phê Duyệt Tuyệt Đối**: Agent không bao giờ tự ý chạy `git commit` hay `git push` nếu không có câu xác nhận rõ ràng từ User.

## 2. Quy Ước Mã Hóa Nhánh & Commit
- **Nhánh phát triển**:
  - `feat/phase-1-docx`: Cho toàn bộ Phase 1.
  - `feat/phase-2-xlsx`: Cho toàn bộ Phase 2.
  - `feat/phase-3-diagram`: Cho toàn bộ Phase 3.
  - `chore/agent-context-architecture`: Cho các tác vụ tinh gọn hạ tầng agent.
- **Cấu trúc Commit Message**:
  ```
  <type>(<scope>): <mô tả súc tích> [<Mã Gate / Spec Ref>]
  ```
  Ví dụ:
  - `feat(docx): implement SchemaHelper, TagOrderRegistry, and PackageIO [DOCX-D-06, ERR_DOCX_001]`
  - `feat(docx): implement TemplateLinter and JinjaNormalizer [DOCX-FR-01, FR-02, D-09]`
  - `chore(agent): optimize context rules to glob triggers and add delivery skill`

## 3. Quy Trình Bàn Giao Từng Bước
1. Hoàn tất mã nguồn của `X.Y.Z` (< 300 dòng/file).
2. Viết unit tests kiểm chứng hành vi.
3. Chạy lệnh kiểm thử toàn diện: `python -m unittest discover -s tests`.
4. Cập nhật `.agent_scratchpad.md` ghi nhận hoàn thành.
5. In báo cáo tóm tắt và đề xuất cú pháp `git commit` cho User.
6. Khi User duyệt, thực thi commit và push lên remote repo con `antigravity-doc-handler`.
