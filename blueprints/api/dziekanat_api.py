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
    praktyki = db.session.query(Praktyka).filter(Praktyka.status != 'OCZEKUJE_NA_ZAL9', Praktyka.status != 'BRAK_ZGŁOSZENIA').all()
    for p in praktyki:
        por = p.porozumienie
        if not por:
            porozumienia_count += 1
        elif por.status in ['Draft', 'ZaakceptowaneDyrektor', 'UwagiZOPZ', 'ZatwierdzoneZOPZ', 'OczekujeZOPZ']:
            porozumienia_count += 1
            
    zal2a_count = db.session.query(Dokument).filter_by(status='Submitted', typ_zalacznika='ZAL2A').count()
            
    return jsonify({
        'zal9_count': zal9_count,
        'porozumienia_count': porozumienia_count,
        'zal2a_count': zal2a_count
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
        return {
            'id': por.id if por else p.id,
            'praktyka_id': p.id,
            'porozumienie_id': por.id if por else None,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'status_porozumienia': por.status if por else 'Brak / Szkic',
            'komentarz_zopz': por.komentarz_zopz if por else None
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
            db.session.commit()
            return jsonify({'success': True, 'message': f'Oświadczenie studenta {student.uzytkownik.nazwisko} zostało zatwierdzone. Dane przekazano do IT.'})
            
        elif akcja == 'odrzuc':
            dokument.status = 'Draft'
            komentarz = data.get('komentarz_dziekanatu')
            dokument.komentarz = komentarz if komentarz else "Dokument został odrzucony do poprawy. Prosimy o wprowadzenie zmian i ponowne przesłanie."
            praktyka.status = 'OCZEKUJE_NA_ZAL9'
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
        'praktyki': [format_praktyka(p) for p in praktyki]
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

    return jsonify({
        'dokument': dokument.to_dict(),
        'karta': karta.to_dict() if karta else None,
        'praktyka': praktyka.to_dict(),
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'porozumienie': porozumienie_data
    })
