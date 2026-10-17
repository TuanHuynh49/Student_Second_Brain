import contextlib
import sys
import os
from pathlib import Path
import json

from mcp.server.mcpserver import MCPServer

from src.mcp.logger import setup_logger
from src.mcp.utils import normalize_text, is_empty
from src.ingestion.chunking.Chunking_helper import loaddoc
from src.rag.vectordb.VectorStore import VectorStore
from src.rag.retrieval.Retriever import retrieve
from src.models.Query import Query


# ============================================================
# 1. CẤU HÌNH
# ============================================================

mcp = MCPServer("student-second-brain")
logger = setup_logger()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
STORE_PATH = PROJECT_ROOT / "document_store_cache.json"


# ============================================================
# 2. LOAD / BUILD VECTOR STORE
# ============================================================

def get_raw_files_signature() -> dict[str, int]:
    """
    Lấy thời gian sửa đổi của các file TXT.
    Nếu file thay đổi, signature sẽ thay đổi theo.
    """
    signature = {}

    if not RAW_DIR.is_dir():
        return signature

    for file_path in sorted(RAW_DIR.glob("*.txt")):
        relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()
        signature[relative_path] = file_path.stat().st_mtime_ns

    return signature


def build_vector_store() -> VectorStore:
    """
    Đọc các file TXT, tạo chunks và embeddings,
    sau đó lưu VectorStore cùng signature của các file.
    """
    store = VectorStore()

    if not RAW_DIR.is_dir():
        logger.warning("Không tìm thấy thư mục: %s", RAW_DIR)
        return store

    old_cwd = Path.cwd()

    try:
        os.chdir(PROJECT_ROOT)

        for file_path in sorted(RAW_DIR.glob("*.txt")):
            try:
                document = loaddoc(file_path.name)

                if document is None:
                    logger.warning("Không đọc được file: %s", file_path)
                    continue

                document.source = (
                    file_path.relative_to(PROJECT_ROOT).as_posix()
                )

                store.add(document)
                logger.info("Đã thêm tài liệu: %s", file_path.name)

            except Exception:
                logger.exception(
                    "Lỗi khi xử lý file: %s", file_path.name
                )

    finally:
        os.chdir(old_cwd)

    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Lưu VectorStore trước.
    with contextlib.redirect_stdout(sys.stderr):
        store.save(str(STORE_PATH))

    # Lưu thời gian sửa đổi của các file TXT vào cache.
    with open(STORE_PATH, "r", encoding="utf-8") as file:
        cache_data = json.load(file)

    cache_data["_raw_files_signature"] = get_raw_files_signature()

    with open(STORE_PATH, "w", encoding="utf-8") as file:
        json.dump(cache_data, file, ensure_ascii=False, indent=4)

    logger.info(
        "Đã tạo cache: %s documents, %s child chunks",
        len(store.documents),
        len(store.child_chunks),
    )

    return store



def load_vector_store() -> VectorStore:
    """
    Load cache nếu dữ liệu TXT chưa thay đổi.
    Nếu TXT thay đổi hoặc chưa có cache thì xây dựng lại.
    """
    if not STORE_PATH.is_file():
        logger.info("Chưa có cache, bắt đầu tạo VectorStore.")
        return build_vector_store()

    try:
        with open(STORE_PATH, "r", encoding="utf-8") as file:
            cache_data = json.load(file)

        cached_signature = cache_data.get("_raw_files_signature")

        current_signature = get_raw_files_signature()

        if cached_signature != current_signature:
            logger.info(
                "File TXT đã thay đổi. Đang xây dựng lại VectorStore."
            )
            return build_vector_store()

        logger.info("Đang tải VectorStore từ cache: %s", STORE_PATH)

        with contextlib.redirect_stdout(sys.stderr):
            return VectorStore.load(str(STORE_PATH))

    except (OSError, json.JSONDecodeError, AttributeError, TypeError):
        logger.exception("Cache không hợp lệ. Đang tạo lại VectorStore.")
        return build_vector_store()


with contextlib.redirect_stdout(sys.stderr):
    vector_store = load_vector_store()


# ============================================================
# 3. HELPER
# ============================================================


def resolve_document_path(source: str) -> Path:
    """
    Chỉ cho phép đọc/ghi file nằm trong data/raw.
    Ngăn đường dẫn thoát ra ngoài thư mục dữ liệu.
    """
    path = (PROJECT_ROOT / source).resolve()
    raw_root = RAW_DIR.resolve()

    if not path.is_relative_to(raw_root):
        raise ValueError("Đường dẫn tài liệu không hợp lệ.")

    if path.suffix.lower() != ".txt":
        raise ValueError("Chỉ hỗ trợ tài liệu TXT.")

    return path


