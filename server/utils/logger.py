# server/utils/logger.py
from loguru import logger
import sys
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "mina.log"

logger.remove()  # Clear default handlers

# Console handler (dev)
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                              "<level>{level: <8}</level> | "
                              "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                              "<level>{message}</level>",
           colorize=True, level="INFO")

# File handler (JSON for structured logging)
logger.add(LOG_FILE, serialize=True, rotation="10 MB", retention=5,
           compression="zip", level="INFO")

def get_logger():
    return logger