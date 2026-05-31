import os
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from extensions import db
from models import (
    Student, Praktyka, Dokument, WpisDziennika, Porozumienie, Oswiadczenie,
    WniosekZaliczeniePraktyki, Protokol,
    HarmonogramPraktyki, ProgramPraktyki, Zal2aPodpisy, Powiadomienie, Uzytkownik,
    Sprawozdanie, KartaPraktyki, ZalacznikDziennika
)
from datetime import datetime, date
from werkzeug.utils import secure_filename
student_api_bp = Blueprint('student_api', __name__, url_prefix='/student')

@student_api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        return jsonify({'error': 'Twój profil studenta nie jest jeszcze kompletny.'}), 404

    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    powiadomienia = []
    
    return jsonify({
        'student': student.to_dict(),
        'praktyka': praktyka.to_dict() if praktyka else None,
        'uzytkownik': current_user.to_dict(),
        'powiadomienia': powiadomienia
    })

@student_api_bp.route('/dziennik', methods=['GET', 'POST'])
@login_required
def dziennik():
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        return jsonify({'error': 'Brak profilu studenta'}), 404

    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        return jsonify({'error': 'Brak praktyki'}), 404

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL6').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL6', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    if request.method == 'POST':
        if 'dane' in request.form:
            import json
            data = json.loads(request.form['dane'])
        else:
            data = request.json
            
        if not data or 'wpisy' not in data:
            return jsonify({'error': 'Nieprawidłowe dane'}), 400

        rok_akademicki = data.get('rok_akademicki')
        if rok_akademicki:
            student.rok_akademicki = rok_akademicki

        wpisy_data = data['wpisy']
        dzisiaj = datetime.now().date()
        bledy = []
        otrzymane_id = []

        wpisy_z_bazy = {str(w.id): w for w in WpisDziennika.query.filter_by(dokument_id=dokument.id).all()}

        for i, wpis in enumerate(wpisy_data):
            wid = str(wpis.get('wpis_id', ''))
            data_str = wpis.get('data')
            opis = wpis.get('opis')
            efekt = wpis.get('efekt', '')

            if wid:
                otrzymane_id.append(wid)

            if not data_str or not opis:
                continue

            try:
                data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
            except ValueError:
                continue
            
            if len(opis.strip()) < 200:
                bledy.append(f"Wpis z dnia {data_str} jest za krótki (minimum 200 znaków).")
                continue
            
            if data_obj > dzisiaj:
                bledy.append(f"Data wpisu z dnia {data_str} nie może być z przyszłości.")
                continue
            
            if praktyka.data_start and data_obj < praktyka.data_start:
                bledy.append(f"Data wpisu z dnia {data_str} jest sprzed rozpoczęcia praktyki.")
                continue

            if wid and wid in wpisy_z_bazy:
                istniejacy = wpisy_z_bazy[wid]
                if istniejacy.potwierdzony_zopz == 1:
                    continue # ignorowanie zmiany w zatwierdzonych
                istniejacy.data_wpisu = data_obj
                istniejacy.opis_prac = opis
                istniejacy.nr_efektu = efekt
                istniejacy.numer_dnia = i + 1
                
                if istniejacy.potwierdzony_zopz == -1:
                    istniejacy.potwierdzony_zopz = 0
                    istniejacy.komentarz_zopz = None
            else:
                nowy_wpis = WpisDziennika(
                    dokument_id=dokument.id,
                    numer_dnia=i + 1,
                    data_wpisu=data_obj,
                    opis_prac=opis,
                    nr_efektu=efekt
                )
                db.session.add(nowy_wpis)

        # usuniecie wpisow o ile nie sa zatwierdzone
        for wid, w in wpisy_z_bazy.items():
            if wid not in otrzymane_id and not w.potwierdzony_zopz:
                db.session.delete(w)
        
        db.session.commit()
        
        if bledy:
            return jsonify({'success': False, 'errors': bledy}), 400
            
        return jsonify({'success': True, 'message': 'Dziennik praktyk został zapisany pomyślnie!'})

    wpisy = WpisDziennika.query.filter_by(dokument_id=dokument.id).order_by(WpisDziennika.numer_dnia).all()

    praktyka_info = {
        'zaklad_nazwa': praktyka.zaklad.nazwa if praktyka.zaklad else 'Brak przypisanej firmy',
        'data_start': praktyka.data_start.isoformat() if praktyka.data_start else '',
        'data_end': praktyka.data_end.isoformat() if praktyka.data_end else '',
        'rok_akademicki': student.rok_akademicki if student.rok_akademicki else ''
    }

    today_date = datetime.now().date().isoformat()
    max_date = today_date
    if praktyka.data_end:
        praktyka_end_str = praktyka.data_end.isoformat()
        max_date = min(today_date, praktyka_end_str)

    efekty_lista = [
        {"kod": "01", "opis": "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych."},
        {"kod": "02", "opis": "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce."},
        {"kod": "03", "opis": "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy."},
        {"kod": "04", "opis": "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka."},
        {"kod": "05", "opis": "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania, posługując się rozmaitymi źródłami literaturowymi i zasobami."},
        {"kod": "06", "opis": "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje zawodowe."},
        {"kod": "07", "opis": "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia."},
        {"kod": "08", "opis": "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy i zaproponować jego rozwiązanie."},
        {"kod": "09", "opis": "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności IT, stosując odpowiednie normy i standardy."},
        {"kod": "10", "opis": "Pracuje w zespole zajmującym się zawodowo branżą IT."},
        {"kod": "11", "opis": "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów."},
        {"kod": "12", "opis": "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje do realizacji zadania, jak i przekazać im w sposób zrozumiały opinie z zakresu informatyki."},
        {"kod": "13", "opis": "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki działalności informatyków, szczególnie te ekonomiczne i społeczne."}
    ]
    
    zalaczniki = ZalacznikDziennika.query.filter_by(dokument_id=dokument.id).all()

    return jsonify({
        'praktyka': praktyka_info,
        'wpisy': [w.to_dict() for w in wpisy],
        'today_date': today_date,
        'max_date': max_date,
        'efekty_lista': efekty_lista,
        'zalaczniki': [z.to_dict() for z in zalaczniki],
        'status_dokumentu': dokument.status
    })