# ============================================================
# 4. TOOL: SEARCH
# ============================================================

@mcp.tool()
def search(query: str, top_k: int = 5) -> str:
    """
    Tìm kiếm các đoạn văn bản liên quan đến câu hỏi.
    """
    if is_empty(query):
        return "Vui lòng nhập nội dung cần tìm kiếm."

    try:
        qr = Query(query, top_k)

        results_chunk = []
        results = retrieve(qr, vector_store)

        for idx, res_chunk in enumerate(results, 1):
                    results_chunk.append(
                    f"[Kết quả {idx}] Score: {res_chunk.score:.4f}\n"
                    f"Doc ID: {res_chunk.parent.doc_id}\n"
                    f"Parent Section: {res_chunk.parent.section}\n"
                    f"Parent Content: {res_chunk.parent.content[:150]}...\n"
                    f"Số lượng matched children: {len(res_chunk.matched_children)}"
                )

        if not results:
            return "Không tìm thấy kết quả phù hợp."

        return "\n\n--------------------\n\n".join(results_chunk)

    except Exception as e:
        logger.exception("Lỗi khi search")
        return f"Lỗi tìm kiếm: {e}"


# ============================================================
# 5. TOOL: GET
# ============================================================

@mcp.tool()
def get(doc_id: str) -> str:
    """
    Lấy toàn bộ nội dung của một tài liệu theo Document ID.
    """
    if is_empty(doc_id):
        return "Vui lòng cung cấp doc_id."

    document = vector_store.get_document(doc_id)

    if document is None:
        return f"Không tìm thấy tài liệu có ID: {doc_id}"

    try:
        path = resolve_document_path(document.source)

        if not path.is_file():
            return (
                f"Đã tìm thấy metadata trong VectorStore nhưng file không tồn tại: "
                f"{document.source}"
            )

        content = path.read_text(encoding="utf-8")

        return (
            f"Document ID: {document.doc_id}\n"
            f"Title: {document.title}\n"
            f"Source: {document.source}\n\n"
            f"Nội dung:\n{content}"
        )

    except Exception as e:
        logger.exception("Lỗi khi get document")
        return f"Lỗi đọc tài liệu: {e}"


# ============================================================
# 6. TOOL: UPDATE
# ============================================================

@mcp.tool()
def update(doc_id: str, content: str) -> str:
    """
    Cập nhật nội dung file TXT và đồng bộ lại VectorStore/cache.
    """
    if is_empty(doc_id):
        return "Vui lòng cung cấp doc_id."

    if content is None or not content.strip():
        return "Nội dung cập nhật không được để trống."

    document = vector_store.get_document(doc_id)

    if document is None:
        return f"Không tìm thấy tài liệu có ID: {doc_id}"

    try:
        path = resolve_document_path(document.source)

        if not path.is_file():
            return f"File không tồn tại: {document.source}"

        old_content = path.read_text(encoding="utf-8")

        # Ghi nội dung mới vào file nguồn.
        path.write_text(content, encoding="utf-8")

        try:
            # Tạo lại VectorStore để embedding phản ánh nội dung mới.
            new_store = build_vector_store()

            if doc_id not in new_store.documents:
                raise RuntimeError(
                    "Không tìm thấy tài liệu sau khi tạo lại VectorStore."
                )

            # Cập nhật store đang được các MCP tools sử dụng.
            vector_store.documents = new_store.documents
            vector_store.parent_chunks = new_store.parent_chunks
            vector_store.child_chunks = new_store.child_chunks
            vector_store.parents_in_doc = new_store.parents_in_doc
            vector_store.children_in_parent = new_store.children_in_parent

            return f"Đã cập nhật tài liệu {doc_id} và lưu lại VectorStore."

        except Exception:
            # Nếu tái tạo index thất bại, khôi phục file nguồn cũ.
            path.write_text(old_content, encoding="utf-8")
            logger.exception("Không thể đồng bộ VectorStore sau khi update")
            return "Cập nhật thất bại khi đồng bộ VectorStore; đã khôi phục file nguồn."

    except Exception as e:
        logger.exception("Lỗi khi update document")
        return f"Lỗi cập nhật tài liệu: {e}"


# ============================================================
# 7. CHẠY MCP SERVER
# ============================================================

if __name__ == "__main__":
    logger.info("MCP Server đang khởi động...")
    mcp.run()
