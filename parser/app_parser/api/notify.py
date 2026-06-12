import os
import logging

import requests

logger = logging.getLogger(__name__)

ADMIN_CHAT_ID = os.getenv("ADMIN_TELEGRAM_ID")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


def notify_admin(message: str):
    if not TELEGRAM_TOKEN or not ADMIN_CHAT_ID:
        logger.warning("TELEGRAM_TOKEN or ADMIN_TELEGRAM_ID not set, skipping admin notification")
        return
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": ADMIN_CHAT_ID, "text": message},
            timeout=10,
        )
        if not response.ok:
            logger.error(f"Failed to notify admin: {response.text}")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")