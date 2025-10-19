import os
from time import sleep

from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv

from logger import logger


def check_login(driver):
    try_num = 0
    wait = WebDriverWait(driver, 10)
    while try_num < 5:
        try:
            wait.until(EC.presence_of_element_located((By.NAME, "username")))
            logger.info("Нашёл страницу авторизации")
            login(driver)
            return
        except NoSuchElementException:
            try_num += 1
        except TimeoutException:
            return



def login(driver):
    load_dotenv()
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    wait = WebDriverWait(driver, 5)
    driver.get("https://www.instagram.com/")
    login_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    login_input.send_keys(email)
    password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    password_input.send_keys(password + "\n")
    sleep(50)
