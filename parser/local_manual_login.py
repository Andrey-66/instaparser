"""
Локальный скрипт для получения свежих Instagram-cookies с доверенного IP.

Чисто ручной вход: открывает окно Chrome на странице логина, вы сами
вводите логин/пароль (и 2FA, если есть) — скрипт ничего не вводит сам и
не трогает .env. Дальше просто жмёте Enter в консоли, и cookies
сохраняются в ig_cookies_local.json рядом со скриптом.

Файл нужно скопировать на сервер как content/ig_cookies.json
(рядом с docker-compose.yml) и перезапустить контейнер parser — он
подхватит cookies через load_cookies() вместо повторного логина.

Запуск (из папки parser/):
    venv-parser\\Scripts\\python.exe local_manual_login.py
"""
import sys
import traceback

from app_parser.autentefication.cooke import save_cookies
from app_parser.driver import driver_manager

OUTPUT_PATH = "ig_cookies_local.json"


def main():
    print("Запускаю локальный Chrome...", flush=True)
    driver_manager.create_driver(debug=True)
    driver = driver_manager.driver
    print("Chrome запущен, открываю страницу логина Instagram...", flush=True)
    driver.get("https://www.instagram.com/accounts/login/")
    print("Готово. Окно Chrome должно быть открыто на экране (проверьте панель задач,", flush=True)
    print("если не видно — возможно, свернулось или открылось на другом мониторе).", flush=True)
    print(flush=True)
    input(">>> Залогиньтесь в Instagram в открывшемся окне вручную, затем нажмите Enter здесь... ")

    save_cookies(driver, path=OUTPUT_PATH)
    print(f"✅ Cookies сохранены в {OUTPUT_PATH}", flush=True)
    print("Скопируй этот файл на сервер как content/ig_cookies.json и перезапусти контейнер parser.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("❌ Ошибка:", flush=True)
        traceback.print_exc()
        sys.exit(1)
    finally:
        driver_manager.quit_driver()
