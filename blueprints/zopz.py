from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

zopz_bp = Blueprint('zopz', __name__, url_prefix='/zopz')

@zopz_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'zopz':
        flash('Brak dostępu. Ten panel jest przeznaczony dla opiekunów zakładowych.', 'danger')
        return redirect(url_for('index'))

    return render_template('zopz/dashboard.html')

@zopz_bp.route('/porozumienie/<int:id>')
@login_required
def porozumienie(id):
    from models import Porozumienie, Oswiadczenie, Dokument
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))

    porozumienie_doc = Porozumienie.query.get_or_404(id)
    if porozumienie_doc.zaklad.zopz_id != current_user.id:
        flash('Odmowa dostępu do tego porozumienia.', 'danger')
        return redirect(url_for('zopz.dashboard'))

    praktyka = porozumienie_doc.praktyka
    student = praktyka.student
    
    oswiadczenie = None
    dokument_zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
    if dokument_zal9:
        oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument_zal9.id).first()

    from datetime import datetime
    return render_template(
        'zopz/weryfikuj_porozumienie.html',
        student=student,
        praktyka=praktyka,
        porozumienie=porozumienie_doc,
        oswiadczenie=oswiadczenie,
        current_date=datetime.today().date()
    )

@zopz_bp.route('/zal2a_harmonogram/<int:student_id>')
@login_required
def zal2a_harmonogram(student_id):
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
    return render_template('zopz/zal2a_harmonogram.html')

@zopz_bp.route('/teczka/<int:student_id>')
@login_required
def teczka(student_id):
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
    return render_template('zopz/teczka.html')

@zopz_bp.route('/zal3_karta/<int:student_id>')
@login_required
def zal3_karta(student_id):
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
    return render_template('zopz/zal3_karta.html')

@zopz_bp.route('/zal3_lista')
@login_required
def zal3_lista():
    if current_user.rola != 'zopz': return redirect(url_for('index'))
    return render_template('zopz/zal3_lista.html')