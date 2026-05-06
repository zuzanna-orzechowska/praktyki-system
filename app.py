from flask import Flask, render_template
from extensions import db, login_manager
from blueprints.auth import auth_bp, init_oauth
from blueprints.student import student_bp 
from blueprints.uopz import uopz_bp
from flask_login import login_required
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SERVER_NAME'] = 'localhost:5001' #TO ZMIENIĆ W PRZYSZŁOŚCI!!!!!!!!!!
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'praktyki.db')
    
    upload_folder = os.path.join(basedir, 'static', 'uploads')
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)
    
    db.init_app(app)
    login_manager.init_app(app)
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp) 
    app.register_blueprint(uopz_bp)
    
    init_oauth(app)
    
    @app.route('/')
    @app.route('/pytania')
    @app.route('/kontakt')
    def index():
        return render_template('index.html')

    @app.route('/dokumenty')
    def dokumenty():
        return render_template('dokumenty.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)