@student_api_bp.route('/dziennik/wyslij_do_zopz', methods=['POST'])
@login_required
def wyslij_do_zopz():
    if current_user.rola != 'student':
        return jsonify({'error': 'Brak dostępu'}), 403
        
    student = current_user.student_profil
    if not student:
        return jsonify({'error': 'Brak profilu studenta'}), 400
        
    praktyka = student.praktyki[0] if student.praktyki else None
    if not praktyka:
        return jsonify({'error': 'Brak przypisanej praktyki'}), 400
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL6').first()
    if not dokument:
        return jsonify({'error': 'Dziennik nie został jeszcze utworzony'}), 400
        
    if dokument.status not in ['Draft', 'Wrócono do poprawy']:
        return jsonify({'error': f'Nie można wysłać dziennika w obecnym statusie: {dokument.status}'}), 400
        
    wpisy_count = WpisDziennika.query.filter_by(dokument_id=dokument.id).count()
    if wpisy_count < 3:
        return jsonify({'error': f'Wymagane minimum 3 wpisów. Obecnie masz {wpisy_count}.'}), 400
        
    dokument.status = 'Weryfikacja ZOPZ'
    
    # Powiadomienie dla ZOPZ
    if praktyka.zaklad and praktyka.zaklad.zopz_id:
        from flask import url_for
        notif = Powiadomienie(
            uzytkownik_id=praktyka.zaklad.zopz_id,
            tresc=f"Student {student.uzytkownik.imie} {student.uzytkownik.nazwisko} ({student.nr_albumu}) przesłał Dziennik Praktyk do weryfikacji.",
            link=url_for('zopz.teczka', student_id=student.id)
        )
        db.session.add(notif)
        
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Dziennik został pomyślnie wysłany do weryfikacji ZOPZ!'})

