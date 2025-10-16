import os

from functools import wraps

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

load_dotenv()
ALLOWED_USERS = set(map(int, os.getenv("ALLOWED_USERS", "").split(",")))

def restricted(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USERS:
            await update.message.reply_text("❌ У вас нет доступа к этой команде.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
