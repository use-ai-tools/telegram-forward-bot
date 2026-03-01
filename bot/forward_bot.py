import asyncio, os, logging, signal, sys

from telegram.ext import Application, MessageHandler, filters, CommandHandler

from telegram import Update

from bot.config import TOKEN, SOURCE_CHAT_IDS, TARGET_CHAT_IDS, CHANNEL_RULES, DELAY

from bot.handlers import * 

from bot.utils import setup_logger, sent_texts, ADD_TEXT, queue 

#print("Running from:", os.getcwd())

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Formatter
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# INFO handler
info_handler = logging.FileHandler("logs/info.log", encoding="utf-8")
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)

# ERROR handler
error_handler = logging.FileHandler("logs/error.log", encoding="utf-8")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(info_handler)
logger.addHandler(error_handler)

worker_task = None

async def queue_worker(bot):
    logger.info("Queue worker started")
    try:
        while True:
            post, new_text = await queue.get()

            logger.info(f"Queue picked message | Queue size now: {queue.qsize()}")

            if new_text.strip().lower() in sent_texts:
                logger.info("Duplicate skipped")
                queue.task_done()
                continue

            for chat_id in TARGET_CHAT_IDS:
                logger.info(f"Message forwarded to {chat_id}")
                if post.text:
                    await bot.send_message(chat_id=chat_id, text=new_text)
                elif post.caption:
                    await post.copy(chat_id=chat_id, caption=new_text)

            logger.info("Message sent successfully")
  
            await asyncio.sleep(DELAY)
            logger.info("Queue task completed")
            queue.task_done()
    except asyncio.CancelledError:
        logger.info("Queue worker stopped gracefully")

app = Application.builder().token(TOKEN).build()

logger, error_logger = setup_logger()

logger.info("Bot file loaded")

logger.info(
    f"BOT_ENABLED={BOT_ENABLED} | Sources={len(SOURCE_CHAT_IDS)} | Targets={len(TARGET_CHAT_IDS)}"
)

logger.info(f"Loaded {len(sent_texts)} sent messages from sent.txt")

logger.info("Forward bot fully initialized")

async def start_worker(app):
    global worker_task
    worker_task = asyncio.create_task(queue_worker(app.bot))

app.post_init = start_worker

async def on_shutdown(app):
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

app.post_shutdown = on_shutdown


app.add_handler(MessageHandler(filters.ALL & filters.Chat(SOURCE_CHAT_IDS), forward_message))

def run():
    print("Forward bot started...")
    app.run_polling()
if __name__ =="__main__":
    run()