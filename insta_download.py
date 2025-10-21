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
    try:
        post = Post.from_shortcode(L_anonim.context, shortcode)
        if username:
            L.download_post(post, target=f"{username}-{shortcode}")
        else:
            L.download_post(post, target=f"{shortcode}")
        logger.info(f"Пост успешно скачан в папку ./{shortcode}/\n")
    except Exception as e:
        try:
            post = Post.from_shortcode(L.context, shortcode)
            if username:
                L.download_post(post, target=f"{username}-{shortcode}")
            else:
                L.download_post(post, target=f"{shortcode}")
        except Exception as e:
            logger.info(f"Ошибка при скачивании поста: {e}")
