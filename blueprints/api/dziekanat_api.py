from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import Dokument, Oswiadczenie, Praktyka, Porozumienie, ProgramPraktyki, HarmonogramPraktyki, Zal2aPodpisy, Powiadomienie, Uzytkownik, KartaPraktyki
from datetime import date, datetime

dziekanat_api_bp = Blueprint('dziekanat_api', __name__, url_prefix='/dziekanat')

@dziekanat_api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    zal9_count = db.session.query(Dokument).filter_by(status='Submitted', typ_zalacznika='ZAL9').count()
    
    porozumienia_count = 0
    praktyki = db.session.query(Praktyka).filter(
        Praktyka.status != 'OCZEKUJE_NA_ZAL9', 
        Praktyka.status != 'BRAK_ZGŁOSZENIA',
        Praktyka.status != 'SCIEZKA_PRACA',
        Praktyka.status != 'ZAL4B_ZATWIERDZONE'
    ).all()
    for p in praktyki:
        por = p.porozumienie
        if not por:
            porozumienia_count += 1
        elif por.status in ['Draft', 'ZaakceptowaneDyrektor', 'UwagiZOPZ', 'ZatwierdzoneZOPZ', 'OczekujeZOPZ']:
            porozumienia_count += 1
            
    zal2a_count = db.session.query(Dokument).filter_by(status='Submitted', typ_zalacznika='ZAL2A').count()
    zal4b_count = db.session.query(Dokument).filter_by(status='Submitted', typ_zalacznika='ZAL4B').count()
    
    praktyki_4b = db.session.query(Praktyka).filter(Praktyka.status == 'ZAL4B_ZATWIERDZONE').all()
    praktyki_4a = db.session.query(Praktyka).join(Dokument).filter(Dokument.typ_zalacznika == 'ZAL4A').all()
    wszystkie_4a = set(praktyki_4b + praktyki_4a)
    zal4a_count = 0
    for p in wszystkie_4a:
        doc = Dokument.query.filter_by(praktyka_id=p.id, typ_zalacznika='ZAL4A').first()
        if not doc or doc.status != 'Zatwierdzony':
            zal4a_count += 1
            
    zal7_count = db.session.query(Dokument).filter(
        Dokument.typ_zalacznika.in_(['ZAL7', 'ZAL7A']),
        Dokument.status.in_(['Weryfikacja UOPZ', 'Weryfikacja Dyrektor'])
    ).count()
            
    return jsonify({
        'zal9_count': zal9_count,
        'porozumienia_count': porozumienia_count,
        'zal2a_count': zal2a_count,
        'zal4b_count': zal4b_count,
        'zal4a_count': zal4a_count,
        'zal7_count': zal7_count
    })

@dziekanat_api_bp.route('/zal9', methods=['GET'])
@login_required
def zal9_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    oswiadczenia_do_weryfikacji = db.session.query(Oswiadczenie)\
        .join(Dokument)\
        .filter(Dokument.status == 'Submitted', Dokument.typ_zalacznika == 'ZAL9').all()
        
    oswiadczenia_zatwierdzone = db.session.query(Oswiadczenie)\
        .join(Dokument)\
        .filter(Dokument.status.in_(['Approved', 'AwaitingAccount', 'AccountCreated']), Dokument.typ_zalacznika == 'ZAL9').order_by(Dokument.updated_at.desc()).all()

    oswiadczenia_odrzucone = db.session.query(Oswiadczenie)\
        .join(Dokument)\
        .filter(Dokument.status == 'Draft', Dokument.komentarz != None, Dokument.typ_zalacznika == 'ZAL9').order_by(Dokument.updated_at.desc()).all()

    def format_oswiadczenie(osw):
        doc = osw.dokument
        student = doc.praktyka.student
        return {
            'id': osw.id,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'status': doc.status,
            'data_zlozenia': doc.updated_at.strftime('%Y-%m-%d %H:%M') if doc.updated_at else '',
            'komentarz': doc.komentarz
        }

    return jsonify({
        'do_weryfikacji': [format_oswiadczenie(o) for o in oswiadczenia_do_weryfikacji],
        'zatwierdzone': [format_oswiadczenie(o) for o in oswiadczenia_zatwierdzone],
        'odrzucone': [format_oswiadczenie(o) for o in oswiadczenia_odrzucone]
    })

