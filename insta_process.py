import os
from asyncio import run_coroutine_threadsafe
from time import sleep

from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
import asyncio

from selenium.webdriver.support.wait import WebDriverWait

from bot import send_content
from cooke import load_cookies, save_cookies
from files_managment import load_profiles, get_directories_list, clean_and_check_user_dirs, get_telegram_ids_by_username
from insta_download import get_content
from login import check_login
from open_page import reject_cookies, open_page
from dotenv import load_dotenv

load_dotenv()
USER = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def get_links(driver, username):
    open_page(driver, f"https://www.instagram.com/{username}/")
    sleep(10)
    try:
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except TimeoutException:
        print(f"Таймаут загрузки страницы для {username}")

    try:
        driver.execute_script("window.scrollBy(0, 500);")
        sleep(2)  # Даем время на завершение прокрутки
    except (TimeoutException, WebDriverException) as e:
        print(f"Ошибка прокрутки для {username}: {e}")

    links = driver.find_elements(By.XPATH, "//a[@href]")
    i = 0
    result = []
    for link in links:
        href = link.get_attribute("href")
        if href and ("/p/" in href or "/reel/" in href):
            i += 1
            result.append(href)
            if i == 7:
                break
    return result

def init_inta(driver):
    open_page(driver, "https://www.instagram.com/")
    load_cookies(driver)
    reject_cookies(driver)
    sleep(5)
    check_login(driver)


def insta_process(driver, bot, loop):
    while True:
        try:
            profiles = load_profiles()
            for username, _ in profiles:
                try:
                    links = get_links(driver, username)
                    directories = get_directories_list(username, links)
                    to_download = clean_and_check_user_dirs(username, directories)
                    print(f"Нужно скачать: {to_download}")
                    for link in to_download:
                        try:
                            get_content(link, username)
                            telegram_ids = get_telegram_ids_by_username(username)
                            for telegram_id in telegram_ids:
                                try:
                                    run_coroutine_threadsafe(
                                        bot.send_message(chat_id=telegram_id, text=f"Пост от {username}"), loop)
                                    run_coroutine_threadsafe(
                                        send_content(f"{username}-{link}", telegram_id, bot, delete=False), loop)
                                except Exception as e:
                                    print(e)
                        except Exception as e:
                            print(f"Ошибка при скачивании {link}: {e}")
                except Exception as e:
                    print(f"Ошибка при обработке профиля {username}: {e}")
                    continue  # Продолжаем со следующим профилем

            save_cookies(driver)
            sleep(10 * 60)

        except (TimeoutException, WebDriverException) as e:
            print(f"Критическая ошибка WebDriver: {e}")
            print("Перезапуск через 1 минуту...")
            sleep(60)
            # Продолжаем цикл - драйвер может восстановиться
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            sleep(60)
