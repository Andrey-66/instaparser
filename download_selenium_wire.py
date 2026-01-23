import base64
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
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    driver.get(link)
    time.sleep(10)
    driver.execute_script("window.scrollBy(0, 100);")
    time.sleep(1)
    driver.execute_script("window.scrollBy(0, -100);")
    time.sleep(30)
    try:
        close_button = driver.find_element(By.XPATH, "//*[@aria-label='Закрыть']")
        close_button.click()
        logger.info("Кнопка 'Закрыть' нажата")
    except Exception:
        logger.info("Кнопка 'Закрыть' не найдена")
    time.sleep(10)
    try:
        mute_button = driver.find_element(By.XPATH, "//*[@aria-label='Звук выключен']")
        mute_button.click()
        logger.info("Кнопка 'Звук' нажата")
    except Exception:
        logger.info("Кнопка 'Звук' не найдена")
    time.sleep(20)
    logger.info('Начинаю искать видео')

    video_url = None
    audio_url = None
    max_video_bitrate = 0

    logger.info(f"Сканирую запросы (глубокий анализ) для {link}...")

    for request in driver.requests:
        if not request.response:
            continue

        url = request.url
        content_type = request.response.headers.get('Content-Type', '').lower()


        if 'video' in content_type or 'audio' in content_type or '.mp4' in url:
            clean_url = re.sub(r'&bytestart=\d+&byteend=\d+', '', url)


            is_audio = False

            efg_match = re.search(r'efg=([^&]+)', clean_url)
            if efg_match:
                try:
                    encoded_efg = efg_match.group(1)
                    decoded_efg = base64.b64decode(encoded_efg + "===").decode('utf-8', errors='ignore')

                    if 'audio' in decoded_efg.lower():
                        is_audio = True
                except Exception:
                    pass

            if not is_audio and 'audio' in clean_url.lower():
                is_audio = True

            if is_audio:
                audio_url = clean_url
            else:
                bitrate_match = re.search(r'bitrate=(\d+)', clean_url)
                bitrate = int(bitrate_match.group(1)) if bitrate_match else 0

                if bitrate > max_video_bitrate:
                    max_video_bitrate = bitrate
                    video_url = clean_url

    if not video_url:
        for request in driver.requests:
            if request.response and request.response.headers:
                content_type = request.response.headers.get('Content-Type', '').lower()

                if 'video' in content_type:
                    url = request.url
                    clean_url = re.sub(r'&bytestart=\d+&byteend=\d+', '', url)

                    if 'audio' in clean_url:
                        audio_url = clean_url
                    else:
                        video_url = clean_url


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
