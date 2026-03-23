import os

from functools import wraps

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

from app_telegram.api.telegram_users import get_telegram_user

def restricted(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        database_user = get_telegram_user(user_id)
        if not database_user:
            await update.message.reply_text("❌ У вас нет доступа к этой команде.")
            return None
        if not database_user.get('is_active'):
            await update.message.reply_text("❌ У вас нет доступа к этой команде.")
            return None
        return await func(update, context, *args, **kwargs)
    return wrapper
