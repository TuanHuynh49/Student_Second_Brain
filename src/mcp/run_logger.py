
import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"

logger = logging.getLogger("student_second_brain")


def safe_data(value):
    """Chuyển dữ liệu về dạng JSON và che các trường nhạy cảm."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            name = str(key)
            if any(
                word in name.lower()
                for word in ("api_key", "password", "secret", "authorization")
            ):
                result[name] = "[REDACTED]"
            else:
                result[name] = safe_data(item)
        return result

    if isinstance(value, (list, tuple)):
        return [safe_data(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


class RunLogger:
    def __init__(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        now = datetime.now().astimezone()
        self.run_id = (
            f"run_{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"
        )
        self.path = LOG_DIR / f"{self.run_id}.jsonl"

        self.write("run_started", log_file=self.path.name)
        logger.info("JSONL run log: %s", self.path)

    def write(self, event, **data):
        record = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "run_id": self.run_id,
            "event": event,
            **safe_data(data),
        }

        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    def close(self, status="completed"):
        self.write("run_finished", status=status)


_current_logger = None


def set_logger(run_logger):
    global _current_logger
    _current_logger = run_logger


def log_event(event, **data):
    if _current_logger is not None:
        _current_logger.write(event, **data)
