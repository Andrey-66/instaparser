import json
import os
import re
from hmac import compare_digest
from urllib.parse import urlencode
from urllib.request import urlopen

import click
from flask import Blueprint, jsonify, request
from flask.cli import with_appcontext

from app_web.db import database

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
            'username': telegram_user.username,
            'is_active': telegram_user.is_active,
            'created_at': telegram_user.created_at,
            'subscriptions': subscriptions,
            'subscriptions_profiles': subscriptions_profiles,
        }
    ), 200


@router.route('/telegram-users/<int:telegram_id>/username', methods=['PUT'])
def update_username(telegram_id):
    token = os.environ.get('TOKEN')
    authorization = request.headers.get('Authorization', '')
    if not token or not compare_digest(authorization.encode(), f'Bearer {token}'.encode()):
        return jsonify({}), 401
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or 'username' not in payload:
        return jsonify({}), 400
    username = payload['username']
    if username is not None and (
        not isinstance(username, str) or not re.fullmatch(r'[A-Za-z0-9_]{1,32}', username)
    ):
        return jsonify({}), 400
    user = TelegramUser.query.filter_by(telegram_id=str(telegram_id)).first_or_404()
    user.username = username
    database.session.commit()
    return jsonify({})


@click.command('sync-telegram-usernames')
@with_appcontext
def sync_telegram_usernames():
    token = os.environ.get('TOKEN')
    if not token:
        raise click.ClickException('TOKEN is missing')
    updated = unavailable = 0
    for user in TelegramUser.query.order_by(TelegramUser.id).all():
        try:
            query = urlencode({'chat_id': user.telegram_id})
            with urlopen(f'https://api.telegram.org/bot{token}/getChat?{query}', timeout=10) as response:
                chat = json.load(response)['result']
        except (OSError, ValueError, KeyError):
            click.echo(f'Telegram chat unavailable: {user.telegram_id}', err=True)
            unavailable += 1
            continue
        user.username = chat.get('username')
        database.session.commit()
        updated += 1
    click.echo(f'Synced: {updated}. Unavailable: {unavailable}.')
