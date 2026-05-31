from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import (
    Praktyka, ZakladPracy, Porozumienie, Student, Dokument, 
    ProgramPraktyki, HarmonogramPraktyki, Zal2aPodpisy, Powiadomienie,
    KartaPraktyki
)
from datetime import date
zopz_api_bp = Blueprint('zopz_api', __name__, url_prefix='/zopz')

@zopz_api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.rola != 'zopz':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    zaklad = ZakladPracy.query.filter_by(zopz_id=current_user.id).first()
    praktyki = []
    
    if zaklad:
        praktyki = Praktyka.query.filter_by(zaklad_id=zaklad.id).all()
        
    def format_praktyka(p):
        student = p.student
        porozumienie = p.porozumienie
        oczekujace = 0
        if porozumienie and porozumienie.status == 'OczekujeZOPZ':
            oczekujace += 1
            
        dokumenty = Dokument.query.filter_by(praktyka_id=p.id).all()
        for doc in dokumenty:
            if doc.typ_zalacznika == 'ZAL2A' and doc.status == 'Sent_to_ZOPZ':
                oczekujace += 1
                
        return {
            'id': p.id,
            'student_id': student.id,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'kierunek': student.kierunek,
            'data_start': str(p.data_start) if p.data_start else '',
            'data_end': str(p.data_end) if p.data_end else '',
            'status': p.status,
            'porozumienie_id': porozumienie.id if porozumienie else None,
            'porozumienie_status': porozumienie.status if porozumienie else None,
            'porozumienie_komentarz': porozumienie.komentarz_zopz if porozumienie else None,
            'oczekujace_akcje': oczekujace
        }

    return jsonify({
        'zaklad': zaklad.to_dict() if zaklad else None,
        'praktyki': [format_praktyka(p) for p in praktyki]
    })

@zopz_api_bp.route('/teczka/<int:student_id>', methods=['GET'])
@login_required
def teczka(student_id):
    if current_user.rola != 'zopz':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    zaklad = ZakladPracy.query.filter_by(zopz_id=current_user.id).first()
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka or not zaklad or praktyka.zaklad_id != zaklad.id:
        return jsonify({'error': 'Brak dostępu do praktyki tego studenta'}), 404

    dokumenty = Dokument.query.filter_by(praktyka_id=praktyka.id).all()
    dok_dict = {d.typ_zalacznika: d.to_dict() for d in dokumenty}

    return jsonify({
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'praktyka': praktyka.to_dict(),
        'zaklad_nazwa': zaklad.nazwa,
        'dokumenty': dok_dict,
        'porozumienie': praktyka.porozumienie.to_dict() if praktyka.porozumienie else None
    })

@zopz_api_bp.route('/zaklad_pracy', methods=['PUT'])
@login_required
def update_zaklad_pracy():    
    if current_user.rola != 'zopz': return jsonify({'error': 'Odmowa dostępu'}), 403
        
    zaklad = ZakladPracy.query.filter_by(zopz_id=current_user.id).first()
    if not zaklad:
        return jsonify({'error': 'Nie znaleziono zakładu pracy przypisanego do Twojego konta.'}), 404
        
    data = request.json
    
    def is_valid_nip(nip_str):
        nip_str = nip_str.replace('-', '').replace(' ', '')
        if len(nip_str) != 10 or not nip_str.isdigit():
            return False
        weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
        checksum = sum(int(nip_str[i]) * weights[i] for i in range(9))
        return (checksum % 11) == int(nip_str[9])

    if 'nip' in data:
        nip_val = data['nip'].replace('-', '').replace(' ', '')
        if not is_valid_nip(nip_val):
            return jsonify({'error': 'Podany NIP jest nieprawidłowy.'}), 400
        zaklad.nip = nip_val

    if 'ulica' in data: zaklad.ulica = data['ulica']
    if 'nr_budynku' in data: zaklad.nr_budynku = data['nr_budynku']
    if 'nr_lokalu' in data: zaklad.nr_lokalu = data['nr_lokalu']
    if 'kod_pocztowy' in data: zaklad.kod_pocztowy = data['kod_pocztowy']
    if 'miasto' in data: zaklad.miasto = data['miasto']
    if 'telefon' in data: zaklad.telefon = data['telefon']
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Dane zakładu zostały zaktualizowane.'})

