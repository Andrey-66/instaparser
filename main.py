import threading
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from telegram import Update
from telegram.ext import Application, CommandHandler
import asyncio

from bot import subscribe, unsubscribe, mysubscriptions, download
from insta_process import insta_process, init_inta
from logger import logger, logger_init


def insta_worker(options, bot, loop):
    while True:
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            init_inta(driver)
            insta_process(driver, bot, loop)
            # если insta_process завершилась нормально — выйдем из цикла
            break
        except Exception:
            # Логируем полный стектрейс — это поможет понять причину падений
            logger.exception("Неизвестная ошибка в insta_worker, перезапуск драйвера")
            # Попытка аккуратно завершить драйвер, если он создан
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass
            time.sleep(5)
            continue
        finally:
            # В finally тоже закрываем драйвер, если он всё ещё жив
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass


def main():
    logger_init()
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    # Не создаём драйвер здесь — он создаётся внутри insta_worker
    auth_token = os.getenv("TOKEN")
    application = Application.builder().token(auth_token).read_timeout(30).connect_timeout(30).build()
    loop = asyncio.get_event_loop()

    # Запускаем фоновый поток, который сам создаёт/рестартует драйвер внутри
    thread_insta = threading.Thread(target=insta_worker, args=(chrome_options, application.bot, loop), daemon=True)
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