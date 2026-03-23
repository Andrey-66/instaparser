import logging
import os

from dotenv import load_dotenv

from app_web.db import database
from app_web.models import AdminUser

logger = logging.getLogger(__name__)

def create_initilal_admin(app, username='admin'):
    load_dotenv()
    password = os.getenv('INITIAL_ADMIN_PASSWORD')
    if not password:
        logger.error('Environment variable INITIAL_ADMIN_PASSWORD for admin is empty')
        return None
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
        logger.info('Admin user created')
        return admin
