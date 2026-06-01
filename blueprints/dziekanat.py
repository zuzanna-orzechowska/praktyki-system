from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Student, Praktyka, Dokument, Sprawozdanie

dziekanat_bp = Blueprint('dziekanat', __name__, url_prefix='/dziekanat')

@dziekanat_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        flash('Brak uprawnień do panelu dziekanatu.', 'danger')
        return redirect(url_for('index'))
    return render_template('dziekanat/dashboard.html')

@dziekanat_bp.route('/zal9')
@login_required
def zal9_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/zal9_lista.html')


@dziekanat_bp.route('/weryfikuj_zal9/<int:id>', methods=['GET'])
@login_required
def weryfikuj_zal9(id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/weryfikuj_zal9.html')

@dziekanat_bp.route('/porozumienia')
@login_required
def porozumienia():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/porozumienia_lista.html')

@dziekanat_bp.route('/weryfikuj_porozumienie/<int:praktyka_id>')
@login_required
def weryfikuj_porozumienie(praktyka_id):
    from models import Praktyka, Oswiadczenie, Dokument
    from datetime import datetime
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    porozumienie = praktyka.porozumienie
    student = praktyka.student
    
    oswiadczenie = None
    dokument_zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
    if dokument_zal9:
        oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument_zal9.id).first()

    current_date = datetime.now().strftime('%Y-%m-%d')
    current_year = datetime.now().year

    return render_template('dziekanat/weryfikuj_porozumienie.html', 
                           porozumienie=porozumienie, 
                           praktyka=praktyka, 
                           student=student,
                           oswiadczenie=oswiadczenie,
                           current_date=current_date,
                           current_year=current_year)

@dziekanat_bp.route('/zal2a')
@login_required
def zal2a_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/zal2a_lista.html')

@dziekanat_bp.route('/weryfikuj_zal2a/<int:praktyka_id>')
@login_required
def weryfikuj_zal2a(praktyka_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/weryfikuj_zal2a.html')

@dziekanat_bp.route('/przypisz_uopz')
@login_required
def przypisz_uopz():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/przypisz_uopz.html')

@dziekanat_bp.route('/zal3')
@login_required
def zal3_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/zal3_lista.html')

@dziekanat_bp.route('/weryfikuj_zal3/<int:praktyka_id>')
@login_required
def weryfikuj_zal3(praktyka_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/weryfikuj_zal3.html')

@dziekanat_bp.route('/zal6_lista')
@login_required
def zal6_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/zal6_lista.html')

@dziekanat_bp.route('/zal7_lista')
@login_required
def zal7_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/zal7_lista.html')

@dziekanat_bp.route('/zal7_sprawozdanie/<int:student_id>')
@login_required
def zal7_sprawozdanie(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7').first() if praktyka else None
    sprawozdanie = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first() if dokument else None
    return render_template('dokumenty/zal7_sprawozdanie.html', student=student, praktyka=praktyka, dokument=dokument, sprawozdanie=sprawozdanie)

@dziekanat_bp.route('/zal7a_sprawozdanie/<int:student_id>')
@login_required
def zal7a_sprawozdanie(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A').first() if praktyka else None
    sprawozdanie = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first() if dokument else None
    return render_template('dokumenty/zal7a_sprawozdanie.html', student=student, praktyka=praktyka, dokument=dokument, sprawozdanie=sprawozdanie)

@dziekanat_bp.route('/dziennik/<int:student_id>')
@login_required
def podglad_dziennika(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/podglad_dziennika.html')

@dziekanat_bp.route('/zal4_lista')
@login_required
def zal4_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/zal4_lista.html')

@dziekanat_bp.route('/zal4_efekty/<int:student_id>')
@login_required
def zal4_efekty(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
        
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4').first() if praktyka else None
    
    import re
    opinia_text = dokument.uwagi_opiekuna if dokument and dokument.uwagi_opiekuna else ''
    podpis_uopz = None
    data_podpisu_uopz = None
    
    if opinia_text:
        match = re.search(r'\[Podpis elektroniczny UOPZ:\s*(.*?),\s*Data:\s*(.*?)\]', opinia_text)
        if match:
            podpis_uopz = match.group(1).strip()
            data_podpisu_uopz = match.group(2).strip()
            opinia_text = opinia_text[:match.start()].strip()

    from models import EfektUczenia
    efekty = EfektUczenia.query.filter_by(dokument_id=dokument.id).order_by(EfektUczenia.kod_efektu).all() if dokument else []
    from blueprints.student import lista_wymaganych_efektow
    
    return render_template('dokumenty/zal4_efekty.html', 
                           student=student, 
                           praktyka=praktyka, 
                           dokument=dokument, 
                           efekty=efekty, 
                           lista_statyczna=lista_wymaganych_efektow,
                           opinia_text=opinia_text,
                           podpis_uopz=podpis_uopz,
                           data_podpisu_uopz=data_podpisu_uopz)
