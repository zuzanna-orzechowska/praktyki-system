from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, UserMixin
from extensions import login_manager

auth_bp = Blueprint('auth', __name__)

# Tymczasowa klasa do testów
class User(UserMixin):
    def __init__(self, id, email, rola):
        self.id = id
        self.email = email
        self.rola = rola 

#pamiętanie sesji
@login_manager.user_loader
def load_user(user_id):
    #DO TESTÓW!!! STATYCZNY UZYTKOWNIK
    return User(user_id, "student@ans.elblag.pl", "student")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # LOGOWANIE DLA TESTÓW
        if email == "student@ans.elblag.pl" and password == "haslo123":
            user = User(id=1, email=email, rola="student")
            
            login_user(user)
            
            flash('Zalogowano pomyślnie!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Błędne dane logowania', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Wylogowano pomyślnie.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-hasla')
def reset_hasla():
    return "Strona resetowania hasła w budowie..."