@student_api_bp.route('/dziennik/wyslij_do_uopz', methods=['POST'])
@login_required
def wyslij_do_uopz():
    if current_user.rola != 'student':
        return jsonify({'error': 'Brak dostępu'}), 403
        
    student = current_user.student_profil
    if not student:
        return jsonify({'error': 'Brak profilu studenta'}), 400
        
    praktyka = student.praktyki[0] if student.praktyki else None
    if not praktyka:
        return jsonify({'error': 'Brak przypisanej praktyki'}), 400
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL6').first()
    if not dokument:
        return jsonify({'error': 'Dziennik nie został jeszcze utworzony'}), 400
        
    if dokument.status != 'Zatwierdzone przez ZOPZ':
        return jsonify({'error': f'Nie można wysłać dziennika w obecnym statusie: {dokument.status}'}), 400
        
    dokument.status = 'Weryfikacja UOPZ'
    
    # Powiadomienie dla UOPZ
    if praktyka.uopz_id:
        from flask import url_for
        notif = Powiadomienie(
            uzytkownik_id=praktyka.uopz_id,
            tresc=f"Student {student.uzytkownik.imie} {student.uzytkownik.nazwisko} ({student.nr_albumu}) przesłał Dziennik Praktyk (zaakceptowany przez ZOPZ) do ostatecznego zatwierdzenia.",
            link=f"/uopz/dziennik/{student.id}"
        )
        db.session.add(notif)
        
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Dziennik został wysłany do ostatecznego zatwierdzenia przez Dziekanat (UOPZ)!'})

@student_api_bp.route('/dziennik/zalacznik', methods=['POST'])
@login_required
def dodaj_zalacznik_dziennika():
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL6').first()
    
    if not dokument:
        return jsonify({'error': 'Nie znaleziono dokumentu'}), 404
        
    zal_count = int(request.form.get('zal_count', 0))
    if zal_count == 0:
        return jsonify({'success': False, 'message': 'Brak załączników do zapisu.'}), 400
        
    bledy = []
    nowe_zalaczniki = []
    for i in range(zal_count):
        opis = request.form.get(f'zal_opis_{i}', '').strip()
        plik = request.files.get(f'zal_plik_{i}')
        
        if not opis or not plik or not plik.filename:
            bledy.append(f'Pominięto plik {i+1} z powodu braku opisu lub pliku.')
            continue
            
        oryginalna_nazwa = secure_filename(plik.filename)
        unikalna_nazwa = f"{student.nr_albumu}_ZAL6_zal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}_{oryginalna_nazwa}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unikalna_nazwa)
        
        try:
            plik.save(filepath)
            zalacznik = ZalacznikDziennika(
                dokument_id=dokument.id,
                opis=opis,
                plik_path=f"uploads/{unikalna_nazwa}"
            )
            db.session.add(zalacznik)
            nowe_zalaczniki.append(zalacznik)
        except Exception as e:
            bledy.append(f"Błąd przy pliku {oryginalna_nazwa}: {str(e)}")
            
    db.session.commit()
    
    zalaczniki_dane = []
    for z in nowe_zalaczniki:
        zalaczniki_dane.append({
            'id': z.id,
            'opis': z.opis,
            'plik_path': z.plik_path
        })
    
    return jsonify({
        'success': True,
        'message': 'Załączniki zapisane pomyślnie.',
        'errors': bledy,
        'zalaczniki': zalaczniki_dane
    })

@student_api_bp.route('/dziennik/zalacznik/<int:zid>', methods=['DELETE'])
@login_required
def usun_zalacznik_dziennika(zid):
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    zalacznik = ZalacznikDziennika.query.get_or_404(zid)
    
    # Check ownership indirectly
    dokument = Dokument.query.get(zalacznik.dokument_id)
    praktyka = Praktyka.query.get(dokument.praktyka_id)
    student = Student.query.get(praktyka.student_id)
    if student.uzytkownik_id != current_user.id:
        return jsonify({'error': 'Odmowa dostępu do pliku'}), 403
        
    if zalacznik.plik_path:
        try:
            nazwa_pliku = zalacznik.plik_path.replace('uploads/', '')
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], nazwa_pliku)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass # ignore deletion errors, just remove from db
            
    db.session.delete(zalacznik)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Załącznik usunięty pomyślnie.'})

