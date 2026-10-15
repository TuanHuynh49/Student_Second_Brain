import logging
import sys

def setup_logger():
    LOG_PATH = "logs/server.log"
    _handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]

    try:
        _handlers.append(logging.FileHandler(LOG_PATH, encoding="utf-8"))
    except OSError as error:
        print(f"warning: cannot open {LOG_PATH}: {error}", file=sys.stderr)

    logging.basicConfig(
        level=logging.INFO,
        handlers=_handlers,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s", 
    )

    return logging.getLogger("student_second_brain")
