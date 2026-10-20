"""
Logging configuration for Automotive Engineering AI Assistant.
Safe formatting that prevents secret/token leakage.
"""
import logging
import sys
from pathlib import Path
from core.config import BASE_DIR

LOG_DIR = BASE_DIR / "storage" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"


class SecretSanitizingFilter(logging.Filter):
    """Filter that strips out sensitive keys or authorization strings."""
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.msg)
        for keyword in ["Bearer ", "sk-", "AIza", "key="]:
            if keyword in msg:
                # Sanitize
                idx = msg.find(keyword)
                end_idx = min(len(msg), idx + 35)
                msg = msg[:idx + len(keyword)] + "***REDACTED***" + msg[end_idx:]
                record.msg = msg
        return True


def setup_logger(name: str = "autosar_assistant") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Console handler
        c_handler = logging.StreamHandler(sys.stdout)
        c_format = logging.Formatter(
            "%(asctime)s - [%(levelname)s] - [%(name)s:%(lineno)d] - %(message)s"
        )
        c_handler.setFormatter(c_format)
        c_handler.addFilter(SecretSanitizingFilter())
        logger.addHandler(c_handler)

        # File handler
        try:
            f_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
            f_format = logging.Formatter(
                "%(asctime)s - [%(levelname)s] - [%(name)s:%(lineno)d] - %(message)s"
            )
            f_handler.setFormatter(f_format)
            f_handler.addFilter(SecretSanitizingFilter())
            logger.addHandler(f_handler)
        except Exception:
            pass

    return logger


logger = setup_logger()
