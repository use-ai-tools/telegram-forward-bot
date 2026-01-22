from telegram.ext import Application, MessageHandler, filters
import asyncio
import os, logging
print("Running from:", os.getcwd())
from config import TOKEN, SOURCE_CHAT_IDS, TARGET_CHAT_IDS, CHANNEL_RULES, DELAY

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
sent_texts = set()

if os.path.exists("sent.txt"):
   with open("sent.txt","r", encoding="utf-8") as f:
        sent_texts = set(line.strip() for line in f)

worker_task = None

ADD_TEXT = "\n\n🔥 Join @Time2winn for more deals"

queue = asyncio.Queue()

async def forward_message(update, context):
    post = update.channel_post
    text = post.text or post.caption or ""

    message_key = text.strip().lower()

    if message_key in sent_texts:
        logging.info("Duplicate skipped")
        return

    channel_id = post.chat_id
    allowed_keywords = CHANNEL_RULES.get(channel_id,[])

    if any(word in text.lower() for word in allowed_keywords):
        try:
            await asyncio.sleep(2)

            # edited text
            new_text = text + ADD_TEXT

            # agar text message hai
            if post.text:
                await queue.put((post,new_text))
                sent_texts.add(message_key)
                with open("sent.txt","a", encoding="utf-8") as f:
                    f.write(message_key + "\n")

            # agar photo/video/document hai
            elif post.caption:
                for chat_id in TARGET_CHAT_IDS:
                    await post.copy(chat_id=chat_id, caption=new_text)

            logging.info("Forwarded with edit")

        except Exception as e:
            logging.error(f"Error:{e}")
    else:
        logging.info(f"Skipped:{text}")

async def queue_worker(bot):
    try:
        while True:
            post, new_text = await queue.get()

            for chat_id in TARGET_CHAT_IDS:
                if post.text:
                    await bot.send_message(chat_id=chat_id, text=new_text)
                elif post.caption:
                    await post.copy(chat_id=chat_id, caption=new_text)

            await asyncio.sleep(DELAY)
            queue.task_done()
    except asyncio.CancelledError:
        print("Queue worker stopped gracefully")

app = Application.builder().token(TOKEN).build()

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

print("Forward bot running...")
app.run_polling()