@student_api_bp.route('/zal9_oswiadczenie', methods=['GET', 'POST'])
@login_required
def zal9_oswiadczenie():
    
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka:
        praktyka = Praktyka(student_id=student.id, status='BRAK_ZGŁOSZENIA')
        db.session.add(praktyka)
        db.session.commit()
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL6_SPRAWOZDANIE').first()
    sprawozdanie_obj = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first() if dokument else None
    
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
        
        data_start_str = request.form.get('data_start')
        data_end_str = request.form.get('data_end')
        if data_start_str:
            try:
                praktyka.data_start = datetime.strptime(data_start_str, '%Y-%m-%d').date()
                oswiadczenie.termin_od = praktyka.data_start
            except ValueError:
                pass
        if data_end_str:
            try:
                praktyka.data_end = datetime.strptime(data_end_str, '%Y-%m-%d').date()
                oswiadczenie.termin_do = praktyka.data_end
            except ValueError:
                pass
        
        rok = request.form.get('rok_studiow')
        if rok and rok.isdigit():
            student.rok_studiow = int(rok)
            oswiadczenie.rok_studiow = int(rok)
            
        kierunek = request.form.get('kierunek')
        if kierunek:
            student.kierunek = kierunek
            oswiadczenie.kierunek = kierunek

        plik = request.files.get('skan_dokumentu')
        if plik and plik.filename != '':
            oryginalna_nazwa = secure_filename(plik.filename)
            unikalna_nazwa = f"{student.nr_albumu}_ZAL9_{oryginalna_nazwa}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unikalna_nazwa)
            plik.save(filepath)
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
            db.session.commit()
            return jsonify({'success': True, 'message': 'Plik usunięty'})
            
        elif akcja == 'wyslij':
            if not (praktyka.data_start and praktyka.data_end):
                return jsonify({'success': False, 'message': 'Błąd: Podaj datę rozpoczęcia i zakończenia praktyki przed wysłaniem formularza.'})

            dokument.status = 'Submitted'
            praktyka.status = 'OCZEKUJE_NA_ZAL9' 
            db.session.commit()
            return jsonify({'success': True, 'message': 'Oświadczenie zostało złożone.'})
        else:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Szkic oświadczenia został zapisany.'})
            
    dzisiaj = datetime.today().strftime('%Y-%m-%d')
    student_dict = student.to_dict()
    student_dict['imie'] = student.uzytkownik.imie
    student_dict['nazwisko'] = student.uzytkownik.nazwisko

    return jsonify({
        'student': student_dict,
        'dokument': dokument.to_dict() if dokument else None,
        'oswiadczenie': oswiadczenie.to_dict() if oswiadczenie else None,
        'praktyka': praktyka.to_dict(),
        'dzisiaj': dzisiaj
    })


