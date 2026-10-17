
def normalize_text(value: str) -> str:
    """Xoa khoang trang o dau va cuoi chuoi."""
    return value.strip()


def is_empty(value: str) -> bool:
    """Kiem tra chuoi co rong hay khong."""
    return not value.strip()

