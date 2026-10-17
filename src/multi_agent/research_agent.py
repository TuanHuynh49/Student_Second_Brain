
from mcp import Client, StdioServerParameters


class ResearchAgent:
    def __init__(self):
        self.name = "Research Agent"

    def _get_server(self):
        return StdioServerParameters(
            command="uv",
            args=["run", "python", "-m", "src.mcp.server"]
        )

    async def _get_tool_names(self, client) -> set[str]:
        """Khám phá các MCP tools server đang cung cấp."""
        response = await client.list_tools()
        return {tool.name for tool in response.tools}

    def _extract_text(self, result) -> str:
        """Chuyển kết quả MCP thành chuỗi văn bản."""
        parts = []

        for block in result.content or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)

        return "\n".join(parts)

    async def research(self, query: str, top_k: int = 3) -> dict:
        query = query.strip()

        if not query:
            raise ValueError("Query không được để trống.")

        if not 1 <= top_k <= 10:
            raise ValueError("top_k phải nằm trong khoảng từ 1 đến 10.")

        async with Client(self._get_server()) as client:
            # Khám phá tools từ MCP server.
            tool_names = await self._get_tool_names(client)

            if "search" not in tool_names:
                return {
                    "task": "search_documents",
                    "query": query,
                    "evidence": [],
                    "status": "error",
                    "error": "MCP server không cung cấp tool search."
                }

            # Gọi search để thu thập bằng chứng.
            result = await client.call_tool(
                "search",
                {
                    "query": query,
                    "top_k": top_k
                }
            )

            content = self._extract_text(result)

            if getattr(result, "is_error", False):
                return {
                    "task": "search_documents",
                    "query": query,
                    "evidence": [content] if content else [],
                    "status": "error",
                    "error": content or "MCP search thất bại."
                }

            return {
                "task": "search_documents",
                "query": query,
                "evidence": [content] if content else [],
                "status": "success" if content else "not_found"
            }
