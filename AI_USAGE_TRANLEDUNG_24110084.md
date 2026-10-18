# AI_USAGE — Nhật ký sử dụng AI

**Đồ án:** AIPR, đề tài T3 "Trợ lý học tập trên lesson plan môn học"
**Người viết:** Trần Lê Dũng (MSSV 24110084), vai trò A trong nhóm 3 người (dữ liệu, ingestion, chunking, embedding, kho dữ liệu, truy xuất)
**Công cụ:** Claude (Anthropic). Mô hình cấu hình cho phiên: `claude-sonnet-5-5` (mô hình thực tế phục vụ từng lượt có thể khác)
**Thời gian:** 12/10/2026 đến 17/10/2026

> Các prompt dưới đây được **tóm tắt**, không phải nguyên văn. Nguyên văn nằm trong lịch sử hội thoại.

---

## 1. Tóm tắt cách dùng AI

- **Ý tưởng refactor:** đưa code của mình cho AI xem, nhờ chỉ lỗi và gợi ý cách tổ chức lại. Việc sửa code do mình làm, sau đó gửi lại để review tiếp.
- **Khi bí:** nhờ AI viết một số tính năng phụ trợ (đọc file, tách đoạn và chunk mẫu), rồi mình đọc, chỉnh và viết lại theo cách của mình.
- **Kiến trúc:** do mình quyết định. AI chỉ là nguồn tham khảo (so sánh phương án, tìm bài viết, đề xuất cách chia thư mục).
- **Học và hiểu đề:** nhờ AI giải thích khái niệm (UUID, `re`, các số đo đánh giá RAG) và giải thích các yêu cầu trong đề.

Từ 13/10, mình yêu cầu AI chuyển sang vai trò cố vấn (chia bài toán thành bước, đặt câu hỏi, không đưa sẵn code). Ngoại lệ có chủ ý là phần store ở dòng 14 bên dưới, ngoài ra AI chỉ đưa vài đoạn minh họa ngắn (ví dụ hằng số đường dẫn).

---

## 2. Nhật ký chi tiết

