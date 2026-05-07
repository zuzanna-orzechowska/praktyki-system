from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Praktyka, Dokument, Oswiadczenie, Uzytkownik, ZakladPracy, Student
from extensions import db

dziekanat_bp = Blueprint('dziekanat', __name__, url_prefix='/dziekanat')

@dziekanat_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'dziekanat':
        flash('Brak uprawnień do panelu dziekanatu.', 'danger')
        return redirect(url_for('index'))
    
    # pobranie oświadczenia (Zał. 9), które mają status 'Submitted'
    oswiadczenia_do_weryfikacji = db.session.query(Oswiadczenie)\
        .join(Dokument)\
        .filter(Dokument.status == 'Submitted', Dokument.typ_zalacznika == 'ZAL9').all()
    
    return render_template('dziekanat/dashboard.html', oswiadczenia=oswiadczenia_do_weryfikacji)

@dziekanat_bp.route('/weryfikuj_zal9/<int:id>', methods=['GET', 'POST'])
@login_required
def weryfikuj_zal9(id):
    if current_user.rola != 'dziekanat':
        return redirect(url_for('index'))
        
    oswiadczenie = Oswiadczenie.query.get_or_404(id)
    dokument = oswiadczenie.dokument
    praktyka = dokument.praktyka
    student = praktyka.student
    
    if request.method == 'POST':
        akcja = request.form.get('akcja')
        
        if akcja == 'zatwierdz':
            # TYLKO ZMIANA STATUSÓW - bez tworzenia kont
            dokument.status = 'Approved'
            dokument.komentarz = None
            praktyka.status = 'ZAL9_ZATWIERDZONE'
            
            db.session.commit()
            flash(f'Oświadczenie studenta {student.uzytkownik.nazwisko} zostało zatwierdzone.', 'success')
            return redirect(url_for('dziekanat.dashboard'))
            
        elif akcja == 'odrzuc':
            dokument.status = 'Draft'
            komentarz = request.form.get('komentarz_dziekanatu')
            dokument.komentarz = komentarz if komentarz else "Dokument został odrzucony do poprawy. Prosimy o wprowadzenie zmian i ponowne przesłanie."
            praktyka.status = 'OCZEKUJE_NA_ZAL9'
            db.session.commit()
            flash('Oświadczenie odrzucone do poprawy przez studenta.', 'warning')
            return redirect(url_for('dziekanat.dashboard'))
            
    return render_template('dokumenty/zal9_oswiadczenie.html', oswiadczenie=oswiadczenie, student=student, dokument=dokument)