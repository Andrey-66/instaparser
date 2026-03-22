from flask import Blueprint, jsonify

from app.models import Profile

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
