from app_web import app
from app_web.db import database
from app_web.models import AdminUser

with app.app_context():
    user = AdminUser(username='admin1')
    user.set_password('admin')
    database.session.add(user)
    database.session.commit()
