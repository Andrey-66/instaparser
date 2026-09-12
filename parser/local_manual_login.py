"""
Локальный скрипт для получения свежих Instagram-cookies с доверенного IP.

Нужен, когда сервер заблокирован Instagram по IP (логин не проходит ни в
одном аккаунте даже вручную через VNC, при этом с локальной машины вход
работает). Логинится через локальный Chrome (chrome-win64) теми же
аккаунтами из .env (EMAILS/PASSWORDS/SECRETS), что использует парсер, и
сохраняет cookies в ig_cookies_local.json рядом со скриптом.

Дальше файл нужно скопировать на сервер как content/ig_cookies.json
(рядом с docker-compose.yml) и перезапустить контейнер parser — он
подхватит cookies через load_cookies() вместо повторного логина.

Запуск (из папки parser/):
    venv-parser\\Scripts\\python.exe local_manual_login.py
"""
import logging
import time

from dotenv import load_dotenv

from app_parser.autentefication.cooke import save_cookies
from app_parser.autentefication.login import check_login, find_login_page, login
from app_parser.driver import driver_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_PATH = "ig_cookies_local.json"


def main():
    load_dotenv()
    driver_manager.create_driver(debug=True)
    driver = driver_manager.driver
    try:
        driver.get(driver_manager.base_url)
        if not check_login(driver):
            logger.info("Не авторизован, пробую логин через .env (EMAILS/PASSWORDS/SECRETS)...")
            if find_login_page(driver):
                login(driver)
            else:
                login(driver, retry=True)
            time.sleep(5)

        if check_login(driver):
            save_cookies(driver, path=OUTPUT_PATH)
            logger.info(f"✅ Готово! Cookies сохранены в {OUTPUT_PATH}")
            logger.info("Скопируй этот файл на сервер как content/ig_cookies.json и перезапусти контейнер parser.")
        else:
            logger.error("❌ Авторизация не удалась даже локально — проверь EMAILS/PASSWORDS/SECRETS в .env "
                         "или пройди её вручную (браузер сейчас открыт, авторизуйся глазами).")
            input("Если авторизовался вручную в открывшемся окне — нажми Enter, чтобы сохранить cookies... ")
            if check_login(driver):
                save_cookies(driver, path=OUTPUT_PATH)
                logger.info(f"✅ Готово! Cookies сохранены в {OUTPUT_PATH}")
    finally:
        driver_manager.quit_driver()


if __name__ == "__main__":
    main()
