import os
from logging.handlers import RotatingFileHandler
from time import sleep

from dotenv import load_dotenv
import logging

from api.profiles import get_profiles
from app.parser import InstagramParser


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
    try:
        logger.info("Starting parser test...")
        with InstagramParser(limit=10) as parser:
            profiles = get_profiles()
            profiles_names = []
            for profile in profiles:
                profiles_names.append(profile.get("username"))
            parser.parse_profiles(profiles_names)
    except Exception as e:
        logger.error(f"Parser test failed: {e}")
        raise


if __name__ == "__main__":
    main()
