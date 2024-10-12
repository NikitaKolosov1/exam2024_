from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy()
db.init_app(app)
migrate = Migrate(app,db)

def create_app():    
    login = LoginManager()
    login.login_view = 'auth.login'
    login.init_app(app)
    
    from app.main import main_bp
    app.register_blueprint(main_bp)

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    '''from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)'''

    @login.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    return app

from app import models

