from flask import Flask
import importlib
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(test_config=None):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///gacha.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PULL_COST=100,  # default cost per single pull (virtual currency)
    )

    if test_config:
        app.config.update(test_config)

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # register user loader after models are available
    with app.app_context():
        # import here to avoid circular import at module level
        from .models import User

        @login_manager.user_loader
        def load_user(user_id):
            try:
                return db.session.get(User, int(user_id))
            except Exception:
                return None

    # register blueprints / routes using dynamic import
    routes_mod = importlib.import_module('app.routes')
    main_bp = getattr(routes_mod, 'bp')
    app.register_blueprint(main_bp)

    return app

# expose objects for other modules
