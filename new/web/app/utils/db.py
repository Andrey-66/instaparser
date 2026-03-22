import os

from app.db import database
from app.models import AdminUser


def create_initilal_admin(app, username='admin'):
    password = os.getenv('INITIAL_ADMIN_PASSWORD')
    with app.app_context():
        if AdminUser.query.first():
            return None
        if not password:
            return None
        admin = AdminUser(
            username=username,
        )
        admin.set_password(password)
        database.session.add(admin)
        database.session.commit()
        return admin
