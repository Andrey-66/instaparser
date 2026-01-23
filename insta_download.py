import shutil
from pathlib import Path

import instaloader
from dotenv import load_dotenv
from instaloader import Post

from logger import logger


load_dotenv()
L = instaloader.Instaloader()
L_anonim = instaloader.Instaloader()
PROJECT_ROOT = Path(__file__).resolve().parent
L.load_session_from_file("valtyry.2016", str(PROJECT_ROOT / "session-valtyry.2016"))

def get_content(shortcode, username=None):
    logger.info(f"Обработка ссылки {shortcode}")
    folder_name = f"{username}-{shortcode}" if username else shortcode
    try:
        post = Post.from_shortcode(L_anonim.context, shortcode)
        L.download_post(post, target=folder_name)
        logger.info(f"Пост успешно скачан в папку {folder_name}/")
        move_dir(folder_name, f'content/{folder_name}')
    except Exception as e:
        try:
            post = Post.from_shortcode(L_anonim.context, shortcode)
            L.download_post(post, target=folder_name)
            logger.info(f"Пост успешно скачан в папку {folder_name}/")
            move_dir(folder_name, f'content/{folder_name}')
        except Exception as e:
            logger.info(f"Ошибка при скачивании поста: {e}")


def move_dir(source_dir, destination_dir):
    try:
        shutil.move(source_dir, destination_dir)
        logger.info(f"Папка успешно перемещена из {source_dir} в {destination_dir}")
    except FileNotFoundError:
        logger.info("Ошибка: Исходная папка не найдена.")
    except Exception as e:
        logger.info(f"Произошла ошибка: {e}")
