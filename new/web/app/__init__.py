from flask import Flask
from flask_migrate import Migrate

from app.db import init_db, database
from app.login_manager import init_lm
from app.settings import Config
from app.admin import setup_admin
from app.auth import bp as auth_module
from app.utils.db import create_initilal_admin
from app.views.profiles import router as profile_api_router

from app.models import Profile, Post, Subscription, AdminUser, TelegramUser

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

setup_admin()