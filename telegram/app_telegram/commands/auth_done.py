import os
import logging

from telegram import Update
from telegram.ext import ContextTypes

AUTH_DONE_FILE = "/content/.auth_done"

logger = logging.getLogger(__name__)


async def auth_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = os.getenv("ADMIN_TELEGRAM_ID")
    if not admin_id or str(update.effective_user.id) != str(admin_id):
        await update.message.reply_text("❌ Нет доступа.")
        return

    try:
        with open(AUTH_DONE_FILE, 'w') as f:
            f.write('done')
        await update.message.reply_text("✅ Сигнал получен. Парсер сохранит куки и продолжит работу.")
        logger.info(f"auth_done signal written by admin {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Failed to write auth_done signal: {e}")
        await update.message.reply_text("❌ Не удалось записать сигнал.")