@dziekanat_api_bp.route('/porozumienia', methods=['GET'])
@login_required
def porozumienia_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    praktyki = db.session.query(Praktyka)\
        .filter(Praktyka.status != 'OCZEKUJE_NA_ZAL9', Praktyka.status != 'BRAK_ZGŁOSZENIA').all()
        
    def format_praktyka_porozumienie(p):
        student = p.student
        por = p.porozumienie
        zal9 = db.session.query(Dokument).filter_by(praktyka_id=p.id, typ_zalacznika='ZAL9').first()
        data_zl = zal9.updated_at.strftime('%Y-%m-%d %H:%M') if zal9 and zal9.updated_at else '---'
        return {
            'id': por.id if por else p.id,
            'praktyka_id': p.id,
            'porozumienie_id': por.id if por else None,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'status_porozumienia': por.status if por else 'Brak / Szkic',
            'komentarz_zopz': por.komentarz_zopz if por else None,
            'data_zlozenia': data_zl
        }

    return jsonify({
        'porozumienia': [format_praktyka_porozumienie(p) for p in praktyki]
    })

@dziekanat_api_bp.route('/akceptuj_dyrektor/<int:praktyka_id>', methods=['POST'])
@login_required
def akceptuj_dyrektor(praktyka_id):
    if current_user.rola != 'dyrektor':
        return jsonify({'error': 'Odmowa dostępu. Tylko Dyrektor może zaakceptować porozumienie.'}), 403
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    if not praktyka.zaklad_id:
        return jsonify({'error': 'Praktyka nie ma przypisanego zakładu pracy (ZAL9 nie został w pełni zatwierdzony/nie utworzono konta).'}), 400
        
    porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
    if not porozumienie:
        porozumienie = Porozumienie(praktyka_id=praktyka.id, zaklad_id=praktyka.zaklad_id, status='ZaakceptowaneDyrektor')
        db.session.add(porozumienie)
    else:
        porozumienie.status = 'ZaakceptowaneDyrektor'
        
    tytul = f"{current_user.tytul_naukowy} " if current_user.tytul_naukowy else ""
    porozumienie.podpisal_dziekanat = f"{tytul}{current_user.imie} {current_user.nazwisko}"
    porozumienie.data_podpisania = date.today()
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Porozumienie zaakceptowane i podpisane przez Dyrektora.'})

