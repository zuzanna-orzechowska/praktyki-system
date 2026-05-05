from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Uzytkownik, Student, Praktyka, Dokument, Protokol

uopz_bp = Blueprint('uopz', __name__, url_prefix='/uopz')

@uopz_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'uopz':
        flash('Odmowa dostępu. Strona tylko dla Uczelnianych Opiekunów Praktyk.', 'danger')
        return redirect(url_for('index'))

    praktyki = Praktyka.query.filter_by(uopz_id=current_user.id).all()

    return render_template('uopz/dashboard.html', praktyki=praktyki)

@uopz_bp.route('/teczka/<int:student_id>')
@login_required
def teczka(student_id):
    if current_user.rola != 'uopz':
        return redirect(url_for('index'))

    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id, uopz_id=current_user.id).first()

    if not praktyka:
        flash('Brak dostępu do tego studenta lub brak przypisanej praktyki.', 'danger')
        return redirect(url_for('uopz.dashboard'))

    dokumenty = Dokument.query.filter_by(praktyka_id=praktyka.id).all()
    dok_dict = {d.typ_zalacznika: d for d in dokumenty}

    return render_template('uopz/teczka.html', student=student, praktyka=praktyka, dokumenty=dok_dict)