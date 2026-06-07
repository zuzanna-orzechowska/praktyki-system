from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'admin':
        return redirect(url_for('index'))
    return render_template('admin/dashboard.html')

@admin_bp.route('/praktyki_lista')
@login_required
def praktyki_lista():
    if current_user.rola != 'admin':
        return redirect(url_for('index'))
    return render_template('admin/praktyki_lista.html')

@admin_bp.route('/logi')
@login_required
def logi():
    if current_user.rola != 'admin':
        return redirect(url_for('index'))
    return render_template('admin/logi.html')