@dziekanat_api_bp.route('/przekaz_dyrektorowi/<int:praktyka_id>', methods=['POST'])
@login_required
def przekaz_dyrektorowi(praktyka_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
    
    if not porozumienie or porozumienie.status != 'UwagiZOPZ':
        return jsonify({'error': 'Nie można przekazać do Dyrektora w obecnym statusie.'}), 400
        
    porozumienie.status = 'Draft'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Dokument przekazany do ponownej akceptacji Dyrektora.'})

@dziekanat_api_bp.route('/wyslij_porozumienie/<int:praktyka_id>', methods=['POST'])
@login_required
def wyslij_porozumienie(praktyka_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
    
    if not porozumienie or porozumienie.status != 'ZaakceptowaneDyrektor':
        return jsonify({'error': 'Porozumienie musi zostać najpierw zaakceptowane przez Dyrektora.'}), 400
        
    porozumienie.status = 'OczekujeZOPZ'
    porozumienie.komentarz_zopz = None # reset komentarza przy ponownym wysłaniu
        
    db.session.commit()
    return jsonify({'success': True, 'message': 'Porozumienie wysłane do ZOPZ.'})

@dziekanat_api_bp.route('/podpisz_porozumienie/<int:id>', methods=['POST'])
@login_required
def podpisz_porozumienie(id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    porozumienie = Porozumienie.query.get_or_404(id)
    if porozumienie.status != 'ZatwierdzoneZOPZ':
        return jsonify({'error': 'Porozumienie nie zostało jeszcze zatwierdzone przez Zakład Pracy.'}), 400
        
    porozumienie.status = 'Podpisane'
    porozumienie.data_podpisania = date.today()
    porozumienie.podpisal_dziekanat = f"{current_user.imie} {current_user.nazwisko}"
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Porozumienie zostało ostatecznie zatwierdzone i podpisane.'})

@dziekanat_api_bp.route('/weryfikuj_zal9/<int:id>', methods=['GET', 'POST'])
@login_required
def weryfikuj_zal9(id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    oswiadczenie = Oswiadczenie.query.get_or_404(id)
    dokument = oswiadczenie.dokument
    praktyka = dokument.praktyka
    student = praktyka.student
    
    if request.method == 'POST':
        data = request.json
        akcja = data.get('akcja')
        
        if akcja == 'zatwierdz':
            dokument.status = 'AwaitingAccount'
            dokument.komentarz = None
            praktyka.status = 'ZAL9_ZATWIERDZONE'
            
            notif_s = Powiadomienie(
                uzytkownik_id=student.uzytkownik.id,
                tresc="Dziekanat ZATWIERDZIŁ Twoje Oświadczenie (Zał. 9). Trwa proces zakładania konta dla Zakładu Pracy.",
                link="/student/dashboard"
            )
            db.session.add(notif_s)
            
            from models import dodaj_log
            dodaj_log(current_user.id, f"Zatwierdzono Oświadczenie (Zał. 9) dla {student.uzytkownik.imie} {student.uzytkownik.nazwisko}")
            
            db.session.commit()
            return jsonify({'success': True, 'message': f'Oświadczenie studenta {student.uzytkownik.nazwisko} zostało zatwierdzone. Dane przekazano do IT.'})
            
        elif akcja == 'odrzuc':
            dokument.status = 'Draft'
            komentarz = data.get('komentarz_dziekanatu')
            dokument.komentarz = komentarz if komentarz else "Dokument został odrzucony do poprawy. Prosimy o wprowadzenie zmian i ponowne przesłanie."
            praktyka.status = 'OCZEKUJE_NA_ZAL9'
            
            notif_s = Powiadomienie(
                uzytkownik_id=student.uzytkownik.id,
                tresc="Dziekanat ZWRÓCIŁ DO POPRAWY Twoje Oświadczenie (Zał. 9). Sprawdź uwagi na dashboardzie.",
                link="/student/zal9_oswiadczenie"
            )
            db.session.add(notif_s)
            
            from models import dodaj_log
            dodaj_log(current_user.id, f"Odrzucono Oświadczenie (Zał. 9) dla {student.uzytkownik.imie} {student.uzytkownik.nazwisko}")
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Oświadczenie odrzucone do poprawy przez studenta.'})
            
        elif akcja == 'przekaz_do_it':
            dokument.status = 'AwaitingAccount'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Dane przekazane do Administratora IT w celu utworzenia konta.'})
        else:
            return jsonify({'error': 'Nieprawidłowa akcja.'}), 400
        
    porozumienie = praktyka.porozumienie
    porozumienie_data = None
    if porozumienie:
        porozumienie_data = {
            'id': porozumienie.id,
            'status': porozumienie.status,
            'komentarz_zopz': porozumienie.komentarz_zopz
        }

    return jsonify({
        'oswiadczenie': oswiadczenie.to_dict(),
        'dokument': dokument.to_dict(),
        'praktyka': praktyka.to_dict(),
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'porozumienie': porozumienie_data
    })

@dziekanat_api_bp.route('/edytuj_zaklad/<int:praktyka_id>', methods=['POST'])
@login_required
def edytuj_zaklad(praktyka_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    zaklad = praktyka.zaklad
    data = request.json
    
    if zaklad:
        zaklad.nazwa = data.get('nazwa', zaklad.nazwa)
        zaklad.nip = data.get('nip', zaklad.nip)
        zaklad.kod_pocztowy = data.get('kod_pocztowy', zaklad.kod_pocztowy)
        zaklad.miasto = data.get('miasto', zaklad.miasto)
        zaklad.ulica = data.get('ulica', zaklad.ulica)
        zaklad.nr_budynku = data.get('nr_budynku', zaklad.nr_budynku)
        zaklad.nr_lokalu = data.get('nr_lokalu', zaklad.nr_lokalu)
    
    dokument_zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
    if dokument_zal9:
        oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument_zal9.id).first()
        if oswiadczenie:
            oswiadczenie.osoba_upowazniona_imie = data.get('osoba_upowazniona_imie', oswiadczenie.osoba_upowazniona_imie)
            oswiadczenie.osoba_upowazniona_nazwisko = data.get('osoba_upowazniona_nazwisko', oswiadczenie.osoba_upowazniona_nazwisko)
            oswiadczenie.osoba_upowazniona_stanowisko = data.get('osoba_upowazniona_stanowisko', oswiadczenie.osoba_upowazniona_stanowisko)
            
    student = praktyka.student
    if student and student.uzytkownik:
        student.uzytkownik.imie = data.get('student_imie', student.uzytkownik.imie)
        nowe_nazwisko_base = data.get('student_nazwisko')
        if nowe_nazwisko_base:
            if '(' in student.uzytkownik.nazwisko:
                dodatek = student.uzytkownik.nazwisko[student.uzytkownik.nazwisko.find('('):]
                student.uzytkownik.nazwisko = f"{nowe_nazwisko_base} {dodatek}"
            else:
                student.uzytkownik.nazwisko = nowe_nazwisko_base

    if data.get('praktyka_data_start'):
        try:
            praktyka.data_start = datetime.strptime(data.get('praktyka_data_start'), '%Y-%m-%d').date()
        except ValueError:
            pass
            
    if data.get('praktyka_data_end'):
        try:
            praktyka.data_end = datetime.strptime(data.get('praktyka_data_end'), '%Y-%m-%d').date()
        except ValueError:
            pass
            
    if data.get('praktyka_liczba_godzin'):
        try:
            praktyka.liczba_godzin = int(data.get('praktyka_liczba_godzin'))
        except ValueError:
            pass
            
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Zaktualizowano dane porozumienia.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@dziekanat_api_bp.route('/zal2a', methods=['GET'])
@login_required
def zal2a_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    dokumenty_do_weryfikacji = db.session.query(Dokument)\
        .filter(Dokument.status == 'Submitted', Dokument.typ_zalacznika == 'ZAL2A').all()
        
    dokumenty_zatwierdzone = db.session.query(Dokument)\
        .filter(Dokument.status == 'Approved', Dokument.typ_zalacznika == 'ZAL2A').order_by(Dokument.updated_at.desc()).all()

    def format_dokument(doc):
        student = doc.praktyka.student
        return {
            'id': doc.id,
            'praktyka_id': doc.praktyka_id,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'status': doc.status,
            'data_zlozenia': doc.updated_at.strftime('%Y-%m-%d %H:%M') if doc.updated_at else ''
        }

    return jsonify({
        'do_weryfikacji': [format_dokument(d) for d in dokumenty_do_weryfikacji],
        'zatwierdzone': [format_dokument(d) for d in dokumenty_zatwierdzone]
    })

@dziekanat_api_bp.route('/weryfikuj_zal2a/<int:praktyka_id>', methods=['GET', 'POST'])
@login_required
def weryfikuj_zal2a(praktyka_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    student = praktyka.student
    
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL2A').first()
    if not dokument:
        return jsonify({'error': 'Brak dokumentu ZAL2A'}), 404

    if request.method == 'POST':
        data = request.json
        akcja = data.get('akcja')
        
        if akcja == 'zatwierdz':
            dokument.status = 'Approved'
            praktyka.status = 'PROGRAM_ZATWIERDZONY'
            
            notif_u = Powiadomienie(
                uzytkownik_id=praktyka.uopz_id,
                tresc=f"Dziekanat ostatecznie ZATWIERDZIŁ Załącznik 2a dla {student.uzytkownik.imie} {student.uzytkownik.nazwisko}.",
                link=f"/uopz/zal2a_harmonogram/{student.id}"
            )
            notif_s = Powiadomienie(
                uzytkownik_id=student.uzytkownik.id,
                tresc="Dziekanat ostatecznie ZATWIERDZIŁ Twój Załącznik 2a.",
                link=f"/student/zal2a_harmonogram"
            )
            db.session.add_all([notif_u, notif_s])
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Harmonogram i Program (ZAL2A) został ostatecznie zatwierdzony!'})
            
        elif akcja == 'odrzuc':
            dokument.status = 'Draft'
            komentarz = data.get('komentarz_dziekanatu')
            dokument.komentarz = komentarz if komentarz else "Odrzucono do poprawy."
            
            notif_u = Powiadomienie(
                uzytkownik_id=praktyka.uopz_id,
                tresc=f"Dziekanat ODRZUCIŁ Załącznik 2a dla {student.uzytkownik.imie} {student.uzytkownik.nazwisko}.",
                link=f"/uopz/zal2a_harmonogram/{student.id}"
            )
            db.session.add(notif_u)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'ZAL2A odrzucony do poprawy.'})

    podpisy = Zal2aPodpisy.query.filter_by(dokument_id=dokument.id).first()
    pozycje = HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).order_by(HarmonogramPraktyki.lp).all()
    suma_dni = sum(p.planowana_liczba_dni for p in pozycje)
    zapisane_programy = {p.kod_efektu: p.dzial_prace for p in ProgramPraktyki.query.filter_by(dokument_id=dokument.id).all()}

    return jsonify({
        'dokument': dokument.to_dict(),
        'praktyka': praktyka.to_dict(),
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'podpisy': podpisy.to_dict() if podpisy else None,
        'pozycje': [p.to_dict() for p in pozycje],
        'zapisane_programy': zapisane_programy,
        'suma_dni': suma_dni
    })

@dziekanat_api_bp.route('/przypisz_uopz', methods=['GET', 'POST'])
@login_required
def przypisz_uopz():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403

    if request.method == 'POST':
        data = request.json
        praktyka_id = data.get('praktyka_id')
        uopz_id = data.get('uopz_id')
        
        if not praktyka_id:
            return jsonify({'error': 'Brak ID praktyki'}), 400
            
        praktyka = Praktyka.query.get_or_404(praktyka_id)
        
        if uopz_id:
            uopz = Uzytkownik.query.filter_by(id=uopz_id, rola='uopz').first()
            if not uopz:
                return jsonify({'error': 'Nieprawidłowe ID UOPZ'}), 400
            praktyka.uopz_id = uopz.id
        else:
            praktyka.uopz_id = None
            
        db.session.commit()
        return jsonify({'success': True, 'message': 'Opiekun Uczelniany został pomyślnie przypisany.'})

    uopz_list = Uzytkownik.query.filter_by(rola='uopz').all()
    praktyki = Praktyka.query.all()
    
    def format_praktyka(p):
        student = p.student
        return {
            'id': p.id,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'kierunek': student.kierunek,
            'uopz_id': p.uopz_id,
            'status': p.status
        }
        
    return jsonify({
        'uopz_list': [{'id': u.id, 'imie': u.imie, 'nazwisko': u.nazwisko, 'tytul': u.tytul_naukowy} for u in uopz_list],
        'praktyki': [format_praktyka(p) for p in praktyki if p.student]
    })

@dziekanat_api_bp.route('/zal3', methods=['GET'])
@login_required
def zal3_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    dokumenty_do_weryfikacji = db.session.query(Dokument)\
        .filter(Dokument.status == 'Weryfikacja_Uczelni', Dokument.typ_zalacznika == 'ZAL3').all()
        
    dokumenty_zatwierdzone = db.session.query(Dokument)\
        .filter(Dokument.status == 'Zatwierdzone', Dokument.typ_zalacznika == 'ZAL3').order_by(Dokument.updated_at.desc()).all()

    def format_dokument(doc):
        student = doc.praktyka.student
        return {
            'id': doc.id,
            'praktyka_id': doc.praktyka_id,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'status': doc.status,
            'data_zlozenia': doc.updated_at.strftime('%Y-%m-%d %H:%M') if doc.updated_at else ''
        }

    return jsonify({
        'do_weryfikacji': [format_dokument(d) for d in dokumenty_do_weryfikacji],
        'zatwierdzone': [format_dokument(d) for d in dokumenty_zatwierdzone]
    })

@dziekanat_api_bp.route('/weryfikuj_zal3/<int:praktyka_id>', methods=['GET', 'POST'])
@login_required
def weryfikuj_zal3(praktyka_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    student = praktyka.student
    
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL3').first()
    if not dokument:
        return jsonify({'error': 'Brak dokumentu ZAL3'}), 404
        
    karta = KartaPraktyki.query.filter_by(dokument_id=dokument.id).first()

    if request.method == 'POST':
        data = request.json
        akcja = data.get('akcja')
        
        if akcja == 'zatwierdz':
            dokument.status = 'Zatwierdzone'
            if karta:
                karta.akceptacja_dziekanat = True
                karta.akceptacja_dziekanat_data = date.today()
            
            notif_u = Powiadomienie(
                uzytkownik_id=praktyka.uopz_id,
                tresc=f"Dziekanat ostatecznie ZATWIERDZIŁ Kartę Praktyki (Zał. 3) dla {student.uzytkownik.imie} {student.uzytkownik.nazwisko}.",
                link=f"/uopz/zal3_karta/{student.id}"
            )
            notif_s = Powiadomienie(
                uzytkownik_id=student.uzytkownik.id,
                tresc="Dziekanat ostatecznie ZATWIERDZIŁ Twoją Kartę Praktyki (Zał. 3).",
                link=f"/student/zal3_karta"
            )
            db.session.add_all([notif_u, notif_s])
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Karta Praktyki (ZAL3) została ostatecznie zatwierdzona!'})
            
        elif akcja == 'odrzuc':
            dokument.status = 'Skierowanie_Wydane'
            komentarz = data.get('komentarz_dziekanatu')
            dokument.komentarz = komentarz if komentarz else "Odrzucono do poprawy."
            
            notif_u = Powiadomienie(
                uzytkownik_id=praktyka.uopz_id,
                tresc=f"Dziekanat cofnął do poprawy Kartę Praktyki (Zał. 3) dla {student.uzytkownik.imie} {student.uzytkownik.nazwisko}.",
                link=f"/uopz/zal3_karta/{student.id}"
            )
            db.session.add(notif_u)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'ZAL3 cofnięty do poprawy.'})

    porozumienie = praktyka.porozumienie
    porozumienie_data = None
    if porozumienie:
        porozumienie_data = {
            'id': porozumienie.id,
            'data_podpisania': porozumienie.data_podpisania.strftime('%Y-%m-%d') if porozumienie.data_podpisania else None
        }

    praktyka_dict = praktyka.to_dict()
    if praktyka.zaklad:
        praktyka_dict['zaklad'] = praktyka.zaklad.to_dict()

    return jsonify({
        'dokument': dokument.to_dict(),
        'karta': karta.to_dict() if karta else None,
        'praktyka': praktyka_dict,
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'porozumienie': porozumienie_data
    })

@dziekanat_api_bp.route('/zal6_lista', methods=['GET'])
@login_required
def zal6_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Brak uprawnień'}), 403

    dokumenty = Dokument.query.filter_by(typ_zalacznika='ZAL6').all()
    
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
        if d.status == 'Weryfikacja Dziekanatu':
            do_akcji.append(fd)
        elif d.status == 'Weryfikacja UOPZ':
            do_akcji.append(fd)
        elif d.status in ['Draft', 'Weryfikacja ZOPZ', 'Wrócono do poprawy', 'Zatwierdzone przez ZOPZ']:
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

@dziekanat_api_bp.route('/zal7_lista', methods=['GET'])
@login_required
def zal7_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Brak uprawnień'}), 403

    dokumenty = Dokument.query.filter(Dokument.typ_zalacznika.in_(['ZAL7', 'ZAL7A'])).all()
    
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
            'typ': doc.typ_zalacznika,
            'data_zlozenia': doc.updated_at.strftime('%Y-%m-%d %H:%M') if doc.updated_at else ''
        }

    do_akcji = []
    w_toku = []
    zatwierdzone = []

    for d in dokumenty:
        fd = format_dokument(d)
        if d.status == 'Weryfikacja UOPZ' or d.status == 'Weryfikacja Dyrektor':
            do_akcji.append(fd)
        elif d.status in ['Draft', 'Weryfikacja ZOPZ', 'OczekujeZOPZ', 'Weryfikacja', 'Rejected']:
            w_toku.append(fd)
        elif d.status == 'Approved':
            zatwierdzone.append(fd)
        else:
            w_toku.append(fd)

    return jsonify({
        'do_akcji': do_akcji,
        'w_toku': w_toku,
        'zatwierdzone': zatwierdzone
    })

