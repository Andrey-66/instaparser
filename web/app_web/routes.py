from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Profile, Post, Subscription

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    # Get stats
    stats = {
        'total_profiles': Profile.query.count(),
        'active_profiles': Profile.query.filter_by(is_active=True).count(),
        'total_posts': Post.query.count(),
        'pending_posts': Post.query.filter_by(is_sent=False).count(),
        'total_subscriptions': Subscription.query.count()
    }
    return render_template('index.html', stats=stats)

@main.route('/profiles')
@login_required
def profiles():
    profiles = Profile.query.all()
    return render_template('profiles.html', profiles=profiles)

@main.route('/api/profiles', methods=['GET'])
@login_required
def api_profiles():
    profiles = Profile.query.all()
    return jsonify([{
        'id': p.id,
        'username': p.username,
        'is_active': p.is_active,
        'last_parsed': p.last_parsed.isoformat() if p.last_parsed else None,
        'post_count': len(p.posts),
        'subscriber_count': len(p.subscriptions)
    } for p in profiles])
