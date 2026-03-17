from flask import Flask, jsonify
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv
import os

from models import get_user_by_id
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.teacher_routes import teacher_bp
from routes.student_routes import student_bp
from api.users_api import users_api

from api.disciplines_api import disciplines_api
from api.groups_api import groups_api
from api.grades_api import grades_api
from api.exams_api import exams_api
from api.account_api import account_api
from api.expulsion_api import expulsion_api
from api.departments_api import departments_api
from api.specialties_api import specialties_api

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'
    app.config['WTF_CSRF_TIME_LIMIT'] = 60 * 60 * 2  # 2 hours
    
    csrf = CSRFProtect()
    csrf.init_app(app)
    app.jinja_env.globals['csrf_token'] = generate_csrf
    
    @app.get('/api/csrf')
    def csrf_token_api():
        return jsonify({'csrf_token': generate_csrf()})

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, выполните вход для доступа к этой странице.'
    login_manager.login_message_category = 'warning'
    login_manager.needs_refresh_message = 'Пожалуйста, повторно войдите для доступа к этой странице.'
    login_manager.needs_refresh_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(users_api)

    app.register_blueprint(disciplines_api)
    app.register_blueprint(groups_api)
    app.register_blueprint(grades_api)
    app.register_blueprint(exams_api)
    app.register_blueprint(account_api)
    app.register_blueprint(expulsion_api)
    app.register_blueprint(departments_api)
    app.register_blueprint(specialties_api)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
