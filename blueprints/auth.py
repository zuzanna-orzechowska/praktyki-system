# plik: blueprints/auth.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
import os
from extensions import login_manager, db, oauth
from models import Uzytkownik, Student

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return Uzytkownik.query.get(int(user_id))

# system ról i uprawnień
def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.rola not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return decorated
    return wrapper

def init_oauth(app):
    oauth.init_app(app)
    
    #Konfiguracja Microsoft Entra ID
    oauth.register(
        name='microsoft',
        client_id=os.getenv('MICROSOFT_CLIENT_ID'),
        client_secret=os.getenv('MICROSOFT_CLIENT_SECRET'),
        # Zamiast server_metadata_url 3 najważniejsze linki ręcznie: #!!!!!!!
        access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
        authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        jwks_uri='https://login.microsoftonline.com/common/discovery/v2.0/keys',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    # Konfiguracja Google
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

@auth_bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

@auth_bp.route('/login/<provider>')
def login_oauth(provider):
    client = oauth.create_client(provider)
    if not client:
        abort(404)
    redirect_uri = url_for('auth.auth_callback', provider=provider, _external=True)
    return client.authorize_redirect(redirect_uri)

@auth_bp.route('/callback/<provider>')
def auth_callback(provider):
    client = oauth.create_client(provider)
    token = client.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
        flash('Nie udało się pobrać danych użytkownika z systemu tożsamości.', 'danger')
        return redirect(url_for('auth.login'))

    email = user_info.get('email')
    external_id = user_info.get('sub') or user_info.get('oid')
    
    # Wyciąganie imienia i nazwiska w zależności od dostawcy
    imie = user_info.get('given_name', '')
    nazwisko = user_info.get('family_name', '')
    if not imie or not nazwisko:
        name_parts = user_info.get('name', 'Nieznane Nieznane').split(' ', 1)
        imie = name_parts[0]
        nazwisko = name_parts[1] if len(name_parts) > 1 else ''

    user = Uzytkownik.query.filter_by(email=email).first()
    
    # Obsługa PIERWSZEGO logowania
    if not user:
        domain = email.split('@')[1] if '@' in email else ''
        nr_albumu = email.split('@')[0] if domain == 'student.ans-elblag.pl' else None
        
        if email == 'orzechosiaa.searchw@gmail.com': #EMAIL DO WYKASOWANIA W PRZYSZLOSCI TYLK ODO CELOW TESTOWYCH
            rola = 'dziekanat'
            aktywny = 1
        elif domain == 'student.ans-elblag.pl': #TUTAJ MA BYĆ IF
            rola = 'student'
            aktywny = 1
        elif domain == 'ans-elblag.pl': #TUTAJ PÓŹNIEJ ZAIMPLEMENTOWAĆ  ŻE TA ROLA JEST NAJPIERW OOCZEUKJACA I ADMIN MUSI ZATWIERDZIC
            rola = 'oczekujacy_pracownik' 
            aktywny = 0 
        else:
            flash('Brak dostępu dla tej domeny e-mail. Jeśli jesteś Opiekunem Zakładowym (ZOPZ), poproś uczelnię o wcześniejsze dodanie Twojego konta.', 'danger')
            return redirect(url_for('auth.login'))

        #Tworzenie konta Użytkownika
        user = Uzytkownik(
            email=email,
            imie=imie,
            nazwisko=nazwisko,
            rola=rola,
            aktywny=aktywny,
            auth_provider=provider,
            external_id=external_id
        )
        db.session.add(user)
        db.session.commit()
        
        #Tworzenie powiązanego profilu Studenta (tylko dla roli student)
        if rola == 'student' and nr_albumu:
            nowy_student = Student(
                uzytkownik_id=user.id,
                nr_albumu=nr_albumu,
                kierunek='Informatyka',      #DOMYŚLNE WARTOŚCI - DO ZMIANY MOGĄ BYĆ
                tryb_studiow='stacjonarne',  
                rok_studiow=3                
            )
            db.session.add(nowy_student)
            db.session.commit()
        
        if aktywny == 0:
            flash('Utworzono konto pracownicze. Poczekaj na weryfikację i przypisanie roli przez Administratora.', 'warning')
            return redirect(url_for('auth.login'))
    if user.aktywny == 0:
        flash('Twoje konto jest zablokowane lub oczekuje na weryfikację.', 'warning')
        return redirect(url_for('auth.login'))

    login_user(user)
    flash(f'Zalogowano pomyślnie przez {provider.capitalize()}!', 'success')
    
    if user.rola == 'dziekanat':
        return redirect(url_for('dziekanat.dashboard'))
    elif user.rola == 'student':
        return redirect(url_for('student.dashboard'))
    elif user.rola == 'uopz':
        return redirect(url_for('uopz.dashboard'))
        
    return redirect(url_for('index'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))