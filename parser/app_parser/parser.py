import re
import time
from contextlib import suppress
from datetime import datetime
from random import uniform

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app_parser.api.posts import create_post, get_posts, update_post, delete_post
from app_parser.download.instaloader_download import instaloader_download
from app_parser.download.iqsaved_download import post_iqsaved_download, story_iqsaved_download
from app_parser.download.selenium_download import selenium_download, selenium_story_download
from app_parser.driver import driver_manager
from app_parser.utils.files import delete_directory
from app_parser.utils.selenium_utils import open_page
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging

from app_parser.api.profiles import get_profile, update_profile

logger = logging.getLogger(__name__)


class InstagramParser:
    def __init__(self, limit=10, debug=False):
        self.limit = limit
        self.driver = None
        self.debug = debug

    def __enter__(self):
        self.driver = driver_manager.get_driver(self.debug)
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
                stories = self.get_stories(profile_name)
                for story in stories:
                    if story in existed_posts_ids:
                        continue
                    create_post(
                        instagram_post_id=story,
                        profile_id=profile.get('id'),
                        media_type='story',
                    )

                logger.info(f"{profile_name} stories: {stories}")
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

    def get_stories(self, profile_name):
        open_page(self.driver, f'https://www.instagram.com/stories/{profile_name}/', 'get_stories')
        current_url = self.driver.current_url
        if current_url != f'https://www.instagram.com/stories/{profile_name}/':
            logger.info(f'No stories for {profile_name}')
            return []
        try:
            view_story_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'View story')]"))
            )
            view_story_button.click()
            logger.info("✅ Button 'View story' pressed")
        except TimeoutException:
            logger.info("ℹ️ Button 'View story' not detected")
        except Exception as e:
            logger.info(f"❌ Error while pressing button: {e}")
            return []
        time.sleep(1)
        actions = ActionChains(self.driver)
        pattern = r'^https://www\.instagram\.com/stories/[^/]+/\d+/?/?.*$'
        stories = []
        actions.send_keys(Keys.ARROW_RIGHT).perform()
        if bool(re.match(pattern, self.driver.current_url)):
            time.sleep(1)
            actions.send_keys(Keys.ARROW_LEFT).perform()
            while re.match(pattern, self.driver.current_url):
                time.sleep(1)
                story_url = self.driver.current_url
                if not story_url.endswith('/'):
                    story_url = story_url + '/'
                stories.append(story_url)
                actions.send_keys(Keys.ARROW_RIGHT).perform()
            return stories
        else:
            open_page(self.driver, f'https://www.instagram.com/stories/{profile_name}/', 'get_stories')
            try:
                view_story_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'View story')]"))
                )
                view_story_button.click()
                logger.info("✅ Button 'View story' pressed")
            except TimeoutException:
                logger.info("ℹ️ Button 'View story' not detected")
            except Exception as e:
                logger.info(f"❌ Error while pressing button: {e}")
                return []
            actions.send_keys(Keys.TAB).perform()
            focused_element = None
            try:
                while not focused_element or focused_element.accessible_name != 'Direct':
                    time.sleep(0.2)
                    actions.send_keys(Keys.TAB).perform()
                    focused_element = self.driver.switch_to.active_element
                    if not self.driver.current_url.startswith(f'https://www.instagram.com/stories/{profile_name}/'):
                        return []
                focused_element.click()
                time.sleep(3)
                self.driver.switch_to.active_element.send_keys('gwawladebola\n')
                time.sleep(5)
                user_element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), 'gwawladebola')]"))
                )
                user_element.click()
                time.sleep(1)
                send_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[text()='Send']"))
                )
                time.sleep(1)
                send_button.click()
                logger.info("✅ Send button clicked")
            except Exception as e:
                logger.error(f'Error while getting story {profile_name}: {e}')
                return []
            open_page(self.driver, 'https://www.instagram.com/direct/t/18016020287648589/', 'get_stories')
            time.sleep(5)
            links = self.driver.find_elements(By.TAG_NAME, "a")
            with suppress(TimeoutException):
                not_now_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Not Now']"))
                )
                not_now_button.click()
                logger.info("✅ 'Not Now' button clicked")
            story_urls = []
            for link in links:
                href = link.get_attribute("href")
                if href and re.match(pattern, href):
                    story_url = '/'.join(href.split('/')[0:6])
                    story_url = story_url.split('?')[0]
                    story_urls.append(story_url)

            if story_urls:
                story_url = story_urls[-1]
                if not story_url.endswith('/'):
                    story_url = story_url + '/'
                stories.append(story_url)
                return stories
            return []

    def parse_posts(self, posts):
        for post in posts:
            sleep_minutes = uniform(60, 240)
            sleep_minutes /= 60
            logger.info(f"Sleep {sleep_minutes / 60} minutes")
            time.sleep(sleep_minutes)
            url = post.get('instagram_post_id')
            author_name = post.get('profile_username')
            errors_count = post.get('errors_count')
            media_type = post.get('media_type')
            username = post.get('profile_username')
            if not url.endswith("/"):
                url += "/"
            if media_type == 'story':
                story_id = url.split('/')[-2]
                folder = f"../content/{username}-{story_id}"
                open_page(self.driver, url, __name__)
                time.sleep(1)
                if self.driver.current_url != url:
                    logger.info(f'Story {url} is not found')
                    delete_directory(folder)
                    delete_post(post.get('id'))
                    continue

                if selenium_story_download(self.driver, url, folder):
                    update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                    logger.info(f"Selenium download success for {story_id}")
                    continue

                if story_iqsaved_download(self.driver, story_id ,author_name, folder):
                    update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                    logger.info(f"Selenium download success for {story_id}")
                    continue

                logger.warning(f'Story {url} is not downloaded')
                delete_directory(folder)
                update_post(post.get('id'), is_downloaded=False, errors_count=errors_count + 1)
                continue

            shortcode = url.split("/")[-2]
            folder = f"../content/{username}-{shortcode}"
            try:
                if instaloader_download(shortcode, folder):
                    logger.info(f"Instaloader download success for {shortcode}")
                    update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                    continue
                author_url = f'https://www.instagram.com/{author_name}/'
                if media_type == 'reel':
                    if post_iqsaved_download(self.driver, shortcode, author_url, folder):
                        update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                        logger.info(f"Iqsaved download success for {shortcode}")
                        continue
                    if selenium_download(self.driver, url, folder, author_name):
                        update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                        logger.info(f"Selenium download success for {shortcode}")
                        continue
                else:
                    if selenium_download(self.driver, url, folder, author_name):
                        update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                        logger.info(f"Selenium download success for {shortcode}")
                        continue
                    if post_iqsaved_download(self.driver, shortcode, author_url, folder):
                        update_post(post.get('id'), is_downloaded=True, file_path=folder[3:], errors_count=0)
                        logger.info(f"Iqsaved download success for {shortcode}")
                        continue
                delete_directory(folder)
                update_post(post.get('id'), is_downloaded=False, errors_count=errors_count + 1)
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
