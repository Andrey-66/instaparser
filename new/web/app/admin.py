from flask import redirect, url_for
from flask_admin import Admin
from app.views_registry import SecureAdminIndexView
from flask_admin.menu import MenuLink
from flask_login import logout_user, login_required

def admin_logout():
    logout_user()
    return redirect(url_for('auth.login'))


def setup_admin():
    """Минимальная админка без циклических импортов."""
    from . import app
    from .db import database
    admin = Admin(
        app,
        name='Admin',
        index_view=SecureAdminIndexView(),
        template_mode='bootstrap3'
    )
    app.add_url_rule('/admin/logout', 'admin_logout', login_required(admin_logout))
    admin.add_link(MenuLink(name='Выйти', endpoint='admin_logout'))

    from app.admins.base import BaseAdminView
    from app.models import Profile
    admin.add_view(BaseAdminView(Profile, database.session))
    from app.models import Subscription
    admin.add_view(BaseAdminView(Subscription, database.session))
    from app.models import Post
    admin.add_view(BaseAdminView(Post, database.session))
    from app.models import TelegramUser
    admin.add_view(BaseAdminView(TelegramUser, database.session))
