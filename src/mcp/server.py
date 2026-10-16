
from mcp.server.mcpserver import MCPServer

from src.mcp.logger import setup_logger
from src.mcp.utils import normalize_text, is_empty
from src.mcp.document_manager import (
    load_metadata,
    save_metadata,
    RAW_DIR,
    PROJECT_ROOT,
)
from src.ingestion.retrieving.Retriever import retrieve
from src.models.VectorStore import VectorStore
from src.ingestion.document_loader import load_documents

mcp = MCPServer(
    "student-second-brain",
    description="Student Second Brain MCP server",
)

logger = setup_logger()
logger.info("MCP Server started")


def build_vector_store():
    """Build a fresh search index from the persisted documents."""
    new_store = VectorStore()

    load_documents(
        vector_store=new_store,
        logger=logger,
    )

    return new_store

vector_store = build_vector_store()

def rebuild_vector_store():
    """Replace the current search index after a successful update."""
    global vector_store

    new_store = build_vector_store()
    vector_store = new_store

    logger.info("Search index rebuilt successfully.")



@mcp.tool()
def search(query: str, k: int = 3) -> str:
    """Search indexed documents by query."""

    query = normalize_text(query).lower()

    if is_empty(query):
        return "Error: query must not be empty."

    if k < 1:
        return "Error: k must be at least 1."

    try:
        results = retrieve(
            query,
            store=vector_store,
            top_k=k,
        )

        if not results:
            return "No matching documents found."

        output = []

        for index, item in enumerate(results, start=1):
            parent = item.parent

            output.append(
                f"Result {index}\n"
                f"Score: {item.score:.4f}\n"
                f"Document ID: {parent.doc_id}\n"
                f"Source: {parent.source}\n"
                f"Section: {parent.section}\n"
                f"Content:\n{parent.content}"
            )

        logger.info(
            "search query=%r results=%d",
            query,
            len(results),
        )

        return "\n\n---\n\n".join(output)

    except Exception:
        logger.exception("Search failed")
        return "Error: search failed. Check the server logs."


# ============================================================
# TOOL 2: GET DOCUMENT
# ============================================================

@mcp.tool()
def get(doc_id: str) -> str:
    """Get document metadata and content by document ID."""

    doc_id = normalize_text(doc_id)

    if is_empty(doc_id):
        return "Error: document ID must not be empty."

    try:
        metadata_list = load_metadata()

        metadata = next(
            (
                item
                for item in metadata_list
                if item.get("doc_id") == doc_id
            ),
            None,
        )

        if metadata is None:
            logger.warning("Document not found: %s", doc_id)
            return f"Error: document '{doc_id}' not found."

        source = metadata.get("source", "")
        file_path = (PROJECT_ROOT / source).resolve()

        try:
            file_path.relative_to(RAW_DIR.resolve())
        except ValueError:
            return "Error: invalid document path."

        if not file_path.is_file():
            return f"Error: source file for '{doc_id}' not found."

        if file_path.suffix.lower() not in {".txt", ".md"}:
            return "Error: only TXT and Markdown files are supported."

        content = file_path.read_text(encoding="utf-8")

        logger.info("get doc_id=%s", doc_id)

        return (
            f"Document ID: {doc_id}\n"
            f"Title: {metadata.get('title', '')}\n"
            f"Date: {metadata.get('date', '')}\n"
            f"Version: {metadata.get('version', '')}\n"
            f"Owner: {metadata.get('owner', '')}\n"
            f"Source: {source}\n"
            f"Content:\n{content}"
        )

    except Exception:
        logger.exception("Get document failed")
        return "Error: failed to get document."


# ============================================================
# TOOL 3: UPDATE DOCUMENT
# ============================================================

@mcp.tool()
def update(doc_id: str, title: str, content: str) -> str:
    """Update document title and content, then rebuild the search index."""

    doc_id = normalize_text(doc_id)
    title = normalize_text(title)
    content = content.strip() if content else ""

    if is_empty(doc_id):
        return "Error: doc_id must not be empty."

    if is_empty(title):
        return "Error: title must not be empty."

    if is_empty(content):
        return "Error: content must not be empty."

    try:
        metadata_list = load_metadata()

        metadata = next(
            (
                item
                for item in metadata_list
                if item.get("doc_id") == doc_id
            ),
            None,
        )

        if metadata is None:
            logger.warning("Cannot update missing document: %s", doc_id)
            return f"Error: document '{doc_id}' not found."

        source = metadata.get("source", "")
        file_path = (PROJECT_ROOT / source).resolve()

        try:
            file_path.relative_to(RAW_DIR.resolve())
        except ValueError:
            return "Error: invalid document path."

        if not file_path.is_file():
            return f"Error: source file for '{doc_id}' not found."

        if file_path.suffix.lower() not in {".txt", ".md"}:
            return "Error: only TXT and Markdown files are supported."

        # Save original values for rollback.
        old_content = file_path.read_text(encoding="utf-8")
        old_metadata = [item.copy() for item in metadata_list]

        try:
            # 1. Save new document content.
            file_path.write_text(content, encoding="utf-8")

            # 2. Update metadata.
            metadata["title"] = title

            # 3. Verify metadata and file persistence.
            save_metadata(metadata_list)

            saved_content = file_path.read_text(encoding="utf-8")
            saved_metadata_list = load_metadata()

            saved_metadata = next(
                (
                    item
                    for item in saved_metadata_list
                    if item.get("doc_id") == doc_id
                ),
                None,
            )

            if (
                saved_content != content
                or saved_metadata is None
                or saved_metadata.get("title") != title
            ):
                raise RuntimeError("Update verification failed.")

            # 4. Build a new index before replacing the current one.
            new_store = VectorStore()

            load_documents(
                vector_store=new_store,
                logger=logger,
            )

            # Replace the old index only after rebuilding succeeds.
            global vector_store
            vector_store = new_store

        except Exception:
            # Restore the original document file.
            file_path.write_text(old_content, encoding="utf-8")

            # Restore the original metadata.
            save_metadata(old_metadata)

            logger.exception(
                "Update or index rebuild failed for document %s",
                doc_id,
            )

            return (
                "Error: update or index rebuild failed. "
                "The original document and metadata were restored. "
                "Check the server logs."
            )

        logger.info(
            "Updated document and rebuilt index: %s",
            doc_id,
        )

        return (
            "Update saved, verified, and search index rebuilt.\n"
            f"Document ID: {doc_id}\n"
            f"Title: {title}\n"
            f"Source: {source}"
        )

    except Exception:
        logger.exception("Update failed")
        return "Error: update failed. Check the server logs."


# ============================================================
# 4. RUN MCP SERVER
# ============================================================

if __name__ == "__main__":
    mcp.run()
