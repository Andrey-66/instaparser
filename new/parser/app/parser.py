import time

from selenium.webdriver.common.by import By

from app.driver import driver_manager
from app.utils.selenium_utils import retry_on_exception, safe_driver_operation, open_page
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging

logger = logging.getLogger(__name__)


class InstagramParser:
    def __init__(self, limit=10):
        self.limit = limit
        self.driver = None

    def __enter__(self):
        self.driver = driver_manager.get_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            driver_manager.quit_driver()


    def parse_profiles(self, profiles_names, limit=10):
        """Парсит посты профиля"""
        try:
            for profile_name in profiles_names:
                posts = self.get_links(f'https://instagram.com/{profile_name}/', limit, exclude='/reel/')
                reels = self.get_links(f'https://instagram.com/{profile_name}/reels', limit, exclude='/p/')
                logger.info(f"{profile_name} posts: {posts} reels: {reels}")
            return []

        except Exception as e:
            logger.error(f"Failed to parse profiles: {e}")
            driver_manager.quit_driver()
            raise
        finally:
            driver_manager.quit_driver()

    def get_links(self, url, limit, exclude=''):
        open_page(self.driver, url)
        time.sleep(10)
        try:
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Ошибка прокрутки для {url}: {e}")

        links = self.driver.find_elements(By.XPATH, "//a[@href]")
        i = 0
        result = []
        for link in links:
            href = link.get_attribute("href")
            if href and ("/p/" in href or "/reel/" in href):
                if exclude and exclude in href:
                    continue
                i += 1
                result.append(href)
                if i == limit:
                    break
        return result