@zopz_api_bp.route('/weryfikuj_porozumienie/<int:porozumienie_id>', methods=['POST'])
@login_required
def weryfikuj_porozumienie(porozumienie_id):    
    if current_user.rola != 'zopz': return jsonify({'error': 'Odmowa dostępu'}), 403
        
    porozumienie = Porozumienie.query.get_or_404(porozumienie_id)
    if porozumienie.zaklad.zopz_id != current_user.id:
        return jsonify({'error': 'Odmowa dostępu do tego porozumienia'}), 403
        
    data = request.json
    akcja = data.get('akcja')
    
    if akcja == 'zatwierdz':
        porozumienie.status = 'Podpisane'
        porozumienie.komentarz_zopz = None
        db.session.commit()
        return jsonify({'success': True, 'message': 'Porozumienie zostało podpisane i zawarte.'})
    elif akcja == 'uwagi':
        komentarz = data.get('komentarz_zopz')
        if not komentarz:
            return jsonify({'error': 'Komentarz jest wymagany przy zgłaszaniu uwag.'}), 400
        porozumienie.status = 'UwagiZOPZ'
        porozumienie.komentarz_zopz = komentarz
        message = 'Uwagi zostały przesłane do Dziekanatu.'
        db.session.commit()
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': 'Nieznana akcja.'}), 400
        
    db.session.commit()
    return jsonify({'success': True, 'message': message})

@zopz_api_bp.route('/zal2a_harmonogram/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal2a_harmonogram(student_id):    
    if current_user.rola != 'zopz': return jsonify({'error': 'Odmowa dostępu'}), 403

    zaklad = ZakladPracy.query.filter_by(zopz_id=current_user.id).first()
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka or not zaklad or praktyka.zaklad_id != zaklad.id:
        return jsonify({'error': 'Brak dostępu do praktyki tego studenta'}), 404

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
        if akcja in ['zapisz', 'wyslij_do_uopz']:
            ProgramPraktyki.query.filter_by(dokument_id=dokument.id).delete()
            programy_data = data.get('programy', {})
            for kod, prace in programy_data.items():
                if prace:
                    nowy_program = ProgramPraktyki(dokument_id=dokument.id, kod_efektu=kod, dzial_prace=prace)
                    db.session.add(nowy_program)

            HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).delete()
            harmonogram_data = data.get('harmonogram', [])
            for i, p in enumerate(harmonogram_data):
                if p['dzial'] and p['dni']:
                    nowa_pozycja = HarmonogramPraktyki(
                        dokument_id=dokument.id, lp=i + 1,
                        dzial_komorka=p['dzial'], planowana_liczba_dni=int(p['dni'])
                    )
                    db.session.add(nowa_pozycja)
            
            dokument.uwagi_opiekuna = ""
            
            if akcja == 'wyslij_do_uopz':
                dokument.status = 'Sent_back_to_UOPZ'
                if data.get('zloz_podpis'):
                    tytul = f"{current_user.tytul_naukowy} " if current_user.tytul_naukowy else ""
                    podpisy.podpis_zopz = f"{tytul}{current_user.imie} {current_user.nazwisko}"
                    podpisy.data_zopz = date.today()
                message = 'Harmonogram zatwierdzono, podpisano i odesłano do Opiekuna Uczelnianego!'
                notif = Powiadomienie(
                    uzytkownik_id=praktyka.uopz_id,
                    tresc=f"Zakład odesłał uzupełniony Załącznik 2a dla {student.uzytkownik.imie} {student.uzytkownik.nazwisko}.",
                    link=f"/uopz/zal2a_harmonogram/{student.id}"
                )
                db.session.add(notif)
            else:
                message = 'Harmonogram został zapisany jako szkic.'
                
            db.session.commit()
            
            return jsonify({'success': True, 'message': message})

    pozycje_harmonogramu = HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).order_by(HarmonogramPraktyki.lp).all()
    zapisane_programy = {p.kod_efektu: p.dzial_prace for p in ProgramPraktyki.query.filter_by(dokument_id=dokument.id).all()}

    return jsonify({
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict(),
        'podpisy': podpisy.to_dict() if podpisy else None,
        'pozycje': [p.to_dict() for p in pozycje_harmonogramu],
        'zapisane_programy': zapisane_programy
    })

