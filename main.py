import threading
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from telegram import Update
from telegram.ext import Application, CommandHandler
import asyncio

from bot import subscribe, unsubscribe, mysubscriptions, download
from insta_process import insta_process, init_inta


def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    auth_token = os.getenv("TOKEN")
    application = Application.builder().token(auth_token).read_timeout(30).connect_timeout(30).build()
    loop = asyncio.get_event_loop()

    init_inta(driver)
    thread_insta = threading.Thread(target=insta_process, args=(driver,application.bot,loop,))
    thread_insta.start()

    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("mysubscriptions", mysubscriptions))
    application.add_handler(CommandHandler("download", download))
    application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)


if __name__ == "__main__":
    main()