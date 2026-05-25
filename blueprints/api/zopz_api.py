from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import Praktyka, ZakladPracy

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
            'porozumienie_komentarz': porozumienie.komentarz_zopz if porozumienie else None
        }

    return jsonify({
        'zaklad': zaklad.to_dict() if zaklad else None,
        'praktyki': [format_praktyka(p) for p in praktyki]
    })

@zopz_api_bp.route('/zaklad_pracy', methods=['PUT'])
@login_required
def update_zaklad_pracy():
    from flask import request
    from extensions import db
    
    if current_user.rola != 'zopz':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
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
    from models import Porozumienie
    from extensions import db
    from flask import request
    
    if current_user.rola != 'zopz':
        return jsonify({'error': 'Odmowa dostępu'}), 403
        
    porozumienie = Porozumienie.query.get_or_404(porozumienie_id)
    if porozumienie.zaklad.zopz_id != current_user.id:
        return jsonify({'error': 'Odmowa dostępu do tego porozumienia'}), 403
        
    data = request.json
    akcja = data.get('akcja')
    
    if akcja == 'zatwierdz':
        porozumienie.status = 'ZatwierdzoneZOPZ'
        porozumienie.komentarz_zopz = None
        message = 'Porozumienie zostało zatwierdzone.'
    elif akcja == 'uwagi':
        komentarz = data.get('komentarz_zopz')
        if not komentarz:
            return jsonify({'error': 'Komentarz jest wymagany przy zgłaszaniu uwag.'}), 400
        porozumienie.status = 'UwagiZOPZ'
        porozumienie.komentarz_zopz = komentarz
        message = 'Uwagi zostały przesłane do Dziekanatu.'
    else:
        return jsonify({'error': 'Nieznana akcja.'}), 400
        
    db.session.commit()
    return jsonify({'success': True, 'message': message})
