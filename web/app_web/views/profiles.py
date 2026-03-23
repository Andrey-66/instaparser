import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from app_web import database
from app_web.models import Profile

logger = logging.getLogger(__name__)
router = Blueprint('api_profile', __name__, url_prefix='/api')

@router.route('/profiles', methods=['GET'])
def get_actual_profiles():
    profiles = Profile.query.all()
    response = []
    for profile in profiles:
        if profile.subscriptions:
            subscriptions = []
            for subscription in profile.subscriptions:
                telegram_user = subscription.telegram_user
                if telegram_user.is_active:
                    subscriptions.append(telegram_user.telegram_id)
            if subscriptions:
                response.append({
                    'id': profile.id,
                    'username': profile.username,
                    'subscriptions': subscriptions
                })
    return jsonify(response), 200

@router.route('/profiles/<string:profile_name>', methods=['GET'])
def get_profile(profile_name):
    profile = Profile.query.filter_by(username=profile_name).first()
    telegram_ids = []
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    subscriptions = []
    if profile.subscriptions:
        for subscription in profile.subscriptions:
            telegram_user = subscription.telegram_user
            telegram_ids.append(telegram_user.telegram_id)
            subscriptions.append(subscription.id)
    return jsonify(
        {
            'id': profile.id,
            'username': profile.username,
            'last_parsed': profile.last_parsed,
            'created_at': profile.created_at,
            'errors_count': profile.errors_count,
            'subscriptions': subscriptions,
            'telegram_ids': telegram_ids if telegram_ids else None
        }
    ), 200


@router.route('/profiles/<string:profile_name>', methods=['PUT'])
def update_profile(profile_name):
    profile = Profile.query.filter_by(username=profile_name).first()

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404

    if 'username' in data:
        if data['username'] != profile.username:
            existing_profile = Profile.query.filter_by(username=data['username']).first()
            if existing_profile:
                return jsonify({'error': f'Profile with username "{data["username"]}" already exists'}), 400
        profile.username = data['username']

    if 'last_parsed' in data:
        try:
            if isinstance(data['last_parsed'], str):
                profile.last_parsed = datetime.fromisoformat(data['last_parsed'].replace('Z', '+00:00'))
            else:
                profile.last_parsed = data['last_parsed']
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid date format. Use ISO 8601 format'}), 400

    if 'errors_count' in data:
        try:
            errors_count = int(data['errors_count'])
            if errors_count < 0:
                return jsonify({'error': 'errors_count cannot be negative'}), 400
            profile.errors_count = errors_count
        except (ValueError, TypeError):
            return jsonify({'error': 'errors_count must be a valid integer'}), 400

    try:
        database.session.commit()
        return jsonify({
            'id': profile.id,
            'username': profile.username,
            'last_parsed': profile.last_parsed.isoformat() if profile.last_parsed else None,
            'created_at': profile.created_at.isoformat(),
            'errors_count': profile.errors_count
        }), 200
    except Exception as e:
        database.session.rollback()
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500


@router.route('/profiles/', methods=['POST'])
def create_profile():
    data = request.get_json()
    if not data:
        logger.warning("No JSON data provided in POST /profiles")
        return jsonify({'error': 'No data provided'}), 400
    if 'username' not in data:
        return jsonify({'error': 'Username required'}), 400
    username = data.get('username')
    existing_profile = Profile.query.filter_by(username=username).first()
    if existing_profile:
        return jsonify({'error': f'Profile with username {username} is already exist'}), 409
    try:
        profile = Profile(
            username=username,
            last_parsed=data.get('last_parsed') if data.get('last_parsed') else None,
        )
        database.session.add(profile)
        database.session.commit()

        logger.info(f"Created profile {profile.id} for profile {profile.username}")
        return jsonify({
            'id': profile.id,
            'username': profile.username,
            'last_parsed': profile.last_parsed,
            'created_at': profile.created_at,
            'errors_count': profile.errors_count,
            'subscriptions': [],
            'telegram_ids': []
        }), 201
    except Exception as e:
        database.session.rollback()
        logger.error(f"Failed to create profile: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create profile'}), 500
