from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
import re
from extensions import login_manager
from models import Uzytkownik

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return Uzytkownik.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        #walidacja formatu e-mail
        student_regex = r'^[0-9]{5}@student\.ans-elblag\.pl$'
        pracownik_regex = r'^[a-z]\.[a-z0-9._-]+@ans-elblag\.pl$'

        if not (re.match(student_regex, email) or re.match(pracownik_regex, email)):
            flash('Błędny format e-mail. Użyj formatu indeks@student.ans-elblag.pl lub i.nazwisko@ans-elblag.pl', 'danger')
            return render_template('login.html')
        
        #szukanie uzytkownika w bazie
        user = Uzytkownik.query.filter_by(email=email).first()
        
        #czy uzytkownik istnieje i czy haslo jest poprawne
        if user and check_password_hash(user.haslo_hash, password):
            login_user(user)
            flash('Zalogowano pomyślnie!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Błędny email lub hasło', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-hasla')
def reset_hasla():
    return "Resetowanie hasła - w budowie"