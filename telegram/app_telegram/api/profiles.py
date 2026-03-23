import logging
import os

import requests

logger = logging.getLogger(__name__)

URL = os.getenv("URL")

def get_profile(profile_name):
    try:
        profile = requests.get(f'{URL}/api/profiles/{profile_name}')
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return {}
    if profile.status_code != 200:
        logger.error(f'Error getting profile: {profile.status_code}')
        return {}
    return profile.json()

def create_profile(username):
    try:
        profile = requests.post(f'{URL}/api/profiles/', json={'username': username})
        if profile.status_code != 201:
            logger.error(f'Error creating profile: {profile.status_code}')
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        return {}
    return profile.json()