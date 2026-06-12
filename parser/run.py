import os
import random
import time
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
import logging

from app_parser.api.notify import notify_admin
from app_parser.api.posts import get_posts
from app_parser.api.profiles import get_profiles
from app_parser.autentefication.cooke import save_cookies
from app_parser.driver import driver_manager
from app_parser.parser import InstagramParser

AUTH_DONE_FILE = "/content/.auth_done"
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


def wait_for_manual_auth(server_url: str):
    if os.path.exists(AUTH_DONE_FILE):
        os.remove(AUTH_DONE_FILE)

    try:
        password = driver_manager.start_vnc_session()
        driver_manager.start_manual_chrome()

        notify_admin(
            f"⚠️ Авторизация Instagram провалилась {MAX_AUTH_FAILURES} раз подряд.\n\n"
            f"Открой в браузере:\n{server_url}:6080/vnc.html?autoconnect=1&password={password}\n\n"
            f"Залогинься в Instagram и отправь /auth_done"
        )

        logger.info("Ожидаем ручной авторизации через noVNC...")
        while not os.path.exists(AUTH_DONE_FILE):
            time.sleep(10)

        os.remove(AUTH_DONE_FILE)
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

    while True:
        try:
            with InstagramParser(limit=10, debug=debug) as parser:
                consecutive_auth_failures = 0
                profiles = get_profiles()
                profiles_names = [p.get("username") for p in profiles]
                parser.parse_profiles(profiles_names)
                posts = get_posts(is_downloaded=False)
                parser.parse_posts(posts)
            sleep_minutes = random.randint(90, 120)
            logger.info(f"Спим {sleep_minutes} минут перед следующей итерацией")
            time.sleep(sleep_minutes * 60)
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
            time.sleep(sleep_minutes * 60)


if __name__ == "__main__":
    main()