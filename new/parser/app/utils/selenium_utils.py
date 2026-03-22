from selenium.webdriver.support.wait import WebDriverWait
import time
import functools
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
    StaleElementReferenceException
)
import logging
logger = logging.getLogger(__name__)


def open_page(driver, url):
    driver.get(url)
    wait = WebDriverWait(driver, 60)
    wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
    logger.info(f"🔄 Page {url} loaded")


def retry_on_exception(max_retries=3, delay=5, exceptions=(Exception,)):
    """Декоратор для retry с логированием"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")

                    if attempt < max_retries:
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")

            raise last_exception

        return wrapper

    return decorator


def safe_driver_operation(func):
    """Декоратор для безопасной работы с драйвером"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from app.driver import driver_manager

        driver = None
        try:
            # Получаем драйвер
            driver = driver_manager.get_driver()
            result = func(driver, *args, **kwargs)
            return result
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"WebDriver error in {func.__name__}: {e}")
            driver_manager.quit_driver()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            driver_manager.quit_driver()
            raise
        finally:
            pass

    return wrapper