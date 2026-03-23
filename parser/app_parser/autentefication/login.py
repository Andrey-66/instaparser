import logging
import os
import random
import pyotp
from contextlib import suppress
from time import sleep

from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

from app_parser.utils.selenium_utils import open_page

logger = logging.getLogger(__name__)

def check_login(driver):
    with suppress(NoSuchElementException, TimeoutException):
        open_page(driver, 'https://www.instagram.com/accounts/edit/', __name__)
        sleep(random.uniform(5, 10))
        driver.find_element(By.XPATH, "//h2[text()='Edit profile']")
        logger.info('Авторизация не требуется')
        return True
    return False

def find_login_page(driver):
    wait = WebDriverWait(driver, 10)
    try_num = 0
    while try_num < 5:
        try:
            logger.info(f'Пытаюсь найти страницу авторизации {try_num + 1}/5')
            xpath_selector = "//div[@role='button'][descendant::*[text()='Использовать другой профиль' or text()='Use another profile']]"
            button = wait.until(expected_conditions.element_to_be_clickable((By.XPATH, xpath_selector)))
            if not button:
                try_num += 1
                continue
            button.click()
            logger.info("Нашёл страницу авторизации, нажал продолжить")
            return True
        except NoSuchElementException:
            try_num += 1
        except TimeoutException:
            try_num += 1
    return False


def login(driver, retry=False):
    emails = os.getenv("EMAILS").split(' ')
    passwords = os.getenv("PASSWORDS").split(' ')
    secrets = os.getenv("SECRETS").split(' ')
    random_num = random.randint(0, len(emails) - 1)
    email = emails[random_num]
    if not emails:
        logger.error("Environment variable EMAILS is not set or empty. Please check your .env file.")
        raise EnvironmentError("Environment variable EMAILS is not set or empty. Please check your .env file.")
    password = passwords[random_num]
    if not password:
        logger.error(f"Environment variable PASSWORDS is empty for {email}. Please check your .env file.")
        raise EnvironmentError(f"Environment variable PASSWORDS is empty for {email}. Please check your .env file.")
    secret = secrets[random_num]
    if not secret:
        logger.error(f"Environment variable SECRETS is empty for {email}. Please check your .env file.")
        raise EnvironmentError(f"Environment variable PASSWORDS is empty for {email}. Please check your .env file.")
    logger.info(str(email), str(password), str(secret))
    wait = WebDriverWait(driver, 10)
    email_xpath_selector = """
        //input[contains(@aria-label, 'Mobile') or contains(@aria-label, 'username') or contains(@aria-label, 'email')] |
        //input[@name='username' or @name='email' or @type='email'] |
        //input[contains(@placeholder, 'username') or contains(@placeholder, 'email')]
        """

    password_xpath_selector = """
        //input[@type='password'] |
        //input[contains(@aria-label, 'Password') or contains(@aria-label, 'Пароль')] |
        //input[@name='password']
        """

    two_fa_xpath_selector = """
        //input[contains(@aria-label, 'Security') or contains(@aria-label, 'Code') or contains(@aria-label, 'Код')] |
        //input[@name='verificationCode' or @name='code' or contains(@placeholder, 'Code')]
        """
    try:
        logger.debug('Ищу куда ввести почту')
        email_input = wait.until(expected_conditions.element_to_be_clickable((By.XPATH, email_xpath_selector)))
        if not email_input:
            raise NoSuchElementException
        email_input.send_keys(email + '\n')
        logger.debug(f'Ввёл почту {email}')
    except (NoSuchElementException, TimeoutException):
        os.makedirs("content/screens", exist_ok=True)
        driver.save_screenshot(os.path.join("content/screens", "email.png"))
        logger.debug('Не нашёл куда ввести почту, сделал скрин email.png')
    sleep(5)
    try:
        logger.debug('Ищу куда ввести пароль')
        password_input = wait.until(expected_conditions.element_to_be_clickable((By.XPATH, password_xpath_selector)))
        if not password_input:
            raise NoSuchElementException
        password_input.send_keys(password + '\n')
        logger.debug('Ввёл пароль')
    except (NoSuchElementException, TimeoutException):
        os.makedirs("content/screens", exist_ok=True)
        driver.save_screenshot(os.path.join("content/screens", "password.png"))
        logger.debug('Не нашёл куда ввести пароль, сделал скрин password.png')
    sleep(5)
    try:
        logger.debug('Ищу куда ввести 2fa код')
        two_fa_input = wait.until(expected_conditions.element_to_be_clickable((By.XPATH, two_fa_xpath_selector)))
        if not two_fa_input:
            raise NoSuchElementException
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        two_fa_input.send_keys(current_code + '\n')
        logger.debug('Ввёл 2fa код')
    except (NoSuchElementException, TimeoutException):
        os.makedirs("content/screens", exist_ok=True)
        driver.save_screenshot(os.path.join("content/screens", "2fa.png"))
        logger.debug('Не нашёл куда 2fa код почту, сделал скрин 2fa.png')
    if retry:
        sleep(5)
        login(driver, retry=False)