@zopz_api_bp.route('/zal3_karta/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal3_karta(student_id):
    if current_user.rola != 'zopz': return jsonify({'error': 'Odmowa dostępu'}), 403

    zaklad = ZakladPracy.query.filter_by(zopz_id=current_user.id).first()
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka or not zaklad or praktyka.zaklad_id != zaklad.id:
        return jsonify({'error': 'Brak dostępu do praktyki tego studenta'}), 404

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL3').first()
    if not dokument:
        return jsonify({'error': 'Uczelnia nie utworzyła jeszcze karty praktyki (Brak Zał. 3).'}), 404
        
    karta = KartaPraktyki.query.filter_by(dokument_id=dokument.id).first()
    if not karta:
        return jsonify({'error': 'Brak wpisów w karcie praktyki.'}), 404

    if request.method == 'POST':
        data = request.json
        akcja = data.get('akcja')
        
        if akcja == 'potwierdz_zgloszenie':
            if data.get('zloz_podpis'):
                tytul = f"{current_user.tytul_naukowy} " if current_user.tytul_naukowy else ""
                karta.podpis_zgloszenie = f"{tytul}{current_user.imie} {current_user.nazwisko}"
            karta.data_zgloszenia = date.today()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Potwierdzono zgłoszenie studenta.'})
            
        elif akcja == 'potwierdz_bhp':
            if data.get('zloz_podpis'):
                tytul = f"{current_user.tytul_naukowy} " if current_user.tytul_naukowy else ""
                karta.podpis_bhp = f"{tytul}{current_user.imie} {current_user.nazwisko}"
            karta.data_bhp = date.today()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Potwierdzono szkolenie BHP.'})
            
        elif akcja in ['zapisz_ocene', 'wyslij_do_uczelni']:
            try:
                if 'zaswiadczenie_uwagi' in data: karta.zaswiadczenie_uwagi = data.get('zaswiadczenie_uwagi')
                if data.get('ocena_zopz_param'): karta.ocena_zopz_param = float(data.get('ocena_zopz_param'))
                if 'ocena_zopz_opis' in data: karta.ocena_zopz_opis = data.get('ocena_zopz_opis')
                
                if akcja == 'wyslij_do_uczelni':
                    dokument.status = 'Weryfikacja_Uczelni'
                    tytul = f"{current_user.tytul_naukowy} " if current_user.tytul_naukowy else ""
                    karta.podpis_zaswiadczenie = f"{tytul}{current_user.imie} {current_user.nazwisko}"
                    karta.zaswiadczenie_data = date.today()
                    karta.podpis_zopz = f"{tytul}{current_user.imie} {current_user.nazwisko}"
                    karta.ocena_zopz_data = date.today()
                    
                    notif = Powiadomienie(
                        uzytkownik_id=praktyka.uopz_id,
                        tresc=f"Zakład pracy (ZOPZ) przesłał kartę praktyki oraz ocenił studenta {student.uzytkownik.imie} {student.uzytkownik.nazwisko}.",
                        link=f"/uopz/zal3_karta/{student.id}"
                    )
                    db.session.add(notif)
                    message = 'Karta praktyki i oceny zostały przesłane do uczelni.'
                else:
                    message = 'Oceny i uwagi zapisane jako szkic.'
                    
                db.session.commit()
                return jsonify({'success': True, 'message': message})
            except ValueError:
                return jsonify({'success': False, 'message': 'Wprowadzono niepoprawny format oceny.'})

    return jsonify({
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict(),
        'karta': karta.to_dict(),
        'zopz': current_user.to_dict()
    })

@zopz_api_bp.route('/zal3_lista', methods=['GET'])
@login_required
def zal3_lista():
    if current_user.rola != 'zopz':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    zaklad = ZakladPracy.query.filter_by(zopz_id=current_user.id).first()
    if not zaklad:
        return jsonify({'do_akcji': [], 'w_toku': [], 'zatwierdzone': []})
        
    praktyki = Praktyka.query.filter_by(zaklad_id=zaklad.id).all()
    praktyka_ids = [p.id for p in praktyki]
    
    dokumenty = Dokument.query.filter(Dokument.praktyka_id.in_(praktyka_ids), Dokument.typ_zalacznika == 'ZAL3').all()
    
    def format_dokument(doc):
        student = doc.praktyka.student
        return {
            'id': doc.id,
            'praktyka_id': doc.praktyka_id,
            'student_id': student.id,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'status': doc.status,
            'data_zlozenia': doc.updated_at.strftime('%Y-%m-%d %H:%M') if doc.updated_at else ''
        }

    do_akcji = []
    w_toku = []
    zatwierdzone = []

    for d in dokumenty:
        fd = format_dokument(d)
        if d.status == 'Weryfikacja_ZOPZ' or d.status == 'Skierowanie_Wydane':
            do_akcji.append(fd)
        elif d.status in ['Draft_UOPZ', 'Weryfikacja_Uczelni']:
            w_toku.append(fd)
        elif d.status == 'Zatwierdzone':
            zatwierdzone.append(fd)
        else:
            w_toku.append(fd)

    return jsonify({
        'do_akcji': do_akcji,
        'w_toku': w_toku,
        'zatwierdzone': zatwierdzone
    })

