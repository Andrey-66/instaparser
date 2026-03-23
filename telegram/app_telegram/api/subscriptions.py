import logging
import os

import requests

logger = logging.getLogger(__name__)

URL = os.getenv("URL")

def get_subscription(subscriptions_id):
    try:
        subscription = requests.get(f'{URL}/api/subscriptions/{subscriptions_id}')
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        return {}
    if subscription.status_code != 200:
        logger.error(f'Error getting subscription: {subscription.status_code}')
        return {}
    return subscription.json()

def create_subscription(profile_id, telegram_user_id):
    try:
        subscription = requests.post(f'{URL}/api/subscriptions', json={'profile_id': profile_id, 'telegram_user_id': telegram_user_id})
        if subscription.status_code == 201:
            return subscription.json()
        logger.error(f'Error creating subscription: {subscription.status_code}')
        return {}
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        return {}


def delete_subscription(subscription_id):
    try:
        subscription = requests.delete(f'{URL}/api/subscriptions/{subscription_id}')
        if subscription.status_code == 200:
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting subscription: {e}")
        return False
