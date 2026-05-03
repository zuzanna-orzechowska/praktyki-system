from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
def dashboard():
    #tylko student ma tu dostęp
    if current_user.rola != 'student':
        flash('Odmowa dostępu. Strona tylko dla studentów.', 'danger')
        return redirect(url_for('index'))
    return render_template('student/dashboard.html')

@student_bp.route('/dziennik', methods=['GET', 'POST'])
@login_required
def dziennik():
    if current_user.rola != 'student':
        flash('Odmowa dostępu.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        #SYMULACJA DO ZMIANY
        dane_formularza = request.form
        print(dane_formularza) 
        flash('Zapisano wpisy w dzienniku (symulacja)!', 'success')
        return redirect(url_for('student.dziennik'))

    # SYMULACJA DANYCH
    praktyka_info = {
        'zaklad_nazwa': 'Brak przypisanej firmy (wypełnij Zał. 9)',
        'data_start': 'YYYY-MM-DD',
        'data_end': 'YYYY-MM-DD'
    }

    return render_template('student/zal6_dziennik.html', praktyka=praktyka_info)