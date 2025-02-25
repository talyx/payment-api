import logging
import os

ROOT_DIR = os.getcwd()

LOG_FILE = os.path.join(ROOT_DIR, "app.log")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(file_handler)