| # | Ngày | Mục đích | Prompt (tóm tắt) | Đầu ra của AI | Cách mình dùng |
|---|---|---|---|---|---|
| 1 | 12/10 | Phân việc | Gửi sơ đồ kiến trúc và bảng thư mục, nhờ chia việc cho nhóm 3 người | Chia 3 vai A, B, C theo thư mục và trình tự làm | Tham khảo để nhóm thống nhất, nhận vai A |
| 2 | 12/10 | Lộ trình | Nhờ lập lộ trình 3 ngày cho cả nhóm | Lộ trình 3 ngày và danh sách phần cắt giảm khi trễ | Tham khảo |
| 3 | 13/10 | Chiến thuật ngày 1 | Hỏi chiến thuật cho từng việc của người A | Hướng dẫn 4 việc: schema, ingestion, embedding, kiểm tra | Tham khảo |
| 4 | 13/10 | Tìm tài liệu | Hỏi có bài viết nào về cách thiết kế model Document và Chunk | Tìm web, tóm tắt các nguồn (Airbyte, Microsoft Learn, ...) | Tham khảo khi chọn trường metadata |
| 5 | 13/10 | Review thiết kế | Dán `Document` và `DocumentChunk`, hỏi đã ổn chưa với Parent-Child | Chỉ lỗi thứ tự trường dataclass, đề xuất `ParentChunk`, `ChildChunk`, `RetrievedChunk` | Áp dụng và chỉnh lại các trường (các class hiện có trong repo) |
| 6 | 13/10 | So sánh phương án | Hai class phẳng hay một class đệ quy | Khuyên dùng hai class phẳng, nêu khi nào nên dùng đệ quy | Chọn hai class phẳng |
| 7 | 13/10 | Khái niệm | UUID là gì | Giải thích và gợi ý id ổn định theo hash | Không dùng `uuid`, tự đặt id khi xử lý tài liệu |
| 8 | 13/10 | Quy ước nhóm | Việc 1 xong chưa, "bước chốt" với nhóm là gì, đặt `retrieve` ở đâu | Giải thích hợp đồng `retrieve(Query) -> list[RetrievedChunk]` và vị trí `src/rag/` | Tham khảo |
| 9 | 13/10 | Tính năng mẫu | Nhờ làm Việc 2 (đọc file và chunk) | Mã mẫu loader và chunker hai tầng, kèm script kiểm tra | Dùng làm cơ sở, sau đó tự viết lại thành `Chunking_helper.py` |
| 10 | 13/10 | Đổi cách làm việc | Yêu cầu AI không đưa code, chỉ cố vấn | AI chia bài toán thành bước và đặt câu hỏi gợi mở | Tự viết code từ đây |
| 11 | 14/10, 15/10 | Review store | Dán `DocumentStore`, hỏi thiết kế truy vấn có tối ưu không, VectorStore kế thừa hay không | Giải thích truy xuất đi từ chunk con lên cha, chỉ lỗi dataclass, so sánh kế thừa và composition | Tự thiết kế lại các dict, giữ `VectorStore` kế thừa `DocumentStore` |
| 12 | 14/10 đến 16/10 | Review code | Nhờ xem `Chunking_helper.py`, store, embedding, Jina wrapper, sơ đồ lớp | Danh sách lỗi theo mức nghiêm trọng và câu hỏi gợi ý hướng sửa | Tự sửa qua nhiều vòng review |
| 13 | 15/10 | Khái niệm | Cách dùng `re` | Bảng hàm, ký hiệu và các bẫy thường gặp | Tham khảo |
| 14 | 15/10 | Thiết kế store (một lần) | Nhờ AI thiết kế store, "chỉ lần này thôi" | `DocumentStore`, `VectorStore`, `retriever.py` và 14 test, chạy bằng embedding giả | **[Cần điền: dùng nguyên / đã chỉnh sửa / chỉ tham khảo]** |
| 15 | 15/10 | Metadata | Cách trích `doc_id`, `title`, `date`, `version`, `owner` | Nguồn trích theo từng định dạng file và các bẫy | Tham khảo |
| 16 | 16/10 | Cấu trúc thư mục | Dán cây thư mục, nhờ sắp xếp lại | Cây thư mục đích và bảng di chuyển file | Tham khảo |
| 17 | 16/10 | Vị trí lưu và cấu hình | Nơi lưu file JSON chunk, nơi để cấu hình cosine, BM25, Hybrid, nơi đặt code ba cách tìm kiếm | Đề xuất `data/index/`, một file cấu hình dùng chung, `rag/retrieval/` | Tham khảo |
| 18 | 16/10 | Hiểu yêu cầu đề | Nhờ giải thích các việc làm thêm (+1) | Giải thích từng việc và gợi ý phân việc | Tham khảo |
| 19 | 17/10 | Học | Nhờ dạy nội dung slide tuần 5 (đánh giá RAG) | Bài giảng tóm tắt, chỉ ra vài chỗ chưa nhất quán trong slide, câu hỏi tự kiểm tra | Học, chưa dùng làm code |
| 20 | 17/10 | Tài liệu | Nhờ viết time line sử dụng | `AI_USAGE.md` | Rà lại và điền các chỗ còn trống |

---

## 3. Phần nào do AI, phần nào do mình

| Thành phần | Nguồn | Ghi chú |
|---|---|---|
| Chọn kiến trúc Parent-Child | Mình | AI chỉ nhận xét và so sánh phương án |
| Chiến lược chunking (heading cho `.md`, recursive cho `.txt`, thử overlap) | Mình | AI nêu câu hỏi cần cân nhắc |
| Lớp `ParentChunk`, `ChildChunk`, `RetrievedChunk`, `Query` | AI đề xuất, mình chỉnh | Mình đã chỉnh lại các trường theo bài toán |
| Loader và chunker mẫu | AI viết mẫu, mình viết lại | Bản trong repo là `Chunking_helper.py` |
| `Chunking_helper.py` (bản hiện tại) | Mình | AI chỉ review |
| `embedding_helper.py`, `jina_embeddings.py` | Không do AI tạo trong phiên này | AI chỉ review |
| `DocumentStore`, `VectorStore`, `retriever.py`, `test_store.py` | AI viết bản tham chiếu | Xem dòng 14: **[Cần điền trạng thái]** |
| Cấu trúc thư mục, vị trí cấu hình, index, ba cách tìm kiếm | AI đề xuất, mình và nhóm quyết định | |
| Nội dung đánh giá RAG (slide tuần 5) | AI giảng lại | Chỉ để học |

---