@dziekanat_api_bp.route('/zal4_lista', methods=['GET'])
@login_required
def zal4_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Brak uprawnień'}), 403

    dokumenty = Dokument.query.filter_by(typ_zalacznika='ZAL4').all()
    
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

    w_toku = []
    zatwierdzone = []

    for d in dokumenty:
        fd = format_dokument(d)
        if d.status == 'Zatwierdzone':
            zatwierdzone.append(fd)
        else:
            w_toku.append(fd)

    return jsonify({
        'w_toku': w_toku,
        'zatwierdzone': zatwierdzone
    })

@dziekanat_api_bp.route('/dziennik/<int:student_id>', methods=['GET'])
@login_required
def dziennik_get(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']: return jsonify({'error': 'Brak uprawnień'}), 403
    from models import Student, Praktyka, Dokument, WpisDziennika
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka: return jsonify({'error': 'Brak praktyki'}), 404
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL6').first()
    if not dokument: return jsonify({'error': 'Dziennik nie został utworzony'}), 404
    
    wpisy = WpisDziennika.query.filter_by(dokument_id=dokument.id).order_by(WpisDziennika.data_wpisu).all()
    
    return jsonify({
        'student': student.uzytkownik.to_dict(),
        'student_profil': student.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict(),
        'wpisy': [w.to_dict() for w in wpisy]
    })

@dziekanat_api_bp.route('/zal4b', methods=['GET'])
@login_required
def zal4b_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    dokumenty_do_weryfikacji = db.session.query(Dokument)\
        .filter(Dokument.status == 'Submitted', Dokument.typ_zalacznika == 'ZAL4B').all()
        
    dokumenty_w_trakcie = db.session.query(Dokument)\
        .filter(Dokument.status == 'Returned', Dokument.typ_zalacznika == 'ZAL4B').order_by(Dokument.updated_at.desc()).all()
        
    dokumenty_zatwierdzone = db.session.query(Dokument)\
        .filter(Dokument.status == 'Approved', Dokument.typ_zalacznika == 'ZAL4B').order_by(Dokument.updated_at.desc()).all()

    def format_dokument(doc):
        student = doc.praktyka.student
        return {
            'id': doc.id,
            'praktyka_id': doc.praktyka_id,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'status': doc.status,
            'data_zlozenia': doc.updated_at.strftime('%Y-%m-%d %H:%M') if doc.updated_at else ''
        }

    return jsonify({
        'do_weryfikacji': [format_dokument(d) for d in dokumenty_do_weryfikacji],
        'w_trakcie': [format_dokument(d) for d in dokumenty_w_trakcie],
        'zatwierdzone': [format_dokument(d) for d in dokumenty_zatwierdzone]
    })

@dziekanat_api_bp.route('/weryfikuj_zal4b/<int:praktyka_id>', methods=['GET', 'POST'])
@login_required
def weryfikuj_zal4b(praktyka_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    student = praktyka.student
    
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4B').first()
    if not dokument:
        return jsonify({'error': 'Brak dokumentu ZAL4B'}), 404

    from models import WniosekZaliczeniePraktyki
    wniosek = WniosekZaliczeniePraktyki.query.filter_by(dokument_id=dokument.id).first()

    if request.method == 'POST':
        data = request.json
        akcja = data.get('akcja')
        
        if akcja == 'zatwierdz':
            dokument.status = 'Approved'
            praktyka.status = 'ZAL4B_ZATWIERDZONE'
            
            notif_s = Powiadomienie(
                uzytkownik_id=student.uzytkownik.id,
                tresc="Dziekanat ostatecznie ZATWIERDZIŁ Twój wniosek o zaliczenie (Zał. 4b).",
                link=f"/student/zal4b_wniosek"
            )
            db.session.add(notif_s)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Wniosek o zaliczenie na podstawie pracy zawodowej (ZAL4B) został ostatecznie zatwierdzony!'})
            
        elif akcja == 'odrzuc':
            dokument.status = 'Returned'
            komentarz = data.get('komentarz_dziekanatu')
            dokument.komentarz = komentarz if komentarz else "Odrzucono do poprawy."
            
            notif_s = Powiadomienie(
                uzytkownik_id=student.uzytkownik.id,
                tresc="Dziekanat ZWRÓCIŁ DO POPRAWY Twój wniosek o zaliczenie (Zał. 4b). Sprawdź uwagi.",
                link=f"/student/zal4b_wniosek"
            )
            db.session.add(notif_s)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'ZAL4B zwrócony do poprawy.'})
            
        elif akcja == 'odrzuc_calkowicie':
            dokument.status = 'Rejected'
            komentarz = data.get('komentarz_dziekanatu')
            dokument.komentarz = komentarz if komentarz else "Ścieżka odrzucona przez Dziekanat."
            
            praktyka.status = 'BRAK_ZGŁOSZENIA'
            
            notif_s = Powiadomienie(
                uzytkownik_id=student.uzytkownik.id,
                tresc="Dziekanat CAŁKOWICIE ODRZUCIŁ Twoją ścieżkę zaliczenia na podstawie pracy. Wybierz ścieżkę od nowa.",
                link=f"/student/dashboard"
            )
            db.session.add(notif_s)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Ścieżka pracy została całkowicie odrzucona i zresetowana.'})

    import json
    zalaczniki = []
    uzupelnienia = []
    if wniosek:
        if wniosek.zalaczniki_paths:
            try:
                zalaczniki = json.loads(wniosek.zalaczniki_paths)
            except Exception:
                pass
        if wniosek.uzupelnienia_paths:
            try:
                uzupelnienia = json.loads(wniosek.uzupelnienia_paths)
            except Exception:
                pass

    return jsonify({
        'dokument': dokument.to_dict(),
        'praktyka': praktyka.to_dict(),
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'wniosek': wniosek.to_dict() if wniosek else None,
        'zalaczniki': zalaczniki,
        'uzupelnienia': uzupelnienia
    })
