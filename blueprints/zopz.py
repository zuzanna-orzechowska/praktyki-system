from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Student, Praktyka, Dokument, Sprawozdanie, db, Powiadomienie, Porozumienie, Oswiadczenie
from datetime import datetime

zopz_bp = Blueprint('zopz', __name__, url_prefix='/zopz')

@zopz_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'zopz':
        flash('Brak dostępu. Ten panel jest przeznaczony dla opiekunów zakładowych.', 'danger')
        return redirect(url_for('index'))

    return render_template('zopz/dashboard.html')

@zopz_bp.route('/porozumienie/<int:id>')
@login_required
def porozumienie(id):
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))

    porozumienie_doc = Porozumienie.query.get_or_404(id)
    if porozumienie_doc.zaklad.zopz_id != current_user.id:
        flash('Odmowa dostępu do tego porozumienia.', 'danger')
        return redirect(url_for('zopz.dashboard'))

    praktyka = porozumienie_doc.praktyka
    student = praktyka.student
    
    oswiadczenie = None
    dokument_zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
    if dokument_zal9:
        oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument_zal9.id).first()

    return render_template(
        'zopz/weryfikuj_porozumienie.html',
        student=student,
        praktyka=praktyka,
        porozumienie=porozumienie_doc,
        oswiadczenie=oswiadczenie,
        current_date=datetime.today().date()
    )

@zopz_bp.route('/zal2a_harmonogram/<int:student_id>')
@login_required
def zal2a_harmonogram(student_id):
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
    return render_template('zopz/zal2a_harmonogram.html')

@zopz_bp.route('/teczka/<int:student_id>')
@login_required
def teczka(student_id):
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
    return render_template('zopz/teczka.html')

@zopz_bp.route('/zal3_karta/<int:student_id>')
@login_required
def zal3_karta(student_id):
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
    return render_template('zopz/zal3_karta.html')

@zopz_bp.route('/zal3_lista')
@login_required
def zal3_lista():
    if current_user.rola != 'zopz': return redirect(url_for('index'))
    return render_template('zopz/zal3_lista.html')

@zopz_bp.route('/dziennik/<int:student_id>')
@login_required
def weryfikuj_dziennik(student_id):
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
    return render_template('zopz/weryfikuj_dziennik.html')

