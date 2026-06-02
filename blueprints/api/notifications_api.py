from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Powiadomienie

notifications_api_bp = Blueprint('notifications_api', __name__, url_prefix='/api/notifications')

@notifications_api_bp.route('', methods=['GET'])
@login_required
def get_notifications():
    powiadomienia = Powiadomienie.query.filter_by(uzytkownik_id=current_user.id).order_by(Powiadomienie.data_utworzenia.desc()).limit(20).all()
    
    return jsonify({
        'powiadomienia': [{
            'id': p.id,
            'tresc': p.tresc,
            'link': p.link,
            'przeczytane': p.przeczytane,
            'data_utworzenia': p.data_utworzenia.strftime('%Y-%m-%d %H:%M') if p.data_utworzenia else ''
        } for p in powiadomienia]
    })

@notifications_api_bp.route('/mark_read/<int:id>', methods=['POST'])
@login_required
def mark_read(id):
    p = Powiadomienie.query.filter_by(id=id, uzytkownik_id=current_user.id).first()
    if p:
        db.session.delete(p)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Nie znaleziono'}), 404

@notifications_api_bp.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    Powiadomienie.query.filter_by(uzytkownik_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True})
