import logging
import sys
from pathlib import Path

def setup_logger():
    project_root = Path(__file__).resolve().parents[2]
    log_path = project_root / "logs" / "server.log"

    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("student_second_brain")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Tránh tạo nhiều handler nếu setup_logger() được gọi lại.
    if not logger.handlers:
        file_handler = logging.FileHandler(
            log_path,
            encoding="utf-8",
        )

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | "
            "%(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
