from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import Dokument, Oswiadczenie, Praktyka

dziekanat_api_bp = Blueprint('dziekanat_api', __name__, url_prefix='/dziekanat')

@dziekanat_api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.rola != 'dziekanat':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    zal9_count = db.session.query(Dokument).filter_by(status='Submitted', typ_zalacznika='ZAL9').count()
    return jsonify({
        'zal9_count': zal9_count
    })

@dziekanat_api_bp.route('/zal9', methods=['GET'])
@login_required
def zal9_lista():
    if current_user.rola != 'dziekanat':
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

    # Zwracamy listę słowników. Musimy ręcznie dodać dane studenta z relacji.
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
    if current_user.rola != 'dziekanat':
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

@dziekanat_api_bp.route('/wyslij_porozumienie/<int:praktyka_id>', methods=['POST'])
@login_required
def wyslij_porozumienie(praktyka_id):
    if current_user.rola != 'dziekanat':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    if not praktyka.zaklad_id:
        return jsonify({'error': 'Praktyka nie ma przypisanego zakładu pracy (ZAL9 nie został w pełni zatwierdzony/nie utworzono konta).'}), 400
        
    porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
    if not porozumienie:
        porozumienie = Porozumienie(praktyka_id=praktyka.id, zaklad_id=praktyka.zaklad_id, status='OczekujeZOPZ')
        db.session.add(porozumienie)
    else:
        porozumienie.status = 'OczekujeZOPZ'
        porozumienie.komentarz_zopz = None # reset komentarza przy ponownym wysłaniu
        
    db.session.commit()
    return jsonify({'success': True, 'message': 'Porozumienie wysłane do ZOPZ.'})

@dziekanat_api_bp.route('/podpisz_porozumienie/<int:id>', methods=['POST'])
@login_required
def podpisz_porozumienie(id):
    from models import Porozumienie
    from datetime import date
    if current_user.rola != 'dziekanat':
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
    if current_user.rola != 'dziekanat':
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
            # Zgodnie z nowym flow to dzieje się już przy "zatwierdz", 
            # ale zostawiam jako osobną akcję, gdyby było osobne kliknięcie.
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
    if current_user.rola != 'dziekanat':
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
            
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Zaktualizowano dane Zakładu Pracy i reprezentanta.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
