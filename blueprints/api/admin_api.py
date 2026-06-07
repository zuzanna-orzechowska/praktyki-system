from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import Uzytkownik, Oswiadczenie, Dokument, db
from extensions import mail
from flask_mail import Message
import string
import random

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/admin')

@admin_api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.rola != 'admin':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    oczekujacy = Uzytkownik.query.filter_by(rola='oczekujacy_pracownik').all()
    pracownicy = Uzytkownik.query.filter(Uzytkownik.rola.in_(['dziekanat', 'uopz', 'admin', 'dyrektor', 'pracownik'])).all()
    opiekunowie = Uzytkownik.query.filter_by(rola='zopz').all()
    
    zgloszenia_zopz = Oswiadczenie.query.join(Dokument).filter(Dokument.status == 'AwaitingAccount').all()
    
    def format_uzytkownik(u):
        return {
            'id': u.id,
            'email': u.email,
            'imie': u.imie,
            'nazwisko': u.nazwisko,
            'rola': u.rola,
            'auth_provider': u.auth_provider,
            'data_utworzenia': u.data_utworzenia.strftime('%Y-%m-%d %H:%M') if getattr(u, 'data_utworzenia', None) else ''
        }
        
    def format_zgloszenie(o):
        doc = o.dokument
        student = doc.praktyka.student
        return {
            'id': o.id,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'nazwa_instytucji': o.nazwa_instytucji,
            'opiekun_imie': o.opiekun_imie,
            'opiekun_nazwisko': o.opiekun_nazwisko,
            'opiekun_email': o.opiekun_email
        }

    return jsonify({
        'oczekujacy': [format_uzytkownik(u) for u in oczekujacy],
        'pracownicy': [format_uzytkownik(u) for u in pracownicy],
        'opiekunowie': [format_uzytkownik(u) for u in opiekunowie],
        'zgloszenia_zopz': [format_zgloszenie(z) for z in zgloszenia_zopz]
    })


@admin_api_bp.route('/akceptuj_pracownika/<int:id>', methods=['POST'])
@login_required
def akceptuj_pracownika(id):
    if current_user.rola != 'admin':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    user = Uzytkownik.query.get_or_404(id)
    data = request.json
    rola = data.get('rola')
    
    if not rola:
        return jsonify({'success': False, 'message': 'Nie podano nowej roli.'})
        
    user.rola = rola
    user.aktywny = 1
    db.session.commit()
    return jsonify({'success': True, 'message': f'Użytkownik {user.email} został aktywowany jako {rola}.'})


