from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import Student, Praktyka, Dokument, WpisDziennika
from datetime import datetime

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
    if praktyka:
        dokument_zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
        from models import Porozumienie
        porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
        
        show_zal9_accepted = True
        
        if porozumienie:
            show_zal9_accepted = False
            if porozumienie.status == 'OczekujeZOPZ':
                powiadomienia.append({
                    'typ': 'info',
                    'tytul': 'Porozumienie wysłane do ZOPZ',
                    'tresc': 'Twoje porozumienie zostało wygenerowane i oczekuje na zatwierdzenie przez Zakład Pracy.'
                })
            elif porozumienie.status == 'UwagiZOPZ':
                powiadomienia.append({
                    'typ': 'warning',
                    'tytul': 'Porozumienie odesłane z uwagami',
                    'tresc': 'Zakład Pracy zgłosił uwagi do porozumienia. Skontaktuj się z Dziekanatem.'
                })
            elif porozumienie.status in ['ZatwierdzoneZOPZ', 'Podpisane']:
                powiadomienia.append({
                    'typ': 'success',
                    'tytul': 'Porozumienie zaakceptowane',
                    'tresc': 'Twoje porozumienie zostało zaakceptowane.'
                })
                
        if dokument_zal9:
            if dokument_zal9.status == 'Draft' and dokument_zal9.komentarz:
                powiadomienia.append({
                    'typ': 'danger',
                    'tytul': 'Oświadczenie (Zał. 9) zostało odrzucone',
                    'tresc': f"Dziekanat odrzucił Twoje oświadczenie z komentarzem: <strong>{dokument_zal9.komentarz}</strong>. Proszę wejść w oświadczenie i poprawić błędy."
                })
            elif dokument_zal9.status in ['AwaitingAccount', 'AccountCreated', 'Approved'] and show_zal9_accepted:
                powiadomienia.append({
                    'typ': 'success',
                    'tytul': 'Oświadczenie (Zał. 9) zaakceptowane',
                    'tresc': 'Twoje oświadczenie zostało zaakceptowane. Jeśli wymagało utworzenia konta dla opiekuna z zakładu pracy, zostanie to wkrótce zrealizowane.'
                })
    
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
        # Accept JSON payload instead of form data
        data = request.json
        if not data or 'wpisy' not in data:
            return jsonify({'error': 'Nieprawidłowe dane'}), 400

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
                if istniejacy.potwierdzony_zopz:
                    continue # ignorowanie zmiany w zatwierdzonych
                istniejacy.data_wpisu = data_obj
                istniejacy.opis_prac = opis
                istniejacy.nr_efektu = efekt
                istniejacy.numer_dnia = i + 1
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

    # GET Request
    wpisy = WpisDziennika.query.filter_by(dokument_id=dokument.id).order_by(WpisDziennika.numer_dnia).all()

    praktyka_info = {
        'zaklad_nazwa': praktyka.zaklad.nazwa if praktyka.zaklad else 'Brak przypisanej firmy',
        'data_start': praktyka.data_start.isoformat() if praktyka.data_start else '',
        'data_end': praktyka.data_end.isoformat() if praktyka.data_end else ''
    }

    today_date = datetime.now().date().isoformat()
    max_date = today_date
    if praktyka.data_end:
        praktyka_end_str = praktyka.data_end.isoformat()
        max_date = min(today_date, praktyka_end_str)

    efekty_lista = [
        {"kod": "EK_01", "opis": "Rozumienie zasad działania systemów i aplikacji"},
        {"kod": "EK_02", "opis": "Umiejętność programowania i testowania"},
        {"kod": "EK_03", "opis": "Znajomość relacyjnych baz danych"},
        {"kod": "EK_04", "opis": "Praca w zespole i komunikacja"},
        {"kod": "EK_05", "opis": "Projektowanie interfejsów użytkownika"}
    ]

    return jsonify({
        'praktyka': praktyka_info,
        'wpisy': [w.to_dict() for w in wpisy],
        'today_date': today_date,
        'max_date': max_date,
        'efekty_lista': efekty_lista
    })

@student_api_bp.route('/zal9_oswiadczenie', methods=['GET', 'POST'])
@login_required
def zal9_oswiadczenie():
    from flask import current_app
    from models import Oswiadczenie
    import os
    from werkzeug.utils import secure_filename
    
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
            db.session.commit()
            return jsonify({'success': True, 'message': 'Oświadczenie zostało złożone.'})
        else:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Szkic oświadczenia został zapisany.'})
            
    # GET
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
    from models import WniosekZaliczeniePraktyki
    
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
@student_api_bp.route('/zal8_protokol', methods=['GET'])
@login_required
def get_dokumenty_readonly():
    from flask import request
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
    
    # We might need specific models for specific documents if they have them, but mostly they just use 'dokument' and 'praktyka'
    from models import KartaPraktyk, DecyzjaDziekana, ProtokolZaliczenia
    karta = KartaPraktyk.query.filter_by(dokument_id=dokument.id).first() if (dokument and typ_zal == 'ZAL3') else None
    decyzja = DecyzjaDziekana.query.filter_by(dokument_id=dokument.id).first() if (dokument and typ_zal == 'ZAL4A') else None
    protokol = ProtokolZaliczenia.query.filter_by(dokument_id=dokument.id).first() if (dokument and typ_zal == 'ZAL8') else None

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
    from flask import request
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

    if request.method == 'POST':
        data = request.json
        akcja = data.get('akcja')
        komentarz = data.get('komentarz')

        if akcja == 'akceptuj':
            dokument.status = 'Approved'
            dokument.uwagi_opiekuna = ""
            if praktyka.status in ['OCZEKUJE_NA_ZAL9', 'ZAL9_PRZYJETY', 'POROZUMIENIE_PODPISANE']:
                praktyka.status = 'PROGRAM_UZGODNIONY'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Zatwierdziłeś harmonogram praktyki!'})

        elif akcja == 'odrzuc':
            dokument.status = 'Rejected'
            dokument.uwagi_opiekuna = f"UWAGA STUDENTA: {komentarz}" if komentarz else "Student odrzucił harmonogram bez komentarza."
            db.session.commit()
            return jsonify({'success': True, 'message': 'Odrzuciłeś harmonogram. UOPZ został o tym poinformowany.'})
            
    from models import HarmonogramPraktyki
    pozycje = HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).order_by(HarmonogramPraktyki.lp).all()
    suma_dni = sum(p.planowana_liczba_dni for p in pozycje)
    
    return jsonify({
        'student': student.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict(),
        'pozycje': [p.to_dict() for p in pozycje],
        'suma_dni': suma_dni
    })

@student_api_bp.route('/zal7a_sprawozdanie', methods=['GET', 'POST'])
@login_required
def zal7a_sprawozdanie_api():
    from flask import request
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

    from models import Sprawozdanie
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
