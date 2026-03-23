import logging
import os
import requests

logger = logging.getLogger(__name__)

URL = os.getenv("URL")
if not URL:
    logger.error("Environment variable URL is empty")
    raise Exception("Environment variable URL is empty")

def get_posts(is_sent=None, is_downloaded=None, profile_id=None):
    url = f'{URL}/api/posts'
    if is_sent is not None or is_downloaded is not None or profile_id:
        url += f'?'
    many_filters = False
    if is_sent is not None:
        url += f'is_sent={is_sent}'
        many_filters = True
    if is_downloaded is not None:
        if many_filters:
            url += '&'
        url += f'is_downloaded={is_downloaded}'
        many_filters = True
    if profile_id:
        if many_filters:
            url += '&'
        if profile_id:
            url += f'profile_id={profile_id}'
    try:
        posts = requests.get(url)
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        return []
    if posts.status_code != 200:
        logger.error(f'Error getting posts: {posts.status_code}')
        return []
    return posts.json()

def update_post(post_id,
                is_sent=None,
                sent_at=None,
                sent_to=None,
                is_downloaded=None,
                file_path=None,
                errors_count=None):
    payload = {}
    if is_sent:
        payload['is_sent'] = is_sent
    if sent_at:
        payload['sent_at'] = sent_at
    if sent_to:
        payload['sent_to'] = sent_to
    if is_downloaded:
        payload['is_downloaded'] = is_downloaded
    if file_path:
        payload['file_path'] = file_path
    if errors_count is not None:
        payload['errors_count'] = errors_count
    if not payload:
        logger.error(f"Error updating post {post_id}: no data to update")
        return False
    try:
        response = requests.put(f'{URL}/api/posts/{post_id}', json=payload)
    except Exception as e:
        logger.error(f"Error updating post: {e}")
        return False
    if response.status_code != 200:
        logger.error(f"Error updating post {post_id}")
        return False
    logger.info(f"Updated post {post_id}")
    return True
