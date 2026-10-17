from src.models.Schemas import Tool


def mcp_result_to_text(result) -> str:
    """Chuyển kết quả MCP thành chuỗi cho LLM."""
    parts = []

    for block in result.content or []:
        text = getattr(block, "text", None)

        if text:
            parts.append(text)

    content = "\n".join(parts)

    if getattr(result, "is_error", False):
        return f"Error: {content or 'MCP tool failed.'}"

    return content or "Tool executed but returned no content."


async def call_mcp_tool(client, tool_name: str, arguments: dict) -> str:
    """Gọi MCP tool bất đồng bộ và chuẩn hóa kết quả."""
    try:
        result = await client.call_tool(tool_name, arguments)
        return mcp_result_to_text(result)
    except Exception as exc:
        return f"Error: MCP tool '{tool_name}' failed: {exc}"


async def discover_mcp_tools(client) -> list[Tool]:
    """Khám phá tool từ MCP Server và chuyển thành Tool."""
    response = await client.list_tools()
    tools = []

    for mcp_tool in response.tools:
        schema = mcp_tool.input_schema or {
            "type": "object",
            "properties": {},
        }

        async def invoke(
            _name=mcp_tool.name,
            **kwargs,
        ):
            return await call_mcp_tool(
                client,
                _name,
                kwargs,
            )

        tools.append(
            Tool(
                name=mcp_tool.name,
                description=mcp_tool.description or "",
                parameters=schema,
                fn=invoke,
            )
        )

    return tools