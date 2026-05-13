from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Uzytkownik, Oswiadczenie, Dokument, db
import string
import random

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'admin':
        return redirect(url_for('index'))
    
    oczekujacy = Uzytkownik.query.filter_by(rola='oczekujacy_pracownik').all()
    pracownicy = Uzytkownik.query.filter(Uzytkownik.rola.in_(['dziekanat', 'uopz', 'admin'])).all()
    opiekunowie = Uzytkownik.query.filter_by(rola='zopz').all()
    
    # pobranie oświadczenia które przekazał dziekanat
    zgloszenia_zopz = Oswiadczenie.query.join(Dokument).filter(Dokument.status == 'AwaitingAccount').all()
    
    return render_template('admin/dashboard.html', 
                           oczekujacy=oczekujacy, 
                           pracownicy=pracownicy, 
                           opiekunowie=opiekunowie,
                           zgloszenia_zopz=zgloszenia_zopz)

@admin_bp.route('/akceptuj_pracownika/<int:id>', methods=['POST'])
@login_required
def akceptuj_pracownika(id):
    if current_user.rola != 'admin': return redirect(url_for('index'))
    
    user = Uzytkownik.query.get_or_404(id)
    rola = request.form.get('rola')
    
    user.rola = rola
    user.aktywny = 1
    db.session.commit()
    flash(f'Użytkownik {user.email} został aktywowany jako {rola}.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/stworz_zopz_z_zal9/<int:oswiadczenie_id>', methods=['POST'])
@login_required
def stworz_zopz_z_zal9(oswiadczenie_id):
    if current_user.rola != 'admin': return redirect(url_for('index'))
    
    oswiadczenie = Oswiadczenie.query.get_or_404(oswiadczenie_id)
    email_zopz = oswiadczenie.opiekun_email.lower()
    domain = email_zopz.split('@')[1] if '@' in email_zopz else ''

    # 1.Czy konto już nie istnieje
    if Uzytkownik.query.filter_by(email=email_zopz).first():
        flash(f'Konto dla {email_zopz} już istnieje w systemie.', 'warning')
        oswiadczenie.dokument.status = 'AccountCreated'
        db.session.commit()
        return redirect(url_for('admin.dashboard'))

    # 2.Wybieranie sposobu logowania
    temp_password = None
    if 'gmail.com' in domain:
        provider = 'google'
    elif 'ans-elblag.pl' in domain:
        provider = 'microsoft'
    else:
        provider = 'local'
        #hasło dla logowania lokalnego
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    nowy_zopz = Uzytkownik(
        email=email_zopz,
        imie=oswiadczenie.opiekun_imie,
        nazwisko=oswiadczenie.opiekun_nazwisko,
        rola='zopz',
        aktywny=1,
        auth_provider=provider
    )
    
    if temp_password:
        nowy_zopz.set_password(temp_password)

    db.session.add(nowy_zopz)
    oswiadczenie.dokument.status = 'AccountCreated'
    db.session.commit()

    if provider == 'local':
        flash(f'Utworzono konto ZOPZ z logowaniem LOKALNYM. Przekaż opiekunowi hasło: {temp_password}', 'success')
    elif provider == 'google':
        flash(f'Utworzono konto ZOPZ z logowaniem GOOGLE. Opiekun ({email_zopz}) może zalogować się jednym kliknięciem bez hasła.', 'success')

    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/stworz_zopz', methods=['POST'])
@login_required
def stworz_zopz():
    if current_user.rola != 'admin': return redirect(url_for('index'))
    
    email = request.form.get('email')
    imie = request.form.get('imie')
    nazwisko = request.form.get('nazwisko')
    
    if Uzytkownik.query.filter_by(email=email).first():
        flash('Użytkownik o tym e-mailu już istnieje!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    haslo = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    nowy_zopz = Uzytkownik(
        email=email,
        imie=imie,
        nazwisko=nazwisko,
        rola='zopz',
        aktywny=1,
        auth_provider='local'
    )
    nowy_zopz.set_password(haslo)
    db.session.add(nowy_zopz)
    db.session.commit()
    
    flash(f'Utworzono konto ZOPZ! E-mail: {email}, Hasło: {haslo}', 'success')
    return redirect(url_for('admin.dashboard'))