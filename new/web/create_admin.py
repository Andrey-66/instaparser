from app import create_app, db
from app.models import AdminUser

app = create_app()
with app.app_context():
    user = AdminUser(username='admin')
    user.set_password('admin')  # поменяй на более надежный пароль
    db.session.add(user)
    db.session.commit()
