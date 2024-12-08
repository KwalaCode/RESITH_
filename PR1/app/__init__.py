from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import logging

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    from app.routes import main, auth, booking, admin
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(booking)
    app.register_blueprint(admin)

    return app