@admin_api_bp.route('/stworz_zopz_z_zal9/<int:oswiadczenie_id>', methods=['POST'])
@login_required
def stworz_zopz_z_zal9(oswiadczenie_id):
    from models import ZakladPracy
    if current_user.rola != 'admin':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    oswiadczenie = Oswiadczenie.query.get_or_404(oswiadczenie_id)
    email_zopz = oswiadczenie.opiekun_email.lower()
    domain = email_zopz.split('@')[1] if '@' in email_zopz else ''

    istniejacy_zopz = Uzytkownik.query.filter_by(email=email_zopz).first()
    
    def przypisz_zaklad_do_praktyki(zopz_id):
        # Sprawdz czy zakład już istnieje dla tego ZOPZ
        zaklad = ZakladPracy.query.filter_by(zopz_id=zopz_id).first()
        if not zaklad:
            zaklad = ZakladPracy(nazwa=oswiadczenie.nazwa_instytucji, zopz_id=zopz_id, miasto=oswiadczenie.miejscowosc, email=email_zopz, telefon=oswiadczenie.opiekun_telefon)
            db.session.add(zaklad)
            db.session.flush() # Wymusza nadanie ID bez commitu
            
        oswiadczenie.dokument.praktyka.zaklad_id = zaklad.id
        oswiadczenie.dokument.praktyka.uopz_id = None # Opcjonalnie

    if istniejacy_zopz:
        przypisz_zaklad_do_praktyki(istniejacy_zopz.id)
        oswiadczenie.dokument.status = 'AccountCreated'
        db.session.commit()
        return jsonify({'success': False, 'message': f'Konto dla {email_zopz} już istnieje w systemie. Zmieniono status dokumentu i automatycznie przypisano studenta do tego ZOPZ.'})

    temp_password = None
    if 'gmail.com' in domain:
        provider = 'google'
    elif 'ans-elblag.pl' in domain:
        provider = 'microsoft'
    else:
        provider = 'local'
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    nowy_zopz = Uzytkownik(
        email=email_zopz,
        imie=oswiadczenie.opiekun_imie,
        nazwisko=oswiadczenie.opiekun_nazwisko,
        rola='zopz',
        aktywny=1,
        auth_provider=provider,
        wymaga_zmiany_hasla=True if temp_password else False
    )
    
    if temp_password:
        nowy_zopz.set_password(temp_password)

    db.session.add(nowy_zopz)
    db.session.flush()
    
    przypisz_zaklad_do_praktyki(nowy_zopz.id)
    
    oswiadczenie.dokument.status = 'AccountCreated'
    db.session.commit()

    msg = Message('Utworzono konto w Systemie Obsługi Praktyk', recipients=[email_zopz])
    if provider == 'local':
        msg.body = f"Witaj {oswiadczenie.opiekun_imie} {oswiadczenie.opiekun_nazwisko},\n\nTwoje konto Opiekuna Zakładowego (ZOPZ) zostało utworzone.\n\nE-mail: {email_zopz}\nTymczasowe hasło: {temp_password}\n\nPrzy pierwszym logowaniu zostaniesz poproszony o zmianę hasła na własne."
    elif provider == 'google':
        msg.body = f"Witaj {oswiadczenie.opiekun_imie} {oswiadczenie.opiekun_nazwisko},\n\nTwoje konto Opiekuna Zakładowego (ZOPZ) zostało utworzone.\n\nPonieważ używasz adresu {email_zopz}, na stronie logowania po prostu kliknij 'Zaloguj się przez Google'. Nie potrzebujesz hasła do systemu."
    else:
        msg.body = f"Witaj {oswiadczenie.opiekun_imie} {oswiadczenie.opiekun_nazwisko},\n\nTwoje konto Opiekuna Zakładowego (ZOPZ) zostało utworzone.\n\nPonieważ używasz adresu {email_zopz}, na stronie logowania po prostu kliknij logowanie przez Microsoft. Nie potrzebujesz hasła do systemu."
        
    try:
        mail.send(msg)
        if provider == 'local':
            return jsonify({'success': True, 'message': f'Utworzono konto ZOPZ z logowaniem lokalnym. Wysłano e-mail z hasłem do {email_zopz}.'})
        elif provider == 'google':
            return jsonify({'success': True, 'message': f'Utworzono konto ZOPZ (GOOGLE). Wysłano powiadomienie e-mail do {email_zopz}.'})
        else:
            return jsonify({'success': True, 'message': f'Utworzono konto ZOPZ (MICROSOFT). Wysłano powiadomienie e-mail do {email_zopz}.'})
    except Exception as e:
        return jsonify({'success': True, 'message': f'Utworzono konto ZOPZ, ale wystąpił błąd przy wysyłaniu powiadomienia e-mail: {e}'})


@admin_api_bp.route('/stworz_zopz', methods=['POST'])
@login_required
def stworz_zopz():
    if current_user.rola != 'admin':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    data = request.json
    email = data.get('email')
    imie = data.get('imie')
    nazwisko = data.get('nazwisko')
    
    if not email or not imie or not nazwisko:
        return jsonify({'success': False, 'message': 'Proszę uzupełnić wszystkie pola.'})
    
    if Uzytkownik.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Użytkownik o tym e-mailu już istnieje!'})
    
    haslo = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    nowy_zopz = Uzytkownik(
        email=email,
        imie=imie,
        nazwisko=nazwisko,
        rola='zopz',
        aktywny=1,
        auth_provider='local',
        wymaga_zmiany_hasla=True
    )
    nowy_zopz.set_password(haslo)
    db.session.add(nowy_zopz)
    db.session.commit()
    
    msg = Message('Utworzono konto w Systemie Obsługi Praktyk', recipients=[email])
    msg.body = f"Witaj {imie} {nazwisko},\n\nTwoje konto Opiekuna Zakładowego (ZOPZ) zostało utworzone.\n\nE-mail: {email}\nTymczasowe hasło: {haslo}\n\nPrzy pierwszym logowaniu zostaniesz poproszony o zmianę hasła na własne."
    try:
        mail.send(msg)
        return jsonify({'success': True, 'message': f'Utworzono konto ZOPZ! Wysłano e-mail z tymczasowym hasłem na adres {email}.'})
    except Exception as e:
        return jsonify({'success': True, 'message': f'Utworzono konto ZOPZ, ale wystąpił błąd przy wysyłaniu e-maila: {e}'})
