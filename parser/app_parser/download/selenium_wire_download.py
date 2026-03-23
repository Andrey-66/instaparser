import base64
import json
import logging
import os
import re
import subprocess

import requests
from selenium.webdriver.common.by import By

from seleniumwire import webdriver
import time


logger = logging.getLogger(__name__)


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
                        logger.debug(f"Найдено аудио: {vencode_tag}")
                    else:
                        # Если это не аудио, проверяем битрейт для видео
                        bitrate = efg_data.get("bitrate", 0)
                        if bitrate > max_video_bitrate:
                            max_video_bitrate = bitrate
                            video_url = clean_url
                            logger.debug(f"Найдено видео: {vencode_tag} (Bitrate: {bitrate})")

                except Exception as e:
                    pass


    logger.debug(f'Нашёл исходник видео для {video_url}')
    logger.debug(f'Нашёл исходник аудио для {audio_url}')
    v_temp = os.path.join(folder_path, "temp_video.mp4")
    a_temp = os.path.join(folder_path, "temp_audio.mp3")
    download_file(video_url, v_temp)
    download_file(audio_url, a_temp)
    target_folder_path = os.path.join(folder_path, f"video_{int(time.time_ns())}.mp4")
    if ffmpeg_merge(video_url, audio_url, target_folder_path):
        driver.quit()
        return True
    driver.quit()
    return False


def download_file(url, target_path):
    try:
        logger.info(f'Downloading file {url[:50]}')
        if url.startswith('http'):
            r = requests.get(url, stream=True, timeout=30)
            if r.status_code == 200:
                with open(target_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        return False
    except Exception as e:
        logger.error(f"Ошибка requests: {e}")
        return False


def ffmpeg_merge(v_temp_path, a_temp_path, target_folder_path):
    try:
        cmd = [
            'ffmpeg', '-y',
            '-i', v_temp_path,
            '-i', a_temp_path,
            '-c:v', 'libx264',  # Перекодирование вместо копирования
            '-c:a', 'aac',
            '-b:v', '1000k',  # Низкий битрейт для экономии ресурсов
            '-b:a', '96k',  # Низкий аудио битрейт
            '-preset', 'ultrafast',  # Быстрая обработка
            '-threads', '1',  # Ограничить количество потоков
            '-pix_fmt', 'yuv420p',  # Совместимость iOS
            '-movflags', '+faststart',  # Оптимизация для веба
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            target_folder_path
        ]

        # Запуск с низким приоритетом (если возможно)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180  # 3 минуты
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False

        logger.info(f"Успешно склеено через FFmpeg: {target_folder_path}")

    except Exception as e:
        logger.error(f"Ошибка при вызове FFmpeg: {e}")
        return False
    finally:
        for tmp in [v_temp_path, a_temp_path]:
            if os.path.exists(tmp):
                os.remove(tmp)
    return True