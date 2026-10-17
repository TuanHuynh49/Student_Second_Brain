
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
    
    
    def _parse_evidence(self, content: str) -> list[dict]:
        """Tách kết quả MCP thành từng evidence có metadata."""

        import re

        blocks = re.split(
            r"(?m)(?=^\[Kết quả \d+\])",
            content.strip()
        )

        evidence_list = []

        for block in blocks:
            block = block.strip()

            if not re.match(r"^\[Kết quả \d+\]", block):
                continue

            def extract(pattern):
                match = re.search(pattern, block, re.MULTILINE)
                return match.group(1).strip() if match else None

            score_text = extract(r"Score:\s*([^\n]+)")

            try:
                score = float(score_text) if score_text else None
            except ValueError:
                score = None

            doc_id = extract(r"Doc ID:\s*([^\n]+)")
            section = extract(r"Parent Section:\s*([^\n]+)")

            content_match = re.search(
                r"Parent Content:\s*(.*?)(?=\nSố lượng matched children:|\Z)",
                block,
                re.DOTALL
            )

            parent_content = (
                content_match.group(1).strip()
                if content_match else ""
            )

            evidence_list.append({
                "score": score,
                "doc_id": doc_id,
                "source": None,
                "section": section,
                "content": parent_content,
                "raw": block
            })

        return evidence_list



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
                    "evidence": [],
                    "status": "error",
                    "error": content or "MCP search thất bại."
                }

            evidence = self._parse_evidence(content)

            if not evidence and content:
                # Giữ lại dữ liệu gốc nếu định dạng MCP
                # chưa khớp với cấu trúc Result/Score/Content.
                evidence = [{
                    "score": None,
                    "doc_id": None,
                    "source": None,
                    "section": None,
                    "content": content,
                    "raw": content
                }]

            return {
                "task": "search_documents",
                "query": query,
                "evidence": evidence,
                "status": "success" if evidence else "not_found"
            }
