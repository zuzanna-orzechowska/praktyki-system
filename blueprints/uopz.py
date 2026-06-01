from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Student, Praktyka, Dokument, Sprawozdanie, Powiadomienie
from datetime import datetime

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

@uopz_bp.route('/zal4_efekty/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal4_efekty(student_id):
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka or praktyka.uopz_id != current_user.id:
        flash('Odmowa dostępu do tego studenta.', 'danger')
        return redirect(url_for('uopz.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4').first()
    if not dokument:
        flash('ZOPZ nie utworzył jeszcze załącznika nr 4.', 'info')
        return redirect(url_for('uopz.teczka', student_id=student_id))

    # Oznacz powiadomienia jako przeczytane
    Powiadomienie.query.filter_by(uzytkownik_id=current_user.id, link=request.path, przeczytane=False).update({'przeczytane': True})
    db.session.commit()

    from models import EfektUczenia
    efekty = EfektUczenia.query.filter_by(dokument_id=dokument.id).order_by(EfektUczenia.kod_efektu).all()
    from blueprints.student import lista_wymaganych_efektow

    if request.method == 'POST':
        akcja = request.form.get('akcja')
        if akcja == 'zapisz_uopz':
            opinia = request.form.get('opinia_uopz', '').strip()
            
            if len(opinia) < 300:
                flash('Opinia musi zawierać co najmniej 300 znaków.', 'danger')
                return redirect(url_for('uopz.zal4_efekty', student_id=student_id))
            
            # Jeśli zaznaczono checkbox podpisu elektronicznego
            if request.form.get('podpis_uopz'):
                opinia += f"\n\n[Podpis elektroniczny UOPZ: {current_user.tytul_naukowy or ''} {current_user.imie} {current_user.nazwisko}, Data: {datetime.today().date()}]"
                
            dokument.uwagi_opiekuna = opinia
            dokument.status = 'Zatwierdzone'
            db.session.commit()
            
            notif = Powiadomienie(
                uzytkownik_id=student.uzytkownik_id,
                tresc="Opiekun Uczelniany zaopiniował i zatwierdził Twoje efekty uczenia się (Zał. 4).",
                link=url_for('student.zal4_efekty')
            )
            db.session.add(notif)
            db.session.commit()
            
            flash('Opinia została zapisana i podpisana pomyślnie.', 'success')
            return redirect(url_for('uopz.teczka', student_id=student_id))

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

    return render_template('dokumenty/zal4_efekty.html',
                           student=student,
                           dokument=dokument,
                           praktyka=praktyka,
                           efekty=efekty,
                           lista_statyczna=lista_wymaganych_efektow,
                           opinia_text=opinia_text,
                           podpis_uopz=podpis_uopz,
                           data_podpisu_uopz=data_podpisu_uopz)

@uopz_bp.route('/zal7_sprawozdanie/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal7_sprawozdanie(student_id):
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return handle_sprawozdanie_view(student_id, 'ZAL7')

@uopz_bp.route('/zal7a_sprawozdanie/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal7a_sprawozdanie(student_id):
    if current_user.rola != 'uopz': return redirect(url_for('index'))
    return handle_sprawozdanie_view(student_id, 'ZAL7A')

def handle_sprawozdanie_view(student_id, typ):
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Brak praktyki', 'danger')
        return redirect(url_for('uopz.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika=typ).first()
    sprawozdanie_doc = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first() if dokument else None

    if request.method == 'POST':
        akcja = request.form.get('akcja')
        uwagi = request.form.get('uwagi_opiekuna', '').strip()

        if dokument:
            dokument.uwagi_opiekuna = uwagi
            if akcja in ['zatwierdz', 'zatwierdz_i_podpisz']:
                dokument.status = 'Approved'
                if akcja == 'zatwierdz_i_podpisz' and sprawozdanie_doc:
                    sprawozdanie_doc.podpis_uopz = f"{current_user.imie} {current_user.nazwisko}"
                db.session.commit()
                
                notif = Powiadomienie(
                    uzytkownik_id=student.uzytkownik_id,
                    tresc=f"UOPZ zatwierdził Twoje Sprawozdanie ({'Zał. 7a' if typ == 'ZAL7A' else 'Zał. 7'}).",
                    link=url_for('student.sprawozdanie') if typ == 'ZAL7' else url_for('student.zal7a_sprawozdanie')
                )
                db.session.add(notif)
                db.session.commit()
                
                flash('Sprawozdanie zostało zatwierdzone.', 'success')
                return redirect(url_for('uopz.teczka', student_id=student_id))
            elif akcja == 'odrzuc':
                dokument.status = 'Rejected'
                db.session.commit()
                
                notif = Powiadomienie(
                    uzytkownik_id=student.uzytkownik_id,
                    tresc=f"UOPZ odrzucił Twoje Sprawozdanie ({'Zał. 7a' if typ == 'ZAL7A' else 'Zał. 7'}). Uwagi: {uwagi}",
                    link=url_for('student.sprawozdanie') if typ == 'ZAL7' else url_for('student.zal7a_sprawozdanie')
                )
                db.session.add(notif)
                db.session.commit()
                
                flash('Sprawozdanie zostało odrzucone do poprawy.', 'danger')
                return redirect(url_for('uopz.teczka', student_id=student_id))
                
    template_name = 'dokumenty/zal7_sprawozdanie.html' if typ == 'ZAL7' else 'dokumenty/zal7a_sprawozdanie.html'
    return render_template(template_name, student=student, dokument=dokument, sprawozdanie=sprawozdanie_doc, praktyka=praktyka)

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
