import time
from datetime import datetime
from random import uniform

from selenium.webdriver.common.by import By

from app_parser.api.posts import create_post, get_posts, update_post
from app_parser.download.instaloader_download import instaloader_download
from app_parser.download.iqsaved_download import iqsaved_download
from app_parser.download.selenium_download import selenium_download
from app_parser.driver import driver_manager
from app_parser.utils.files import delete_directory
from app_parser.utils.selenium_utils import open_page
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging

from app_parser.api.profiles import get_profile, update_profile

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
        for profile_name in profiles_names:
            try:
                profile = get_profile(profile_name)
                existed_posts = get_posts(profile_id=profile.get('id'))
                existed_posts_ids = [post['instagram_post_id'] for post in existed_posts]
                posts = self.get_links(f'https://instagram.com/{profile_name}/', limit, exclude='/reel/')
                reels = self.get_links(f'https://instagram.com/{profile_name}/reels', limit, exclude='/p/')
                logger.info(f"{profile_name} posts: {posts} reels: {reels}")
                if not profile:
                    raise
                if not update_profile(profile_name, last_parsed=datetime.now().isoformat()):
                    raise
                for post in posts:
                    if post in existed_posts_ids:
                        continue
                    create_post(
                        instagram_post_id=post,
                        profile_id=profile.get('id'),
                        media_type='post',
                    )
                for reel in reels:
                    if reel in existed_posts_ids:
                        continue
                    create_post(
                        instagram_post_id=reel,
                        profile_id=profile.get('id'),
                        media_type='reel',
                    )
                update_profile(profile_name, errors_count=0)
            except TimeoutException as e:
                logger.warning('Driver timeout, restarting...')
                if self.driver:
                    driver_manager.quit_driver()
                time.sleep(5)
                self.driver = driver_manager.get_driver()
            except Exception as e:
                logger.error(f"Failed to parse profiles: {e}")
                profile = get_profile(profile_name)
                update_profile(profile_name, errors_count=profile.get('errors_count')+1)
                raise

    def get_links(self, url, limit, exclude=''):
        open_page(self.driver, url, __name__)
        time.sleep(10)
        try:
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Ошибка прокрутки для {url}: {e}")
            raise

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

    def parse_posts(self, posts):
        for post in posts:
            sleep_minutes = uniform(60, 240)
            logger.info(f"Sleep {sleep_minutes / 60} minutes")
            time.sleep(sleep_minutes)
            url = post.get('instagram_post_id')
            author_name = post.get('profile_username')
            errors_count = post.get('errors_count')
            media_type = post.get('media_type')
            if not url.endswith("/"):
                url += "/"
            shortcode = url.split("/")[-2]
            username = post.get('profile_username')
            folder = f"../content/{username}-{shortcode}"
            try:
                if instaloader_download(shortcode, folder):
                    update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                    continue
                author_url = f'https://www.instagram.com/{author_name}/'
                if media_type == 'reel':
                    if iqsaved_download(self.driver, shortcode, author_url, folder):
                        update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                        continue
                    if selenium_download(self.driver, url, folder, author_name):
                        update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                        continue
                else:
                    if selenium_download(self.driver, url, folder, author_name):
                        update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                        continue
                    if iqsaved_download(self.driver, shortcode, author_url, folder):
                        update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                        continue
                delete_directory(folder)
                update_post(post.get('id'), is_downloaded=False, errors_count=errors_count+1)
            except TimeoutException as e:
                delete_directory(folder)
                update_post(post.get('id'), is_downloaded=False, errors_count=errors_count + 1)
                logger.warning('Driver timeout, restarting...')
                logger.warning(f'Skipping post {url}')
                if self.driver:
                    driver_manager.quit_driver()
                time.sleep(5)
                self.driver = driver_manager.get_driver()
            except Exception as e:
                logger.error(f"Failed to parse posts: {e}")
                delete_directory(folder)
                update_post(post.get('id'), is_downloaded=False, errors_count=errors_count + 1)
