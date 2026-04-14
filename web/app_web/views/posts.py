from datetime import datetime
import logging

from flask import Blueprint, request, jsonify

from app_web import database
from app_web.models import Post, Profile

logger = logging.getLogger(__name__)

router = Blueprint('api_post', __name__, url_prefix='/api')


@router.route('/posts', methods=['GET'])
def get_posts():
    """
    Получает список постов с фильтрацией.

    Параметры фильтрации (в query string):
    - is_sent: true/false
    - is_downloaded: true/false
    - profile_id: int
    """
    try:
        # Параметры фильтрации
        is_sent = request.args.get('is_sent')
        is_downloaded = request.args.get('is_downloaded')
        profile_id = request.args.get('profile_id', type=int)

        query = Post.query

        if is_sent is not None:
            is_sent_bool = is_sent.lower() in ['true', '1', 'yes', 'on']
            query = query.filter(Post.is_sent == is_sent_bool)

        if is_downloaded is not None:
            is_downloaded_bool = is_downloaded.lower() in ['true', '1', 'yes', 'on']
            query = query.filter(Post.is_downloaded == is_downloaded_bool)

        if profile_id:
            query = query.filter(Post.profile_id == profile_id)


        # Формируем ответ
        result = []
        for post in query:
            result.append({
                'id': post.id,
                'instagram_post_id': post.instagram_post_id,
                'profile_username': post.profile.username if post.profile else None,
                'media_type': post.media_type,
                'is_sent': post.is_sent,
                'sent_at': post.sent_at.isoformat() if post.sent_at else None,
                'sent_to': post.sent_to,
                'is_downloaded': post.is_downloaded,
                'file_path': post.file_path,
                'created_at': post.created_at.isoformat(),
                'errors_count': post.errors_count
            })

        logger.info(f"Retrieved {len(result)} posts with filters: "
                    f"is_sent={is_sent}, is_downloaded={is_downloaded}, "
                    f"profile_id={profile_id}")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error fetching posts: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch posts'}), 500

@router.route('/posts/<string:instagram_post_id>', methods=['GET'])
def get_post(instagram_post_id):
    post = Post.query.filter_by(instagram_post_id=instagram_post_id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    return jsonify({
        'id': post.id,
        'instagram_post_id': post.instagram_post_id,
        'profile_id': post.profile_id,
        'media_type': post.media_type,
        'is_sent': post.is_sent,
        'sent_at': post.sent_at,
        'sent_to': post.sent_to,
        'is_downloaded': post.is_downloaded,
        'file_path': post.file_path,
        'created_at': post.created_at.isoformat(),
        'errors_count': post.errors_count
    })

@router.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    if not data:
        logger.warning("No JSON data provided in POST /posts")
        return jsonify({'error': 'No data provided'}), 400

    instagram_post_id = data.get('instagram_post_id')
    profile_id = data.get('profile_id')

    if not instagram_post_id:
        return jsonify({'error': 'instagram_post_id is required'}), 400
    if not profile_id:
        return jsonify({'error': 'profile_id is required'}), 400

    profile = Profile.query.get(profile_id)
    if not profile:
        return jsonify({'error': f'Profile with id {profile_id} not found'}), 404

    existing_post = Post.query.filter_by(
        instagram_post_id=instagram_post_id,
        profile_id=profile_id
    ).first()
    if existing_post:
        logger.info(f"Post {instagram_post_id} for profile {profile_id} already exists")
        return jsonify({
            'error': 'Post already exists',
            'post_id': existing_post.id
        }), 409

    try:
        post = Post(
            instagram_post_id=instagram_post_id,
            profile_id=profile_id,
            media_type=data.get('media_type'),
            is_sent=data.get('is_sent', False),
            sent_at=None,
            sent_to=None,
            is_downloaded=data.get('is_downloaded', False),
            file_path=data.get('file_path'),
            errors_count=data.get('errors_count', 0)
        )

        sent_at = data.get('sent_at')
        if sent_at:
            try:
                if isinstance(sent_at, str):
                    from datetime import datetime
                    post.sent_at = datetime.fromisoformat(sent_at.replace('Z', '+00:00'))
                else:
                    post.sent_at = sent_at
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid sent_at format: {sent_at}")
                return jsonify({'error': 'Invalid sent_at format. Use ISO 8601'}), 400

        sent_to = data.get('sent_to')
        if sent_to:
            if not isinstance(sent_to, str):
                return jsonify({'error': 'sent_to must be a string'}), 400
            post.sent_to = sent_to

        database.session.add(post)
        database.session.commit()

        logger.info(f"Created post {post.id} for profile {profile_id}")
        return jsonify({
            'id': post.id,
            'instagram_post_id': post.instagram_post_id,
            'profile_id': post.profile_id,
            'media_type': post.media_type,
            'is_sent': post.is_sent,
            'sent_at': post.sent_at.isoformat() if post.sent_at else None,
            'sent_to': post.sent_to,
            'is_downloaded': post.is_downloaded,
            'file_path': post.file_path,
            'created_at': post.created_at.isoformat(),
            'errors_count': post.errors_count
        }), 201

    except Exception as e:
        database.session.rollback()
        logger.error(f"Failed to create post: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create post'}), 500

@router.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if not post:
        return jsonify({'error': 'Profile not found'}), 404
    if 'is_sent' in data:
        post.is_sent = data['is_sent']
    if 'sent_at' in data:
        post.sent_at = datetime.fromisoformat(data['sent_at'])
    if 'sent_to' in data:
        post.sent_to = data['sent_to']
    if 'is_downloaded' in data:
        post.is_downloaded = data['is_downloaded']
    if 'file_path' in data:
        post.file_path = data['file_path']
    if 'errors_count' in data:
        post.errors_count = data['errors_count']
    try:
        database.session.commit()
        return jsonify({
            'id': post.id,
            'instagram_post_id': post.instagram_post_id,
            'profile_id': post.profile_id,
            'media_type': post.media_type,
            'is_sent': post.is_sent,
            'sent_at': post.sent_at.isoformat() if post.sent_at else None,
            'sent_to': post.sent_to,
            'is_downloaded': post.is_downloaded,
            'file_path': post.file_path,
            'created_at': post.created_at.isoformat(),
            'errors_count': post.errors_count
        }), 200
    except Exception as e:
        database.session.rollback()
        return jsonify({'error': f'Failed to update post: {str(e)}'}), 500


@router.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Удаление подписки по ID"""
    try:
        post = Post.query.filter_by(id=post_id).first()

        if not post:
            return jsonify({'error': 'Post not found'}), 404

        database.session.delete(post)
        database.session.commit()

        return jsonify({'message': 'Post deleted successfully'}), 200

    except Exception as e:
        database.session.rollback()
        logger.error(f"Error deleting post {post_id}: {e}")
        return jsonify({'error': 'Failed to delete post'}), 500