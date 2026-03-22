import os
import time
import json
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging

from app.autentefication.cooke import load_cookies, save_cookies
from app.autentefication.login import check_login, find_login_page, login

logger = logging.getLogger(__name__)


class DriverManager:
    def __init__(self):
        self.driver = None
        self.cookies_file = "instagram_cookies.pkl"
        self.base_url = "https://www.instagram.com"

    def create_driver(self):
        """Создает новый экземпляр драйвера"""
        chrome_options = Options()

        # chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')

        # Таймауты
        chrome_options.add_argument("--page-load-strategy=normal")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            logger.info("WebDriver created successfully")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to create WebDriver: {e}")
            raise

    def load_cookies(self):
        """Загружает сохраненные куки"""
        if not os.path.exists(self.cookies_file):
            logger.info("Cookies file not found")
            return False

        try:
            self.driver.get(self.base_url)
            time.sleep(2)

            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
                loaded_count = 0
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                        loaded_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to load cookie {cookie.get('name', 'unknown')}: {e}")
                        continue

                logger.info(f"Loaded {loaded_count} cookies")

                self.driver.refresh()
                time.sleep(3)

                return loaded_count > 0

        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False

    def save_cookies(self):
        """Сохраняет текущие куки"""
        if not self.driver:
            return

        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info("Cookies saved successfully")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    def authenticate(self):
        """Авторизация в Instagram"""
        if not self.driver:
            self.create_driver()

        try:
            self.driver.get(self.base_url)
            load_cookies(self.driver)
            if check_login(self.driver):
                logger.info("Successfully authenticated with cookies")
                return True

            logger.info("Performing login...")
            if find_login_page(self.driver):
                login(self.driver)
            else:
                os.makedirs("content/screens", exist_ok=True)
                self.driver.save_screenshot(os.path.join("content/screens", "login.png"))
                logger.error('Не смог авторизоваться, скрин login.png, пытаюсь авторизоваться "на дурака"')
                login(self.driver, retry=True)
            time.sleep(5)
            if check_login(self.driver):
                save_cookies(self.driver)
                logger.info("Login successful")
                return True

            logger.error(f"Authentication failed")
            return False

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def get_driver(self):
        """Получает готовый к работе драйвер"""
        try:
            self.create_driver()
            self.authenticate()
            return self.driver
        except Exception as e:
            logger.error(f"Failed to get driver: {e}")
            self.quit_driver()
            raise

    def quit_driver(self):
        """Закрывает драйвер"""
        if self.driver:
            try:
                save_cookies(self.driver)
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None

driver_manager = DriverManager()
