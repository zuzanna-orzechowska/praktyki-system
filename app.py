from flask import Flask, render_template
from extensions import db, login_manager
from blueprints.auth import auth_bp
from flask_login import login_required
import os

def create_app():
    app = Flask(__name__)

    #do testowania
    app.config['SECRET_KEY'] = 'twoj-bardzo-tajny-klucz-123'

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'praktyki.db')
    
    #inicjalizacja rozszerzeń
    db.init_app(app)
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)
    
    @app.route('/')
    @app.route('/pytania')
    @app.route('/kontakt')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)