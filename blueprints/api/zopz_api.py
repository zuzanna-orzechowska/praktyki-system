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
        return {
            'id': p.id,
            'student_id': student.id,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'kierunek': student.kierunek,
            'data_start': str(p.data_start) if p.data_start else '',
            'data_end': str(p.data_end) if p.data_end else '',
            'status': p.status
        }

    return jsonify({
        'zaklad': zaklad.to_dict() if zaklad else None,
        'praktyki': [format_praktyka(p) for p in praktyki]
    })
