from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Student, Praktyka, Dokument, WpisDziennika, Porozumienie, HarmonogramPraktyki, Uzytkownik, Protokol, Sprawozdanie, EfektUczenia, WniosekZaliczeniePraktyki, Oswiadczenie
from datetime import datetime
from werkzeug.utils import secure_filename
import os

student_bp = Blueprint('student', __name__, url_prefix='/student')

UPLOAD_FOLDER = 'static/uploads/zal4b'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'student':
        flash('Odmowa dostępu. Strona tylko dla studentów.', 'danger')
        return redirect(url_for('index'))
    return render_template('student/dashboard.html')

@student_bp.route('/dziennik', methods=['GET'])
@login_required
def dziennik():
    if current_user.rola != 'student':
        flash('Odmowa dostępu.', 'danger')
        return redirect(url_for('index'))

    return render_template('dokumenty/zal6_dziennik.html')


@student_bp.route('/porozumienie')
@login_required
def porozumienie():
    if current_user.rola != 'student':
        flash('Odmowa dostępu.', 'danger')
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student:
        flash('Twój profil studenta nie jest jeszcze kompletny.', 'warning')
        return redirect(url_for('student.dashboard'))

    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Nie masz jeszcze przypisanej praktyki w systemie.', 'warning')
        return redirect(url_for('student.dashboard'))

    #jesli nie ma porozumienia to pusty szkic z danymi z praktyki
    porozumienie_doc = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
    
    # Pobierz oświadczenie z ZAL9, aby mieć dane reprezentanta Zakładu
    oswiadczenie = None
    dokument_zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
    if dokument_zal9:
        oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument_zal9.id).first()

    return render_template(
        'dokumenty/zal1_porozumienie.html',
        student=student,
        praktyka=praktyka,
        porozumienie=porozumienie_doc,
        oswiadczenie=oswiadczenie,
        current_date=datetime.today().date()
    )

@student_bp.route('/zal2_program')
@login_required
def zal2_program():
    if current_user.rola != 'student': return redirect(url_for('index'))
    return render_template('dokumenty/zal2_program_student.html')

@student_bp.route('/zal2a_harmonogram', methods=['GET'])
@login_required
def zal2a_harmonogram():
    if current_user.rola != 'student': return redirect(url_for('index'))
    return render_template('dokumenty/zal2a_harmonogram_student.html')

@student_bp.route('/zal3_karta')
@login_required
def zal3_karta():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))

    uopz = Uzytkownik.query.get(praktyka.uopz_id) if praktyka.uopz_id else None
    porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
    protokol = Protokol.query.filter_by(praktyka_id=praktyka.id).first()
    
    zopz = Uzytkownik.query.get(praktyka.zaklad.zopz_id) if praktyka.zaklad and praktyka.zaklad.zopz_id else None

    return render_template(
        'dokumenty/zal3_karta.html', 
        student=student, 
        praktyka=praktyka, 
        uopz=uopz, 
        zopz=zopz,
        porozumienie=porozumienie, 
        protokol=protokol
    )

@student_bp.route('/sprawozdanie', methods=['GET', 'POST'])
@login_required
def sprawozdanie():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL7', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    sprawozdanie_doc = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first()

    if request.method == 'POST':
        charakterystyka = request.form.get('charakterystyka', '').strip()
        opis = request.form.get('opis', '').strip()
        wiedza = request.form.get('wiedza', '').strip()

        if len(charakterystyka) < 150 or len(opis) < 300 or len(wiedza) < 300:
            flash('Błąd zapisu! Niektóre sekcje są zbyt krótkie. Wymagamy dłuższego, merytorycznego opisu.', 'danger')
        else:
            if not sprawozdanie_doc:
                sprawozdanie_doc = Sprawozdanie(dokument_id=dokument.id)
                db.session.add(sprawozdanie_doc)

            sprawozdanie_doc.charakterystyka = charakterystyka
            sprawozdanie_doc.opis_prac = opis
            sprawozdanie_doc.wiedza_umiejetnosci = wiedza
            
            db.session.commit()
            flash('Sprawozdanie zapisano pomyślnie!', 'success')
            return redirect(url_for('student.sprawozdanie'))

    return render_template(
        'dokumenty/zal7_sprawozdanie.html', 
        student=student, 
        praktyka=praktyka, 
        sprawozdanie=sprawozdanie_doc
    )

@student_bp.route('/zal4_efekty')
@login_required
def zal4_efekty():
    if current_user.rola != 'student':
        return redirect(url_for('index'))

    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4').first()
    efekty = []
    
    if dokument:
        efekty = EfektUczenia.query.filter_by(dokument_id=dokument.id).order_by(EfektUczenia.kod_efektu).all()

    lista_wymaganych_efektow = [
        "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych",
        "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce",
        "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy",
        "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka",
        "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania...",
        "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje...",
        "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia",
        "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy / instytucji, opisać go, przedstawić koncepcję rozwiązania i ją zrealizować.",
        "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności informatycznej...",
        "Pracuje w zespole zajmującym się zawodowo branżą IT",
        "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów",
        "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje...",
        "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki działalności informatyków..."
    ]

    return render_template(
        'dokumenty/zal4_efekty.html', 
        student=student, 
        praktyka=praktyka, 
        dokument=dokument,
        efekty=efekty,
        lista_statyczna=lista_wymaganych_efektow
    )

@student_bp.route('/zal4a_decyzja')
@login_required
def zal4a_decyzja():
    if current_user.rola != 'student': return redirect(url_for('index'))
    return render_template('dokumenty/zal4a_decyzja_student.html')

@student_bp.route('/zal4b_wniosek', methods=['GET'])
@login_required
def zal4b_wniosek():
    if current_user.rola != 'student':
        return redirect(url_for('index'))
    return render_template('dokumenty/zal4b_wniosek_student.html')

@student_bp.route('/zal7a_sprawozdanie', methods=['GET'])
@login_required
def zal7a_sprawozdanie():
    if current_user.rola != 'student': return redirect(url_for('index'))
    return render_template('dokumenty/zal7a_sprawozdanie_student.html')

@student_bp.route('/zal8_protokol')
@login_required
def zal8_protokol():
    if current_user.rola != 'student': return redirect(url_for('index'))
    return render_template('dokumenty/zal8_protokol_student.html')


@student_bp.route('/zal9_oswiadczenie', methods=['GET'])
@login_required
def zal9_oswiadczenie():
    if current_user.rola != 'student':
        return redirect(url_for('index'))
    return render_template('dokumenty/zal9_oswiadczenie_student.html')