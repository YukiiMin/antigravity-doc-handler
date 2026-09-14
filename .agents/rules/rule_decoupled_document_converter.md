---
description: Decoupled Document Architecture & PDF to DOCX 100% Fidelity Standard
---

# Quy chuẩn Chuyển đổi Tài liệu (Decoupled Document Architecture Standards)

## 1. Nguyên tắc cốt lõi: PDF → DOCX đạt chuẩn 100% trước tiên
- Chuyển đổi từ DOCX sang Markdown rất dễ dàng khi cấu trúc DOCX đã chuẩn.
- **Tiên quyết**: Quá trình chuyển đổi từ **PDF sang DOCX** phải đạt độ chính xác 100% về cả dữ liệu (không mất bullet, không mất cell/nội dung bảng) lẫn định dạng (màu heading `#C00000`, màu nền header bảng `#FFE8E0`, lề trang, dot leader tab stop).
- Tuyệt đối không nhảy cóc qua Markdown khi file DOCX nền móng chưa đạt chuẩn đối chiếu với PDF gốc.

## 2. Kiến trúc phân tách 2 tầng (Decoupled Data vs Presentation Layer)
Tương tự mô hình **HTML + CSS**:
1. **Data Layer (`[name].md`)**:
   - Chứa cấu trúc ngữ nghĩa và dữ liệu thuần túy (Headings `#`, Lists `- `, Tables GFM `| Col 1 | Col 2 |`, Text paragraphs, Media `![alt](path)`).
   - Tuyệt đối sạch sẽ, không chứa YAML Frontmatter hay thẻ `<style>` làm bẩn dữ liệu.
2. **Style Layer (`[name].style.yaml`)**:
   - Đóng vai trò như file stylesheet (CSS), lưu trữ:
     - `geometry`: lề trang (`top`, `bottom`, `left`, `right`), khổ giấy (`page_size`).
     - `typography`: kiểu font (`font_family`), cỡ chữ (`font_size`), màu chữ, khoảng cách dòng.
     - `headings`: màu sắc (`#C00000`), kích thước H1-H4.
     - `tables`: màu nền tiêu đề bảng (`header_background: '#FFE8E0'`), viền bảng (`border_color`), đệm ô.
     - `lists`: ký hiệu bullet, khoảng cách đoạn trước/sau.

## 3. Quy chuẩn bộ biên dịch 3 tầng (Bidirectional Compiler)
- **Tầng 1 (PDF -> DOCX v6)**: Sử dụng `smart_post_processor.py` trên nền OpenXML:
  - Đổ màu Peach `#FFE8E0` (`<w:shd>`) cho hàng 0 của 100% bảng.
  - Tách triệt để các đoạn văn bản gộp đa dòng (`\n`), bảo toàn đủ số lượng bullet items (`w:numPr`).
  - Chuẩn hóa toàn bộ dòng TOC thành Tab Stop căn phải có dot leader native.
- **Tầng 2 (Bóc tách)**:
  - Lệnh chuyển sang MD tự động sinh cặp file song song `[name].md` và `[name].style.yaml`.
- **Tầng 3 (Biên dịch tái tạo)**:
  - Tự động nạp file `[name].style.yaml` cùng tên (hoặc qua cờ `--style`) để tái tạo DOCX/PDF chuẩn xác 100% như tài liệu gốc.

## 4. Quy chuẩn Bảng biểu OpenXML (Word Table Invariants)
Bất kỳ bảng nào được tạo mới, chuyển đổi hoặc cập nhật trong tài liệu Word (`.docx`) đều phải tuân thủ nghiêm ngặt 4 quy tắc sau:
1. **Chống vỡ hàng qua trang (`<w:cantSplit/>`)**:
   - 100% các hàng (`trPr`) trong bảng phải có thẻ `<w:cantSplit/>`.
   - Tuyệt đối không để xảy ra hiện tượng 1 hàng bị cắt đôi giữa 2 trang văn bản. Nếu hàng không vừa ở cuối trang, toàn bộ hàng phải được chuyển sang đầu trang mới.
2. **Lặp lại hàng tiêu đề qua trang (`<w:tblHeader/>`)**:
   - Hàng 0 (`trPr`) của mọi bảng phải có thẻ `<w:tblHeader/>`.
   - Khi bảng kéo dài qua nhiều trang, tiêu đề cột phải tự động lặp lại ở đầu trang tiếp theo.
3. **Canh giữa toàn bộ text trong các ô theo chiều dọc (`<w:vAlign w:val="center"/>`)**:
   - 100% các ô (`tcPr`) phải có `<w:vAlign w:val="center"/>` và `cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER`.
   - Chữ ngắn (như tên Feature, trạng thái, ID) không bao giờ được dính sát mép trên mà phải nằm cân đối chính giữa ô theo chiều dọc.
4. **Quy chuẩn canh lề ngang (Horizontal Alignment)**:
   - Cột STT / Index (`#`): Canh giữa (`WD_ALIGN_PARAGRAPH.CENTER`).
   - Cột nội dung / mô tả / tên màn hình: Canh trái (`WD_ALIGN_PARAGRAPH.LEFT`).

## 5. Quy chuẩn Thiết kế Sơ đồ Kỹ thuật (Technical Diagram Standards)
1. **Kiến trúc Hub & Spoke & Tỷ lệ vàng (1.6:1 đến 1.85:1)**:
   - Hub trung tâm điều hướng tự nhiên sang 4 góc (Top Discovery, Right Cart/Maps, Bottom-Left Auth, Bottom-Right Account).
   - Tỷ lệ khung hình $1.6:1 - 1.85:1$ vừa vặn trang giấy A4 Word, font chữ to rõ không cần zoom.
2. **Định tuyến trực giao Manhattan (Orthogonal Manhattan Routing)**:
   - Đường nối vuông góc 90 độ gập chữ L, chữ Z.
   - Cổng vào/ra xác định rõ ràng trên chu vi (`top`, `bottom`, `left`, `right`).
3. **Bảo vệ đường viền bằng SVG Text Halo**:
   - Áp dụng `paint-order="stroke fill"` với viền trắng `stroke="#ffffff" stroke-width="4px"` cho nhãn chữ thay vì dùng badge chữ nhật, chống đè che viền hộp lân cận.
4. **Độ phân giải chuẩn in ấn (`scale: 3`)**:
   - Kết xuất tối thiểu 300+ DPI (scale factor 3x) qua Chromium/Edge headless để tài liệu in ấn sắc nét tuyệt đối.
