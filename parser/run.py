import os
import random
import time
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from selenium.common.exceptions import WebDriverException
import logging

from app_parser.api.notify import notify_admin
from app_parser.api.posts import get_posts
from app_parser.api.profiles import get_profiles
from app_parser.autentefication.cooke import save_cookies
from app_parser.driver import driver_manager
from app_parser.parser import InstagramParser

AUTH_DONE_FILE = "/content/.auth_done"
FORCE_AUTH_FILE = "/content/.force_auth"
MAX_AUTH_FAILURES = 5

logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                "parser.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8"
            )
        ]
    )


def interruptible_sleep(total_seconds: int) -> bool:
    """Спит с проверкой флага /force_auth каждые 30 сек.
    Возвращает True если сон был прерван командой."""
    deadline = time.time() + total_seconds
    while time.time() < deadline:
        if os.path.exists(FORCE_AUTH_FILE):
            os.remove(FORCE_AUTH_FILE)
            return True
        remaining = deadline - time.time()
        time.sleep(min(30, remaining))
    return False


def _focus_remaining_window(driver):
    """Админ может залогиниться в новой вкладке, а не в той, что открыл Selenium,
    и закрыть исходную. Переключаемся на то, что осталось открытым, иначе
    save_cookies упадёт с 'no such window' на закрытой вкладке."""
    try:
        handles = driver.window_handles
        if handles:
            driver.switch_to.window(handles[-1])
    except WebDriverException as e:
        logger.warning(f"Не удалось переключиться на открытую вкладку: {e}")


def wait_for_manual_auth(server_url: str, reason: str = f"Авторизация Instagram провалилась {MAX_AUTH_FAILURES} раз подряд."):
    if os.path.exists(AUTH_DONE_FILE):
        os.remove(AUTH_DONE_FILE)

    try:
        password = driver_manager.start_vnc_session()
        driver_manager.start_manual_chrome()

        notify_admin(
            f"⚠️ {reason}\n\n"
            f"Открой в браузере:\n{server_url}:6080/vnc.html?autoconnect=1&password={password}\n\n"
            f"Залогинься в Instagram и отправь /auth_done"
        )

        logger.info("Ожидаем ручной авторизации через noVNC...")
        while not os.path.exists(AUTH_DONE_FILE):
            time.sleep(10)

        os.remove(AUTH_DONE_FILE)
        _focus_remaining_window(driver_manager.driver)
        save_cookies(driver_manager.driver)
        logger.info("Куки сохранены после ручной авторизации")

    except Exception as e:
        logger.error(f"Ошибка во время ручной авторизации: {e}")
    finally:
        driver_manager.quit_driver()
        driver_manager.stop_vnc_session()


def main():
    load_dotenv()
    setup_logging()
    debug = os.getenv("DEBUG", "False").lower() not in ("false", "0", "")
    server_url = os.getenv("SERVER_URL", "http://localhost")

    consecutive_auth_failures = 0

    logger.info("Первый запуск: авторизация строго через VNC")
    wait_for_manual_auth(server_url, reason="Первый запуск парсера, нужна авторизация Instagram.")

    while True:
        try:
            with InstagramParser(limit=10, debug=debug) as parser:
                consecutive_auth_failures = 0
                posts = get_posts(is_downloaded=False)
                parser.parse_posts(posts)
                profiles = get_profiles()
                profiles_names = [p.get("username") for p in profiles]
                parser.parse_profiles(profiles_names)
                posts = get_posts(is_downloaded=False)
                parser.parse_posts(posts)
            sleep_minutes = random.randint(90, 120)
            logger.info(f"Спим {sleep_minutes} минут перед следующей итерацией")
            if interruptible_sleep(sleep_minutes * 60):
                wait_for_manual_auth(server_url)
        except Exception as e:
            logger.error(f"Parser failed: {e}")
            if "authentication failed" in str(e).lower():
                consecutive_auth_failures += 1
                logger.warning(f"Провалов авторизации подряд: {consecutive_auth_failures}/{MAX_AUTH_FAILURES}")
                if consecutive_auth_failures >= MAX_AUTH_FAILURES:
                    wait_for_manual_auth(server_url)
                    consecutive_auth_failures = 0
                    continue
            sleep_minutes = random.randint(90, 120)
            logger.info(f"Спим {sleep_minutes} минут перед следующей итерацией")
            if interruptible_sleep(sleep_minutes * 60):
                wait_for_manual_auth(server_url)
                consecutive_auth_failures = 0


if __name__ == "__main__":
    main()