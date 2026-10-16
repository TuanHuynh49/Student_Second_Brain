
import asyncio

from mcp import Client, StdioServerParameters


# ============================================================
# HELPER: PRINT TOOL RESULT
# ============================================================

def print_result(test_name: str, result) -> None:
    print("\n" + "=" * 60)
    print(f"TEST: {test_name}")
    print("=" * 60)

    print(f"MCP is_error: {result.is_error}")

    for block in result.content or []:
        if getattr(block, "text", None):
            print(block.text)

    if not result.content:
        print("No content returned.")


# ============================================================
# MAIN TEST
# ============================================================

async def main():
    server = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "src.mcp.server"],
    )

    async with Client(server) as client:

        # ----------------------------------------------------
        # 1. DISCOVER AVAILABLE TOOLS
        # ----------------------------------------------------

        tools = (await client.list_tools()).tools

        print(f"\nDiscovered {len(tools)} tool(s):")

        for tool in tools:
            print(f"\nTool: {tool.name}")
            print(f"Description: {tool.description}")
            print(f"Input schema: {tool.input_schema}")

        available_tools = {tool.name for tool in tools}

        required_tools = {"search", "get", "update"}
        missing_tools = required_tools - available_tools

        if missing_tools:
            print(f"\nMissing tools: {missing_tools}")
            return

        # ----------------------------------------------------
        # 2. CONFIGURATION
        # ----------------------------------------------------

        # IMPORTANT:
        # Change this to a real doc_id in data/documents.json.
        doc_id = "test"

        updated_title = "MCP Update Test"
        updated_content = (
            "This document was updated through the MCP client. "
            "It is used to verify persistent updates and search indexing."
        )

        # ----------------------------------------------------
        # 3. TEST SEARCH WITH A NORMAL QUERY
        # ----------------------------------------------------

        result = await client.call_tool(
            "search",
            {
                "query": "trinh la gi",
                "k": 1,
            },
        )
        print_result("1. SEARCH - normal query", result)

        # ----------------------------------------------------
        # 4. TEST GET BEFORE UPDATE
        # ----------------------------------------------------

        result = await client.call_tool(
            "get",
            {
                "doc_id": doc_id,
            },
        )
        print_result("2. GET - before update", result)

        # ----------------------------------------------------
        # 5. TEST UPDATE
        # ----------------------------------------------------

        result = await client.call_tool(
            "update",
            {
                "doc_id": doc_id,
                "title": updated_title,
                "content": updated_content,
            },
        )
        print_result("3. UPDATE - existing document", result)

        # ----------------------------------------------------
        # 6. TEST GET AFTER UPDATE
        # ----------------------------------------------------

        result = await client.call_tool(
            "get",
            {
                "doc_id": doc_id,
            },
        )
        print_result("4. GET - verify updated content", result)

        # ----------------------------------------------------
        # 7. TEST SEARCH FOR THE NEW CONTENT
        # ----------------------------------------------------

        result = await client.call_tool(
            "search",
            {
                "query": "verify persistent updates and search indexing",
                "k": 3,
            },
        )
        print_result("5. SEARCH - updated content", result)

        # ----------------------------------------------------
        # 8. TEST GET WITH NONEXISTENT DOCUMENT ID
        # ----------------------------------------------------

        result = await client.call_tool(
            "get",
            {
                "doc_id": "doc_DOES_NOT_EXIST",
            },
        )
        print_result("6. GET - nonexistent document", result)

        # ----------------------------------------------------
        # 9. TEST UPDATE WITH NONEXISTENT DOCUMENT ID
        # ----------------------------------------------------

        result = await client.call_tool(
            "update",
            {
                "doc_id": "doc_DOES_NOT_EXIST",
                "title": "Invalid Update",
                "content": "This document does not exist.",
            },
        )
        print_result("7. UPDATE - nonexistent document", result)

        # ----------------------------------------------------
        # 10. TEST SEARCH WITH EMPTY QUERY
        # ----------------------------------------------------

        result = await client.call_tool(
            "search",
            {
                "query": "",
                "k": 1,
            },
        )
        print_result("8. SEARCH - empty query", result)

        # ----------------------------------------------------
        # 11. TEST GET WITH EMPTY DOCUMENT ID
        # ----------------------------------------------------

        result = await client.call_tool(
            "get",
            {
                "doc_id": "",
            },
        )
        print_result("9. GET - empty document ID", result)

        # ----------------------------------------------------
        # 12. TEST UPDATE WITH EMPTY TITLE
        # ----------------------------------------------------

        result = await client.call_tool(
            "update",
            {
                "doc_id": doc_id,
                "title": "",
                "content": "This update should be rejected.",
            },
        )
        print_result("10. UPDATE - empty title", result)

        # ----------------------------------------------------
        # 13. TEST SEARCH WITH INVALID K
        # ----------------------------------------------------

        result = await client.call_tool(
            "search",
            {
                "query": "test query",
                "k": 0,
            },
        )
        print_result("11. SEARCH - invalid k", result)

        print("\n" + "=" * 60)
        print("ALL TEST CALLS COMPLETED")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())