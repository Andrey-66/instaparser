import glob
import os
import random
import time
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from download_selenium_wire import download_instagram_video_via_network

from open_page import open_page
from logger import logger


def selenium_download_media(driver, link, save_dir):
    open_page(driver, link)
    sleep(10)
    # 1. Находим основной блок публикации
    urls = clean_and_get_big_imgs(driver, link, save_dir)
    for i, url in enumerate(urls, 1):
        logger.info(f"Большая картинка {i}: {url}")
        selenium_save_image(driver, url, f"{save_dir}/image_{int(time.time_ns())}.jpg")
    return


def clean_and_get_big_imgs(driver, url, save_dir):
    # 2. Удаляем блок "Ещё публикации" через JavaScript
    # Мы ищем заголовки h2 или h3, содержащие текст "Ещё" или "More"
    current_post_id = url.split('/p/')[1].split('/')[0]
    script = """
        let currentId = arguments[0];
        // Находим все ссылки на посты
        let links = document.querySelectorAll('a[href*="/p/"]');

        links.forEach(a => {
            let href = a.getAttribute('href');
            // Если ссылка ведет на ДРУГОЙ пост (не содержит id текущего)
            if (!href.includes(currentId)) {
                // Ищем самый верхний родительский контейнер, который похож на карточку поста
                // Обычно это div с определенным набором классов, но мы удалим ближайший крупный блок
                let container = a.closest('div[style*="padding-bottom"], div.html-div'); 
                if (container) {
                    container.remove();
                } else {
                    a.remove(); // Если контейнер не найден, удаляем хотя бы саму ссылку
                }
            }
        });
        """
    driver.execute_script(script, current_post_id)
    logger.info("Похожие публикации удалены по фильтру ссылок.")

    # 3. Собираем все img, которые остались на странице
    all_imgs = driver.find_elements(By.TAG_NAME, "img")
    big_images = []

    for img in all_imgs:
        try:
            # Получаем реальные размеры картинки через JS
            size = driver.execute_script(
                "return {w: arguments[0].naturalWidth, h: arguments[0].naturalHeight};",
                img
            )

            src = img.get_attribute("src")
            # Фильтр: берем только те, что шире 400px (обычно посты 640-1080px)
            if src and size['w'] > 400:
                big_images.append(src)
        except:
            continue

    next_buttons = driver.find_elements(By.XPATH, "//button[@aria-label='Далее' or @aria-label='Next']")

    if not big_images:
        download_instagram_video_via_network(url, save_dir)


    if next_buttons:
        next_buttons[0].click()
        logger.info("Нажал кнопку 'Далее'")
        sleep(random.uniform(2, 5))
        big_images += clean_and_get_big_imgs(driver, url, save_dir)

    big_images = list(dict.fromkeys(big_images))

    return list(big_images)


def selenium_save_image(driver, image_url, save_path):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(image_url)

    # Скрипт скачивает данные картинки прямо из браузера
    get_base64_js = """
    var canvas = document.createElement('canvas');
    var img = document.querySelector('img');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    return canvas.toDataURL('image/jpeg').replace(/^data:image\/jpeg;base64,/, "");
    """

    try:
        sleep(2)  # Даем картинке отрисоваться
        base64_image = driver.execute_script(get_base64_js)

        import base64
        with open(save_path, "wb") as fh:
            fh.write(base64.decodebytes(base64_image.encode()))
        logger.info(f"Файл сохранен в: {save_path}")

    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

def find_profile(driver, post_url):
    try:
        open_page(driver, post_url)
        sleep(random.uniform(5, 15))
        author_element = driver.find_element(By.XPATH, "//div[contains(text(), 'Ещё публикации от')]//a")
        author_url = author_element.get_attribute("href")
        author_name = author_element.text
        return author_name, author_url
    except:
        screen_name = f'{int(time.time_ns())}.png'
        os.makedirs("content/screens", exist_ok=True)
        driver.save_screenshot(os.path.join("content/screens", screen_name))
        logger.error(f"Не удалось найти блок автора по тексту, сделал скрин {screen_name}")


def get_text_preview(driver, author_url, post_shortcode, save_dir, download_preview = True):
    open_page(driver, author_url)
    sleep(random.uniform(3, 6))
    driver.execute_script("window.scrollBy(0, 500);")
    sleep(random.uniform(1, 3))
    driver.execute_script("window.scrollBy(0, 500);")
    sleep(random.uniform(1, 3))
    driver.execute_script("window.scrollBy(0, 500);")
    all_links = driver.find_elements(By.TAG_NAME, "a")
    for link in all_links:
        url = link.get_attribute("href")
        if url and post_shortcode in url:
            try:
                img_tag = link.find_element(By.TAG_NAME, "img")
                caption = img_tag.get_attribute("alt")
                img_src = img_tag.get_attribute("src")
                logger.debug(f"✅ Описание найдено: {caption}")
                logger.debug(f"🖼️ Ссылка на превью: {img_src}")
                file_path = os.path.join(save_dir, f"text_{int(time.time_ns())}.txt")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(caption)
                logger.info(f"✅ Описание успешно сохранено в: {file_path}")
                if download_preview:
                    selenium_save_image(driver, img_src, f"{save_dir}/image_{int(time.time_ns())}.jpg")
                    logger.info(f"✅ Превью успешно сохранено в: {save_dir}/image_{int(time.time_ns())}.jpg")
                return
            except Exception as e:
                logger.error("В этой ссылке нет тега img или он еще не прогрузился")

    if author_url.endswith("reels/"):
        return
    get_text_preview(driver, author_url, post_shortcode, save_dir)


def selenium_download(driver, url, save_dir=None):
    logger.info(f'Сохраняю {url}')
    author_name, author_url = find_profile(driver, url)
    post_shortcode = url.split("/")[-2]
    if not save_dir:
        save_dir = f'content/{author_name}-{post_shortcode}'
    os.makedirs(save_dir, exist_ok=True)
    selenium_download_media(driver, url, save_dir)
    files = glob.glob(os.path.join(save_dir, "*.mp4"))
    if files:
        get_text_preview(driver, author_url, post_shortcode, save_dir)
    else:
        get_text_preview(driver, author_url, post_shortcode, save_dir, False)
