import os

import requests
from dotenv import load_dotenv

from logger import logger

load_dotenv()
URL = os.getenv("URL")

def get_profiles():
    try:
        profiles = requests.get(f'{URL}/api/profiles')
    except Exception as e:
        logger.error(f"Error getting profiles: {e}")
        return []
    if profiles.status_code != 200:
        logger.error(f'Error getting profiles: {profiles.status_code}')
        return []
    return profiles.json()
