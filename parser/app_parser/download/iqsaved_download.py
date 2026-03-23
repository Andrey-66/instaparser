import glob
import logging
import os
import random
import time

import requests
from selenium.webdriver.common.by import By

from app_parser.download.selenium_download import get_text_preview
from app_parser.utils.selenium_utils import open_page

logger = logging.getLogger(__name__)


def iqsaved_download(driver, post_shortcode, author_url, dir_path=None):
    try:
        logger.info(f'Iqsaved download {post_shortcode}')
        open_page(driver, f'https://iqsaved.com/download-posts/{post_shortcode}/', __name__)
        time.sleep(random.uniform(3, 6))
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(random.uniform(1, 3))
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(random.uniform(1, 3))
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(random.uniform(3, 6))
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(random.uniform(1, 3))
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(random.uniform(1, 3))
        driver.execute_script("window.scrollBy(0, 500);")

        video_elements = driver.find_elements(By.XPATH,
                                              "//a[contains(text(), 'Download video') or contains(text(), 'Скачать видео')]")

        photo_elements = driver.find_elements(By.XPATH,
                                              "//a[contains(text(), 'Download photo') or contains(text(), 'Скачать фото')]")

        logger.debug(f"Find video: {len(video_elements)}")
        logger.debug(f"Find photo: {len(photo_elements)}")

        video_links = []
        for i, elem in enumerate(video_elements):
            try:
                link_info = elem.get_attribute('href')
                video_links.append(link_info)
            except Exception as e:
                logger.error(f"Error while getting video url {i + 1}: {e}")
                return False

        photo_links = []
        for i, elem in enumerate(photo_elements):
            try:
                link_info = elem.get_attribute('href')
                photo_links.append(link_info)
            except Exception as e:
                logger.error(f"Error while getting photo url {i + 1}: {e}")
                return False

        os.makedirs(dir_path, exist_ok=True)
        for link in photo_links:
            response = requests.get(link, stream=True)
            file_path = os.path.join(dir_path, f"photo_{int(time.time_ns())}.jpg")
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.debug(f"✅ Photo saved successfully in: {file_path}")
            time.sleep(5)
        for link in video_links:
            response = requests.get(link, stream=True)
            response.raise_for_status()
            file_path = os.path.join(dir_path, f"video_{int(time.time_ns())}.mp4")
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"✅ Video saved successfully in: {file_path}")
            time.sleep(5)
        files = glob.glob(os.path.join(dir_path, "*.mp4"))
        if files:
            get_text_preview(driver, author_url, post_shortcode, dir_path)
        else:
            get_text_preview(driver, author_url, post_shortcode, dir_path, False)
        time.sleep(5)
        return True
    except Exception as e:
        logger.error(f"Error while getting post: {e}")
        return False
