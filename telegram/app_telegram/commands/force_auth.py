import os
import logging

from telegram import Update
from telegram.ext import ContextTypes

FORCE_AUTH_FILE = "/content/.force_auth"

logger = logging.getLogger(__name__)


async def force_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = os.getenv("ADMIN_TELEGRAM_ID")
    if not admin_id or str(update.effective_user.id) != str(admin_id):
        await update.message.reply_text("❌ Нет доступа.")
        return

    try:
        with open(FORCE_AUTH_FILE, 'w') as f:
            f.write('force')
        await update.message.reply_text(
            "✅ Сигнал отправлен. Парсер запустит ручную авторизацию при первой возможности (в течение 30 сек)."
        )
        logger.info(f"force_auth signal written by admin {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Failed to write force_auth signal: {e}")
        await update.message.reply_text("❌ Не удалось записать сигнал.")
