import asyncio, logging

import datetime

from telegram import ReplyKeyboardMarkup

from bot.utils import *

from bot.config import *

logger, error_logger = setup_logger()

async def forward_message(update, context):
   
    if not BOT_ENABLED:
        return

    post = update.effective_message
    if not post:
        return

    text = post.text or post.caption or ""

    logger.info("New message recived")

    message_key = " ".join(text.strip().lower())

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
                await queue.put((post, new_text))
                sent_texts.add(message_key)
                with open("sent.txt","a", encoding="utf-8") as f:
                    f.write(message_key + "\n")

            # agar photo/video/document hai
            elif post.caption:
                for chat_id in TARGET_CHAT_IDS:
                    await post.copy(chat_id=chat_id, caption=new_text)

            else:
               logger.info(f"Skipped:{text}")

        except Exception as e:
            error_logger.error(f"Error in forward_message:{e}")

async def status_command(update, context):
    queued = queue.qsize()
    total_saved = len(sent_texts)

    msg = update.effective_message
    if not msg or not msg.text:
        return

    await msg.reply_text(f"Bot is running\nQueued: {queued}\nSaved: {total_saved}")