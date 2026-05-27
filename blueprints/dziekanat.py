from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

dziekanat_bp = Blueprint('dziekanat', __name__, url_prefix='/dziekanat')

@dziekanat_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        flash('Brak uprawnień do panelu dziekanatu.', 'danger')
        return redirect(url_for('index'))
    return render_template('dziekanat/dashboard.html')

@dziekanat_bp.route('/zal9')
@login_required
def zal9_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/zal9_lista.html')


@dziekanat_bp.route('/weryfikuj_zal9/<int:id>', methods=['GET'])
@login_required
def weryfikuj_zal9(id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/weryfikuj_zal9.html')

@dziekanat_bp.route('/porozumienia')
@login_required
def porozumienia():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/porozumienia_lista.html')

@dziekanat_bp.route('/weryfikuj_porozumienie/<int:praktyka_id>')
@login_required
def weryfikuj_porozumienie(praktyka_id):
    from models import Praktyka, Oswiadczenie, Dokument
    from datetime import datetime
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    porozumienie = praktyka.porozumienie
    student = praktyka.student
    
    oswiadczenie = None
    dokument_zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
    if dokument_zal9:
        oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument_zal9.id).first()

    current_date = datetime.now().strftime('%Y-%m-%d')
    current_year = datetime.now().year

    return render_template('dziekanat/weryfikuj_porozumienie.html', 
                           porozumienie=porozumienie, 
                           praktyka=praktyka, 
                           student=student,
                           oswiadczenie=oswiadczenie,
                           current_date=current_date,
                           current_year=current_year)