from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

dziekanat_bp = Blueprint('dziekanat', __name__, url_prefix='/dziekanat')

@dziekanat_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'dziekanat':
        flash('Brak uprawnień do panelu dziekanatu.', 'danger')
        return redirect(url_for('index'))
    return render_template('dziekanat/dashboard.html')

@dziekanat_bp.route('/zal9')
@login_required
def zal9_lista():
    if current_user.rola != 'dziekanat':
        return redirect(url_for('index'))
    return render_template('dziekanat/zal9_lista.html')


@dziekanat_bp.route('/weryfikuj_zal9/<int:id>', methods=['GET'])
@login_required
def weryfikuj_zal9(id):
    if current_user.rola != 'dziekanat':
        return redirect(url_for('index'))
    return render_template('dziekanat/weryfikuj_zal9.html')