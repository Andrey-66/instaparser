import os
import secrets
import string
import subprocess
import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import logging

from app_parser.autentefication.cooke import load_cookies, save_cookies
from app_parser.autentefication.login import check_login, find_login_page, login

logger = logging.getLogger(__name__)


class DriverManager:
    def __init__(self):
        self.driver = None
        self.base_url = "https://www.instagram.com"
        self._xvfb_proc = None
        self._vnc_proc = None
        self._novnc_proc = None

    def _kill_zombie_chromes(self):
        """Убивает зависшие процессы Chrome/Chromium перед новым запуском"""
        try:
            subprocess.run(
                ['pkill', '-f', 'chromium'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(1)
        except Exception:
            pass

    def create_driver(self, debug=False):
        """Создает новый экземпляр драйвера"""
        if not debug:
            self._kill_zombie_chromes()

        chrome_options = Options()

        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1280,800")
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disk-cache-size=1")
        chrome_options.add_argument("--media-cache-size=1")
        # Поднято с 256 до 512 в 818c04c в надежде, что дело в GC-трэшинге на
        # 1 vCPU — но зависания (Read timed out >120с) повторились и с 512,
        # без OOM и без свопа (см. docker-compose.yml: parser), так что тесный
        # heap не был (единственной) причиной. Оставляем 512 как разумный
        # запас, но реальная причина зависаний chromedriver'а ещё не найдена.
        # Картинки НЕ отключаем: selenium_download.py читает naturalWidth и
        # рисует img на canvas, чтобы вытащить байты — для этого браузер должен
        # реально их декодировать.
        chrome_options.add_argument("--js-flags=--max-old-space-size=512")
        chrome_options.binary_location = "/usr/bin/chromium"

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')

        chrome_options.add_argument("--page-load-strategy=normal")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        try:
            if debug:
                chrome_options.binary_location = 'E:\projects\instaparser\chrome-win64\chrome.exe'
            else:
                chrome_options.add_argument("--headless=old")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            logger.info("WebDriver created successfully")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to create WebDriver: {e}")
            raise

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

    def get_driver(self, debug=False):
        """Получает готовый к работе драйвер"""
        try:
            self.create_driver(debug)
            if not self.authenticate():
                raise Exception("Instagram authentication failed")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to get driver: {e}")
            self.quit_driver()
            raise

    def start_vnc_session(self) -> str:
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))

        # Stale files from a previous ungracefully-killed Xvfb make it refuse to bind :99
        for stale in ("/tmp/.X99-lock", "/tmp/.X11-unix/X99"):
            try:
                os.remove(stale)
            except FileNotFoundError:
                pass

        self._xvfb_proc = subprocess.Popen(
            ['Xvfb', ':99', '-screen', '0', '1280x800x24'],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        deadline = time.time() + 10
        while time.time() < deadline and not os.path.exists("/tmp/.X11-unix/X99"):
            if self._xvfb_proc.poll() is not None:
                stderr = self._xvfb_proc.stderr.read().decode(errors="replace")
                raise RuntimeError(f"Xvfb exited immediately (code {self._xvfb_proc.returncode}): {stderr}")
            time.sleep(0.2)
        if not os.path.exists("/tmp/.X11-unix/X99"):
            raise RuntimeError("Xvfb did not create display :99 within 10s")

        self._vnc_proc = subprocess.Popen(
            ['x11vnc', '-display', ':99', '-forever', '-passwd', password,
             '-rfbport', '5900', '-noxdamage', '-quiet'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(1)

        self._novnc_proc = subprocess.Popen(
            ['websockify', '--web=/usr/share/novnc/', '6080', 'localhost:5900'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        time.sleep(1)

        logger.info("VNC session started on :6080")
        return password

    def start_manual_chrome(self):
        os.environ['DISPLAY'] = ':99'

        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,800")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.binary_location = "/usr/bin/chromium"

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(60)
        try:
            self.driver.get("https://www.instagram.com/accounts/login/")
            logger.info("Manual Chrome session started, navigated to Instagram login")
        except TimeoutException:
            # Страница ещё догружается в фоне — админ может подождать/обновить
            # вручную через VNC, не нужно валить всю сессию из-за этого
            logger.warning("Instagram login page is loading slowly, leaving it to finish in the background")

    def stop_vnc_session(self):
        for proc in [self._novnc_proc, self._vnc_proc, self._xvfb_proc]:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()
        self._xvfb_proc = self._vnc_proc = self._novnc_proc = None
        os.environ.pop('DISPLAY', None)
        logger.info("VNC session stopped")

    def quit_driver(self, kill_timeout=15):
        """Закрывает драйвер.

        Если chromedriver уже завис (мёртвое HTTP-соединение), save_cookies()
        и driver.quit() виснут на тех же retry-таймаутах urllib3 (до ~20 минут
        суммарно). Поэтому ждём штатное закрытие ограниченное время в фоновом
        потоке, а если не уложились — убиваем процесс chromedriver напрямую.
        Оставшиеся дочерние процессы chrome подчистит _kill_zombie_chromes()
        перед следующим create_driver().
        """
        if not self.driver:
            return

        driver, self.driver = self.driver, None

        def graceful_shutdown():
            try:
                save_cookies(driver)
            except Exception:
                pass
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")

        shutdown_thread = threading.Thread(target=graceful_shutdown, daemon=True)
        shutdown_thread.start()
        shutdown_thread.join(timeout=kill_timeout)

        if shutdown_thread.is_alive():
            logger.warning(
                f"WebDriver не ответил за {kill_timeout}с, убиваю процесс chromedriver напрямую"
            )
            try:
                driver.service.process.kill()
            except Exception as e:
                logger.error(f"Не удалось убить процесс chromedriver: {e}")
        else:
            logger.info("WebDriver closed")

driver_manager = DriverManager()
