import threading
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from telegram import Update
from telegram.ext import Application, CommandHandler
import asyncio

from bot import subscribe, unsubscribe, mysubscriptions, download
from insta_process import insta_process
from logger import logger, logger_init



def main():
    logger_init()
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--lang=en-US")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    # Не создаём драйвер здесь — он создаётся внутри insta_process
    auth_token = os.getenv("TOKEN")
    application = Application.builder().token(auth_token).read_timeout(30).connect_timeout(30).build()
    loop = asyncio.get_event_loop()

    # Запускаем фоновый поток, который сам создаёт/рестартует драйвер внутри
    thread_insta = threading.Thread(target=insta_process, args=(chrome_options, application.bot, loop), daemon=True)
    thread_insta.start()

    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("mysubscriptions", mysubscriptions))
    application.add_handler(CommandHandler("download", download))
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received — stopping application")
    finally:
        try:
            application.stop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
