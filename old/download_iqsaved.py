import os
import random
from time import sleep, time_ns

import requests
from selenium.webdriver.common.by import By

from logger import logger
from open_page import open_page


def download_iqsaved(driver, url, save_dir=None):
    logger.info('Сохраняю через iqsaved')
    if not url.startswith("http"):
        url = "https://" + url
    if not url.endswith("/"):
        url = url + "/"
    post_shortcode = url.split("/")[-2]
    open_page(driver, f'https://iqsaved.com/download-posts/{post_shortcode}/')
    sleep(random.uniform(3, 6))
    driver.execute_script("window.scrollBy(0, 500);")
    sleep(random.uniform(1, 3))
    driver.execute_script("window.scrollBy(0, 500);")
    sleep(random.uniform(1, 3))
    driver.execute_script("window.scrollBy(0, 500);")
    sleep(random.uniform(3, 6))
    driver.execute_script("window.scrollBy(0, 500);")
    sleep(random.uniform(1, 3))
    driver.execute_script("window.scrollBy(0, 500);")
    sleep(random.uniform(1, 3))
    driver.execute_script("window.scrollBy(0, 500);")

    video_elements = driver.find_elements(By.XPATH,
                                          "//a[contains(text(), 'Download video') or contains(text(), 'Скачать видео')]")

    photo_elements = driver.find_elements(By.XPATH,
                                          "//a[contains(text(), 'Download photo') or contains(text(), 'Скачать фото')]")

    logger.debug(f"Найдено видео для скачивания: {len(video_elements)}")
    logger.debug(f"Найдено фото для скачивания: {len(photo_elements)}")

    video_links = []
    for i, elem in enumerate(video_elements):
        try:
            link_info = elem.get_attribute('href')
            video_links.append(link_info)
        except Exception as e:
            logger.error(f"Ошибка при обработке видео {i + 1}: {e}")

    photo_links = []
    for i, elem in enumerate(photo_elements):
        try:
            link_info = elem.get_attribute('href')
            photo_links.append(link_info)
        except Exception as e:
            logger.error(f"Ошибка при обработке фото {i + 1}: {e}")

    for link in photo_links:
        response = requests.get(link, stream=True)
        file_path = os.path.join(save_dir, f"photo_{int(time_ns())}.jpg")
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.debug(f"✅ Фото успешно сохранено в: {file_path}")
        sleep(5)
    for link in video_links:
        response = requests.get(link, stream=True)
        response.raise_for_status()
        file_path = os.path.join(save_dir, f"video_{int(time_ns())}.mp4")
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"✅ Видео успешно сохранено в: {file_path}")
        sleep(5)
