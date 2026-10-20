# MCP — Model Context Protocol

## Tổng quan
- **MCP (Model Context Protocol)** là một giao thức mở giúp ứng dụng AI/LLM kết nối theo cách chuẩn hóa với nguồn dữ liệu, công cụ và workflow bên ngoài.
- MCP tách **host/client** (ứng dụng AI) khỏi **server** (dịch vụ cung cấp context hoặc khả năng thao tác), giúp giảm tích hợp riêng lẻ cho từng mô hình.
- MCP không phải là một mô hình AI; đây là lớp giao tiếp và quy ước để mô hình sử dụng context và tool một cách có cấu trúc.

## Các thành phần chính
- **Host:** ứng dụng chứa trải nghiệm AI, ví dụ IDE hoặc chatbot.
- **MCP client:** thành phần trong host duy trì kết nối tới một MCP server.
- **MCP server:** cung cấp các capability cho client, thường gồm:
  - **Resources:** dữ liệu/context để đọc, chẳng hạn tài liệu, file hoặc schema.
  - **Tools:** hàm mà mô hình có thể yêu cầu gọi để thực hiện hành động hoặc truy vấn.
  - **Prompts:** template/prompt được server cung cấp để tái sử dụng.

## Luồng hoạt động điển hình
1. Client kết nối và thương lượng capability với server.
2. Client khám phá resources, tools và prompts khả dụng.
3. Ứng dụng đưa mô tả tool cùng context phù hợp vào phiên làm việc của LLM.
4. LLM yêu cầu gọi tool khi cần; client chuyển yêu cầu đến server.
5. Server kiểm tra đầu vào, thực thi, rồi trả kết quả có cấu trúc cho client/LLM.

## Ví dụ khái niệm
Một MCP server cho cơ sở dữ liệu có thể cung cấp resource là schema và tool `search_products(query, limit)`. LLM không truy cập trực tiếp database; nó yêu cầu client gọi tool với tham số đã khai báo, sau đó dùng kết quả để tạo câu trả lời.

## Thiết kế tool an toàn
- Khai báo **tên, mô tả, input schema và output** rõ ràng; dùng kiểu dữ liệu chặt chẽ.
- Xác thực tham số ở server, giới hạn quyền truy cập và tránh cấp quyền rộng không cần thiết.
- Với thao tác có side effect (ghi/xóa/gửi dữ liệu), yêu cầu xác nhận người dùng và ghi log.
- Không đưa secret/API key vào prompt hoặc kết quả tool; lọc dữ liệu nhạy cảm trước khi trả về model.
- Xử lý timeout, lỗi, retry và kết quả lớn bằng phân trang/giới hạn kích thước.

## Liên hệ với kiến thức Python tuần 1
- Tool arguments/results thường được biểu diễn bằng **dict và JSON**.
- Có thể dùng `@dataclass` và type hints để model hóa request/response của tool.
- Dùng `list` cho danh sách kết quả, `dict` cho metadata/record, `tuple` cho khóa bất biến và `set` để khử trùng lặp.
- Khi serialize kiểu như `datetime`, cần chuyển sang dạng JSON-compatible (ví dụ ISO 8601) hoặc dùng custom encoder.

## Tóm tắt 3 ý chính
1. MCP là giao thức chuẩn hóa kết nối AI/LLM với dữ liệu, công cụ và workflow bên ngoài; MCP không phải là mô hình AI.
2. Kiến trúc MCP gồm Host, MCP Client và MCP Server; server cung cấp Resources, Tools và Prompts.
3. Tool MCP phải được thiết kế an toàn bằng schema rõ ràng, xác thực đầu vào, giới hạn quyền, bảo vệ secret và yêu cầu xác nhận với thao tác có side effect.

## Ghi nhớ
MCP chuẩn hóa cách ứng dụng AI khám phá và sử dụng context/tools, nhưng **không tự động bảo đảm an toàn**. Quyền hạn, xác thực, phê duyệt hành động và kiểm tra dữ liệu vẫn phải được thiết kế ở client/server.

## Cập nhật
- Khi tích hợp MCP, cần phân biệt rõ **Resources** (dữ liệu/context để đọc), **Tools** (hành động hoặc truy vấn có thể thực thi) và **Prompts** (mẫu hướng dẫn tái sử dụng).
- Client/server nên áp dụng nguyên tắc **quyền tối thiểu**, xác thực đầu vào, xác nhận các thao tác có side effect, ghi log và bảo vệ secret.
- MCP chuẩn hóa việc khám phá và sử dụng context/tools nhưng không tự động bảo đảm an toàn; bảo mật vẫn thuộc trách nhiệm của client/server.