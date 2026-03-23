from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()

def init_db(app):
    """Инициализировать расширение в момент, когда приложение уже создано."""
    database.init_app(app)