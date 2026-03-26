import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

PORT_COOKIES = {5010: "hs_session_5010", 5011: "hs_session_5011", 5012: "hs_session_5012"}


def create_app(port: int = 5010) -> Flask:
    app = Flask(__name__)

    # Import CLI command from utility package at project root
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from utility.seed_users import seed_users, seed_data
    from utility.seed_projects import seed_projects
    from utility.clear_db import clear_db
    app.cli.add_command(seed_users)
    app.cli.add_command(seed_data)
    app.cli.add_command(seed_projects)
    app.cli.add_command(clear_db)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "postgresql://hiresense:hiresense@db:5432/hiresense"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_COOKIE_NAME"] = PORT_COOKIES.get(port, f"hs_session_{port}")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "danger"

    from .auth import auth_bp
    from .views import views_bp
    from .admin import admin_bp
    from .manager import manager_bp
    from .employee import employee_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(employee_bp)

    return app
