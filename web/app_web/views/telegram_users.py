from flask import Blueprint, jsonify

from app_web.models import TelegramUser, Profile

router = Blueprint('api_telegram_user', __name__, url_prefix='/api')


@router.route('/telegram-users/<int:telegram_id>', methods=['GET'])
def get_user(telegram_id):
    telegram_user = TelegramUser.query.filter_by(telegram_id=str(telegram_id)).first()
    if not telegram_user:
        return jsonify({}), 404
    subscriptions = []
    subscriptions_profiles = []
    if telegram_user.subscriptions:
        for subscription in telegram_user.subscriptions:
            subscription_id = subscription.id
            profile_id = subscription.profile_id
            profile = Profile.query.filter_by(id=profile_id).first()
            subscriptions.append(subscription_id)
            subscriptions_profiles.append(profile.username)
    return jsonify(
        {
            'id': telegram_user.id,
            'telegram_id': telegram_user.telegram_id,
            'is_active': telegram_user.is_active,
            'created_at': telegram_user.created_at,
            'subscriptions': subscriptions,
            'subscriptions_profiles': subscriptions_profiles,
        }
    ), 200
