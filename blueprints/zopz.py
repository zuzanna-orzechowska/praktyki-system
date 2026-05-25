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