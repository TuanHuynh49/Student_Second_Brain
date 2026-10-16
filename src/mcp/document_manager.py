from pathlib import Path
from dataclasses import asdict
import json
from datetime import date



PROJECT_ROOT = Path(__file__).resolve().parents[2]

# File lưu metadata
DOCUMENTS_PATH = PROJECT_ROOT / "data" / "documents.json"

# Thư mục chứa file TXT/Markdown
RAW_DIR = PROJECT_ROOT / "data" / "raw"

def load_metadata() -> list[dict]:
    if not DOCUMENTS_PATH.exists():
        return []
    with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
         return json.load(f)


def save_metadata(metadata: list[dict]) -> None:

    with open(DOCUMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata,f,indent=2)

def create_metadata(file_path: Path,title: str,owner: str,version: str = "1.0") -> dict:
    doc_id = file_path.stem
    created_at = date.today().isoformat()

    return {
        "doc_id": doc_id,
        "title": title,
        "date": created_at,
        "version": version,
        "owner": owner,
        "source": str(file_path.resolve().relative_to(PROJECT_ROOT))
    }

def register_document(file_path: Path,title: str,owner: str,version: str = "1.0") -> dict:
    # Kiểm tra file có tồn tại không
    file_path = file_path.resolve()

    if not file_path.exists():
        raise FileNotFoundError(
            f"Document file not found: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError("The specified path is not a file.")

    try:
        file_path.relative_to(PROJECT_ROOT)
    except ValueError:
        raise ValueError("Document must be inside the project directory.")

    # Tạo metadata
    new_metadata = create_metadata(
        file_path=file_path,
        title=title,
        owner=owner,
        version=version
    )

    # Đọc metadata hiện tại
    metadata = load_metadata()

    # Kiểm tra ID đã tồn tại chưa
    for document in metadata:
        if document["doc_id"] == new_metadata["doc_id"]:
            raise ValueError(
                f"Document ID already exists: {new_metadata['doc_id']}"
            )

    # Thêm và lưu metadata mới
    metadata.append(new_metadata)
    save_metadata(metadata)

    return new_metadata
    



if __name__ == "__main__":
    try:
        result = register_document(
            file_path=RAW_DIR / "test.txt",
            title="Test Document",
            owner="Team A"
        )

        print("Registered successfully:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
