# MCP (Model Context Protocol)

## 1. Tổng quan
MCP là giao thức chuẩn hóa cách ứng dụng AI kết nối với dữ liệu, công cụ và các dịch vụ bên ngoài. MCP giúp mô hình sử dụng ngữ cảnh và khả năng bên ngoài theo một giao diện nhất quán, thay vì phải tích hợp riêng cho từng hệ thống.

## 2. Các thành phần chính
- **Host:** Ứng dụng AI mà người dùng tương tác.
- **MCP Client:** Thành phần trong Host quản lý kết nối tới MCP Server.
- **MCP Server:** Cung cấp tài nguyên, công cụ hoặc prompt cho Client.
- **Resources:** Dữ liệu/ngữ cảnh mà mô hình có thể đọc, chẳng hạn tài liệu, tệp hoặc bản ghi cơ sở dữ liệu.
- **Tools:** Các hàm thao tác mà mô hình có thể gọi để thực hiện hành động.
- **Prompts:** Mẫu hướng dẫn được chuẩn hóa và tái sử dụng.

## 3. Luồng hoạt động
1. Host khởi tạo MCP Client và kết nối tới MCP Server.
2. Client khám phá các capabilities mà Server cung cấp.
3. Mô hình yêu cầu đọc Resource, dùng Prompt hoặc gọi Tool khi cần.
4. Server xác thực yêu cầu, thực thi trong phạm vi được cấp phép và trả kết quả.
5. Host đưa kết quả vào ngữ cảnh để mô hình tiếp tục xử lý.

## 4. Thiết kế và bảo mật
- Áp dụng nguyên tắc quyền tối thiểu cho từng Tool và Resource.
- Xác thực và kiểm tra đầu vào trước khi thực thi.
- Yêu cầu người dùng xác nhận trước các thao tác có side effect hoặc không thể hoàn tác.
- Không đưa secret, token hay thông tin nhạy cảm vào prompt hoặc log.
- Ghi log có kiểm soát để phục vụ giám sát và kiểm toán.
- Phân tách quyền đọc và quyền ghi; giới hạn phạm vi tệp, dữ liệu và thời gian truy cập.
- Xử lý lỗi rõ ràng, tránh tiết lộ thông tin nội bộ của hệ thống.

## 5. Ví dụ
Một trợ lý học tập có thể kết nối MCP Server để đọc ghi chú bài giảng (Resource), tìm kiếm tài liệu (Tool) và tạo bản tóm tắt theo mẫu (Prompt). Với thao tác cập nhật ghi chú, hệ thống nên xác nhận dữ liệu đầu vào, thực hiện ghi, sau đó đọc lại để đối soát kết quả.

## 6. Liên hệ với lập trình Python
Trong Python, một Tool có thể được biểu diễn bằng hàm với schema đầu vào rõ ràng. Cần kiểm tra kiểu dữ liệu, xử lý ngoại lệ, giới hạn quyền truy cập và trả về kết quả có cấu trúc để mô hình dễ sử dụng.

## 7. Ghi nhớ
MCP không tự động làm cho hệ thống an toàn hay chính xác. Chất lượng phụ thuộc vào thiết kế schema, kiểm soát quyền, xác thực dữ liệu, cơ chế xác nhận hành động và việc kiểm tra kết quả sau khi ghi.