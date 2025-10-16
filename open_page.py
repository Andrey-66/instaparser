from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

def open_page(driver, url):
    driver.get(url)
    wait = WebDriverWait(driver, 60)
    wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
    print(f"🔄 Страница {url} загружена")


def reject_cookies(driver, max_wait=15):
    # 3. Пытаемся нажать кнопку "Отклонить cookie", если она есть
    cookie_texts = [
        "Отклонить", "Отклонить все", "Отказаться", "Отклонить cookies",
        "Reject", "Reject all", "Decline", "Decline optional", "Отклонить необязательные файлы cookie"
    ]

    def try_click_cookie_button_in_context(context_desc):
        for text in cookie_texts:
            try:
                button = driver.find_element(By.XPATH, f"//button[text()='{text}']")
                button.click()
                print(f"✅ Кнопка cookie нажата: '{text}' ({context_desc})")
                return True
            except NoSuchElementException:
                continue
        return False

    # Сначала пробуем на основной странице
    if try_click_cookie_button_in_context("основная страница"):
        return

    # 4. Если не получилось — ищем в iframe
    print("🔍 Ищем кнопку отклонения cookie в iframe...")
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for iframe in iframes:
        try:
            driver.switch_to.frame(iframe)
            if try_click_cookie_button_in_context("в iframe"):
                driver.switch_to.default_content()
                return
            driver.switch_to.default_content()
        except Exception as e:
            driver.switch_to.default_content()
            continue

    print("ℹ️ Кнопка отклонения cookie не найдена — ничего не нажато.")