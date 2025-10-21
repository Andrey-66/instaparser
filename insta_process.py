import os
import random
from asyncio import run_coroutine_threadsafe
from time import sleep

from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By

from selenium.webdriver.support.wait import WebDriverWait

from bot import send_content
from cooke import load_cookies, save_cookies
from files_managment import load_profiles, get_directories_list, clean_and_check_user_dirs, \
    get_telegram_ids_by_username, folder_has_files
from insta_download import get_content
from logger import logger
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
        logger.error(f"Таймаут загрузки страницы для {username}")

    try:
        driver.execute_script("window.scrollBy(0, 500);")
        sleep(2)  # Даем время на завершение прокрутки
    except (TimeoutException, WebDriverException) as e:
        logger.error(f"Ошибка прокрутки для {username}: {e}")

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
        except Exception:
            logger.exception("Не удалось загрузить профили")
            sleep(60)
            continue
        for username, _ in profiles:
            try:
                links = get_links(driver, username)
                logger.debug(links)
                if not links:
                    continue
                directories = get_directories_list(username, links)
                to_download = clean_and_check_user_dirs(username, directories)
                logger.info(f"Нужно скачать: {to_download}")
            except (TimeoutException, WebDriverException) as e:
                logger.warning(f"Ошибка при получении ссылок для {username}: {e}")
                continue
            except Exception as e:
                logger.error(f"Ошибка при обработке ссылок для {username}: {e}")
                continue
            for link in to_download:
                sleep_minutes = random.randint(1, 5)
                logger.info(f"Спим {sleep_minutes} минут перед скачиванием {link}")
                sleep(sleep_minutes * 60)
                try:
                    get_content(link, username)
                    telegram_ids = get_telegram_ids_by_username(username)
                    for telegram_id in telegram_ids:
                        try:
                            if folder_has_files(username, link):
                                run_coroutine_threadsafe(
                                    bot.send_message(chat_id=telegram_id, text=f"Пост от {username}"), loop)
                                run_coroutine_threadsafe(
                                    send_content(f"{username}-{link}", telegram_id, bot, delete=False), loop)
                            else:
                                logger.warning(f"Не удалось скачать контент {username}-{link}")
                        except Exception as e:
                            logger.error(e)
                except Exception as e:
                    logger.error(f"Ошибка при скачивании {link}: {e}")

        try:
            save_cookies(driver)
        except Exception:
            logger.exception("Не удалось сохранить куки")

        sleep_minutes = random.randint(5, 10)
        logger.info(f"Спим {sleep_minutes} минут перед следующей итерацией")
        sleep(sleep_minutes * 60)
