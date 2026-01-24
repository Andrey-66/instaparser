import base64
import json
import os
import re

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from selenium.webdriver.common.by import By

from seleniumwire import webdriver
import time

from logger import logger


def download_instagram_video_via_network(link, folder_path):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(options=options)

    driver.get(link)
    time.sleep(10)
    driver.execute_script("window.scrollBy(0, 100);")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, -100);")
    time.sleep(30)
    try:
        close_button = driver.find_element(By.XPATH, "//*[@aria-label='Закрыть' or @aria-label='Close']")
        close_button.click()
        logger.info("Кнопка 'Закрыть' нажата")
    except Exception:
        logger.info("Кнопка 'Закрыть' не найдена")
    time.sleep(10)
    try:
        mute_button = driver.find_element(By.XPATH, "//*[@aria-label='Звук выключен' or @aria-label='Audio is muted']")
        mute_button.click()
        logger.info("Кнопка 'Звук' нажата")
    except Exception:
        logger.info("Кнопка 'Звук' не найдена")
    time.sleep(20)
    logger.info('Начинаю искать видео')

    video_url = None
    audio_url = None
    max_video_bitrate = 0

    os.makedirs("content/screens", exist_ok=True)
    driver.save_screenshot(os.path.join("content/screens", f"123.png"))
    logger.info(f"Сканирую запросы (глубокий анализ) для {link}...")

    for request in driver.requests:
        if not request.response:
            continue

        url = request.url
        content_type = request.response.headers.get('Content-Type', '').lower()

        if 'video' in content_type or 'audio' in content_type or '.mp4' in url:
            clean_url = re.sub(r'&bytestart=\d+&byteend=\d+', '', url)
            efg_match = re.search(r'efg=([^&]+)', clean_url)

            if efg_match:
                try:
                    # Декодируем efg
                    encoded_efg = efg_match.group(1)
                    decoded_str = base64.b64decode(encoded_efg + "===").decode('utf-8', errors='ignore')

                    # На всякий случай чистим строку от лишних символов в конце (как та '7' в твоем примере)
                    valid_json_str = re.search(r'(\{.*?\})', decoded_str).group(1)
                    efg_data = json.loads(valid_json_str)

                    vencode_tag = efg_data.get("vencode_tag", "").lower()

                    # Прямая логика разделения
                    if "_audio" in vencode_tag:
                        audio_url = clean_url
                        print(f"Найдено аудио: {vencode_tag}")
                    else:
                        # Если это не аудио, проверяем битрейт для видео
                        bitrate = efg_data.get("bitrate", 0)
                        if bitrate > max_video_bitrate:
                            max_video_bitrate = bitrate
                            video_url = clean_url
                            print(f"Найдено видео: {vencode_tag} (Bitrate: {bitrate})")

                except Exception as e:
                    print(f"Ошибка парсинга efg: {e}")


    logger.debug(f'Нашёл исходник видео для {video_url}')
    logger.debug(f'Нашёл исходник аудио для {audio_url}')
    download_media_combined(driver, video_url, audio_url, folder_path)

    driver.quit()


def download_media_combined(driver, video_url, audio_url, folder_path):
    v_temp = os.path.join(folder_path, "temp_video.mp4")
    a_temp = os.path.join(folder_path, "temp_audio.mp3")
    final_path = os.path.join(folder_path, f"video_{int(time.time_ns())}.mp4")

    def fetch_blob_to_file(url, target_path):
        driver.execute_script(f"window.open('{url}');")
        driver.switch_to.window(driver.window_handles[-1])

        js_fetch = """
        var callback = arguments[arguments.length - 1];
        fetch(window.location.href).then(r => r.blob()).then(b => {
            var reader = new FileReader();
            reader.onloadend = () => callback(reader.result.split(',')[1]);
            reader.readAsDataURL(b);
        }).catch(e => callback("error:" + e));
        """
        try:
            driver.set_script_timeout(60)
            b64 = driver.execute_async_script(js_fetch)
            if not b64.startswith("error"):
                with open(target_path, "wb") as f:
                    f.write(base64.b64decode(b64))
                return True
        finally:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        return False

    logger.info("Загрузка видео-потока...")
    if fetch_blob_to_file(video_url, v_temp):
        logger.info("Загрузка аудио-потока...")
        if fetch_blob_to_file(audio_url, a_temp):
            logger.info("Склеивание дорожек...")
            try:
                with VideoFileClip(v_temp) as video:
                    current_fps = video.fps if video.fps else 30
                    with AudioFileClip(a_temp) as audio:
                        final_video = video.set_audio(audio)
                        final_video.write_videofile(final_path, codec="libx264", audio_codec="aac", fps=current_fps,
                                                    logger=None)

                logger.info(f"Готово! Видео со звуком: {final_path}")
                return 0
            except Exception as e:
                logger.error(f"Ошибка при обработке видео: {e}")
            finally:
                if os.path.exists(v_temp): os.remove(v_temp)
                if os.path.exists(a_temp): os.remove(a_temp)
    return 1
