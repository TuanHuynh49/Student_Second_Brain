
from pathlib import Path
import sys

# Đảm bảo Python tìm thấy package src khi chạy từ thư mục gốc.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))



def load_store():
    from src.rag.vectordb.VectorStore import VectorStore
    return VectorStore.load()



def test_filter(store, mode, query, metadata_filter, top_k=5):
    print(f"\n--- TEST {mode.upper()} ---")
    print("Filter:", metadata_filter)

    if mode == "dense":
        results = store.dense_search(
            query=query,
            top_k=top_k,
            metadata=metadata_filter
        )
    else:
        results = store.hybrid_search(
            query=query,
            top_k=top_k,
            metadata=metadata_filter
        )

    print("Số kết quả:", len(results))

    for index, (chunk, score) in enumerate(results, start=1):
        print(f"\nKết quả {index} | Score: {score:.4f}")
        print("Doc ID:", chunk.doc_id)
        print("Course:", (chunk.metadata or {}).get("course"))
        print("Content:", chunk.content[:150])

    # Xác nhận tất cả kết quả đều thỏa filter.
    for chunk, _ in results:
        for key, expected in metadata_filter.items():
            actual = (
                chunk.doc_id
                if key == "doc_id"
                else (chunk.metadata or {}).get(key)
            )

            if isinstance(expected, (list, tuple, set)):
                assert actual in expected, (
                    f"FAIL: {key}={actual!r}, expected {expected!r}"
                )
            else:
                assert actual == expected, (
                    f"FAIL: {key}={actual!r}, expected {expected!r}"
                )

    print("PASS: tất cả kết quả đều thỏa filter.")
    return results


def main():
    store = load_store()

    if not store.child_chunks:
        print("FAIL: VectorStore không có child_chunks.")
        return

    # In metadata mẫu để xem dữ liệu thực tế.
    print("=== METADATA MẪU ===")
    for index, chunk in enumerate(store.child_chunks.values()):
        print("Doc ID:", chunk.doc_id)
        print("Metadata:", chunk.metadata)
        if index >= 2:
            break

    # Tìm chunk có course để lấy giá trị filter thật.
    sample_chunk = next(iter(store.child_chunks.values()))
    sample_course = (sample_chunk.metadata or {}).get("course")
    sample_doc_id = sample_chunk.doc_id

    for mode in ("dense", "hybrid"):
        if sample_course:
            test_filter(
                store,
                mode,
                "What are the prerequisites for this course?",
                {"course": sample_course}
            )
        else:
            print(
                f"SKIP {mode}: chunk mẫu không có metadata course."
            )

        if sample_doc_id:
            test_filter(
                store,
                mode,
                "course prerequisites",
                {"doc_id": sample_doc_id}
            )
        else:
            print(f"SKIP {mode}: chunk mẫu không có doc_id.")

        # Course không tồn tại phải trả về rỗng.
        if mode == "dense":
            results = store.dense_search(
                query="test metadata filter",
                top_k=5,
                metadata={"course": "__COURSE_NOT_EXIST__"}
            )
        else:
            results = store.hybrid_search(
                query="test metadata filter",
                top_k=5,
                metadata={"course": "__COURSE_NOT_EXIST__"}
            )

        assert not results, (
            f"FAIL: {mode} vẫn trả kết quả khi course không tồn tại."
        )
        print(f"PASS: {mode} trả về 0 kết quả với course không tồn tại.")

    print("\n=== HOÀN TẤT KIỂM TRA ===")


if __name__ == "__main__":
    main()