@zopz_bp.route('/zal7_sprawozdanie/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal7_sprawozdanie(student_id):
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
    
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka or praktyka.zaklad.zopz_id != current_user.id:
        flash('Odmowa dostępu. Ten student nie jest przypisany do twojej firmy.', 'danger')
        return redirect(url_for('zopz.teczka', student_id=student.id))
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7').first()
    sprawozdanie_doc = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first() if dokument else None
    
    if request.method == 'POST':
        if not dokument or dokument.status not in ['OczekujeZOPZ', 'Weryfikacja']:
            flash('Dokument nie jest obecnie w fazie weryfikacji przez ZOPZ.', 'danger')
            return redirect(url_for('zopz.zal7_sprawozdanie', student_id=student_id))
            
        akcja = request.form.get('akcja')
        uwagi = request.form.get('uwagi_zopz', '').strip()
        
        if akcja == 'odrzuc':
            if not uwagi:
                flash('Musisz podać powód odrzucenia sprawozdania.', 'danger')
            else:
                dokument.status = 'Draft'
                if sprawozdanie_doc:
                    sprawozdanie_doc.uwagi_zopz = uwagi
                db.session.commit()
                
                powiadomienie_student = Powiadomienie(
                    uzytkownik_id=student.uzytkownik_id,
                    tresc=f"Twoje Sprawozdanie (Zał. 7) zostało odrzucone do poprawy przez ZOPZ. Powód: {uwagi}",
                    link=url_for('student.sprawozdanie')
                )
                db.session.add(powiadomienie_student)
                db.session.commit()
                
                flash('Sprawozdanie zostało odrzucone do poprawy.', 'success')
                return redirect(url_for('zopz.teczka', student_id=student_id))
                
        elif akcja == 'zatwierdz':
            dokument.status = 'Weryfikacja UOPZ'
            if sprawozdanie_doc:
                sprawozdanie_doc.uwagi_zopz = uwagi
                sprawozdanie_doc.podpis_zopz = f"{current_user.imie} {current_user.nazwisko}"
            db.session.commit()
            
            powiadomienie_student = Powiadomienie(
                uzytkownik_id=student.uzytkownik_id,
                tresc=f"ZOPZ zatwierdził Twoje Sprawozdanie (Zał. 7). Dokument został przesłany do UOPZ.",
                link=url_for('student.sprawozdanie')
            )
            db.session.add(powiadomienie_student)
            
            if praktyka.uopz_id:
                powiadomienie_uopz = Powiadomienie(
                    uzytkownik_id=praktyka.uopz_id,
                    tresc=f"ZOPZ zatwierdził Sprawozdanie (Zał. 7) studenta {student.uzytkownik.imie} {student.uzytkownik.nazwisko}. Dokument oczekuje na weryfikację.",
                    link=url_for('uopz.teczka', student_id=student.id)
                )
                db.session.add(powiadomienie_uopz)
                
            db.session.commit()
            
            flash('Sprawozdanie zatwierdzone i podpisane.', 'success')
            return redirect(url_for('zopz.teczka', student_id=student_id))

    return render_template('dokumenty/zal7_sprawozdanie.html', 
                           student=student, 
                           dokument=dokument, 
                           sprawozdanie=sprawozdanie_doc,
                           praktyka=praktyka)

@zopz_bp.route('/zal4_efekty/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal4_efekty(student_id):
    if current_user.rola != 'zopz':
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
        
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka or praktyka.zaklad.zopz_id != current_user.id:
        flash('Odmowa dostępu.', 'danger')
        return redirect(url_for('zopz.dashboard'))
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL4', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()
        
    Powiadomienie.query.filter_by(uzytkownik_id=current_user.id, link=request.path, przeczytane=False).update({'przeczytane': True})
    db.session.commit()
        
    from models import EfektUczenia
    efekty = EfektUczenia.query.filter_by(dokument_id=dokument.id).order_by(EfektUczenia.kod_efektu).all()
    
    from blueprints.student import lista_wymaganych_efektow
    
    if request.method == 'POST':
        akcja = request.form.get('akcja')
        if akcja == 'zapisz_zopz':
            podpis = f"{current_user.imie} {current_user.nazwisko}" if request.form.get('podpis_zopz') else None
            liczba_efektow = int(request.form.get('liczba_efektow', 0))
            
            if not efekty:
                for i in range(1, liczba_efektow + 1):
                    kod = request.form.get(f'kod_efektu_{i}')
                    opis = request.form.get(f'opis_efektu_{i}')
                    uzyskany = int(request.form.get(f'efekt_{i}', 0))
                    
                    if kod and opis:
                        nowy_efekt = EfektUczenia(
                            dokument_id=dokument.id,
                            kod_efektu=kod,
                            opis_efektu=opis,
                            uzyskany=uzyskany,
                            podpis_zopz=podpis,
                            data_podpisu=datetime.today().date() if podpis else None
                        )
                        db.session.add(nowy_efekt)
            else:
                for i, efekt in enumerate(efekty, 1):
                    uzyskany = int(request.form.get(f'efekt_{i}', 0))
                    efekt.uzyskany = uzyskany
                    efekt.podpis_zopz = podpis
                    if podpis:
                        efekt.data_podpisu = datetime.today().date()
            
            ogolny_wynik = int(request.form.get('ogolny_wynik', 0))
            
            dokument.status = 'Weryfikacja UOPZ'
            db.session.commit()
            
            powiadomienie_student = Powiadomienie(
                uzytkownik_id=student.uzytkownik_id,
                tresc="ZOPZ ocenił i podpisał Twoje efekty uczenia się (Zał. 4). Dokument przesłany do UOPZ.",
                link=url_for('student.zal4_efekty')
            )
            db.session.add(powiadomienie_student)
            
            if praktyka.uopz_id:
                powiadomienie_uopz = Powiadomienie(
                    uzytkownik_id=praktyka.uopz_id,
                    tresc=f"ZOPZ zatwierdził efekty uczenia się studenta {student.uzytkownik.imie} {student.uzytkownik.nazwisko} (Zał. 4). Dokument oczekuje na Twoją opinię.",
                    link=url_for('uopz.teczka', student_id=student.id)
                )
                db.session.add(powiadomienie_uopz)
                
            db.session.commit()
            flash('Efekty uczenia się zostały ocenione i podpisane.', 'success')
            return redirect(url_for('zopz.teczka', student_id=student_id))

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