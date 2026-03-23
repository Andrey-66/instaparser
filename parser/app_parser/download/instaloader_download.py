import instaloader

import logging

from instaloader import Post

from app_parser.utils.files import move_directory

logger = logging.getLogger(__name__)


def instaloader_download(shortcode, folder):
    L = instaloader.Instaloader()
    content_folder = folder.split("/")[-1]
    logger.info(f"Instaloader download: {shortcode}")
    try:
        post = Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=content_folder)
        logger.info(f"Instaloader download success for {shortcode}")
        return move_directory(content_folder, folder)

    except Exception as e:
        logger.warning(f"Error while instaloader downloading {shortcode}: {e}")
        return False



