import asyncio
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from app_telegram.api.telegram_users import get_telegram_user, update_telegram_username

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
        username = update.effective_user.username
        if database_user.get('username') != username:
            await asyncio.to_thread(update_telegram_username, user_id, username, context.bot.token)
        return await func(update, context, *args, **kwargs)
    return wrapper
