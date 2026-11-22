import json
from datetime import datetime, timedelta
from pathlib import Path

from flask import jsonify, redirect, request, url_for
from flask_admin import AdminIndexView, expose
from flask_login import current_user
from sqlalchemy import and_, func, or_, select

from .db import database
from .models import Post, Profile, Subscription, TelegramUser

PARSER_STATUS_FILE = Path("/content/.parser_status.json")


def parser_activity():
    try:
        activity = json.loads(PARSER_STATUS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return activity if isinstance(activity, dict) else None


def media_status(post):
    if post.is_sent:
        return "sent"
    if post.is_downloaded:
        return "ready"
    return "error" if post.errors_count else "pending"

class SecureAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        return self.render('admin/home.html')

    @expose('/home-data')
    def home_data(self):
        now = datetime.utcnow()
        local_now = datetime.now()
        profiles = database.session.scalars(select(Profile).order_by(Profile.username)).all()
        rows = {
            profile.id: {
                "id": profile.id,
                "username": profile.username,
                "checked_seconds": (
                    max(0, int((local_now - profile.last_parsed).total_seconds()))
                    if profile.last_parsed else None
                ),
                "subscribers": [],
                "post": [],
                "reel": [],
                "story": [],
            }
            for profile in profiles
        }
        subscribers = select(Subscription.profile_id, TelegramUser.telegram_id, TelegramUser.username).join(
            TelegramUser, TelegramUser.id == Subscription.telegram_user_id
        ).order_by(TelegramUser.username, TelegramUser.telegram_id)
        for profile_id, telegram_id, username in database.session.execute(subscribers):
            if profile_id in rows:
                rows[profile_id]["subscribers"].append(f"@{username}" if username else telegram_id)

        recent = select(
            Post.id, Post.profile_id, Post.media_type, Post.is_sent, Post.is_downloaded,
            Post.errors_count, Post.instagram_post_id,
            func.row_number().over(
                partition_by=(Post.profile_id, Post.media_type),
                order_by=(Post.created_at.desc().nulls_last(), Post.id.desc()),
            ).label("position"),
        ).where(or_(
            Post.media_type.in_(("post", "reel")),
            and_(Post.media_type == "story", Post.created_at >= now - timedelta(hours=24)),
        )).subquery()
        media = select(recent).where(or_(
            recent.c.media_type == "story", recent.c.position <= 10
        )).order_by(recent.c.position)
        for post in database.session.execute(media):
            if post.profile_id in rows:
                rows[post.profile_id][post.media_type].append({
                    "status": media_status(post),
                    "label": post.instagram_post_id,
                })

        response = jsonify(profiles=list(rows.values()), parser_activity=parser_activity())
        response.headers["Cache-Control"] = "no-store"
        return response

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))
