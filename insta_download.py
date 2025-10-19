import instaloader

from logger import logger

L = instaloader.Instaloader()

def get_content(shortcode, username=None):
    logger.info(f"Обработка ссылки {shortcode}")
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if username:
            L.download_post(post, target=f"{username}-{shortcode}")
        else:
            L.download_post(post, target=f"{shortcode}")
        logger.info(f"Пост успешно скачан в папку ./{shortcode}/\n")
    except Exception as e:
        logger.info(f"Ошибка при скачивании поста: {e}")