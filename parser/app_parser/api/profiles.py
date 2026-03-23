import os

import requests

import logging

logger = logging.getLogger(__name__)

URL = os.getenv("URL")
if not URL:
    logger.error("Environment variable URL is empty")
    raise Exception("Environment variable URL is empty")


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

def update_profile(profile_id, last_parsed=None, errors_count=None):
    payload = {}
    if last_parsed:
        payload['last_parsed'] = last_parsed
    if errors_count is not None:
        payload['errors_count'] = errors_count
    if not payload:
        logger.error(f"Error updating profile {profile_id}: no data to update")
        return False
    try:
        response = requests.put(f'{URL}/api/profiles/{profile_id}', json=payload)
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return False
    if response.status_code != 200:
        logger.error(f"Error updating profile {profile_id}")
        return False
    logger.info(f"Updated profile {profile_id}")
    return True
