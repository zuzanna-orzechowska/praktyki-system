from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Student, Praktyka, Dokument, WpisDziennika, Porozumienie
from datetime import datetime

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'student':
        flash('Odmowa dostępu. Strona tylko dla studentów.', 'danger')
        return redirect(url_for('index'))
    return render_template('student/dashboard.html')

@student_bp.route('/dziennik', methods=['GET', 'POST'])
@login_required
def dziennik():
    if current_user.rola != 'student':
        flash('Odmowa dostępu.', 'danger')
        return redirect(url_for('index'))

    # profil student i jego główna praktyka
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        flash('Twój profil studenta nie jest jeszcze kompletny.', 'warning')
        return redirect(url_for('student.dashboard'))

    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Nie masz jeszcze przypisanej praktyki w systemie.', 'warning')
        return redirect(url_for('student.dashboard'))

    # dokument "ZAL6"
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL6').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL6', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    # ZAPIS (POST)
    if request.method == 'POST':
        daty = request.form.getlist('data[]')
        opisy = request.form.getlist('opis[]')
        efekty = request.form.getlist('efekty[]')
        wpis_ids = request.form.getlist('wpis_id[]')

        dzisiaj = datetime.now().date()
        bledy = []

        wpisy_z_bazy = {str(w.id): w for w in WpisDziennika.query.filter_by(dokument_id=dokument.id).all()}
        otrzymane_id = []

        #zapis i aktualizacja wpisu
        for i in range(len(daty)):
            wid = wpis_ids[i] if i < len(wpis_ids) else ""
            if wid:
                otrzymane_id.append(wid)

            if not daty[i] or not opisy[i]:
                continue
                
            try:
                data_obj = datetime.strptime(daty[i], '%Y-%m-%d').date()
            except ValueError:
                continue
            
            if len(opisy[i].strip()) < 200:
                bledy.append(f"Wpis z dnia {daty[i]} jest za krótki (minimum 200 znaków) i nie został zapisany/zaktualizowany.")
                continue
            
            if data_obj > dzisiaj:
                bledy.append(f"Data wpisu z dnia {daty[i]} nie może być z przyszłości.")
                continue
            
            if praktyka.data_start and data_obj < praktyka.data_start:
                bledy.append(f"Data wpisu z dnia {daty[i]} jest sprzed rozpoczęcia praktyki.")
                continue

            if wid and wid in wpisy_z_bazy:
                istniejacy = wpisy_z_bazy[wid]
                if istniejacy.potwierdzony_zopz:
                    continue # ignorowanie zmiany w zatwierdzonych
                istniejacy.data_wpisu = data_obj
                istniejacy.opis_prac = opisy[i]
                istniejacy.nr_efektu = efekty[i] if i < len(efekty) else ''
                istniejacy.numer_dnia = i + 1
            else:
                nowy_wpis = WpisDziennika(
                    dokument_id=dokument.id,
                    numer_dnia=i + 1,
                    data_wpisu=data_obj,
                    opis_prac=opisy[i],
                    nr_efektu=efekty[i] if i < len(efekty) else ''
                )
                db.session.add(nowy_wpis)
                
        # usuniecie wpisow o ile nie sa zatwierdzone
        for wid, w in wpisy_z_bazy.items():
            if wid not in otrzymane_id and not w.potwierdzony_zopz:
                db.session.delete(w)
        
        db.session.commit()
        if bledy:
            for b in bledy:
                flash(b, 'danger')
            flash('Pozostałe wpisy zostały zapisane pomyślnie.', 'success')
        else:
            flash('Dziennik praktyk został zapisany pomyślnie!', 'success')
        return redirect(url_for('student.dziennik'))

    # 4. OBSŁUGA WYŚWIETLANIA (GET)
    wpisy = WpisDziennika.query.filter_by(dokument_id=dokument.id).order_by(WpisDziennika.numer_dnia).all()

    # Przygotowanie danych do nagłówka HTML
    praktyka_info = {
        'zaklad_nazwa': praktyka.zaklad.nazwa if praktyka.zaklad else 'Brak przypisanej firmy',
        'data_start': praktyka.data_start.strftime('%Y-%m-%d') if praktyka.data_start else '',
        'data_end': praktyka.data_end.strftime('%Y-%m-%d') if praktyka.data_end else ''
    }

    today_date = datetime.now().date().strftime('%Y-%m-%d')
    max_date = today_date
    if praktyka.data_end:
        praktyka_end_str = praktyka.data_end.strftime('%Y-%m-%d')
        max_date = min(today_date, praktyka_end_str)

    efekty_lista = [
        {"kod": "EK_01", "opis": "Rozumienie zasad działania systemów i aplikacji"},
        {"kod": "EK_02", "opis": "Umiejętność programowania i testowania"},
        {"kod": "EK_03", "opis": "Znajomość relacyjnych baz danych"},
        {"kod": "EK_04", "opis": "Praca w zespole i komunikacja"},
        {"kod": "EK_05", "opis": "Projektowanie interfejsów użytkownika"}
    ]

    return render_template('student/zal6_dziennik.html', praktyka=praktyka_info, wpisy=wpisy, today_date=today_date, max_date=max_date, efekty_lista=efekty_lista)


@student_bp.route('/porozumienie')
@login_required
def porozumienie():
    if current_user.rola != 'student':
        flash('Odmowa dostępu.', 'danger')
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        flash('Twój profil studenta nie jest jeszcze kompletny.', 'warning')
        return redirect(url_for('student.dashboard'))

    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Nie masz jeszcze przypisanej praktyki w systemie.', 'warning')
        return redirect(url_for('student.dashboard'))

    #jesli nie ma porozumienia to pusty szkic z danymi z praktyki
    porozumienie_doc = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()

    return render_template(
        'student/zal1_porozumienie.html',
        student=student,
        praktyka=praktyka,
        porozumienie=porozumienie_doc
    )