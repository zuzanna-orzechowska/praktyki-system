from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Praktyka, ZakladPracy
from extensions import db

zopz_bp = Blueprint('zopz', __name__, url_prefix='/zopz')

@zopz_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'zopz':
        flash('Brak dostępu. Ten panel jest przeznaczony dla opiekunów zakładowych.', 'danger')
        return redirect(url_for('index'))

    # szukanie firmy przypisanej do tego opiekuna
    zaklad = ZakladPracy.query.filter_by(zopz_id=current_user.id).first()

    # jeśli firma istnieje, pobranie listy studentów (praktyk) w tej firmie
    praktyki = []
    if zaklad:
        praktyki = Praktyka.query.filter_by(zaklad_id=zaklad.id).all()

    return render_template('zopz/dashboard.html', zaklad=zaklad, praktyki=praktyki)