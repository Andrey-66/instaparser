import logging
import os
import requests

logger = logging.getLogger(__name__)

URL = os.getenv("URL")
if not URL:
    logger.error("Environment variable URL is empty")
    raise Exception("Environment variable URL is empty")

def get_telegram_user(telegram_id):
    url = f'{URL}/api/telegram-users/{telegram_id}'
    try:
        user = requests.get(url)
    except Exception as e:
        logger.error(f"Error getting telegram_user {telegram_id}: {e}")
        return {}
    if user.status_code != 200:
        logger.error(f'Error getting telegram_user {telegram_id}: {user.status_code}')
        return {}
    return user.json()


def update_telegram_username(telegram_id, username, token):
    try:
        response = requests.put(
            f'{URL}/api/telegram-users/{telegram_id}/username',
            json={'username': username},
            headers={'Authorization': f'Bearer {token}'},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.warning('Could not sync username for Telegram user %s', telegram_id)