@student_api_bp.route('/zal4b_wniosek', methods=['GET', 'POST'])
@login_required
def zal4b_wniosek():
    
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka:
        praktyka = Praktyka(student_id=student.id, status='BRAK_ZGŁOSZENIA')
        db.session.add(praktyka)
        db.session.commit()
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4B').first()
    wniosek = WniosekZaliczeniePraktyki.query.filter_by(dokument_id=dokument.id).first() if dokument else None
    
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'error': 'Brak danych'}), 400
            
        if not dokument:
            dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL4B', utworzony_przez=current_user.id)
            db.session.add(dokument)
            db.session.commit()
            
        if not wniosek:
            wniosek = WniosekZaliczeniePraktyki(dokument_id=dokument.id)
            db.session.add(wniosek)
            
        if 'specjalnosc' in data:
            student.specjalnosc = data.get('specjalnosc')

        try:
            wniosek.okres_zatrudnienia_od = datetime.strptime(data.get('data_od'), '%Y-%m-%d').date()
            wniosek.okres_zatrudnienia_do = datetime.strptime(data.get('data_do'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass
            
        wniosek.stanowisko = data.get('stanowisko')
        wniosek.zakres_obowiazkow = data.get('zakres_obowiazkow')
        wniosek.uzasadnienie = data.get('uzasadnienie')
        
        akcja = data.get('akcja')
        if akcja == 'wyslij':
            dokument.status = 'Submitted'
            praktyka.status = 'SCIEZKA_PRACA'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Wniosek został złożony. Uruchomiono ścieżkę zaliczenia na podstawie pracy zawodowej.'})
        else:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Szkic wniosku został zapisany.'})
            
    return jsonify({
        'student': student.to_dict(),
        'dokument': dokument.to_dict() if dokument else None,
        'wniosek': wniosek.to_dict() if wniosek else None,
        'praktyka': praktyka.to_dict()
    })

@student_api_bp.route('/porozumienie', methods=['GET'])
@student_api_bp.route('/zal2_program', methods=['GET'])
@student_api_bp.route('/zal3_karta', methods=['GET'])
@student_api_bp.route('/zal4_efekty', methods=['GET'])
@student_api_bp.route('/zal4a_decyzja', methods=['GET'])
@student_api_bp.route('/edytuj_dane', methods=['POST'])
@login_required
def edytuj_dane():
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403
    
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

@student_api_bp.route('/zal8_protokol', methods=['GET'])
@login_required
def get_dokumenty_readonly():
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403
    
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not student or not praktyka:
        return jsonify({'error': 'Brak praktyki'}), 404
        
    path = request.path
    typ_zal = None
    if 'porozumienie' in path: typ_zal = 'Porozumienie'
    elif 'zal2_program' in path: typ_zal = 'ZAL2'
    elif 'zal3_karta' in path: typ_zal = 'ZAL3'
    elif 'zal4_efekty' in path: typ_zal = 'ZAL4'
    elif 'zal4a_decyzja' in path: typ_zal = 'ZAL4A'
    elif 'zal8_protokol' in path: typ_zal = 'ZAL8'
    
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika=typ_zal).first() if typ_zal else None
    
    karta = KartaPraktyki.query.filter_by(dokument_id=dokument.id).first() if (dokument and typ_zal == 'ZAL3') else None
    decyzja = None
    protokol = Protokol.query.filter_by(dokument_id=dokument.id).first() if (dokument and typ_zal == 'ZAL8') else None

    return jsonify({
        'student': student.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict() if dokument else None,
        'karta': karta.to_dict() if karta else None,
        'decyzja': decyzja.to_dict() if decyzja else None,
        'protokol': protokol.to_dict() if protokol else None
    })

@student_api_bp.route('/zal2a_harmonogram', methods=['GET', 'POST'])
@login_required
def zal2a_harmonogram_api():
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        return jsonify({'error': 'Brak praktyki'}), 404

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL2A').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL2A', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    podpisy = Zal2aPodpisy.query.filter_by(dokument_id=dokument.id).first()
    if not podpisy:
        podpisy = Zal2aPodpisy(dokument_id=dokument.id)
        db.session.add(podpisy)
        db.session.commit()

    if request.method == 'POST':
        data = request.json
        akcja = data.get('akcja')
        komentarz = data.get('komentarz')

        if komentarz is not None:
            dokument.komentarz = komentarz
            
        specjalnosc = data.get('specjalnosc')
        if specjalnosc is not None:
            student.specjalnosc = specjalnosc

        if akcja == 'akceptuj':
            dokument.status = 'Submitted'
            dokument.uwagi_opiekuna = ""
            if data.get('zloz_podpis'):
                clean_nazwisko = current_user.nazwisko.split('(')[0].strip()
                podpisy.podpis_student = f"{current_user.imie} {clean_nazwisko}"
                podpisy.data_student = date.today()
                
            notif = Powiadomienie(
                uzytkownik_id=praktyka.uopz_id,
                tresc=f"Student {current_user.imie} {current_user.nazwisko} zaakceptował Załącznik 2a (przesłano do Dziekanatu).",
                link=f"/uopz/zal2a_harmonogram/{student.id}"
            )
            db.session.add(notif)
            
            pracownicy_dziekanatu = Uzytkownik.query.filter(Uzytkownik.rola.in_(['dziekanat', 'dyrektor'])).all()
            for pd in pracownicy_dziekanatu:
                notif_d = Powiadomienie(
                    uzytkownik_id=pd.id,
                    tresc=f"Student {current_user.imie} {current_user.nazwisko} zaakceptował Załącznik 2a do końcowej weryfikacji.",
                    link=f"/dziekanat/weryfikuj_zal2a/{praktyka.id}"
                )
                db.session.add(notif_d)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Zatwierdziłeś harmonogram praktyki i przekazałeś do Dziekanatu!'})

        elif akcja == 'odrzuc':
            dokument.status = 'Draft_UOPZ'
            if komentarz:
                dokument.uwagi_opiekuna = f"UWAGA STUDENTA: {komentarz}"
            else:
                dokument.uwagi_opiekuna = "Student odrzucił harmonogram bez komentarza."
                
            notif = Powiadomienie(
                uzytkownik_id=praktyka.uopz_id,
                tresc=f"Student {current_user.imie} {current_user.nazwisko} ODRZUCIŁ Załącznik 2a.",
                link=f"/uopz/zal2a_harmonogram/{student.id}"
            )
            db.session.add(notif)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Odrzuciłeś harmonogram. Zwrócono do UOPZ do poprawy.'})
            
        elif akcja == 'zapisz_komentarz':
            db.session.commit()
            return jsonify({'success': True, 'message': 'Twój komentarz został zapisany.'})
            
        elif akcja == 'zapisz_specjalnosc':
            db.session.commit()
            return jsonify({'success': True, 'message': 'Specjalność została zapisana.'})

    pozycje = HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).order_by(HarmonogramPraktyki.lp).all()
    suma_dni = sum(p.planowana_liczba_dni for p in pozycje)
    zapisane_programy = {p.kod_efektu: p.dzial_prace for p in ProgramPraktyki.query.filter_by(dokument_id=dokument.id).all()}
    
    student_data = student.to_dict()
    student_data['imie'] = current_user.imie
    student_data['nazwisko'] = current_user.nazwisko
    
    praktyka_data = praktyka.to_dict()
    praktyka_data['zaklad_nazwa'] = praktyka.zaklad.nazwa if praktyka.zaklad else ''

    return jsonify({
        'student': student_data,
        'praktyka': praktyka_data,
        'dokument': dokument.to_dict(),
        'podpisy': podpisy.to_dict() if podpisy else None,
        'pozycje': [p.to_dict() for p in pozycje],
        'zapisane_programy': zapisane_programy,
        'suma_dni': suma_dni
    })

