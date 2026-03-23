import logging

from flask import Blueprint, jsonify, request

from app_web import database
from app_web.models import Subscription, Profile, TelegramUser

logger = logging.getLogger(__name__)
router = Blueprint('api_subscriptions', __name__, url_prefix='/api')


@router.route('/subscriptions/<int:subscriptions_id>', methods=['GET'])
def get_subscription(subscriptions_id):
    subscription = Subscription.query.filter_by(id=subscriptions_id).first()
    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404
    return jsonify(
        {
            'id': subscription.id,
            'profile': subscription.profile_id,
            'telegram_user_id': subscription.telegram_user_id,
            'created_at': subscription.created_at,
        }
    ), 200


@router.route('/subscriptions', methods=['POST'])
def create_subscription():
    data = request.get_json()
    if not data:
        logger.warning("No JSON data provided in POST /subscriptions")
        return jsonify({'error': 'No data provided'}), 400

    profile_id = data.get('profile_id')
    telegram_user_id = data.get('telegram_user_id')

    if not profile_id:
        return jsonify({'error': 'instagram_post_id is required'}), 400
    if not telegram_user_id:
        return jsonify({'error': 'profile_id is required'}), 400

    profile = Profile.query.get(profile_id)
    if not profile:
        return jsonify({'error': f'Profile with id {profile_id} not found'}), 404
    telegram_user = TelegramUser.query.get(telegram_user_id)
    if not telegram_user:
        return jsonify({'error': f'Telegram_user with id {telegram_user_id} not found'}), 404

    existing_subscription = Subscription.query.filter_by(
        profile_id=profile_id,
        telegram_user_id=telegram_user_id
    ).first()
    if existing_subscription:
        logger.info(f"Subscription {existing_subscription} already exists")
        return jsonify({
            'error': 'Subscription already exists',
            'Subscription_id': existing_subscription.id
        }), 409

    try:
        subscription = Subscription(
            profile_id=profile_id,
            telegram_user_id=telegram_user_id
        )
        database.session.add(subscription)
        database.session.commit()

        logger.info(f"Created subscription {subscription.id} for profile {profile_id}, telegram_user {telegram_user_id}")
        return jsonify({
            'id': subscription.id,
            'profile_id': subscription.profile_id,
            'telegram_user_id': subscription.telegram_user_id,
            'created_at': subscription.created_at.isoformat(),
        }), 201

    except Exception as e:
        database.session.rollback()
        logger.error(f"Failed to create post: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create post'}), 500

@router.route('/subscriptions/<int:subscriptions_id>', methods=['DELETE'])
def delete_subscription(subscriptions_id):
    """Удаление подписки по ID"""
    try:
        subscription = Subscription.query.filter_by(id=subscriptions_id).first()

        if not subscription:
            return jsonify({'error': 'Subscription not found'}), 404

        database.session.delete(subscription)
        database.session.commit()

        return jsonify({'message': 'Subscription deleted successfully'}), 200

    except Exception as e:
        database.session.rollback()
        logger.error(f"Error deleting subscription {subscriptions_id}: {e}")
        return jsonify({'error': 'Failed to delete subscription'}), 500
