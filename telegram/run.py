import logging
import os
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler

from app_telegram.api.posts import get_posts, update_post
from app_telegram.api.profiles import get_profile
from app_telegram.commands.my_subscriptions import my_subscriptions
from app_telegram.commands.subscribe import subscribe
from app_telegram.commands.unsubscribe import unsubscribe
from app_telegram.utils.files import delete_directory, folder_has_files
from app_telegram.utils.send_content import send_content

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Вывод в stdout
            RotatingFileHandler(
                "telegram.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8"
            )
        ]
    )

async def background_monitoring(context):
    """Фоновый мониторинг"""
    try:
        logger.info("Запуск фонового мониторинга...")
        posts = get_posts(is_sent=False, is_downloaded=True)
        bot = context.bot
        for post in posts:
            try:
                instagram_profile_username = post.get("profile_username")
                instagram_profile = get_profile(instagram_profile_username)
                link = post.get('instagram_post_id')
                file = post.get('file_path')
                file = '../'+file
                media_type = post.get('media_type')
                post_id = post.get('id')
                telegram_ids = instagram_profile.get("telegram_ids")
                if not folder_has_files(file):
                    logger.error(f'Folder {file} is empty or does not exist')
                    delete_directory(file)
                    update_post(post_id, is_sent=False, is_downloaded=False)
                    continue
                for telegram_id in telegram_ids:
                    logger.info(f'Sending {link} to {telegram_id}')
                    if media_type == 'reel':
                        await bot.send_message(chat_id=telegram_id,
                                               text=f"<a href='{link}'>Рилс</a> от {instagram_profile_username}",
                                               parse_mode="HTML")
                    else:
                        await bot.send_message(chat_id=telegram_id,
                                               text=f"<a href='{link}'>Пост</a> от {instagram_profile_username}",
                                               parse_mode="HTML")

                    await send_content(file, telegram_id, bot)
                    delete_directory(file)
                update_post(post_id, is_sent=True, sent_at=datetime.now().isoformat(), sent_to=', '.join(telegram_ids))
                time.sleep(3)
            except Exception as e:
                logger.error(f"Error while sending post: {e}")
                continue

    except Exception as e:
        logger.error(f"Ошибка в фоновом мониторинге: {e}")


def main():
    load_dotenv()
    setup_logging()
    auth_token = os.getenv("TOKEN")
    application = Application.builder().token(auth_token).read_timeout(30).connect_timeout(30).build()
    job_queue = application.job_queue
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("mysubscriptions", my_subscriptions))
    job_queue.run_repeating(
        background_monitoring,
        interval=300,
        first=10,
    )
    application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)

if __name__ == "__main__":
    main()