@student_api_bp.route('/sprawozdanie', methods=['GET', 'POST'])
@login_required
def sprawozdanie():
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

@student_api_bp.route('/zal7a_sprawozdanie', methods=['GET', 'POST'])
@login_required
def zal7a_sprawozdanie_api():
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        return jsonify({'error': 'Brak praktyki'}), 404

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    sprawozdanie_doc = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first()

    if request.method == 'POST':
        data = request.json
        charakterystyka = data.get('charakterystyka', '').strip()
        opis = data.get('opis', '').strip()
        wiedza = data.get('wiedza', '').strip()

        if len(charakterystyka) < 150 or len(opis) < 300 or len(wiedza) < 300:
            return jsonify({'success': False, 'message': 'Błąd zapisu! Niektóre sekcje są zbyt krótkie.'})
        else:
            if not sprawozdanie_doc:
                sprawozdanie_doc = Sprawozdanie(dokument_id=dokument.id)
                db.session.add(sprawozdanie_doc)

            sprawozdanie_doc.charakterystyka = charakterystyka
            sprawozdanie_doc.opis_prac = opis
            sprawozdanie_doc.wiedza_umiejetnosci = wiedza
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Sprawozdanie z pracy zawodowej zapisano pomyślnie!'})

    return jsonify({
        'student': student.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict(),
        'sprawozdanie': sprawozdanie_doc.to_dict() if sprawozdanie_doc else None
    })
