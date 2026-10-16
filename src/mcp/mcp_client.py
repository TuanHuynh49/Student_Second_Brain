
import asyncio

from mcp import Client, StdioServerParameters

# ============================================================
# 1. HELPER: IN KET QUA
# ============================================================

def print_result(test_name: str, result) -> None:
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)

    print(f"MCP is_error: {result.is_error}")

    for block in result.content or []:
        if getattr(block, "text", None):
            print(block.text)

    if not result.content:
        print("No content returned.")


# ============================================================
# 2. GOI TOOL
# ============================================================

async def call_and_print(client, tool_name: str, arguments: dict, test_name: str):
    result = await client.call_tool(tool_name, arguments)
    print_result(test_name, result)
    return result


# ============================================================
# 3. MAIN TEST
# ============================================================

async def main():
    server = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "src.mcp.server"]
    )

    async with Client(server) as client:

        # ----------------------------------------------------
        # TEST 1: DISCOVER TOOLS
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

        # ID lấy từ document_store_cache.json của bạn
        doc_id = "doc_test"

        # ----------------------------------------------------
        # TEST 2: SEARCH
        # ----------------------------------------------------

        await call_and_print(
            client,
            "search",
            {
                "query": "What does no cap mean?",
                "top_k": 3,
            },
            "1. SEARCH - normal query",
        )

        # ----------------------------------------------------
        # TEST 3: GET EXISTING DOCUMENT
        # ----------------------------------------------------

        await call_and_print(
            client,
            "get",
            {
                "doc_id": doc_id,
            },
            "2. GET - existing document",
        )

        # ----------------------------------------------------
        # TEST 4: GET NONEXISTENT DOCUMENT
        # ----------------------------------------------------

        await call_and_print(
            client,
            "get",
            {
                "doc_id": "doc_DOES_NOT_EXIST",
            },
            "3. GET - nonexistent document",
        )

        # ----------------------------------------------------
        # TEST 5: SEARCH WITH EMPTY QUERY
        # ----------------------------------------------------

        await call_and_print(
            client,
            "search",
            {
                "query": "",
                "top_k": 3,
            },
            "4. SEARCH - empty query",
        )

        # ----------------------------------------------------
        # TEST 6: GET WITH EMPTY ID
        # ----------------------------------------------------

        await call_and_print(
            client,
            "get",
            {
                "doc_id": "",
            },
            "5. GET - empty document ID",
        )

        # ----------------------------------------------------
        # TEST 7: UPDATE WITH NONEXISTENT ID
        # ----------------------------------------------------

        await call_and_print(
            client,
            "update",
            {
                "doc_id": "doc_DOES_NOT_EXIST",
                "content": "This document does not exist.",
            },
            "6. UPDATE - nonexistent document",
        )

        # ----------------------------------------------------
        # TEST 8: UPDATE WITH EMPTY CONTENT
        # ----------------------------------------------------

        await call_and_print(
            client,
            "update",
            {
                "doc_id": doc_id,
                "content": "",
            },
            "7. UPDATE - empty content",
        )

        # ----------------------------------------------------
        # TEST 9: OPTIONAL UPDATE REAL DOCUMENT
        # ----------------------------------------------------

        print("\n" + "=" * 70)
        print("OPTIONAL TEST: UPDATE REAL DOCUMENT")
        print("=" * 70)
        print("Can thi thay doi truc tiep file data/raw/test.txt.")

        confirm = input(
            "Ban co muon cap nhat noi dung that khong? (yes/no): "
        ).strip().lower()

        if confirm == "yes":
            new_content = (
                "# MCP Update Test\n\n"
                "This document was updated through the MCP client. "
                "The purpose is to test document updating, cache persistence, "
                "and search indexing."
            )

            await call_and_print(
                client,
                "update",
                {
                    "doc_id": doc_id,
                    "content": new_content,
                },
                "8. UPDATE - existing document",
            )

            await call_and_print(
                client,
                "get",
                {
                    "doc_id": doc_id,
                },
                "9. GET - verify updated document",
            )

            await call_and_print(
                client,
                "search",
                {
                    "query": "test document updating cache persistence",
                    "top_k": 3,
                },
                "10. SEARCH - updated content",
            )
        else:
            print("Bo qua update. Tai lieu goc duoc giu nguyen.")

        print("\n" + "=" * 70)
        print("ALL TEST CALLS COMPLETED")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
