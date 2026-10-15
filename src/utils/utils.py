
def normalize_text(value: str) -> str:
    """Xoa khoang trang o dau va cuoi chuoi."""
    return value.strip()


def is_empty(value: str) -> bool:
    """Kiem tra chuoi co rong hay khong."""
    return not value.strip()


def create_doc_id(documents: dict) -> str:
    """Tao ID moi cho tai lieu."""
    
    numbers =[]
    for doc in documents:
        if doc[3:].isdigit() and doc.startswith("DOC"):
            numbers.append(int(doc[3:]))

    next_number = max(numbers,0) + 1
    return f"DOC{next_number:04d}"