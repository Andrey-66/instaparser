import json
import os
import time
from selenium import webdriver

COOKIES_FILE = "ig_cookies.json"
BASE_URL = "https://www.instagram.com/"

def normalize_cookie(cookie):
    c = cookie.copy()
    c.pop("sameSite", None)
    if "expiry" in c:
        try:
            c["expiry"] = int(c["expiry"])
        except Exception:
            c.pop("expiry", None)
    return c

def load_cookies(driver, path=COOKIES_FILE):
    """Загрузить cookies (если есть). Вернёт True, если файл был загружен."""
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    driver.get(BASE_URL)
    time.sleep(1)
    for c in cookies:
        try:
            driver.add_cookie(normalize_cookie(c))
        except Exception as e:
            print("warning: cookie not added:", e)
    driver.refresh()
    return True

def save_cookies(driver, path=COOKIES_FILE):
    """Сохранить текущие cookies в файл."""
    cookies = driver.get_cookies()
    cookies = [normalize_cookie(c) for c in cookies]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
    print(f"Saved {len(cookies)} cookies to {path}")

# --- Пример использования ---
if __name__ == "__main__":
    driver = webdriver.Chrome()
    # Попытка восстановить сессию
    loaded = load_cookies(driver)
    if loaded:
        print("Cookies загружены — проверяй, залогинен ли ты.")
    else:
        print("Файл cookies не найден — откроется страница входа.")

    # Открываем страницу и даём шанс вручную залогиниться (если требуется)
    driver.get(BASE_URL)
    input("Если нужно — залогиньтесь вручную в открывшемся окне. Нажмите Enter в консоли, чтобы продолжить и сохранить cookies...")

    # Сохраняем cookies в конце
    save_cookies(driver)

    driver.quit()
