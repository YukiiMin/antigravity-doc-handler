# Quy tắc bất biến cho file Excel

Các quy tắc dưới đây đã được **code cưỡng chế**; tài liệu này chỉ để bạn hiểu lý do khi gặp lỗi.

1. Không bao giờ ghi đè file nguồn: `tool:set_cells_xlsx` luôn ghi ra bản sao (lỗi `E-IO-OVERWRITE`).
2. Vùng khóa là của người dùng: gặp `E-LOCK-001` thì dừng và hỏi, không tự đổi tham số để lách.
3. Mọi thay đổi Inventory phải được khai báo; `E-DIFF-UNDECLARED` nghĩa là file chưa được phát hành.
4. Số liệu đo hình thức chỉ là ước lượng; đừng cam kết "đúng pixel".
