#plik zawierający obiekty wspóldzielone przez calą aplikacje - system logowania, baza danych
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = None