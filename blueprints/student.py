from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Student, Praktyka, Dokument, WpisDziennika, Porozumienie, HarmonogramPraktyki, Uzytkownik, Protokol, Sprawozdanie, EfektUczenia, WniosekZaliczeniePraktyki, Oswiadczenie
from datetime import datetime
from werkzeug.utils import secure_filename
import os

student_bp = Blueprint('student', __name__, url_prefix='/student')

UPLOAD_FOLDER = 'static/uploads/zal4b'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

    return render_template('dokumenty/zal6_dziennik.html', praktyka=praktyka_info, wpisy=wpisy, today_date=today_date, max_date=max_date, efekty_lista=efekty_lista)


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
        'dokumenty/zal1_porozumienie.html',
        student=student,
        praktyka=praktyka,
        porozumienie=porozumienie_doc
    )

@student_bp.route('/zal2_program')
@login_required
def zal2_program():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    return render_template('dokumenty/zal2_program.html', student=student, praktyka=praktyka)

@student_bp.route('/zal2a_harmonogram', methods=['GET', 'POST'])
@login_required
def zal2a_harmonogram():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL2A').first()
    if not dokument:
        # Jeśli UOPZ jeszcze nic nie stworzył, tworzymy pusty wgląd
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL2A', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    if request.method == 'POST':
        akcja = request.form.get('akcja')
        komentarz = request.form.get('komentarz')

        if akcja == 'akceptuj':
            dokument.status = 'Approved'
            dokument.uwagi_opiekuna = ""
            if praktyka.status in ['OCZEKUJE_NA_ZAL9', 'ZAL9_PRZYJETY', 'POROZUMIENIE_PODPISANE']:
                praktyka.status = 'PROGRAM_UZGODNIONY'
            flash('Zatwierdziłeś harmonogram praktyki!', 'success')

        elif akcja == 'odrzuc':
            dokument.status = 'Rejected'
            dokument.uwagi_opiekuna = f"UWAGA STUDENTA: {komentarz}" if komentarz else "Student odrzucił harmonogram bez komentarza."
            flash('Odrzuciłeś harmonogram. UOPZ został o tym poinformowany.', 'warning')
            
        db.session.commit()
        return redirect(url_for('student.zal2a_harmonogram'))

    pozycje = HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).order_by(HarmonogramPraktyki.lp).all()
    suma_dni = sum(p.planowana_liczba_dni for p in pozycje)

    return render_template('dokumenty/zal2a_harmonogram.html', student=student, praktyka=praktyka, pozycje=pozycje, suma_dni=suma_dni, dokument=dokument)

@student_bp.route('/zal3_karta')
@login_required
def zal3_karta():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))

    uopz = Uzytkownik.query.get(praktyka.uopz_id) if praktyka.uopz_id else None
    porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
    protokol = Protokol.query.filter_by(praktyka_id=praktyka.id).first()
    
    zopz = Uzytkownik.query.get(praktyka.zaklad.zopz_id) if praktyka.zaklad and praktyka.zaklad.zopz_id else None

    return render_template(
        'dokumenty/zal3_karta.html', 
        student=student, 
        praktyka=praktyka, 
        uopz=uopz, 
        zopz=zopz,
        porozumienie=porozumienie, 
        protokol=protokol
    )

@student_bp.route('/sprawozdanie', methods=['GET', 'POST'])
@login_required
def sprawozdanie():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL7', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    sprawozdanie_doc = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first()

    if request.method == 'POST':
        charakterystyka = request.form.get('charakterystyka', '').strip()
        opis = request.form.get('opis', '').strip()
        wiedza = request.form.get('wiedza', '').strip()

        if len(charakterystyka) < 150 or len(opis) < 300 or len(wiedza) < 300:
            flash('Błąd zapisu! Niektóre sekcje są zbyt krótkie. Wymagamy dłuższego, merytorycznego opisu.', 'danger')
        else:
            if not sprawozdanie_doc:
                sprawozdanie_doc = Sprawozdanie(dokument_id=dokument.id)
                db.session.add(sprawozdanie_doc)

            sprawozdanie_doc.charakterystyka = charakterystyka
            sprawozdanie_doc.opis_prac = opis
            sprawozdanie_doc.wiedza_umiejetnosci = wiedza
            
            db.session.commit()
            flash('Sprawozdanie zapisano pomyślnie!', 'success')
            return redirect(url_for('student.sprawozdanie'))

    return render_template(
        'dokumenty/zal7_sprawozdanie.html', 
        student=student, 
        praktyka=praktyka, 
        sprawozdanie=sprawozdanie_doc
    )

@student_bp.route('/zal4_efekty')
@login_required
def zal4_efekty():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4').first()
    efekty = []
    
    if dokument:
        efekty = EfektUczenia.query.filter_by(dokument_id=dokument.id).order_by(EfektUczenia.kod_efektu).all()

    lista_wymaganych_efektow = [
        "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych",
        "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce",
        "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy",
        "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka",
        "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania...",
        "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje...",
        "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia",
        "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy / instytucji, opisać go, przedstawić koncepcję rozwiązania i ją zrealizować.",
        "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności informatycznej...",
        "Pracuje w zespole zajmującym się zawodowo branżą IT",
        "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów",
        "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje...",
        "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki działalności informatyków..."
    ]

    return render_template(
        'dokumenty/zal4_efekty.html', 
        student=student, 
        praktyka=praktyka, 
        dokument=dokument,
        efekty=efekty,
        lista_statyczna=lista_wymaganych_efektow
    )

@student_bp.route('/zal4a_decyzja')
@login_required
def zal4a_decyzja():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4A').first()

    return render_template('dokumenty/zal4a_decyzja.html', student=student, praktyka=praktyka, dokument=dokument)

@student_bp.route('/zal4b_wniosek', methods=['GET', 'POST'])
@login_required
def zal4b_wniosek():
    if current_user.rola != 'student':
        return redirect(url_for('index'))
        
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    # stworzenie parktyki jeśli nie istnieje
    if not praktyka:
        praktyka = Praktyka(student_id=student.id, status='BRAK_ZGŁOSZENIA')
        db.session.add(praktyka)
        db.session.commit()
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4B').first()
    wniosek = WniosekZaliczeniePraktyki.query.filter_by(dokument_id=dokument.id).first() if dokument else None
    
    if request.method == 'POST':
        if not dokument:
            dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL4B', utworzony_przez=current_user.id)
            db.session.add(dokument)
            db.session.commit()
            
        if not wniosek:
            wniosek = WniosekZaliczeniePraktyki(dokument_id=dokument.id)
            db.session.add(wniosek)
            
        if 'specjalnosc' in request.form:
            student.specjalnosc = request.form.get('specjalnosc')

        wniosek.okres_zatrudnienia_od = datetime.strptime(request.form.get('data_od'), '%Y-%m-%d').date()
        wniosek.okres_zatrudnienia_do = datetime.strptime(request.form.get('data_do'), '%Y-%m-%d').date()
        wniosek.stanowisko = request.form.get('stanowisko')
        wniosek.zakres_obowiazkow = request.form.get('zakres_obowiazkow')
        wniosek.uzasadnienie = request.form.get('uzasadnienie')
        
        akcja = request.form.get('akcja')
        if akcja == 'wyslij':
            dokument.status = 'Submitted'
            praktyka.status = 'SCIEZKA_PRACA'
            flash('Wniosek został złożony. Uruchomiono ścieżkę zaliczenia na podstawie pracy zawodowej.', 'success')
        else:
            flash('Szkic wniosku został zapisany.', 'info')
            
        db.session.commit()
        return redirect(url_for('student.zal4b_wniosek'))
        
    return render_template('dokumenty/zal4b_wniosek.html', student=student, dokument=dokument, wniosek=wniosek, praktyka=praktyka)

@student_bp.route('/zal7a_sprawozdanie', methods=['GET', 'POST'])
@login_required
def zal7a_sprawozdanie():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    sprawozdanie_doc = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first()

    if request.method == 'POST':
        charakterystyka = request.form.get('charakterystyka', '').strip()
        opis = request.form.get('opis', '').strip()
        wiedza = request.form.get('wiedza', '').strip()

        if len(charakterystyka) < 150 or len(opis) < 300 or len(wiedza) < 300:
            flash('Błąd zapisu! Niektóre sekcje są zbyt krótkie.', 'danger')
        else:
            if not sprawozdanie_doc:
                sprawozdanie_doc = Sprawozdanie(dokument_id=dokument.id)
                db.session.add(sprawozdanie_doc)

            sprawozdanie_doc.charakterystyka = charakterystyka
            sprawozdanie_doc.opis_prac = opis
            sprawozdanie_doc.wiedza_umiejetnosci = wiedza
            
            db.session.commit()
            flash('Sprawozdanie z pracy zawodowej zapisano pomyślnie!', 'success')
            return redirect(url_for('student.zal7a_sprawozdanie'))

    return render_template(
        'dokumenty/zal7a_sprawozdanie.html', 
        student=student, 
        praktyka=praktyka, 
        sprawozdanie=sprawozdanie_doc
    )

