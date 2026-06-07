from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Student, Praktyka, Dokument, Sprawozdanie, Powiadomienie
from datetime import datetime

uopz_bp = Blueprint('uopz', __name__, url_prefix='/uopz')

@uopz_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola not in ['uopz', 'admin']:
        flash('Odmowa dostępu. Strona tylko dla Uczelnianych Opiekunów Praktyk.', 'danger')
        return redirect(url_for('index'))
    return render_template('uopz/dashboard.html')

@uopz_bp.route('/teczka/<int:student_id>')
@login_required
def teczka(student_id):
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    return render_template('uopz/teczka.html')

@uopz_bp.route('/zal3_karta/<int:student_id>')
@login_required
def zal3_karta(student_id):
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    return render_template('uopz/zal3_karta.html')

@uopz_bp.route('/zal2a_harmonogram/<int:student_id>')
@login_required
def zal2a_harmonogram(student_id):
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    return render_template('uopz/zal2a_harmonogram.html')

@uopz_bp.route('/zal4_efekty/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal4_efekty(student_id):
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka or (praktyka.uopz_id != current_user.id and current_user.rola != 'admin'):
        flash('Odmowa dostępu do tego studenta.', 'danger')
        return redirect(url_for('uopz.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4').first()
    if not dokument:
        flash('ZOPZ nie utworzył jeszcze załącznika nr 4.', 'info')
        return redirect(url_for('uopz.teczka', student_id=student_id))

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
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    return handle_sprawozdanie_view(student_id, 'ZAL7')

@uopz_bp.route('/zal7a_sprawozdanie/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal7a_sprawozdanie(student_id):
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
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
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    return render_template('uopz/zal2a_lista.html')

@uopz_bp.route('/zal3_lista')
@login_required
def zal3_lista():
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    return render_template('uopz/zal3_lista.html')

@uopz_bp.route('/zal6_lista')
@login_required
def zal6_lista():
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    return render_template('uopz/zal6_lista.html')

@uopz_bp.route('/dziennik/<int:student_id>')
@login_required
def dziennik(student_id):
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    return render_template('uopz/weryfikuj_dziennik.html')

@uopz_bp.route('/zal8_lista')
@login_required
def zal8_lista():
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    from models import Student, Praktyka, Protokol
    
    studenci = Student.query.join(Praktyka).outerjoin(Protokol).filter(
        db.or_(
            Praktyka.uopz_id == current_user.id,
            Protokol.komisja_2 == f"{current_user.imie} {current_user.nazwisko}"
        )
    ).all()
    
    return render_template('uopz/zal8_lista.html', studenci=studenci)

@uopz_bp.route('/zal8_protokol/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal8_protokol(student_id):
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    from models import Student, Praktyka, Dokument, KartaPraktyki, Protokol, Uzytkownik
    from datetime import datetime
    
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka:
        flash('Student nie ma przypisanej praktyki.', 'warning')
        return redirect(url_for('uopz.zal8_lista'))

    dokument_karta = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL3').first()
    karta = KartaPraktyki.query.filter_by(dokument_id=dokument_karta.id).first() if dokument_karta else None
    
    pracownicy = Uzytkownik.query.filter(Uzytkownik.rola.in_(['pracownik', 'uopz', 'dziekanat', 'dyrektor'])).all()
    protokol = Protokol.query.filter_by(praktyka_id=praktyka.id).first()

    if request.method == 'POST':
        if not protokol:
            protokol = Protokol(praktyka_id=praktyka.id)
            db.session.add(protokol)
            
        def safe_float(val):
            try:
                return float(val.replace(',', '.'))
            except (ValueError, TypeError, AttributeError):
                return None
                
        protokol.instytucja_1 = request.form.get('instytucja_1')
        protokol.okres_1 = request.form.get('okres_1')
        protokol.instytucja_2 = request.form.get('instytucja_2')
        protokol.okres_2 = request.form.get('okres_2')
        
        protokol.ocena_s = safe_float(request.form.get('ocena_s'))
        protokol.ocena_u = safe_float(request.form.get('ocena_u'))
        protokol.ocena_z = safe_float(request.form.get('ocena_z'))
        
        data_egz = request.form.get('data_egzaminu')
        if data_egz:
            try:
                protokol.data_egzaminu = datetime.strptime(data_egz, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        protokol.pytanie_1 = request.form.get('pytanie_1')
        protokol.ocena_czastkowa_1 = safe_float(request.form.get('ocena_czastkowa_1'))
        protokol.pytanie_2 = request.form.get('pytanie_2')
        protokol.ocena_czastkowa_2 = safe_float(request.form.get('ocena_czastkowa_2'))
        protokol.pytanie_3 = request.form.get('pytanie_3')
        protokol.ocena_czastkowa_3 = safe_float(request.form.get('ocena_czastkowa_3'))
        
        protokol.ocena_e = safe_float(request.form.get('ocena_e_manual'))
        protokol.ocena_koncowa = safe_float(request.form.get('ocena_k'))
        protokol.ocena_k_slownie = request.form.get('ocena_k_slownie')
        
        try:
            db.session.commit()
            flash('Zapisano protokół pomyślnie.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd podczas zapisywania: {str(e)}', 'danger')
            
        return redirect(url_for('uopz.zal8_protokol', student_id=student.id))

    return render_template('dokumenty/zal8_protokol.html', student=student, karta=karta, pracownicy=pracownicy, protokol=protokol)

@uopz_bp.route('/zal8a_protokol/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal8a_protokol(student_id):
    if current_user.rola not in ['uopz', 'admin']: return redirect(url_for('index'))
    from models import Student, Praktyka, Protokol, Uzytkownik, Powiadomienie
    from datetime import datetime
    
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka:
        flash('Student nie ma przypisanej praktyki.', 'warning')
        return redirect(url_for('uopz.zal8_lista'))

    pracownicy = Uzytkownik.query.filter(Uzytkownik.rola.in_(['pracownik', 'uopz', 'dziekanat', 'dyrektor'])).all()
    protokol = Protokol.query.filter_by(praktyka_id=praktyka.id).first()

    if not protokol:
        flash('Protokół nie został jeszcze utworzony i przypisany przez Dziekanat.', 'danger')
        return redirect(url_for('uopz.teczka', student_id=student.id))
        
    if protokol.komisja_2 != f"{current_user.imie} {current_user.nazwisko}" and current_user.rola != 'admin':
        flash('Nie jesteś przypisany jako członek komisji do tego protokołu.', 'danger')
        return redirect(url_for('uopz.teczka', student_id=student.id))

    if request.method == 'POST':
        akcja = request.form.get('akcja')
            
        def safe_float(val):
            if val is None: return None
            try:
                return float(val.replace(',', '.'))
            except (ValueError, TypeError, AttributeError):
                return None
                
        protokol.instytucja_1 = request.form.get('instytucja_1')
        protokol.okres_1 = request.form.get('okres_1')
        protokol.instytucja_2 = request.form.get('instytucja_2')
        protokol.okres_2 = request.form.get('okres_2')
        
        protokol.ocena_s = safe_float(request.form.get('ocena_s'))
        
        if request.form.get('generateSignatureUOPZ'):
            protokol.podpis_opiekuna_s = f"[Podpis elektroniczny UOPZ: {current_user.tytul_naukowy or ''} {current_user.imie} {current_user.nazwisko}, Data: {datetime.today().strftime('%d.%m.%Y')}]"
        elif request.form.get('podpis_opiekuna_s') is not None:
            protokol.podpis_opiekuna_s = request.form.get('podpis_opiekuna_s')
            
        data_egz = request.form.get('data_egzaminu')
        if data_egz:
            try:
                protokol.data_egzaminu = datetime.strptime(data_egz, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        protokol.pytanie_1 = request.form.get('pytanie_1')
        protokol.ocena_czastkowa_1 = safe_float(request.form.get('ocena_czastkowa_1'))
        protokol.pytanie_2 = request.form.get('pytanie_2')
        protokol.ocena_czastkowa_2 = safe_float(request.form.get('ocena_czastkowa_2'))
        protokol.pytanie_3 = request.form.get('pytanie_3')
        protokol.ocena_czastkowa_3 = safe_float(request.form.get('ocena_czastkowa_3'))
        
        protokol.ocena_e = safe_float(request.form.get('ocena_e_manual'))
        protokol.ocena_koncowa = safe_float(request.form.get('ocena_k'))
        protokol.ocena_k_slownie = request.form.get('ocena_k_slownie')
        protokol.podpis_przewodniczacego = request.form.get('podpis_przewodniczacego')
        
        try:
            db.session.commit()
            flash('Zapisano protokół (szkic) pomyślnie.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd podczas zapisywania: {str(e)}', 'danger')
            
        return redirect(url_for('uopz.zal8a_protokol', student_id=student.id))

    instytucja_1 = praktyka.zaklad.nazwa if praktyka.zaklad else ''
    okres_1 = ''
    from models import Dokument, DecyzjaZal4a
    zal4a_doc = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4A').first()
    if zal4a_doc:
        d4a = DecyzjaZal4a.query.filter_by(dokument_id=zal4a_doc.id).first()
        if d4a and d4a.wymiar_godzin:
            okres_1 = f"{d4a.wymiar_godzin} godz."

    return render_template('dokumenty/zal8a_protokol.html', student=student, pracownicy=pracownicy, protokol=protokol, instytucja_1=instytucja_1, okres_1=okres_1)
