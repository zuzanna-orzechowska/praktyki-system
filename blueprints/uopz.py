from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Uzytkownik, Student, Praktyka, Dokument, Protokol, HarmonogramPraktyki, ProgramPraktyki, Porozumienie

uopz_bp = Blueprint('uopz', __name__, url_prefix='/uopz')

@uopz_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola != 'uopz':
        flash('Odmowa dostępu. Strona tylko dla Uczelnianych Opiekunów Praktyk.', 'danger')
        return redirect(url_for('index'))

    praktyki = Praktyka.query.filter_by(uopz_id=current_user.id).all()

    return render_template('uopz/dashboard.html', praktyki=praktyki)

@uopz_bp.route('/teczka/<int:student_id>')
@login_required
def teczka(student_id):
    if current_user.rola != 'uopz':
        return redirect(url_for('index'))

    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id, uopz_id=current_user.id).first()

    if not praktyka:
        flash('Brak dostępu do tego studenta lub brak przypisanej praktyki.', 'danger')
        return redirect(url_for('uopz.dashboard'))

    dokumenty = Dokument.query.filter_by(praktyka_id=praktyka.id).all()
    dok_dict = {d.typ_zalacznika: d for d in dokumenty}

    return render_template('uopz/teczka.html', student=student, praktyka=praktyka, dokumenty=dok_dict)

@uopz_bp.route('/zal3_karta/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal3_karta(student_id):
    if current_user.rola != 'uopz':
        return redirect(url_for('index'))

    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki dla tego studenta.', 'danger')
        return redirect(url_for('uopz.dashboard'))

    protokol = Protokol.query.filter_by(praktyka_id=praktyka.id).first()
    porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
    zopz = Uzytkownik.query.get(praktyka.zaklad.zopz_id) if praktyka.zaklad and praktyka.zaklad.zopz_id else None

    if request.method == 'POST':
        akcja = request.form.get('akcja')
        
        if akcja == 'wydaj_skierowanie':
            praktyka.status = 'SKIEROWANIE_WYDANE'
            db.session.commit()
            flash('Skierowanie zostało oficjalnie wydane.', 'success')
            
        elif akcja == 'zapisz_ocene':
            if not protokol:
                protokol = Protokol(praktyka_id=praktyka.id)
                db.session.add(protokol)
            
            try:
                ocena_u_val = request.form.get('ocena_u')
                ocena_s_val = request.form.get('ocena_s')
                if ocena_u_val: protokol.ocena_u = float(ocena_u_val)
                if ocena_s_val: protokol.ocena_s = float(ocena_s_val)
                db.session.commit()
                flash('Oceny UOPZ zostały zapisane w Karcie Praktyki.', 'success')
            except ValueError:
                flash('Wprowadzono niepoprawny format oceny. Użyj formatu liczbowego (np. 4.5).', 'danger')

        return redirect(url_for('uopz.zal3_karta', student_id=student_id))

    return render_template(
        'dokumenty/zal3_karta.html', 
        student=student, 
        praktyka=praktyka, 
        uopz=current_user, 
        zopz=zopz,
        porozumienie=porozumienie, 
        protokol=protokol
    )

@uopz_bp.route('/zal2a_harmonogram/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal2a_harmonogram(student_id):
    if current_user.rola != 'uopz':
        return redirect(url_for('index'))

    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()

    if not praktyka:
        flash('Brak przypisanej praktyki dla tego studenta.', 'warning')
        return redirect(url_for('uopz.dashboard'))

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL2A').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL2A', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    if request.method == 'POST':
        if request.form.get('akcja') == 'zapisz':
            ProgramPraktyki.query.filter_by(dokument_id=dokument.id).delete()
            for i in range(1, 14):
                kod = f"{i:02d}"
                prace = request.form.get(f'prace_{kod}', '')
                nowy_program = ProgramPraktyki(dokument_id=dokument.id, kod_efektu=kod, dzial_prace=prace)
                db.session.add(nowy_program)

            dzialy = request.form.getlist('dzial[]')
            dni = request.form.getlist('dni[]')
            HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).delete()
            for i in range(len(dzialy)):
                if dzialy[i] and dni[i]:
                    nowa_pozycja = HarmonogramPraktyki(
                        dokument_id=dokument.id, lp=i + 1,
                        dzial_komorka=dzialy[i], planowana_liczba_dni=int(dni[i])
                    )
                    db.session.add(nowa_pozycja)
            
            dokument.status = 'Under_Review'
            dokument.uwagi_opiekuna = "" 
            db.session.commit()
            
            flash('Program i Harmonogram został zapisany i wysłany do studenta!', 'success')
            return redirect(url_for('uopz.zal2a_harmonogram', student_id=student.id))

    pozycje_harmonogramu = HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).order_by(HarmonogramPraktyki.lp).all()
    suma_dni = sum(p.planowana_liczba_dni for p in pozycje_harmonogramu)
    
    zapisane_programy = {p.kod_efektu: p.dzial_prace for p in ProgramPraktyki.query.filter_by(dokument_id=dokument.id).all()}

    efekty_definicje = [
        ("01", "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki..."),
        ("02", "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce"),
        ("03", "Zna ekonomiczne, prawne skutki własnych działań..."),
        ("04", "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka"),
        ("05", "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu..."),
        ("06", "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje..."),
        ("07", "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań..."),
        ("08", "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy..."),
        ("09", "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności..."),
        ("10", "Pracuje w zespole zajmującym się zawodowo branżą IT"),
        ("11", "Przestrzega zasad etyki zawodowej..."),
        ("12", "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje..."),
        ("13", "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej...")
    ]

    return render_template(
        'dokumenty/zal2a_harmonogram.html', 
        student=student, 
        praktyka=praktyka, 
        pozycje=pozycje_harmonogramu, 
        suma_dni=suma_dni, 
        dokument=dokument,
        efekty_definicje=efekty_definicje,
        zapisane_programy=zapisane_programy
    )