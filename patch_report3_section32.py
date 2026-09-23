import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

sys.stdout.reconfigure(encoding='utf-8')

DOC_PATH = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\src\Report3_Software Requirement Specification.docx'
SCREENSHOT_DIR = r'e:\Do_an_SU26\SuperMarketBot-Android-Robot\screenShot'
MEDIA_DIR = r'e:\Do_an_SU26\antigravity-doc-handler\extracted_docx_media'

def create_full_sec32_data():
    """Build the comprehensive, professional Vietnamese technical content for Section 3.2."""
    return [
        {
            "id": "3.2.1",
            "title": "3.2.1 Khởi động Hệ thống & Trạng thái Kiosk Chờ (System Startup & Idle Kiosk Mode)",
            "images": [("01_Welcome_Kiosk_Idle.jpg", 2.8)],
            "caption": "Hình 3.2.1: Màn hình chào mừng và chế độ Kiosk chờ của Robot (Welcome Screen)",
            "triggers": [
                ("Khởi động hệ thống tự động:", "Hệ thống tự động kích hoạt ngay khi robot được bật nguồn hoặc ứng dụng Android Robot Kiosk khởi chạy. Sau chuỗi tự chẩn đoán phần cứng (diagnostics) trong 3 giây, ứng dụng chuyển mượt mà vào Màn hình Chào mừng (Welcome Screen)."),
                ("Chế độ chờ tiết kiệm năng lượng:", "Khi không có người dùng tương tác trong vòng 60 giây, robot tự động chuyển sang chế độ Standby tiết kiệm năng lượng và sẵn sàng nhận lệnh điều phối tuần tra/quảng cáo từ hệ thống trung tâm."),
                ("Tương tác chạm của người dùng:", "Khách hàng chạm vào bất kỳ điểm nào trên màn hình chào mừng hoặc nhấn trực tiếp nút \"Khuyến mãi hôm nay\" để bắt đầu phiên mua sắm.")
            ],
            "timing": [
                ("Khởi chạy ứng dụng:", "Thực thi một lần duy nhất khi tiến trình ứng dụng khởi động."),
                ("Duy trì trạng thái chờ:", "Hoạt động liên tục 24/7 tại trạm đỗ Kiosk hoặc giữa các phiên phục vụ khách hàng.")
            ],
            "description": [
                ("Tác nhân / Vai trò:", "Khách hàng mua sắm tại siêu thị, Kỹ thuật viên / Quản trị viên vận hành robot."),
                ("Hệ thống liên quan:", "Ứng dụng Android Robot Kiosk (React Native / Expo SDK 57), Bộ máy phát giọng nói (RobotVoiceService), Dịch vụ quản lý phiên khách hàng (CustomerSessionContext)."),
                ("Mục đích:", "Mang lại lời chào đón công nghệ cao, hiển thị thời gian số chuẩn xác và cung cấp các lối tắt nhanh bắt đầu hành trình mua sắm thông minh."),
                ("Giao diện tương tác:", "Đồng hồ số thời gian thực hiển thị ngày tháng tiếng Việt (Thứ Năm, 17/09/2026); avatar robot 2D với hiệu ứng sóng radar tỏa sáng; nhãn định danh \"TRỢ LÝ SIÊU THỊ THÔNG MINH\"; nút kêu gọi hành động lớn \"[ CHẠM ĐỂ BẮT ĐẦU ]\"; nút khuyến mãi nổi bật \"Khuyến mãi hôm nay\" với biểu tượng hộp quà.")
            ],
            "normal_flow": [
                "1. Ứng dụng khởi động, hiển thị logo robot cùng hiệu ứng xoay nạp dữ liệu và các dòng trạng thái: 'Đang khởi động hệ thống robot...', 'Đang kiểm tra Camera AI & Cảm biến...', 'Đang kích hoạt cổng nhận diện giọng nói...'.",
                "2. Sau 3 giây tự chẩn đoán, Màn hình Chào mừng xuất hiện với hiệu ứng mờ dần (fade-in). Trợ lý Robot phát lời chào qua hệ thống loa: \"Chào mừng quý khách đến với Smart Market Bot! Tôi có thể giúp gì cho bạn?\".",
                "3. Khách hàng quan sát đồng hồ số thời gian thực và vùng chạm tương tác ở trung tâm màn hình.",
                "4. Khách hàng chạm vào màn hình -> Hệ thống phát âm thanh phản hồi xác nhận \"Tuyệt vời! Chúng ta bắt đầu thôi.\" và chuyển ngay sang Màn hình Chọn Vai Trò (RoleSelectionScreen).",
                "5. Nếu khách hàng nhấn trực tiếp nút \"Khuyến mãi hôm nay\", hệ thống điều hướng thẳng đến Màn hình Siêu Khuyến Mãi (GuestCampaignScreen)."
            ],
            "abnormal_cases": [
                ("Mất kết nối mạng hoặc SignalR Hub:", "Hệ thống hiển thị biểu tượng cảnh báo mạng ngoại tuyến màu đỏ ở thanh trạng thái phía trên, trong khi giao diện Kiosk cục bộ và các nút điều hướng cơ bản vẫn hoạt động bình thường; hệ thống tự động thử kết nối lại sau mỗi 5 giây."),
                ("Quá thời gian chờ (Idle Timeout):", "Nếu khách hàng chạm vào màn hình nhưng không thực hiện thêm thao tác nào trong 60 giây, hệ thống hiển thị hộp thoại đếm ngược 10 giây rồi tự động quay về Màn hình Chào mừng để bảo vệ tính toàn vẹn của phiên.")
            ],
            "data_processing": [
                ("Quản lý phiên và viễn thám thiết bị:", "Khởi tạo mã phiên CustomerSessionId theo định dạng session-{ROBOT_ID}-{timestamp}; theo dõi mức pin và nhiệt độ thiết bị qua BatteryService, truyền gói tin nhịp tim (heartbeat) định kỳ 10 giây/lần tới endpoint REST API /api/v1/robot-operations/devices/{ROBOT_CODE}/heartbeat.")
            ],
            "business_rules": [
                ("BR-ROBOT-01:", "Luôn duy trì cờ giữ sáng màn hình (useKeepAwake) để ngăn tablet tự tắt màn hình trong suốt thời gian Kiosk hoạt động."),
                ("BR-ROBOT-02:", "Âm lượng phát âm giọng nói chào mừng của robot tự động điều chỉnh theo khung giờ hoạt động của siêu thị (mặc định 80% ban ngày, 60% sau 21h00 tối).")
            ]
        },
        {
            "id": "3.2.2",
            "title": "3.2.2 Chọn Vai trò Người dùng & Xác thực Face ID (User Onboarding & Face ID Authentication)",
            "images": [("03_Role_Selection.jpg", 2.5), ("08_Face_Scan_Success.jpg", 2.5)],
            "caption": "Hình 3.2.2: Màn hình lựa chọn vai trò mua sắm (trái) và Nhận diện khuôn mặt Face ID thành công (phải)",
            "triggers": [
                ("Kích hoạt chọn vai trò & Đăng nhập:", "Từ Màn hình Chào mừng, khách hàng chạm màn hình để chuyển sang RoleSelectionScreen. Khách nhấn \"QUÉT FACE ID ĐĂNG NHẬP\" để kích hoạt nhận diện khuôn mặt, hoặc nhấn \"BẮT ĐẦU NGAY\" tại thẻ Khách vãng lai để mua sắm tự do."),
                ("Quét lại khuôn mặt:", "Nhấn nút \"Quét lại Face ID\" trên màn hình quét khuôn mặt nếu lần nhận diện trước bị gián đoạn.")
            ],
            "timing": [
                ("Khởi tạo phiên:", "Thực hiện ở đầu mỗi phiên tương tác mua sắm mới của khách hàng."),
                ("Thời gian xử lý nhận diện AI:", "Thời gian đáp ứng trích xuất vector khuôn mặt và so khớp tại máy chủ AI dưới 25ms.")
            ],
            "description": [
                ("Tác nhân / Vai trò:", "Khách hàng vãng lai (Guest), Khách hàng thành viên siêu thị có tài khoản (Member)."),
                ("Hệ thống liên quan:", "Mô-đun Camera trước của Robot, Máy chủ AI Face Recognition (OpenCV YuNet + SFace Engine ONNX), Dịch vụ xác thực sinh trắc học (/api/v1/auth/face-login), Ngữ cảnh xác thực RobotAuthContext."),
                ("Mục đích:", "Định danh tức thì khách hàng thành viên thông qua công nghệ sinh trắc học khuôn mặt AI không tiếp xúc, mở khóa toàn bộ quyền lợi thành viên, hồ sơ dị ứng/sức khỏe và giỏ hàng cá nhân hóa.")
            ],
            "normal_flow": [
                "1. Khách hàng tiếp cận Màn hình Chọn Vai Trò, quan sát hai lựa chọn: thẻ \"Khách vãng lai\" và thẻ \"Khách hàng thành viên\".",
                "2. Khách hàng thành viên chạm nút \"QUÉT FACE ID ĐĂNG NHẬP\".",
                "3. Ứng dụng chuyển sang màn hình FaceScanScreen, tự động bật camera trước và hiển thị khung tròn hướng dẫn căn chỉnh gương mặt kèm hiệu ứng quét quét radar.",
                "4. Robot phát giọng nói hướng dẫn: \"Xin mời quý khách nhìn thẳng vào camera để đăng nhập!\".",
                "5. Camera chụp khung hình chân dung (tự động căn giữa, nén tối ưu 640px) và gửi tới endpoint /api/v1/auth/face-login.",
                "6. Máy chủ AI trích xuất vector đặc trưng 128 chiều, tính toán độ tương đồng Cosine Similarity với cơ sở dữ liệu khuôn mặt đã đăng ký.",
                "7. Xác thực thành công: Giao diện hiển thị dấu tích xanh nổi bật, thông báo \"Xác thực thành công!\", hiển thị họ tên thành viên và hạng thẻ hội viên.",
                "8. Robot Assistant phát lời chào thân mật: \"Xin chào quý khách [Tên thành viên]! Chúc bạn có một buổi mua sắm thật tuyệt vời!\" và tự động chuyển vào Màn hình Chính Thành Viên (MemberHomeScreen)."
            ],
            "abnormal_cases": [
                ("Không tìm thấy khuôn mặt trong hệ thống:", "Hệ thống hiển thị thông báo lỗi thân thiện \"Không nhận diện được khuôn mặt. Quý khách vui lòng thử lại hoặc chọn mua sắm với tư cách Khách vãng lai\", cho phép quét lại tối đa 3 lần."),
                ("Ánh sáng yếu hoặc góc chụp quá lệch:", "Robot phát giọng nói nhắc nhở: \"Quý khách vui lòng đứng đối diện camera và giữ yên trong giây lát nhé!\"."),
                ("Mất kết nối tới máy chủ AI:", "Hệ thống hiển thị nút chuyển đổi sang phương thức đăng nhập bằng số điện thoại/mã thẻ thành viên hoặc tiếp tục như khách vãng lai.")
            ],
            "data_processing": [
                ("Xử lý khung hình sinh trắc học:", "Mã hóa khung hình camera JPEG chất lượng 85, độ phân giải tối đa 640px; gửi qua HTTP POST multipart/form-data có gắn kèm cờ ngrok-skip-browser-warning."),
                ("Cập nhật trạng thái phiên:", "Lưu trữ Access Token và thông tin Member Profile (MemberId, FullName, MembershipLevel, ShoppingBudget) vào RobotAuthContext.")
            ],
            "business_rules": [
                ("BR-ROBOT-03:", "Chỉ những tài khoản có vai trò 'Member' trong hệ thống mới được phép truy cập vào các tính năng cá nhân hóa giỏ hàng và danh sách ưu đãi riêng."),
                ("BR-ROBOT-04:", "Ngưỡng tin cậy Cosine Similarity tối thiểu để phê duyệt xác thực khuôn mặt là 0.65.")
            ]
        },
        {
            "id": "3.2.3",
            "title": "3.2.3 Trải nghiệm Mua sắm Khách vãng lai & Khuyến mãi Mỗi ngày (Guest Shopping Experience & Daily Promotions)",
            "images": [("02_Daily_Promotions.jpg", 2.5), ("04_Guest_Home_Dashboard.jpg", 2.5)],
            "caption": "Hình 3.2.3: Màn hình khuyến mãi mỗi ngày (trái) và Trang chủ mua sắm khách vãng lai (phải)",
            "triggers": [
                ("Kích hoạt phiên khách vãng lai:", "Khách hàng chạm nút \"BẮT ĐẦU NGAY\" trên thẻ Khách vãng lai tại RoleSelectionScreen, hoặc nhấn nút \"Khuyến mãi hôm nay\" trên WelcomeScreen."),
                ("Xem chi tiết khuyến mãi:", "Chạm vào banner khuyến mãi hoặc các sản phẩm giảm giá hiển thị trên trang chủ.")
            ],
            "timing": [
                ("Thời gian phục vụ:", "Kéo dài suốt phiên tương tác của khách vãng lai cho đến khi khách rời đi hoặc hết thời gian chờ.")
            ],
            "description": [
                ("Tác nhân / Vai trò:", "Khách mua sắm tự do chưa đăng ký tài khoản thành viên."),
                ("Hệ thống liên quan:", "Dịch vụ khuyến mãi công cộng (/api/v1/search/deals), Dịch vụ danh mục sản phẩm (/api/v1/products), Dịch vụ bản đồ siêu thị 2D (MapViewerScreen)."),
                ("Mục đích:", "Cung cấp cho khách vãng lai giao diện tra cứu trực quan, dễ sử dụng để tìm kiếm sản phẩm, xem danh mục ngành hàng, duyệt các mặt hàng khuyến mãi sốc và yêu cầu robot dẫn đường đơn điểm.")
            ],
            "normal_flow": [
                "1. Khách hàng vào trang chủ Guest Home Dashboard, quan sát thanh tìm kiếm nhanh, các thẻ lối tắt chức năng (\"Tìm kiếm giọng nói\", \"Bản đồ siêu thị\", \"Ưu đãi sốc\") và danh sách các sản phẩm đang được quan tâm nhiều nhất.",
                "2. Khách nhấn vào thẻ \"Siêu Ưu Đãi Hôm Nay\" -> Hệ thống mở GuestCampaignScreen hiển thị danh sách các sản phẩm giảm giá sâu trong ngày kèm phần trăm chiết khấu (\"GIẢM 20%\").",
                "3. Khách hàng chạm vào một thẻ sản phẩm bất kỳ để xem thông tin chi tiết (tên hàng, giá gốc gạch ngang, giá ưu đãi màu xanh, vị trí quầy kệ).",
                "4. Khách hàng nhấn nút \"Dẫn đến kệ\" trên thẻ sản phẩm.",
                "5. Robot phát thông báo bằng giọng nói: \"Dạ vâng! Robot sẽ dẫn quý khách đến quầy bán [Tên sản phẩm]. Xin mời quý khách đi theo tôi!\", kích hoạt lệnh điều khiển ROS2 và chuyển sang màn hình bản đồ 2D dẫn đường."
            ],
            "abnormal_cases": [
                ("Không có sản phẩm khuyến mãi hoạt động:", "Hệ thống tự động hiển thị danh mục các sản phẩm bán chạy nhất kèm thông báo thân thiện \"Chưa có ưu đãi mới hôm nay, mời bạn xem các món hàng nổi bật nhé!\".")
            ],
            "data_processing": [
                ("Truy vấn ưu đãi:", "Gọi API GET /api/v1/search/deals nạp danh sách sản phẩm giảm giá; gọi GET /api/v1/ad-campaigns/robot-playlist để nạp các chiến dịch quảng cáo công cộng.")
            ],
            "business_rules": [
                ("BR-ROBOT-05:", "Khách vãng lai không được hỗ trợ lưu giỏ hàng lâu dài lên đám mây; dữ liệu giỏ hàng chỉ lưu tạm thời trong phiên làm việc hiện tại."),
                ("BR-ROBOT-06:", "Khách vãng lai chỉ được phép yêu cầu robot dẫn đường đơn điểm (1 sản phẩm/1 quầy kệ cho mỗi lượt yêu cầu).")
            ]
        },
        {
            "id": "3.2.4",
            "title": "3.2.4 Cá nhân hóa Thành viên & Ưu đãi Đặc quyền (Member Personalization & Special Offers)",
            "images": [("09_Member_Home_Dashboard.jpg", 1.85), ("10_Member_Special_Offers.jpg", 1.85), ("13_Recipe_Detail_Cook_Guide.jpg", 1.85)],
            "caption": "Hình 3.2.4: Trang chủ thành viên (trái), Danh sách ưu đãi đặc quyền (giữa) và Gợi ý công thức món ăn AI (phải)",
            "triggers": [
                ("Tự động kích hoạt:", "Kích hoạt ngay sau khi khách hàng xác thực Face ID thành công từ FaceScanScreen."),
                ("Chuyển đổi phân hệ:", "Chạm vào các tab chức năng: \"Dành riêng cho bạn\", \"Ưu đãi thành viên\", hoặc widget \"Gợi ý món ngon hôm nay\".")
            ],
            "timing": [
                ("Thời gian duy trì:", "Hoạt động liên tục trong suốt phiên mua sắm của thành viên đến khi nhấn \"Đăng xuất\" hoặc hết phiên làm việc.")
            ],
            "description": [
                ("Tác nhân / Vai trò:", "Khách hàng thành viên siêu thị đã được định danh sinh trắc học."),
                ("Hệ thống liên quan:", "Hệ thống cá nhân hóa gợi ý sản phẩm (/api/v1/search/personalized), Mô-đun phân tích thẻ dinh dưỡng (Health Tags: Eat Clean, Keto, Thuần chay, Cảnh báo dị ứng), Tiện ích gợi ý công thức món ăn AI (MealSuggestionsController)."),
                ("Mục đích:", "Tạo ra không gian mua sắm được may đo riêng biệt cho từng thành viên, tối ưu ngân sách cá nhân và chăm sóc sức khỏe dinh dưỡng gia đình.")
            ],
            "normal_flow": [
                "1. Thành viên đăng nhập thành công vào MemberHomeScreen, nhìn thấy lời chào kèm tên riêng, cấp bậc thẻ hội viên (Bạc, Vàng, Kim Cương) và số điểm tích lũy hiện có.",
                "2. Lưới sản phẩm thông minh tự động đề xuất các món hàng phù hợp với hồ sơ dinh dưỡng của khách (ví dụ khách chọn nhãn 'Eat Clean' sẽ thấy ức gà tươi, hạt chia, dầu ô-liu).",
                "3. Khách hàng chạm vào tab \"Ưu đãi đặc quyền\" -> Mở MemberOffersScreen hiển thị danh sách các sản phẩm giảm giá riêng biệt dành cho cấp bậc thẻ của mình.",
                "4. Khách hàng chạm vào banner \"Gợi ý món ngon hôm nay\" -> Mở Recipe Detail Screen hiển thị công thức chế biến (ví dụ: 'Salad Bơ Trứng'), định lượng nguyên liệu, trạng thái còn hàng trên kệ và nút \"Thêm toàn bộ nguyên liệu vào giỏ hàng\"."
            ],
            "abnormal_cases": [
                ("Thành viên chưa thiết lập Health Tags:", "Hệ thống tự động hiển thị gợi ý thân thiện \"Hãy thiết lập sở thích dinh dưỡng để nhận thực đơn riêng cho bạn!\" và nạp các sản phẩm xu hướng chung."),
                ("Hết hạn phiên đăng nhập (Token Expired):", "Hệ thống hiển thị thông báo nhỏ và tự động mở camera quét lại Face ID trong 1 giây mà không làm gián đoạn giỏ hàng.")
            ],
            "data_processing": [
                ("Tổng hợp dữ liệu cá nhân hóa:", "Gọi API GET /api/v1/members/me lấy thông tin tài khoản và danh sách HealthTagId; gọi GET /api/v1/search/personalized lọc sản phẩm an toàn loại trừ thành phần dị ứng.")
            ],
            "business_rules": [
                ("BR-ROBOT-07:", "Tuyệt đối không hiển thị các sản phẩm chứa thành phần dị ứng mà khách hàng đã khai báo trong danh mục cảnh báo sức khỏe."),
                ("BR-ROBOT-08:", "Tự động áp dụng mức chiết khấu thành viên cao nhất theo hạng thẻ khi tính giá hiển thị trên màn hình.")
            ]
        },
        {
            "id": "3.2.5",
            "title": "3.2.5 Tìm kiếm Thông minh & Trợ lý Giọng nói AI (Smart Search & AI Voice Assistant)",
            "images": [("05_Voice_Search_Listening.jpg", 1.85), ("06_Category_Catalog.jpg", 1.85), ("07_Product_Search_Result.jpg", 1.85)],
            "caption": "Hình 3.2.5: Trợ lý lắng nghe giọng nói (trái), Danh mục ngành hàng (giữa) và Kết quả tìm kiếm sản phẩm (phải)",
            "triggers": [
                ("Tìm kiếm bằng giọng nói:", "Khách hàng chạm vào biểu tượng Micro trên thanh tìm kiếm hoặc nhấn nút \"Tìm bằng giọng nói\" tại bất kỳ màn hình nào."),
                ("Tìm kiếm bằng văn bản / danh mục:", "Gõ từ khóa vào ô tìm kiếm hoặc nhấn vào thẻ danh mục ngành hàng.")
            ],
            "timing": [
                ("Thời gian xử lý giọng nói:", "Thu âm tối đa 8 giây/lần; chuyển đổi giọng nói thành văn bản và trả kết quả dưới 1.2 giây.")
            ],
            "description": [
                ("Tác nhân / Vai trò:", "Khách hàng mua sắm cần tra cứu thông tin sản phẩm, giá bán hoặc vị trí quầy kệ."),
                ("Hệ thống liên quan:", "Mô-đun nhận dạng giọng nói tiếng Việt (Speech-to-Text), Máy chủ phân tích ngữ nghĩa AI (Gemini AI / SearchController), Cơ sở dữ liệu danh mục quầy kệ siêu thị."),
                ("Mục đích:", "Mang lại trải nghiệm tra cứu không chạm hiện đại, giúp khách hàng tìm thấy đúng sản phẩm và vị trí kệ hàng chỉ bằng một câu nói tự nhiên.")
            ],
            "normal_flow": [
                "1. Khách hàng nhấn nút Micro -> Màn hình hiển thị hoạt họa sóng âm đang lắng nghe (Voice Listening Waveform) kèm âm hiệu thông báo sẵn sàng.",
                "2. Khách hàng nói tự nhiên: \"Tìm cho tôi gạo hạt dài\" hoặc \"Nước giặt ở đâu\".",
                "3. Ứng dụng ghi âm, xử lý lọc tiếng ồn môi trường và gửi âm thanh tới dịch vụ Voice AI.",
                "4. Dịch vụ AI chuyển đổi giọng nói thành chuỗi từ khóa chuẩn xác và truy vấn danh mục qua API GET /api/v1/search/products?q=...",
                "5. Màn hình ProductSearchResult hiển thị danh sách các món hàng trùng khớp kèm hình ảnh, giá bán, trạng thái còn hàng và thẻ vị trí: \"Kệ 2 • Dãy A01\".",
                "6. Khách hàng có thể nhấn vào sản phẩm để xem chi tiết hoặc bấm nút \"Dẫn đến kệ\" để robot lập lộ trình đưa đến tận nơi."
            ],
            "abnormal_cases": [
                ("Tiếng ồn môi trường lớn hoặc không nghe rõ:", "Sau 5 giây im lặng, robot phát âm thanh nhắc nhở nhẹ nhàng: \"Xin lỗi, tôi chưa nghe rõ. Bạn có thể nói lại hoặc dùng bàn phím trên màn hình nhé!\".")
            ],
            "data_processing": [
                ("Xử lý tín hiệu âm thanh:", "Ghi âm định dạng PCM 16kHz đơn kênh; gửi dữ liệu qua WebSocket hoặc REST HttpClient tới dịch vụ AI Voice."),
                ("So khớp từ khóa:", "Thực hiện tìm kiếm toàn văn Full-Text Search kết hợp xếp hạng độ tương đồng ngữ nghĩa.")
            ],
            "business_rules": [
                ("BR-ROBOT-09:", "Giới hạn thời gian lắng nghe tối đa là 8 giây cho mỗi lượt thu âm để tránh làm gián đoạn trải nghiệm."),
                ("BR-ROBOT-10:", "Các sản phẩm đang có chương trình tài trợ (Sponsored Ads) được tự động ưu tiên xếp lên đầu kết quả tìm kiếm nếu độ tương đồng từ khóa đạt chuẩn.")
            ]
        },
        {
            "id": "3.2.6",
            "title": "3.2.6 Chi tiết Sản phẩm & Thao tác Giỏ hàng Tức thì (Product Detail & Instant Cart Operations)",
            "images": [("11_Product_Detail_View.jpg", 2.5), ("12_Product_Detail_Added_Cart.jpg", 2.5)],
            "caption": "Hình 3.2.6: Chi tiết thông số sản phẩm (trái) và Trạng thái xác nhận thêm vào giỏ hàng thành công (phải)",
            "triggers": [
                ("Xem chi tiết:", "Khách hàng chạm vào bất kỳ thẻ sản phẩm nào từ màn hình Tìm kiếm, Khuyến mãi hoặc Danh mục."),
                ("Thao tác giỏ hàng:", "Nhấn nút \"+\", \"-\" để thay đổi số lượng và nhấn nút màu xanh \"Thêm vào giỏ hàng\".")
            ],
            "timing": [
                ("Phản hồi tương tác:", "Thao tác cập nhật số lượng và thêm giỏ hàng diễn ra tức thì dưới 200ms.")
            ],
            "description": [
                ("Tác nhân / Vai trò:", "Khách hàng xem xét sản phẩm trước khi quyết định mua hàng."),
                ("Hệ thống liên quan:", "Dịch vụ quản lý sản phẩm (/api/v1/products/{id}), Dịch vụ giỏ hàng đám mây (/api/v1/cart), RobotVoiceService."),
                ("Mục đích:", "Hiển thị minh bạch toàn bộ thông số sản phẩm: hình ảnh chất lượng cao, thành phần, giá gốc, giá giảm, vị trí chính xác trên sơ đồ quầy kệ (Kệ, Tầng, Ô) và thực hiện thêm vào giỏ tức thì.")
            ],
            "normal_flow": [
                "1. Khách hàng chọn sản phẩm (ví dụ: 'Quả bơ sáp Đắk Lắk').",
                "2. Giao diện ProductDetailScreen hiển thị đầy đủ thông tin: giá 45.000₫/kg, vị trí \"Kệ 3 - Dãy B01\", mô tả nguồn gốc và chứng nhận vệ sinh an toàn thực phẩm.",
                "3. Khách hàng điều chỉnh số lượng mua bằng nút \"+\" hoặc \"-\" (số lượng mặc định là 1).",
                "4. Khách hàng nhấn nút \"Thêm vào giỏ hàng\".",
                "5. Hệ thống hiển thị thanh thông báo nổi màu xanh lá cây \"Đã thêm vào giỏ hàng thành công!\", cập nhật số đếm trên biểu tượng giỏ hàng ở thanh tiêu đề.",
                "6. Robot phát giọng nói xác nhận: \"Đã thêm [Tên sản phẩm] vào giỏ hàng của bạn!\"."
            ],
            "abnormal_cases": [
                ("Sản phẩm tạm hết hàng:", "Nếu số lượng tồn kho bằng 0, nút \"Thêm vào giỏ hàng\" tự động bị vô hiệu hóa chuyển sang màu xám với nhãn \"Tạm hết hàng\", đồng thời gợi ý các sản phẩm cùng loại còn hàng trên kệ.")
            ],
            "data_processing": [
                ("Lưu trữ giỏ hàng:", "Gửi yêu cầu POST /api/v1/cart/items với ProductId và Quantity; cập nhật dữ liệu giỏ hàng cục bộ và đồng bộ máy chủ.")
            ],
            "business_rules": [
                ("BR-ROBOT-11:", "Số lượng sản phẩm thêm vào giỏ không được vượt quá số lượng hàng tồn thực tế đang trưng bày trên quầy kệ."),
                ("BR-ROBOT-12:", "Hộp thông báo thêm giỏ hàng thành công tự động biến mất sau 2.5 giây để tránh che khuất nội dung.")
            ]
        },
        {
            "id": "3.2.7",
            "title": "3.2.7 Giỏ hàng Thông minh & Robot Dẫn đường Mua sắm (Smart Cart & Autonomous Robot Navigation Guide)",
            "images": [("14_Member_Cart_List.jpg", 1.85), ("15_Cart_Guide_Dispatching.jpg", 1.85), ("16_Cart_Guide_Timeout.png", 1.85)],
            "caption": "Hình 3.2.7: Giỏ hàng thông minh (trái), Bản đồ 2D robot đang dẫn đường (giữa) và Giao diện xử lý quá giờ chờ (phải)",
            "triggers": [
                ("Yêu cầu dẫn đường theo giỏ hàng:", "Tại MemberCartScreen, khách hàng kiểm tra danh sách món hàng và nhấn nút màu xanh nổi bật \"Robot dẫn theo giỏ hàng\"."),
                ("Dẫn đường từ chi tiết:", "Tại ProductDetailScreen, khách nhấn nút \"Dẫn đường đến kệ\".")
            ],
            "timing": [
                ("Lập lộ trình:", "Backend tính toán thứ tự kệ hàng tối ưu (TSP) và khởi tạo lộ trình trong vòng 500ms.")
            ],
            "description": [
                ("Tác nhân / Vai trò:", "Khách hàng mua sắm cần robot dẫn đường trực tiếp qua các quầy kệ trong siêu thị."),
                ("Hệ thống liên quan:", "Dịch vụ điều hướng robot (/api/v1/navigation/dispatch-autonomous), Thuật toán tối ưu hóa hành trình người đưa thư (TSP Planner kết hợp Dijkstra), Bộ điều khiển di chuyển ROS2 Nav2, Bản đồ siêu thị 2D (CartGuideMapScreen)."),
                ("Mục đích:", "Dẫn dắt khách hàng di chuyển theo lộ trình ngắn nhất, khoa học nhất qua từng kệ hàng chứa các sản phẩm trong giỏ, cập nhật tiến trình thời gian thực và thông báo khi đến từng điểm dừng.")
            ],
            "normal_flow": [
                "1. Khách hàng kiểm tra các mặt hàng trong giỏ và nhấn \"Robot dẫn theo giỏ hàng\".",
                "2. Hệ thống gửi yêu cầu điều phối POST /api/v1/navigation/dispatch-autonomous với flowType: 'guide' và danh sách các ProductId.",
                "3. Backend giải thuật toán TSP, sắp xếp thứ tự quầy kệ tối ưu (ví dụ: Kệ 1 -> Kệ 3 -> Kệ 5) và gửi lệnh điều khiển xuống động cơ robot.",
                "4. Màn hình tablet chuyển sang CartGuideMapScreen ở trạng thái DISPATCHED, hiển thị thông tin lộ trình và phát giọng nói: \"Tôi bắt đầu dẫn đường. Xin quý khách vui lòng đi theo tôi!\".",
                "5. Robot di chuyển (MOVING), bản đồ 2D vẽ đường đi trực quan và hiển thị tiến trình: 'Chặng 1/3: Đang đến Kệ 1 - Rau củ tươi'.",
                "6. Khi đến quầy kệ, robot dừng lại an toàn, chuyển trạng thái ARRIVED, phát thông báo: \"Chúng ta đã đến quầy [Tên kệ]. Quý khách có thể lấy sản phẩm tại đây!\".",
                "7. Khách hàng lấy sản phẩm xong và nhấn \"Tiếp tục chặng tiếp theo\" -> Robot tiếp tục dẫn tới kệ kế tiếp cho đến khi hoàn tất toàn bộ giỏ hàng."
            ],
            "abnormal_cases": [
                ("Phát hiện vật cản trên đường đi:", "Cảm biến LiDAR/Sonar phát hiện chướng ngại vật phía trước trong khoảng cách dưới 0.6m -> Robot tự động giảm tốc dừng lại an toàn và phát thông báo: \"Phía trước có vật cản, robot đang tính toán đường vòng tránh an toàn!\". Khi vật cản rời đi, robot tự tiếp tục lộ trình."),
                ("Dừng khẩn cấp (E-Stop):", "Khi kích hoạt E-Stop phần cứng hoặc chạm nút Dừng trên màn hình, động cơ ngắt điện trong vòng 50ms, màn hình hiển thị cảnh báo đỏ EMERGENCY STOP."),
                ("Khách không tương tác tại kệ (Timeout):", "Nếu robot đỗ tại kệ quá 60 giây mà khách không xác nhận, hệ thống hiển thị màn hình đếm ngược (Cart Guide Timeout) và tự động quay về chế độ chờ.")
            ],
            "data_processing": [
                ("Truyền phát viễn thám điều hướng:", "Nhận luồng tọa độ thời gian thực (x, y) và góc quay qua SignalR Hub sự kiện ReceiveLocation và NavigationStatus."),
                ("Hủy lệnh dẫn đường:", "Gửi yêu cầu hủy qua POST /api/v1/navigation/robots/{ROBOT_CODE}/cancel khi khách hủy lộ trình.")
            ],
            "business_rules": [
                ("BR-ROBOT-13:", "Vận tốc di chuyển dẫn đường tối đa của robot trong siêu thị được khống chế ở mức an toàn 0.5 m/s."),
                ("BR-ROBOT-14:", "Lộ trình TSP ưu tiên sắp xếp các mặt hàng tươi sống đông lạnh ở chặng cuối cùng để đảm bảo chất lượng bảo quản.")
            ]
        },
        {
            "id": "3.2.8",
            "title": "3.2.8 Quảng cáo Tự hành, Lớp phủ Ngữ cảnh & Điều hướng Sản phẩm Tương tác (Contextual Overlays, Autonomous Advertising & Interactive Guidance Flow)",
            "images": [("17_Zone_Ad_Modal.png", 2.5), ("phone_now.png", 2.5)],
            "caption": "Hình 3.2.8: Lớp phủ quảng cáo ngữ cảnh tại quầy kệ (trái) và Giao diện Chọn nhiều sản phẩm quảng cáo AdMultiProductSelectScreen (phải)",
            "triggers": [
                ("Admin phát lệnh quảng cáo từ Web Admin:", "Quản trị viên phát lệnh quảng cáo tự hành cho robot theo 3 phạm vi: Theo Kệ (Shelf), Theo Khu vực (Zone), hoặc Tuyến tuần tra tự do toàn siêu thị (Route / Free-Roam)."),
                ("Tương tác điều hướng của khách hàng:", "Khách hàng đi dạo trong siêu thị nhìn thấy màn hình quảng cáo trên robot và chạm vào màn hình để xem thông tin hoặc yêu cầu robot dẫn đường mua sản phẩm."),
                ("Kích hoạt theo tọa độ địa lý (Geofencing):", "Khi robot di chuyển vào bán kính tọa độ của một kệ hàng hoặc khu vực nhất định, lớp phủ quảng cáo ngữ cảnh (Zone Ad Modal) tự động hiển thị trên màn hình.")
            ],
            "timing": [
                ("Thời lượng ca tuần tra quảng cáo:", "Thực thi liên tục theo thời lượng ấn định (ví dụ 180s - 300s/ca tuần tra) hoặc chạy vòng lặp theo lịch điều phối của siêu thị."),
                ("Thời lượng hiển thị sản phẩm:", "Mỗi banner/video sản phẩm được trình chiếu từ 10 đến 12 giây kèm đếm ngược và giọng nói giới thiệu tương ứng.")
            ],
            "description": [
                ("Tác nhân / Vai trò:", "Quản trị viên siêu thị (Admin), Đối tác thương hiệu (Brands), Khách mua sắm (Khách vãng lai & Khách thành viên)."),
                ("Hệ thống liên quan:", "Web Admin Quản trị Quảng cáo, Dịch vụ điều phối robot trung tâm (NavigationService), Dịch vụ tính cước và xếp hạng AdScore (AdPackageService, AdCampaignService), Trợ lý giọng nói Robot (RobotVoiceService), Dịch vụ ngắt và khôi phục quảng cáo (AdInterruptionService), Màn hình chọn nhiều sản phẩm quảng cáo (AdMultiProductSelectScreen), Bản đồ dẫn đường 2D (CartGuideMapScreen)."),
                ("Mục đích:", "Thiết lập quy trình truyền thông đa phương tiện tự hành khép kín: phân bổ thứ tự phát sóng theo điểm ưu tiên AdScore của gói cước, trình chiếu quảng cáo thông minh kết hợp giọng nói, hỗ trợ khách hàng điều hướng mua sản phẩm tức thì với phân quyền rõ ràng giữa Khách vãng lai và Thành viên, và tự động khôi phục tiếp tục phát quảng cáo sau khi hoàn thành dẫn đường.")
            ],
            "normal_flow": [
                "Bước 1: Brand chọn Gói cước & Xác lập Điểm ưu tiên AdScore:\nĐối tác thương hiệu (Brand) đăng ký chiến dịch quảng cáo và lựa chọn gói cước tương ứng: Gói VIP (AdScore = 1.000 điểm), Gói Pro (AdScore = 500 điểm), Gói Standard (AdScore = 100 điểm). Mỗi gói cước quy định rõ ngân sách, đơn giá phát theo Khu vực (ZoneUnitPrice), đơn giá theo Kệ (ShelfUnitPrice), đơn giá tuần tra theo Tuyến (RouteUnitPrice) và phí cho mỗi lượt khách chạm tương tác (ClickFee).",
                "Bước 2: Admin phát lệnh quảng cáo từ Web Admin:\nQuản trị viên truy cập màn hình Robot Advertisement Management (/robots hoặc /ad-management), chọn robot mục tiêu (RB0001) và cấu hình phạm vi phát quảng cáo:\n- Theo Kệ (Shelf): Chọn danh sách các kệ hàng và thời gian đỗ tại kệ (Dwell Time: ví dụ 20s/kệ).\n- Theo Khu vực (Zone): Chọn khu vực cần tăng cường truyền thông (Zone 1, Zone 2,...).\n- Theo Tuyến tự do (Route / Free-Roam): Robot di chuyển tuần tra liên tục khắp các hành lang siêu thị trong thời lượng ấn định (ví dụ: 180 giây).\nAdmin nhấn \"Bắt đầu quảng cáo\" -> Hệ thống gửi yêu cầu POST /api/v1/navigation/dispatch-autonomous với flowType: 'ad'.",
                "Bước 3: Sắp xếp danh sách phát theo AdScore & Trình chiếu đa phương tiện:\nBackend truy vấn tất cả các chiến dịch quảng cáo (AdCampaign) đang hoạt động, còn ngân sách, phù hợp với phạm vi phát và tự động sắp xếp danh sách phát (Playlist) theo thứ tự ưu tiên:\n  1. Điểm ưu tiên gói cước AdScore (Gói VIP > Pro > Standard luôn được ưu tiên phát trước).\n  2. Điểm ưu tiên chiến dịch (Priority).\n  3. Thời gian tạo chiến dịch (CreatedAt).\nRobot nhận Playlist, tự động phát âm thanh giọng nói TTS tiếng Việt tự nhiên (FPT banmai) giới thiệu tên món hàng và giá ưu đãi: \"Tiếp theo là [Tên sản phẩm], giá ưu đãi chỉ [Giá] đồng. Mời quý khách chạm màn hình để xem thêm nhé!\". Màn hình hiển thị banner/video chất lượng cao, thanh đếm ngược thời lượng hiển thị sản phẩm (10-12s) và thời lượng đỗ tại kệ. Hệ thống tự động ghi nhận Lượt hiển thị (Impression) gửi về máy chủ để tính phí theo gói.",
                "Bước 4: Điều hướng tương tác & Phân quyền Khách vãng lai vs Khách thành viên:\nTrong lúc robot đang phát quảng cáo (đặc biệt trong chế độ quảng cáo tự do dọc hành lang), khách hàng có thể chạm vào màn hình:\n- Trường hợp Khách vãng lai (Guest):\n  Khách hàng nhấn nút nổi bật \"DẪN TÔI MUA MÓN NÀY\" trên banner món hàng đang phát. Hệ thống cho phép robot dẫn đường tới DUY NHẤT 1 sản phẩm đó. Nếu khách bấm \"Xem tất cả món\", hệ thống hiển thị pop-up yêu cầu Đăng nhập tài khoản / Quét Face ID: \"Quý khách vui lòng đăng nhập tài khoản thành viên để chọn nhiều sản phẩm dẫn đường cùng lúc!\".\n- Trường hợp Khách hàng thành viên (Member):\n  Khách hàng đăng nhập (qua Face ID hoặc tài khoản). Hệ thống mở Màn hình Chọn Nhiều Sản Phẩm Quảng Cáo (AdMultiProductSelectScreen). Màn hình liệt kê toàn bộ các mặt hàng trong phiên quảng cáo đã được khử trùng lặp và sắp xếp theo AdScore. Khách hàng có thể nhấn \"Chọn tất cả\", \"Bỏ chọn\" hoặc tích chọn nhiều món hàng khác nhau. Khách nhấn \"Bắt đầu dẫn đường\" -> Robot dừng tiến trình quảng cáo, giải bài toán TSP lập lộ trình tối ưu qua các quầy kệ chứa các sản phẩm đã chọn, phát giọng nói xác nhận và chuyển sang bản đồ 2D CartGuideMapScreen dẫn khách đi.",
                "Bước 5: Tự động khôi phục phát quảng cáo khi điều hướng xong:\nTrước khi chuyển sang dẫn đường, dịch vụ AdInterruptionService tự động lưu lại toàn bộ ngữ cảnh quảng cáo dở dang (ID nhiệm vụ, các kệ còn lại, thời lượng phút còn lại). Robot di chuyển dẫn khách tới quầy kệ sản phẩm. Ngay khi chạm mốc tọa độ kệ hàng đích cuối cùng (trạng thái ARRIVED), robot phát giọng nói thông báo hoàn tất: \"Quý khách đã đến nơi, chúc quý khách mua sắm vui vẻ!\". Ngay lập tức, hệ thống kết thúc màn hình dẫn đường và tự động gọi API khôi phục (RobotControlService.dispatchAutonomous) để robot tiếp tục phát quảng cáo theo lộ trình dang dở mà không cần Admin thao tác lại."
            ],
            "abnormal_cases": [
                ("Chống gian lận lượt click (Click Fraud Prevention):", "Hệ thống áp dụng cơ chế Client Debounce 1.5 giây giữa các lần nhấn. Nếu phát hiện cùng một người dùng bấm liên tục vào một banner trong phiên, hệ thống chặn gửi request và không trừ tiền phí click (ClickFee) của Brand."),
                ("Khách chưa chọn sản phẩm nào trên AdMultiProductSelectScreen:", "Khi nhấn \"Bắt đầu dẫn đường\" mà chưa chọn món nào, hệ thống hiển thị modal thông báo lịch sự: \"Quý khách vui lòng chạm vào các món hàng trên màn hình để chọn sản phẩm trước khi bắt đầu dẫn đường nhé!\"."),
                ("Sản phẩm quảng cáo tạm hết hàng trên kệ:", "Nếu sản phẩm khách chọn bị hết hàng hoặc chưa gán vị trí quầy kệ, hệ thống phát giọng nói thân thiện thông báo quầy đang bảo trì/hết hàng và gợi ý chọn món tương tự khác.")
            ],
            "data_processing": [
                ("Theo dõi tương tác quảng cáo:", "Ghi nhận Lượt hiển thị (Impression) và Lượt chạm (Click) qua POST /api/v1/ad-resources/interactions kèm tọa độ x, y để phục vụ bản đồ nhiệt (Heatmap)."),
                ("Lưu trữ trạng thái ngắt quảng cáo:", "Lưu trữ trạng thái nhiệm vụ vào AdInterruptionService (RAM và AsyncStorage) bao gồm originalMissionId, remainingNodeIds, remainingShelfIds, durationMinutes, isFreeRoam.")
            ],
            "business_rules": [
                ("BR-ROBOT-15 (Quy tắc ưu tiên AdScore):", "Chiến dịch thuộc gói cước có điểm AdScore cao hơn phải luôn được phát với tần suất cao hơn và luôn nằm trên đầu danh sách trong màn hình Chọn nhiều sản phẩm quảng cáo."),
                ("BR-ROBOT-16 (Quy tắc phân quyền điều hướng):", "Khách vãng lai chỉ được phép yêu cầu dẫn đường tối đa 1 sản phẩm đơn lẻ từ banner quảng cáo; tính năng dẫn đường đa điểm (Multi-Stop Guide qua AdMultiProductSelectScreen) là đặc quyền riêng dành cho khách hàng thành viên có tài khoản."),
                ("BR-ROBOT-17 (Quy tắc khôi phục quảng cáo tức thì):", "Ngay khi robot chạm mốc tọa độ đích cuối cùng (ARRIVED), hệ thống tự động gọi API khôi phục phát quảng cáo mà không cần độ trễ chờ đợi, sử dụng đúng thời lượng phút còn lại được tính toán bù trừ từ AdInterruptionService.")
            ]
        }
    ]

print("Script template ready")
