import os
import random
from contextlib import suppress
from random import randint
from time import sleep

import pyotp
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv

from logger import logger
from open_page import open_page


def check_login(driver):
    wait = WebDriverWait(driver, 10)
    try:
        open_page(driver, 'https://www.instagram.com/accounts/edit/')
        sleep(random.uniform(5, 10))
        driver.find_element(By.XPATH, "//h2[text()='Edit profile']")
        logger.info('Авторизация не требуется')
        return
    except NoSuchElementException:
        try_num = 0
    except TimeoutException:
        try_num = 0
    while try_num < 5:
        try:
            logger.info(f'Пытаюсь найти страницу авторизации {try_num+1}/5')
            xpath_selector = "//div[@role='button'][descendant::*[text()='Использовать другой профиль' or text()='Use another profile']]"
            button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_selector)))
            if not button:
                try_num += 1
                continue
            button.click()
            logger.info("Нашёл страницу авторизации, нажал продолжить")
            new_login(driver)
            return
        except NoSuchElementException:
            try_num += 1
        except TimeoutException:
            try_num += 1
    try_num = 0
    # while try_num < 5:
    #     try:
    #         logger.info(f'Пытаюсь найти старую страницу авторизации {try_num+1}/5')
    #         wait.until(EC.presence_of_element_located((By.NAME, "username")))
    #         logger.info("Нашёл страницу авторизации")
    #         login(driver)
    #         return
    #     except NoSuchElementException:
    #         try_num += 1
    #     except TimeoutException:
    #         try_num += 1
    os.makedirs("content/screens", exist_ok=True)
    driver.save_screenshot(os.path.join("content/screens", "login.png"))
    logger.error('Не смог авторизоваться, скрин login.png, пытаюсь авторизоваться "на дурака"')
    new_login(driver)



# def old_login(driver):
#     load_dotenv()
#     email = os.getenv("EMAIL")
#     password = os.getenv("PASSWORD")
#     secret = os.getenv("SECRET")
#     wait = WebDriverWait(driver, 5)
#     driver.get("https://www.instagram.com/")
#     login_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
#     login_input.send_keys(email)
#     password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
#     password_input.send_keys(password + "\n")
#     sleep(20)
#     two_fa_input = driver.find_element(By.NAME, "verificationCode")
#     if two_fa_input:
#         totp = pyotp.TOTP(secret)
#         two_fa_code = totp.now()
#         two_fa_input.send_keys(two_fa_code + "\n")
#     sleep(40)

def new_login(driver, repeat=False):
    load_dotenv()
    emails = os.getenv("EMAILS").split(' ')
    passwords = os.getenv("PASSWORDS").split(' ')
    secrets = os.getenv("SECRETS").split(' ')
    random_num = randint(0, len(emails) - 1)
    email=emails[random_num]
    password = passwords[random_num]
    secret = secrets[random_num]
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
        email_input = wait.until(EC.element_to_be_clickable((By.XPATH, email_xpath_selector)))
        if not email_input:
            raise NoSuchElementException
        email_input.send_keys(email+'\n')
        logger.debug(f'Ввёл почту {email}')
    except (NoSuchElementException, TimeoutException):
        os.makedirs("content/screens", exist_ok=True)
        driver.save_screenshot(os.path.join("content/screens", "email.png"))
        logger.debug('Не нашёл куда ввести почту, сделал скрин email.png')
    sleep(5)
    try:
        logger.debug('Ищу куда ввести пароль')
        password_input = wait.until(EC.element_to_be_clickable((By.XPATH, password_xpath_selector)))
        if not password_input:
            raise NoSuchElementException
        password_input.send_keys(password+'\n')
        logger.debug('Ввёл пароль')
    except (NoSuchElementException, TimeoutException):
        os.makedirs("content/screens", exist_ok=True)
        driver.save_screenshot(os.path.join("content/screens", "password.png"))
        logger.debug('Не нашёл куда ввести пароль, сделал скрин password.png')
    sleep(5)
    try:
        logger.debug('Ищу куда ввести 2fa код')
        two_fa_input = wait.until(EC.element_to_be_clickable((By.XPATH, two_fa_xpath_selector)))
        if not two_fa_input:
            raise NoSuchElementException
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        two_fa_input.send_keys(current_code+'\n')
        logger.debug('Ввёл 2fa код')
    except (NoSuchElementException, TimeoutException):
        os.makedirs("content/screens", exist_ok=True)
        driver.save_screenshot(os.path.join("content/screens", "2fa.png"))
        logger.debug('Не нашёл куда 2fa код почту, сделал скрин 2fa.png')

    if repeat:
        new_login(driver)
    sleep(20)
