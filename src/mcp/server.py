
import logging


from mcp.server.mcpserver import MCPServer

from logger import setup_logger
from utils import normalize_text, is_empty
import models.Document 


mcp = MCPServer(
    "student-second-brain",
    description="Mock MCP server for Student Second Brain"
)

logger = setup_logger()
logger.info("MCP Server started")


@mcp.tool()
def search(query: str, k: int) -> str:
    """Search mock documents by title or content."""
    query = normalize_text(query).lower()

    if is_empty(query):
        return "Error: query must not be empty."

    result = retrieve(query, k = 5)

    logger.info("search query=%r results=%d", query, len(result))

    if not result:
        return "No matching documents found."

    return "\n\n".join(result)



@mcp.tool()
def get(doc_id: str) -> str:
    """Get a mock document by its ID."""
    doc_id = normalize_text(doc_id).upper()

    if is_empty(doc_id):
        return "Error: document ID must not be empty."

    doc = 
    if doc is None:
        logger.warning("get document not found: %s", doc_id)
        return f"Error: document {doc_id} not found."
    logger.info("get doc_id=%s", doc_id)
    
    return (
        f'ID: {doc["doc_id"]}\n'
        f'Title: {doc["title"]}\n'
        f'Content: {doc["content"]}\n'
        f'Source: {doc["source"]}\n'
        f'Section: {doc["section"]}'
    )
    



@mcp.tool()
def update(doc_id: str, title: str, content: str) -> str:
    """Update an existing mock document."""
    doc_id = normalize_text(doc_id)
    title = normalize_text(title)
    content = normalize_text(content)

    if is_empty(doc_id):
        logger.warning("update rejected: empty doc_id")
        return "Error: doc_id must not be empty."

    if doc_id not in DOCUMENTS:
        logger.warning("update rejected: document not found: %s", doc_id)
        return f"Error: document not found: {doc_id}"

    if is_empty(title):
        logger.warning("update rejected: empty title")
        return "Error: title must not be empty."

    if is_empty(content):
        logger.warning("update rejected: empty content")
        return "Error: content must not be empty."

    DOCUMENTS[doc_id]["title"] = title
    DOCUMENTS[doc_id]["content"] = content

    logger.info("update doc_id=%s title=%r", doc_id, title)

    return f"Updated successfully: {doc_id}"


    


if __name__ == "__main__":
    mcp.run()
