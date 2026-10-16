
import asyncio

from mcp import Client, StdioServerParameters


class ResearchAgent:
    def __init__(self):
        self.name = "Research Agent"

    async def research(self, query: str, top_k: int = 3) -> dict:
        if not query.strip():
            raise ValueError("Query không được để trống.")

        server = StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "src.mcp.server"]
        )

        async with Client(server) as client:
            # Gọi MCP tool search
            result = await client.call_tool(
                "search",
                {
                    "query": query,
                    "top_k": top_k
                }
            )

            # Chuyển kết quả MCP thành dữ liệu dễ sử dụng
            evidence = []

            for block in result.content or []:
                if getattr(block, "text", None):
                    evidence.append(block.text)

            return {
                "task": "search_documents",
                "query": query,
                "evidence": evidence,
                "status": "error" if result.is_error else (
                    "success" if evidence else "not_found"
                )
            }
