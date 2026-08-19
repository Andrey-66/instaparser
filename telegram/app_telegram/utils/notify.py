import logging
import os

logger = logging.getLogger(__name__)

ADMIN_CHAT_ID = os.getenv("ADMIN_TELEGRAM_ID")


async def notify_admin(bot, message: str):
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_TELEGRAM_ID not set, skipping admin notification")
        return
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
