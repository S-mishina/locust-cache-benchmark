import logging
import sys
from pythonjsonlogger.json import JsonFormatter


class _ConfigContextFilter(logging.Filter):
    """Inject command/mode context from AppConfig into every log record."""

    def filter(self, record):
        try:
            from cache_benchmark.config import get_config
            cfg = get_config()
            record.cache_type = cfg.cache_type
            record.cluster_mode = cfg.cluster_mode or "local"
        except RuntimeError:
            record.cache_type = "unknown"
            record.cluster_mode = "unknown"
        return True


def setup_json_logging():
    handler = logging.StreamHandler(sys.stderr)
    formatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(funcName)s %(process)s %(threadName)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
            "funcName": "function",
            "process": "pid",
            "threadName": "thread",
        },
    )
    handler.setFormatter(formatter)
    handler.addFilter(_ConfigContextFilter())
    logging.root.handlers.clear()
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.DEBUG)
    logging.getLogger("locust").setLevel(logging.INFO)
