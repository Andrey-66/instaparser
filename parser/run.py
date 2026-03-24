import random
import time
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
import logging

from app_parser.api.posts import get_posts
from app_parser.api.profiles import get_profiles
from app_parser.parser import InstagramParser


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Вывод в stdout
            RotatingFileHandler(
                "parser.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8"
            )
        ]
    )


def main():
    load_dotenv()
    setup_logging()
    logger = logging.getLogger(__name__)
    while True:
        try:
            logger.info("Starting parser...")
            with InstagramParser(limit=10) as parser:
                profiles = get_profiles()
                profiles_names = []
                for profile in profiles:
                    profiles_names.append(profile.get("username"))
                parser.parse_profiles(profiles_names)
                posts = get_posts(is_downloaded=False)
                parser.parse_posts(posts)
            sleep_minutes = random.randint(90, 120)
            logger.info(f"Спим {sleep_minutes} минут перед следующей итерацией")
            time.sleep(sleep_minutes * 60)
        except Exception as e:
            logger.error(f"Parser failed: {e}")


if __name__ == "__main__":
    main()
