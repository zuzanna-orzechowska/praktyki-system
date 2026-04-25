#plik zawierający obiekty wspóldzielone przez calą aplikacje - system logowania, baza danych
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  #przekieroeanie niezalogowanego użytkownika
login_manager.login_message = "Zaloguj się, aby uzyskać dostęp."
login_manager.login_message_category = "info"