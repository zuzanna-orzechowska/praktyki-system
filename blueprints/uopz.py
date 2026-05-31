from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

uopz_bp = Blueprint('uopz', __name__, url_prefix='/uopz')

@uopz_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'uopz':
        flash('Odmowa dostępu. Strona tylko dla Uczelnianych Opiekunów Praktyk.', 'danger')
        return redirect(url_for('index'))
    return render_template('uopz/dashboard.html')

@uopz_bp.route('/teczka/<int:student_id>')
@login_required
def teczka(student_id):
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return render_template('uopz/teczka.html')

@uopz_bp.route('/zal3_karta/<int:student_id>')
@login_required
def zal3_karta(student_id):
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return render_template('uopz/zal3_karta.html')

@uopz_bp.route('/zal2a_harmonogram/<int:student_id>')
@login_required
def zal2a_harmonogram(student_id):
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return render_template('uopz/zal2a_harmonogram.html')

@uopz_bp.route('/zal4_efekty/<int:student_id>')
@login_required
def zal4_efekty(student_id):
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return render_template('uopz/zal4_efekty.html')

@uopz_bp.route('/zal7_sprawozdanie/<int:student_id>')
@login_required
def zal7_sprawozdanie(student_id):
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return render_template('uopz/zal7_sprawozdanie.html')

@uopz_bp.route('/zal7a_sprawozdanie/<int:student_id>')
@login_required
def zal7a_sprawozdanie(student_id):
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return render_template('uopz/zal7a_sprawozdanie.html')

@uopz_bp.route('/zal2a_lista')
@login_required
def zal2a_lista():
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return render_template('uopz/zal2a_lista.html')

@uopz_bp.route('/zal3_lista')
@login_required
def zal3_lista():
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return render_template('uopz/zal3_lista.html')

@uopz_bp.route('/zal6_lista')
@login_required
def zal6_lista():
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return render_template('uopz/zal6_lista.html')

@uopz_bp.route('/dziennik/<int:student_id>')
@login_required
def dziennik(student_id):
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return render_template('uopz/weryfikuj_dziennik.html')