@student_bp.route('/zal8_protokol')
@login_required
def zal8_protokol():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))

    protokol = Protokol.query.filter_by(praktyka_id=praktyka.id).first()

    return render_template('dokumenty/zal8_protokol.html', student=student, praktyka=praktyka, protokol=protokol)


@student_bp.route('/zal9_oswiadczenie', methods=['GET', 'POST'])
@login_required
def zal9_oswiadczenie():
    if current_user.rola != 'student':
        return redirect(url_for('index'))
        
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    #jeśli praktyka nie istnieje to tworzymy
    if not praktyka:
        praktyka = Praktyka(student_id=student.id, status='BRAK_ZGŁOSZENIA')
        db.session.add(praktyka)
        db.session.commit()
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
    oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument.id).first() if dokument else None
    
    if request.method == 'POST':
        if not dokument:
            dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL9', utworzony_przez=current_user.id)
            db.session.add(dokument)
            db.session.commit()
            
        if not oswiadczenie:
            oswiadczenie = Oswiadczenie(dokument_id=dokument.id)
            db.session.add(oswiadczenie)
            
        oswiadczenie.miejscowosc = request.form.get('miejscowosc')
        data_str = request.form.get('data_oswiadczenia')
        if data_str:
            try:
                oswiadczenie.data_oswiadczenia = datetime.strptime(data_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        oswiadczenie.nazwa_instytucji = request.form.get('nazwa_instytucji')
        oswiadczenie.opiekun_imie = request.form.get('opiekun_imie')
        oswiadczenie.opiekun_nazwisko = request.form.get('opiekun_nazwisko')
        oswiadczenie.opiekun_stanowisko = request.form.get('opiekun_stanowisko')
        oswiadczenie.opiekun_telefon = request.form.get('opiekun_telefon')
        oswiadczenie.opiekun_email = request.form.get('opiekun_email')
        oswiadczenie.osoba_upowazniona_imie = request.form.get('osoba_upowazniona_imie')
        oswiadczenie.osoba_upowazniona_nazwisko = request.form.get('osoba_upowazniona_nazwisko')
        oswiadczenie.osoba_upowazniona_stanowisko = request.form.get('osoba_upowazniona_stanowisko')
        plik = request.files.get('skan_dokumentu')
        if plik and plik.filename != '':
            #czyszczenie nazwy pliku
            oryginalna_nazwa = secure_filename(plik.filename)
            #tworzenie unikalnej nazwy
            unikalna_nazwa = f"{student.nr_albumu}_ZAL9_{oryginalna_nazwa}"
            #zbudowanie pełnej ścieżki
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unikalna_nazwa)
            #fizyczny zapis pliku na dysku
            plik.save(filepath)
            #zapisanie ścieżki w bazie danych
            oswiadczenie.skan_path = f"uploads/{unikalna_nazwa}"

        akcja = request.form.get('akcja')
        if akcja == 'usun_plik':
            if oswiadczenie.skan_path:
                try:
                    nazwa_pliku = oswiadczenie.skan_path.replace('uploads/', '')
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], nazwa_pliku))
                except Exception:
                    pass
                oswiadczenie.skan_path = ""
            flash('Zapisany plik został usunięty ze szkicu.', 'info')
        elif akcja == 'wyslij':
            dokument.status = 'Submitted'
            praktyka.status = 'OCZEKUJE_NA_ZAL9' 
            flash('Oświadczenie zostało złożone. Oczekuje na zatwierdzenie przez Dziekanat.', 'success')
        else:
            flash('Szkic oświadczenia został zapisany.', 'info')
            
        db.session.commit()
        return redirect(url_for('student.zal9_oswiadczenie'))
        
    dzisiaj = datetime.today().strftime('%Y-%m-%d')
    return render_template('dokumenty/zal9_oswiadczenie.html', student=student, dokument=dokument, oswiadczenie=oswiadczenie, praktyka=praktyka, dzisiaj=dzisiaj)