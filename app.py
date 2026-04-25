from flask import Flask, render_template
from extensions import db, login_manager
from blueprints.auth import auth_bp
from flask_login import login_required

def create_app():
    app = Flask(__name__)

    #do testowania
    app.config['SECRET_KEY'] = 'twoj-bardzo-tajny-klucz-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///praktyki.db'
    
    #inicjalizacja rozszerzeń
    db.init_app(app)
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)
    
    @app.route('/')
    @login_required
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)