from src.mcp.document_manager import (
    load_metadata,
    PROJECT_ROOT,
    RAW_DIR,
)
from src.ingestion.chunking.Chunking_helper import loaddoc


def load_documents(vector_store, logger) -> None:
    """Load registered text documents into the vector store."""

    metadata_list = load_metadata()

    for metadata in metadata_list:
        doc_id = metadata.get("doc_id", "")
        source = metadata.get("source", "")

        if not doc_id or not source:
            logger.warning("Invalid document metadata: %s", metadata)
            continue

        file_path = (PROJECT_ROOT / source).resolve()

        # Chỉ cho phép đọc file bên trong data/raw.
        try:
            file_path.relative_to(RAW_DIR.resolve())
        except ValueError:
            logger.warning("Invalid document path: %s", source)
            continue

        if not file_path.is_file():
            logger.warning("Document file not found: %s", file_path)
            continue

        try:
            # loaddoc hiện đọc file từ data/raw/{filename}.
            document = loaddoc(file_path.name)

            if document is None:
                logger.warning("Could not load document: %s", source)
                continue

            # Đồng bộ thông tin từ metadata đã đăng ký.
            document.doc_id = doc_id
            document.title = metadata.get(
                "title",
                document.title,
            )
            document.source = source

            vector_store.add(document)

            logger.info(
                "Loaded document: %s",
                doc_id,
            )

        except Exception:
            logger.exception(
                "Failed to load document: %s",
                source,
            )


