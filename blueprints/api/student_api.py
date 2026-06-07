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
    
    zal7a_status = None
    zal9_status = None
    zal9_komentarz = None
    dokumenty_dict = {}
    if praktyka:
        zal7a = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A').first()
        if zal7a:
            zal7a_status = zal7a.status
            
        zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
        if zal9:
            zal9_status = zal9.status
            zal9_komentarz = zal9.komentarz
            
        for d in praktyka.dokumenty:
            dokumenty_dict[d.typ_zalacznika] = True
    
    etap_standardowy = 1
    if praktyka and praktyka.status not in ['BRAK_ZGŁOSZENIA', 'OCZEKUJE_NA_ZAL9']:
        from models import Porozumienie
        porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
        
        poroz_ok = porozumienie and porozumienie.status in ['Podpisane', 'ZaakceptowaneDyrektor']
        
        if poroz_ok:
            etap_standardowy = 3
        else:
            etap_standardowy = 2
            
    powiadomienia = []
    
    return jsonify({
        'student': student.to_dict(),
        'praktyka': praktyka.to_dict() if praktyka else None,
        'uzytkownik': current_user.to_dict(),
        'powiadomienia': powiadomienia,
        'zal7a_status': zal7a_status,
        'zal9_status': zal9_status,
        'zal9_komentarz': zal9_komentarz,
        'dokumenty': dokumenty_dict,
        'etap_standardowy': etap_standardowy
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
        {"kod": "01", "opis": "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych"},
        {"kod": "02", "opis": "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce"},
        {"kod": "03", "opis": "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy"},
        {"kod": "04", "opis": "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka"},
        {"kod": "05", "opis": "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania, posługując się rozmaitymi źródłami literaturowymi i zasobami publikowanymi w języku polskim jak i angielskim"},
        {"kod": "06", "opis": "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje, wiedzę i umiejętności, co najmniej z dwóch zakresów: zadania dotyczące sprzętu i oprogramowania: np.: programowania, administrowanie siecią komputerową, konserwacja sprzętu i oprogramowania, bieżące usuwanie usterek, administrowanie zasobami informatycznymi, zakładu pracy / instytucji, (e)-usługami."},
        {"kod": "07", "opis": "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia"},
        {"kod": "08", "opis": "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy / instytucji, opisać go, przedstawić koncepcję rozwiązania i ją zrealizować."},
        {"kod": "09", "opis": "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności informatycznej zakładu pracy/instytucji stosując normy i standardy stosowane w informatyce oraz biorąc pod uwagę aspekty środowiskowe i etyczne."},
        {"kod": "10", "opis": "Pracuje w zespole zajmującym się zawodowo branżą IT,"},
        {"kod": "11", "opis": "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów"},
        {"kod": "12", "opis": "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje do realizacji planowanego zadania, jak i przekazać im w sposób zrozumiały informacje i opinie z zakresu informatyki"},
        {"kod": "13", "opis": "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki działalności informatyków w szczególności ekonomiczne i społeczne"}
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
            
            from models import dodaj_log
            dodaj_log(current_user.id, "Złożono wniosek o akceptację Zakładu Pracy (Zał. 9)")
            
            from models import Uzytkownik, Powiadomienie
            safe_nazwisko = current_user.nazwisko.split('(')[0].strip()
            dziekanat_users = Uzytkownik.query.filter(Uzytkownik.rola.in_(['dziekanat', 'dyrektor'])).all()
            for du in dziekanat_users:
                notif = Powiadomienie(
                    uzytkownik_id=du.id,
                    tresc=f"Student {current_user.imie} {safe_nazwisko} złożył oświadczenie o zatrudnieniu (Zał. 9).",
                    link=f"/dziekanat/weryfikuj_zal9/{oswiadczenie.id}"
                )
                db.session.add(notif)
                
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
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form
        else:
            data = request.json or {}

        if not data and not request.files:
            return jsonify({'error': 'Brak danych'}), 400
            
        if not dokument:
            dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL4B', utworzony_przez=current_user.id)
            db.session.add(dokument)
            db.session.commit()
            
        if not wniosek:
            wniosek = WniosekZaliczeniePraktyki(dokument_id=dokument.id)
            db.session.add(wniosek)
            
        akcja = data.get('akcja')
        
        import json
        
        if akcja == 'dodaj_zalacznik':
            zalaczniki = []
            if wniosek.zalaczniki_paths:
                try:
                    zalaczniki = json.loads(wniosek.zalaczniki_paths)
                except Exception:
                    if len(wniosek.zalaczniki_paths) > 5:
                        zalaczniki = [{"path": wniosek.zalaczniki_paths, "opis": "Załącznik (stary format)"}]
            
            if 'nowy_plik' in request.files:
                file = request.files['nowy_plik']
                if file and file.filename != '':
                    filename = secure_filename(f"ZAL4B_{student.nr_albumu}_{int(datetime.now().timestamp())}_{file.filename}")
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    opis = data.get('opis', '')
                    zalaczniki.append({"path": f"uploads/{filename}", "opis": opis})
                    
                    wniosek.zalaczniki_paths = json.dumps(zalaczniki)
                    db.session.commit()
                    return jsonify({'success': True, 'message': 'Załącznik dodany'})
            return jsonify({'success': False, 'message': 'Brak pliku do wgrania.'})
            
        if akcja == 'usun_zalacznik':
            idx = int(data.get('index', -1))
            if wniosek.zalaczniki_paths:
                try:
                    zalaczniki = json.loads(wniosek.zalaczniki_paths)
                    if 0 <= idx < len(zalaczniki):
                        usun_plik = zalaczniki.pop(idx)
                        try:
                            nazwa_pliku = usun_plik['path'].replace('uploads/', '')
                            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], nazwa_pliku))
                        except Exception:
                            pass
                        wniosek.zalaczniki_paths = json.dumps(zalaczniki)
                        db.session.commit()
                        return jsonify({'success': True, 'message': 'Załącznik usunięty'})
                except Exception:
                    pass
            return jsonify({'success': False, 'message': 'Błąd usuwania załącznika'})

        if akcja == 'dodaj_uzupelnienie':
            uzupelnienia = []
            if wniosek.uzupelnienia_paths:
                try:
                    uzupelnienia = json.loads(wniosek.uzupelnienia_paths)
                except Exception:
                    pass
            if 'nowy_plik' in request.files:
                file = request.files['nowy_plik']
                if file and file.filename != '':
                    filename = secure_filename(f"ZAL4B_UZUP_{student.nr_albumu}_{int(datetime.now().timestamp())}_{file.filename}")
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    opis = data.get('opis', '')
                    uzupelnienia.append({"path": f"uploads/{filename}", "opis": opis})
                    wniosek.uzupelnienia_paths = json.dumps(uzupelnienia)
                    db.session.commit()
                    return jsonify({'success': True, 'message': 'Dokument uzupełniający dodany'})
            return jsonify({'success': False, 'message': 'Brak pliku do wgrania.'})

        if akcja == 'usun_uzupelnienie':
            idx = int(data.get('index', -1))
            if wniosek.uzupelnienia_paths:
                try:
                    uzupelnienia = json.loads(wniosek.uzupelnienia_paths)
                    if 0 <= idx < len(uzupelnienia):
                        usun_plik = uzupelnienia.pop(idx)
                        try:
                            nazwa_pliku = usun_plik['path'].replace('uploads/', '')
                            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], nazwa_pliku))
                        except Exception:
                            pass
                        wniosek.uzupelnienia_paths = json.dumps(uzupelnienia)
                        db.session.commit()
                        return jsonify({'success': True, 'message': 'Dokument uzupełniający usunięty'})
                except Exception:
                    pass
            return jsonify({'success': False, 'message': 'Błąd usuwania uzupełnienia'})

        if 'specjalnosc' in data:
            student.specjalnosc = data.get('specjalnosc')

        try:
            if data.get('data_od'):
                wniosek.okres_zatrudnienia_od = datetime.strptime(data.get('data_od'), '%Y-%m-%d').date()
            if data.get('data_do'):
                wniosek.okres_zatrudnienia_do = datetime.strptime(data.get('data_do'), '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass
            
        if data.get('stanowisko'):
            wniosek.stanowisko = data.get('stanowisko')
        if data.get('zakres_obowiazkow'):
            wniosek.zakres_obowiazkow = data.get('zakres_obowiazkow')
        if data.get('uzasadnienie'):
            wniosek.uzasadnienie = data.get('uzasadnienie')

        if akcja == 'wyslij':
            safe_nazwisko = current_user.nazwisko.split('(')[0].strip()
            wniosek.podpis_studenta = f"{current_user.imie} {safe_nazwisko}"
            wniosek.data_podpisu = date.today()
            
            dokument.status = 'Submitted'
            praktyka.status = 'SCIEZKA_PRACA'
            
            from models import Uzytkownik, Powiadomienie
            dziekanat_users = Uzytkownik.query.filter(Uzytkownik.rola.in_(['dziekanat', 'dyrektor'])).all()
            for du in dziekanat_users:
                notif = Powiadomienie(
                    uzytkownik_id=du.id,
                    tresc=f"Nowy wniosek (Zał. 4b) od studenta {current_user.imie} {safe_nazwisko}.",
                    link=f"/dziekanat/weryfikuj_zal4b/{praktyka.id}"
                )
                db.session.add(notif)
                
            db.session.commit()
            return jsonify({'success': True, 'message': 'Wniosek został złożony. Uruchomiono ścieżkę zaliczenia na podstawie pracy zawodowej.'})

        if akcja == 'wyslij_uzupelnienia':
            dokument.status = 'Uzupełniono'
            from models import Uzytkownik, Powiadomienie
            safe_nazwisko = current_user.nazwisko.split('(')[0].strip()
            dziekanat_users = Uzytkownik.query.filter(Uzytkownik.rola.in_(['dziekanat', 'dyrektor'])).all()
            for du in dziekanat_users:
                notif = Powiadomienie(
                    uzytkownik_id=du.id,
                    tresc=f"Student {current_user.imie} {safe_nazwisko} dodał uzupełnienia do wniosku (Zał. 4b).",
                    link=f"/dziekanat/weryfikuj_zal4b/{praktyka.id}"
                )
                db.session.add(notif)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Uzupełnienia zostały przesłane.'})
            
        else:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Szkic wniosku został zapisany.'})
            
    student_dict = student.to_dict()
    student_dict['imie'] = student.uzytkownik.imie
    student_dict['nazwisko'] = student.uzytkownik.nazwisko

    zal4a_doc = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4A').first()
    zal4a_decyzja = None
    if zal4a_doc:
        from models import DecyzjaZal4a
        d4a = DecyzjaZal4a.query.filter_by(dokument_id=zal4a_doc.id).first()
        if d4a:
            zal4a_decyzja = d4a.to_dict()

    return jsonify({
        'student': student_dict,
        'dokument': dokument.to_dict() if dokument else None,
        'wniosek': wniosek.to_dict() if wniosek else None,
        'praktyka': praktyka.to_dict(),
        'zal4a_decyzja': zal4a_decyzja
    })

@student_api_bp.route('/edytuj_dane', methods=['POST'])
@login_required
def edytuj_dane():
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403
    
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    return jsonify({'success': False, 'message': 'Nie zaimplementowano.'})

@student_api_bp.route('/porozumienie', methods=['GET'])
@student_api_bp.route('/zal2_program', methods=['GET'])
@student_api_bp.route('/zal3_karta', methods=['GET'])
@student_api_bp.route('/zal4_efekty', methods=['GET'])
@student_api_bp.route('/zal4a_decyzja', methods=['GET'])
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
    
    from models import DecyzjaZal4a
    decyzja = DecyzjaZal4a.query.filter_by(dokument_id=dokument.id).first() if (dokument and typ_zal == 'ZAL4A') else None
    
    protokol = Protokol.query.filter_by(dokument_id=dokument.id).first() if (dokument and typ_zal == 'ZAL8') else None

    student_data = student.to_dict()
    student_data['uzytkownik_imie'] = current_user.imie
    student_data['uzytkownik_nazwisko'] = current_user.nazwisko
    student_data['imie'] = current_user.imie
    student_data['nazwisko'] = current_user.nazwisko
    student_data['imie_i_nazwisko'] = f"{current_user.imie} {current_user.nazwisko}"

    from models import EfektUczenia
    efekty = EfektUczenia.query.filter_by(dokument_id=dokument.id).all() if dokument else []

    return jsonify({
        'student': student_data,
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict() if dokument else None,
        'karta': karta.to_dict() if karta else None,
        'decyzja': decyzja.to_dict() if decyzja else None,
        'protokol': protokol.to_dict() if protokol else None,
        'efekty': [e.to_dict() for e in efekty]
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
@student_api_bp.route('/zal7a_sprawozdanie', methods=['GET', 'POST'])
@login_required
def handle_sprawozdanie_api():
    if current_user.rola != 'student':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        return jsonify({'error': 'Brak praktyki'}), 404

    typ_zal = 'ZAL7' if 'sprawozdanie' in request.path and 'zal7a' not in request.path else 'ZAL7A'

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika=typ_zal).first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika=typ_zal, utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    sprawozdanie_doc = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first()

    if request.method == 'POST':
        data = request.json
        akcja = data.get('akcja', 'wyslij')
        charakterystyka = data.get('charakterystyka', '').strip()
        opis = data.get('opis', '').strip()
        wiedza = data.get('wiedza', '').strip()

        if akcja == 'wyslij':
            if len(charakterystyka) < 150 or len(opis) < 300 or len(wiedza) < 300:
                return jsonify({'success': False, 'message': 'Błąd wysyłania! Niektóre sekcje są zbyt krótkie.'})
            
        if not sprawozdanie_doc:
            sprawozdanie_doc = Sprawozdanie(dokument_id=dokument.id)
            db.session.add(sprawozdanie_doc)

        sprawozdanie_doc.charakterystyka = charakterystyka
        sprawozdanie_doc.opis_prac = opis
        sprawozdanie_doc.wiedza_umiejetnosci = wiedza
        
        if akcja == 'wyslij':
            dokument.status = 'Weryfikacja ZOPZ' if typ_zal == 'ZAL7' else 'Weryfikacja UOPZ'
            db.session.commit()
            
            from models import Powiadomienie
            if typ_zal == 'ZAL7' and praktyka.zaklad and praktyka.zaklad.zopz_id:
                from flask import url_for
                notif = Powiadomienie(
                    uzytkownik_id=praktyka.zaklad.zopz_id,
                    tresc=f"Student {current_user.imie} {current_user.nazwisko} przesłał Sprawozdanie z praktyki (Zał. 7) do oceny.",
                    link=url_for('zopz.teczka', student_id=student.id)
                )
                db.session.add(notif)
            elif typ_zal == 'ZAL7A' and praktyka.uopz_id:
                from flask import url_for
                notif = Powiadomienie(
                    uzytkownik_id=praktyka.uopz_id,
                    tresc=f"Student {current_user.imie} {current_user.nazwisko} przesłał Sprawozdanie z pracy (Zał. 7a) do oceny.",
                    link=url_for('uopz.teczka', student_id=student.id)
                )
                db.session.add(notif)
            db.session.commit()
                
            return jsonify({'success': True, 'message': 'Sprawozdanie przesłane do weryfikacji!'})
        else:
            dokument.status = 'Draft'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Szkic sprawozdania został zapisany.'})

    return jsonify({
        'student': student.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict(),
        'sprawozdanie': sprawozdanie_doc.to_dict() if sprawozdanie_doc else None
    })
