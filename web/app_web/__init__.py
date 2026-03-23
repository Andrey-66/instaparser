from flask import Flask
from flask_migrate import Migrate

from app_web.db import init_db, database
from app_web.login_manager import init_lm
from app_web.settings import Config
from app_web.admin import setup_admin
from app_web.auth import bp as auth_module
from app_web.utils.db import create_initilal_admin
from app_web.views.profiles import router as profile_api_router
from app_web.views.posts import router as posts_api_router
from app_web.views.telegram_users import router as telegram_users_api_router
from app_web.views.subscriptions import router as subscriptions_api_router

from app_web.models import Profile, Post, Subscription, AdminUser, TelegramUser

app = Flask(__name__)
app.config.from_object(Config)

init_db(app)
with app.app_context():
    database.create_all()
migrate = Migrate(app, database)


init_lm(app)
create_initilal_admin(app)

app.register_blueprint(auth_module)
app.register_blueprint(profile_api_router)
app.register_blueprint(posts_api_router)
app.register_blueprint(telegram_users_api_router)
app.register_blueprint(subscriptions_api_router)

setup_admin()