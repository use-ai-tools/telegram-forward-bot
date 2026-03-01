import asyncio
import logging
import os

def setup_logger():
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/info.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    error_logger = logging.getLogger("error")
    error_handler = logging.FileHandler("logs/error.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_logger.addHandler(error_handler)

    return logging.getLogger(), error_logger

sent_texts = set()

if os.path.exists("sent.txt"):
    with open("sent.txt", "r", encoding="utf-8") as f:
        sent_texts = set(line.strip() for line in f if line.strip())

ADD_TEXT = "\n\n🔥 Join @Time2winn for more deals"

queue = asyncio.Queue()
