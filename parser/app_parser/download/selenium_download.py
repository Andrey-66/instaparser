import glob
import logging
import os
import time
from random import uniform

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app_parser.download.selenium_wire_download import download_instagram_video_via_network
from app_parser.utils.files import folder_has_files
from app_parser.utils.selenium_utils import open_page

logger = logging.getLogger(__name__)

def selenium_download_media(driver, link, save_dir):
    open_page(driver, link, __name__)
    time.sleep(10)
    urls = clean_and_get_big_imgs(driver, link, save_dir)
    for i, url in enumerate(urls, 1):
        logger.info(f"Big image {i}: {url}")
        selenium_save_image(driver, url, f"{save_dir}/image_{int(time.time_ns())}.jpg")
    return


def clean_and_get_big_imgs(driver, url, save_dir):
    current_post_id = url.split('/')[-2]
    script_reel = """
        let currentId = arguments[0];
        let links = document.querySelectorAll('a[href*="/reel/"]');

        links.forEach(a => {
            let href = a.getAttribute('href');
            if (!href.includes(currentId)) {
                let container = a.closest('div[style*="padding-bottom"], div.html-div'); 
                if (container) {
                    container.remove();
                } else {
                    a.remove();
                }
            }
        });
        """
    script_post = """
            let currentId = arguments[0];
            let links = document.querySelectorAll('a[href*="/p/"]');

            links.forEach(a => {
                let href = a.getAttribute('href');
                if (!href.includes(currentId)) {
                    let container = a.closest('div[style*="padding-bottom"], div.html-div'); 
                    if (container) {
                        container.remove();
                    } else {
                        a.remove();
                    }
                }
            });
            """
    driver.execute_script(script_reel, current_post_id)
    driver.execute_script(script_post, current_post_id)
    logger.info("Similar publications have been removed by the link filter.")

    all_imgs = driver.find_elements(By.TAG_NAME, "img")
    big_images = []

    for img in all_imgs:
        try:
            size = driver.execute_script(
                "return {w: arguments[0].naturalWidth, h: arguments[0].naturalHeight};",
                img
            )

            src = img.get_attribute("src")
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
        time.sleep(uniform(2, 5))
        big_images += clean_and_get_big_imgs(driver, url, save_dir)

    big_images = list(dict.fromkeys(big_images))

    return list(big_images)


def selenium_save_image(driver, image_url, save_path):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(image_url)

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
        time.sleep(2)
        base64_image = driver.execute_script(get_base64_js)

        import base64
        with open(save_path, "wb") as fh:
            fh.write(base64.decodebytes(base64_image.encode()))
        logger.info(f"File saved as: {save_path}")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

def get_text_preview(driver, author_url, post_shortcode, save_dir, download_preview = True):
    open_page(driver, author_url, __name__)
    time.sleep(uniform(3, 6))
    driver.execute_script("window.scrollBy(0, 500);")
    time.sleep(uniform(1, 3))
    driver.execute_script("window.scrollBy(0, 500);")
    time.sleep(uniform(1, 3))
    driver.execute_script("window.scrollBy(0, 500);")
    all_links = driver.find_elements(By.TAG_NAME, "a")
    for link in all_links:
        url = link.get_attribute("href")
        if url and post_shortcode in url:
            try:
                img_tag = link.find_element(By.TAG_NAME, "img")
                caption = img_tag.get_attribute("alt")
                img_src = img_tag.get_attribute("src")
                logger.info(f"✅ Find description: {caption}")
                logger.info(f"🖼️ Link to preview: {img_src}")
                file_path = os.path.join(save_dir, f"text_{int(time.time_ns())}.txt")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(caption)
                logger.info(f"✅ Description saved successfully in: {file_path}")
                if download_preview:
                    selenium_save_image(driver, img_src, f"{save_dir}/image_{int(time.time_ns())}.jpg")
                    logger.info(f"✅ Preview saved successfully in: {save_dir}/image_{int(time.time_ns())}.jpg")
                else:
                    logger.info(f"✅ Don't download the preview.")
                return
            except Exception as e:
                logger.error("This link doesn't have an img tag or it hasn't loaded yet.")
                raise
    return

def selenium_download(driver, url, save_dir, author_name):
    logger.info(f'Selenium download {url}')
    if not url.startswith("http"):
        url = "https://" + url
    if not url.endswith("/"):
        url = url + "/"
    post_shortcode = url.split("/")[-2]
    os.makedirs(save_dir, exist_ok=True)
    try:
        selenium_download_media(driver, url, save_dir)
        if not folder_has_files(save_dir):
            logger.warning('Download via selenium failed')
            return False
    except TimeoutException as e:
        raise e
    except Exception as e:
        logger.warning(f'Download via selenium failed: {e}')
    if not folder_has_files(save_dir):
        return False
    v_temp = os.path.join(save_dir, "temp_video.mp4")
    a_temp = os.path.join(save_dir, "temp_audio.mp3")
    for tmp in [v_temp, a_temp]:
        if os.path.exists(tmp):
            os.remove(tmp)
    files = glob.glob(os.path.join(save_dir, "*.mp4"))
    author_url = f'https://www.instagram.com/{author_name}/'
    try:
        if files:
            get_text_preview(driver, author_url, post_shortcode, save_dir)
        else:
            get_text_preview(driver, author_url, post_shortcode, save_dir, False)
        return True
    except Exception as e:
        return False


def selenium_story_download(driver, url, save_dir):
    open_page(driver, url, 'selenium_story_download')
    time.sleep(1)
    try:
        view_story_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'View story')]"))
        )
        view_story_button.click()
        logger.info("✅ Button 'View story' pressed")
    except TimeoutException:
        logger.info("ℹ️ Button 'View story' not detected")
    except Exception as e:
        logger.info(f"❌ Error while pressing button: {e}")
        return False
    time.sleep(1)
    all_imgs = driver.find_elements(By.TAG_NAME, "img")
    for img in all_imgs:
        try:
            size = driver.execute_script(
                "return {w: arguments[0].naturalWidth, h: arguments[0].naturalHeight};",
                img
            )

            src = img.get_attribute("src")
            if src and size['w'] > 400:
                os.makedirs(save_dir, exist_ok=True)
                selenium_save_image(driver, src, f"{save_dir}/image.jpg")
                return True
        except Exception as e:
            continue
    return False