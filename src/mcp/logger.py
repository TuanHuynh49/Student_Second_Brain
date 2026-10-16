import logging
import sys

def setup_logger():
    LOG_PATH = "logs/server.log"
    _handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]

    try:
        _handlers.append(logging.FileHandler(LOG_PATH, encoding="utf-8"))
    except OSError as error:
        print(f"warning: cannot open {LOG_PATH}: {error}", file=sys.stderr)

    logger = logging.getLogger("student_second_brain")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

    for handler in _handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
 
