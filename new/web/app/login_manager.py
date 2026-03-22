from flask_login import LoginManager

# Создаем LoginManager
login_manager = LoginManager()

def init_lm(app):
    """Инициализация LoginManager с Flask приложением"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

# Декоратор должен быть после создания login_manager
@login_manager.user_loader
def load_user(user_id):
    from app.models import AdminUser  # Локальный импорт чтобы избежать циклических зависимостей
    return AdminUser.query.get(int(user_id))
