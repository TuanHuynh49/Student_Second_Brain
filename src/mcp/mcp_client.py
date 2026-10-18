import asyncio
import os
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

# Đảm bảo Python luôn tìm thấy thư mục gốc src/ dù chạy ở bất kỳ đâu
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 1. HÀM IN KẾT QUẢ TỪ MCP SERVER
# ============================================================

def print_result(test_name: str, result) -> None:
    print("\n" + "=" * 60)
    print(f"📊 KẾT QUẢ: {test_name}")
    print("=" * 60)
    print(f"MCP is_error: {result.is_error}")

    has_content = False
    for block in result.content or []:
        if getattr(block, "text", None):
            print(block.text)
            has_content = True

    if not has_content:
        print("Không có nội dung trả về.")


# ============================================================
# 2. HÀM GỌI TOOL CHUẨN CỦA MCP SDK
# ============================================================

async def call_and_print(client, tool_name: str, arguments: dict, test_name: str):
    # Gọi hàm call_tool theo đúng chuẩn MCP SDK
    result = await client.call_tool(tool_name, arguments)
    print_result(test_name, result)
    return result


# ============================================================
# 3. CHẾ ĐỘ TỰ NHẬP TAY LINH HOẠT (CHO THẦY TEST TẠI CHỖ)
# ============================================================

async def run_interactive_mode(client):
    while True:
        print("\n" + "─" * 60)
        print("CHỌN CÔNG CỤ MCP MUỐN THỰC THI:")
        print("  [1] search — Tìm kiếm văn bản ngữ nghĩa (Hybrid / Dense + BM25)")
        print("  [2] get    — Đọc toàn bộ nội dung tài liệu theo Document ID")
        print("  [3] update — Cập nhật nội dung tài liệu + Tự động kiểm chứng")
        print("  [0] Thoát chương trình")
        print("─" * 60)

        chon = input("👉 Nhập lựa chọn (0-3): ").strip()

        if chon == "0" or chon.lower() == "exit":
            print("\n👋 Đã đóng kết nối MCP Client 2. Tạm biệt!")
            break

        # ── 1. TEST SEARCH ──
        elif chon == "1":
            q = input("\n🔍 Nhập câu hỏi tìm kiếm: ").strip()
            if not q:
                print("⚠️  Vui lòng không để trống câu hỏi.")
                continue

            k = input("🔢 Số lượng kết quả top_k (nhấn Enter để mặc định 3): ").strip()
            top_k = int(k) if k.isdigit() else 3

            await call_and_print(client, "search", {"query": q, "top_k": top_k}, f"SEARCH: '{q}' (top_k={top_k})")

        # ── 2. TEST GET ──
        elif chon == "2":
            print("\n💡 Gợi ý Document ID: doc_DOC0001, doc_DOC0002, doc_DOC0003, ..., doc_DOC0008")
            d_id = input("🆔 Nhập Document ID cần đọc: ").strip()
            if not d_id:
                print("⚠️  Document ID không được để trống.")
                continue

            await call_and_print(client, "get", {"doc_id": d_id}, f"GET: {d_id}")

        # ── 3. TEST UPDATE + VERIFY ──
        elif chon == "3":
            print("\n💡 Gợi ý Document ID: doc_DOC0001")
            d_id = input("🆔 Nhập Document ID cần cập nhật: ").strip()
            if not d_id:
                print("⚠️  Document ID không được để trống.")
                continue

            print("📝 Nhập hoặc dán nội dung mới (sau khi dán xong, gõ 'END' trên dòng mới rồi nhấn Enter):")
            lines = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                if line.strip() == "END":
                    break
                lines.append(line)

            noi_dung = "\n".join(lines).strip()
            if not noi_dung:
                print("⚠️  Nội dung không được để trống.")
                continue

            # Bước 1: Gọi lệnh update (thao tác ghi)
            await call_and_print(client, "update", {"doc_id": d_id, "content": noi_dung}, f"UPDATE: {d_id}")

            # Bước 2: Tự động gọi lại get để đối soát kiểm chứng (Side-effect + Verification)
            print("\n🔎 Đang tự động gọi lại tool 'get' để đối soát kiểm chứng sau khi cập nhật:")
            await call_and_print(client, "get", {"doc_id": d_id}, f"VERIFY: {d_id}")

        else:
            print("⚠️  Lựa chọn không hợp lệ, vui lòng chọn 1, 2, 3 hoặc 0.")


# ============================================================
# 4. HÀM MAIN KHỞI ĐỘNG CLIENT VÀ KẾT NỐI MCP SERVER
# ============================================================

async def main():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    server = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "src.mcp.server"],
        env=env,
    )

    print("\n╔══════════════════════════════════════════════════════════════════════╗")
    print("║               🛠️  MCP PYTHON CLIENT 2 (INTEROPERABILITY)             ║")
    print("║          Ứng dụng Client thứ 2 độc lập kết nối MCP Server            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print("🔌 Đang kết nối tới MCP Server qua stdio...")

    async with Client(server) as client:
        # Bước 1: Dynamic Discovery - Tự động khám phá danh sách tools
        tools = (await client.list_tools()).tools
        print(f"\n[MCP Discovery] Đã kết nối và tự động khám phá {len(tools)} tools từ Server:")
        for t in tools:
            print(f"   ├─ 🔧 {t.name}: {t.description.strip().splitlines()[0]}")

        # Bước 2: Vào thẳng chế độ tương tác tự nhập tay
        await run_interactive_mode(client)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Client đã dừng.")
