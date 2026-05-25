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
            
    return jsonify({
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict(),
        'oswiadczenie': oswiadczenie.to_dict()
    })
