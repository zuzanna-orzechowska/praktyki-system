from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
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

@dziekanat_bp.route('/weryfikuj_porozumienie/<int:praktyka_id>', methods=['GET', 'POST'])
@login_required
def weryfikuj_porozumienie(praktyka_id):
    from models import Praktyka, Oswiadczenie, Dokument, Porozumienie, Powiadomienie
    from datetime import datetime, date
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
        
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    porozumienie = praktyka.porozumienie
    student = praktyka.student
    
    oswiadczenie = None
    dokument_zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
    if dokument_zal9:
        oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument_zal9.id).first()

    if request.method == 'POST':
        akcja = request.form.get('akcja')
        
        # Save inline form data if provided
        imie = request.form.get('student_imie')
        if imie:
            student.uzytkownik.imie = imie
            
        nazwisko = request.form.get('student_nazwisko')
        if nazwisko:
            if '(' in student.uzytkownik.nazwisko:
                nr_idx = student.uzytkownik.nazwisko.find('(')
                rest = student.uzytkownik.nazwisko[nr_idx:]
                student.uzytkownik.nazwisko = f"{nazwisko} {rest}"
            else:
                student.uzytkownik.nazwisko = nazwisko
                
        data_start = request.form.get('praktyka_data_start')
        if data_start:
            praktyka.data_start = datetime.strptime(data_start, '%Y-%m-%d').date()
            
        data_end = request.form.get('praktyka_data_end')
        if data_end:
            praktyka.data_end = datetime.strptime(data_end, '%Y-%m-%d').date()
            
        liczba_godzin = request.form.get('praktyka_liczba_godzin')
        if liczba_godzin:
            praktyka.liczba_godzin = int(liczba_godzin)
            
        if praktyka.zaklad:
            nazwa = request.form.get('nazwa')
            if nazwa: praktyka.zaklad.nazwa = nazwa
            praktyka.zaklad.nip = request.form.get('nip', praktyka.zaklad.nip)
            praktyka.zaklad.kod_pocztowy = request.form.get('kod_pocztowy', praktyka.zaklad.kod_pocztowy)
            praktyka.zaklad.miasto = request.form.get('miasto', praktyka.zaklad.miasto)
            praktyka.zaklad.ulica = request.form.get('ulica', praktyka.zaklad.ulica)
            praktyka.zaklad.nr_budynku = request.form.get('nr_budynku', praktyka.zaklad.nr_budynku)
            praktyka.zaklad.nr_lokalu = request.form.get('nr_lokalu', praktyka.zaklad.nr_lokalu)
            
        if oswiadczenie:
            oswiadczenie.osoba_upowazniona_imie = request.form.get('osoba_upowazniona_imie', oswiadczenie.osoba_upowazniona_imie)
            oswiadczenie.osoba_upowazniona_nazwisko = request.form.get('osoba_upowazniona_nazwisko', oswiadczenie.osoba_upowazniona_nazwisko)
            oswiadczenie.osoba_upowazniona_stanowisko = request.form.get('osoba_upowazniona_stanowisko', oswiadczenie.osoba_upowazniona_stanowisko)

        if akcja == 'zapisz':
            db.session.commit()
            flash('Zmiany w dokumencie zostały zapisane.', 'success')
            
        elif akcja == 'akceptuj_dyrektor' and current_user.rola == 'dyrektor':
            if request.form.get('generateSignatureDyrektor'):
                if not porozumienie:
                    porozumienie = Porozumienie(praktyka_id=praktyka.id, zaklad_id=praktyka.zaklad_id, status='ZaakceptowaneDyrektor')
                    db.session.add(porozumienie)
                else:
                    porozumienie.status = 'ZaakceptowaneDyrektor'
                
                tytul = f"{current_user.tytul_naukowy} " if current_user.tytul_naukowy else ""
                porozumienie.podpisal_dziekanat = f"{tytul}{current_user.imie} {current_user.nazwisko}"
                porozumienie.data_podpisania = date.today()
                
                db.session.commit()
                flash('Porozumienie zaakceptowane i podpisane przez Dyrektora.', 'success')
            else:
                flash('Wymagane jest zaznaczenie pola z podpisem elektronicznym.', 'danger')

        elif akcja == 'wyslij_zopz':
            if porozumienie and porozumienie.status == 'ZaakceptowaneDyrektor':
                porozumienie.status = 'OczekujeZOPZ'
                porozumienie.komentarz_zopz = None
                
                if praktyka.zaklad and praktyka.zaklad.zopz_id:
                    from models import Powiadomienie
                    powiadomienie = Powiadomienie(
                        uzytkownik_id=praktyka.zaklad.zopz_id,
                        tresc=f"Dziekanat przekazał Porozumienie i Program Praktyki studenta {student.uzytkownik.imie} {student.uzytkownik.nazwisko} do Twojej weryfikacji.",
                        link=url_for('zopz.porozumienie', id=porozumienie.id)
                    )
                    db.session.add(powiadomienie)
                    
                db.session.commit()
                flash('Porozumienie wysłane do ZOPZ.', 'success')
            else:
                flash('Porozumienie musi zostać najpierw zaakceptowane przez Dyrektora.', 'danger')

        elif akcja == 'przekaz_dyrektorowi':
            if porozumienie and porozumienie.status == 'UwagiZOPZ':
                porozumienie.status = 'Draft'
                db.session.commit()
                flash('Dokument przekazany do ponownej akceptacji Dyrektora.', 'success')
                
        elif akcja == 'podpisz_ostatecznie':
            if porozumienie and porozumienie.status == 'ZatwierdzoneZOPZ':
                porozumienie.status = 'Podpisane'
                if not porozumienie.data_podpisania:
                    porozumienie.data_podpisania = date.today()
                db.session.commit()
                flash('Porozumienie zostało ostatecznie zatwierdzone i podpisane.', 'success')
        
        return redirect(url_for('dziekanat.weryfikuj_porozumienie', praktyka_id=praktyka.id))

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

@dziekanat_bp.route('/zal7_sprawozdanie/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal7_sprawozdanie(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7').first() if praktyka else None
    sprawozdanie = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first() if dokument else None
    
    if request.method == 'POST' and current_user.rola == 'dyrektor':
        akcja = request.form.get('akcja')
        dokument.uwagi_dyrektora = request.form.get('uwagi_dyrektora')
        
        if not request.form.get('generateSignatureDyrektor'):
            flash('Złożenie podpisu cyfrowego jest wymagane!', 'danger')
            return redirect(url_for('dziekanat.zal7_sprawozdanie', student_id=student.id))
            
        if akcja == 'zatwierdz':
            dokument.status = 'Approved'
            sprawozdanie.podpis_dyrektora = f"{current_user.imie} {current_user.nazwisko}"
            from models import Powiadomienie
            notif = Powiadomienie(uzytkownik_id=student.uzytkownik.id, tresc="Dyrektor zaakceptował Twoje Sprawozdanie (Zał. 7).", link="/student/zal7_sprawozdanie")
            db.session.add(notif)
            db.session.commit()
            flash('Sprawozdanie zatwierdzone przez Dyrektora.', 'success')
        elif akcja == 'odrzuc':
            dokument.status = 'Rejected'
            sprawozdanie.podpis_dyrektora = f"{current_user.imie} {current_user.nazwisko}"
            from models import Powiadomienie
            notif = Powiadomienie(uzytkownik_id=student.uzytkownik.id, tresc="Dyrektor odrzucił Twoje Sprawozdanie (Zał. 7) do poprawy.", link="/student/zal7_sprawozdanie")
            db.session.add(notif)
            db.session.commit()
            flash('Sprawozdanie odrzucone przez Dyrektora do poprawy.', 'warning')
        return redirect(url_for('dziekanat.zal7_lista'))
        
    return render_template('dokumenty/zal7_sprawozdanie.html', student=student, praktyka=praktyka, dokument=dokument, sprawozdanie=sprawozdanie)

@dziekanat_bp.route('/zal7a_sprawozdanie/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal7a_sprawozdanie(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A').first() if praktyka else None
    sprawozdanie = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first() if dokument else None
    
    if request.method == 'POST':
        akcja = request.form.get('akcja')
        
        if current_user.rola == 'dyrektor':
            if not request.form.get('generateSignatureDyrektor'):
                flash('Złożenie podpisu cyfrowego jest wymagane!', 'danger')
                return redirect(url_for('dziekanat.zal7a_sprawozdanie', student_id=student.id))
                
            dokument.uwagi_dyrektora = request.form.get('uwagi_dyrektora')
            if akcja == 'zatwierdz':
                dokument.status = 'Approved'
                sprawozdanie.podpis_dyrektora = f"{current_user.imie} {current_user.nazwisko}"
                from models import Powiadomienie
                notif = Powiadomienie(uzytkownik_id=student.uzytkownik.id, tresc="Dyrektor zaakceptował Twoje Sprawozdanie (Zał. 7a).", link="/student/zal7a_sprawozdanie")
                db.session.add(notif)
                db.session.commit()
                flash('Zatwierdzono sprawozdanie.', 'success')
            elif akcja == 'odrzuc':
                dokument.status = 'Rejected'
                sprawozdanie.podpis_dyrektora = f"{current_user.imie} {current_user.nazwisko}"
                from models import Powiadomienie
                notif = Powiadomienie(uzytkownik_id=student.uzytkownik.id, tresc="Dyrektor odrzucił Twoje Sprawozdanie (Zał. 7a) do poprawy.", link="/student/zal7a_sprawozdanie")
                db.session.add(notif)
                db.session.commit()
                flash('Odrzucono sprawozdanie do poprawy.', 'warning')
            return redirect(url_for('dziekanat.zal7_lista'))
        else:
            dokument.uwagi_opiekuna = request.form.get('uwagi_opiekuna')
            if akcja == 'zatwierdz_i_podpisz':
                dokument.status = 'Approved'
                sprawozdanie.podpis_uopz = f"{current_user.imie} {current_user.nazwisko}"
                db.session.commit()
                flash('Zatwierdzono sprawozdanie.', 'success')
            elif akcja == 'odrzuc':
                dokument.status = 'Rejected'
                db.session.commit()
                flash('Odrzucono sprawozdanie do poprawy.', 'warning')
            return redirect(url_for('dziekanat.zal7_lista'))
        
    return render_template('dokumenty/zal7a_sprawozdanie.html', student=student, praktyka=praktyka, dokument=dokument, sprawozdanie=sprawozdanie)

@dziekanat_bp.route('/dziennik/<int:student_id>')
@login_required
def podglad_dziennika(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    return render_template('dziekanat/podglad_dziennika.html')

@dziekanat_bp.route('/zal4b_lista')
@login_required
def zal4b_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
    return render_template('dziekanat/zal4b_lista.html')

@dziekanat_bp.route('/weryfikuj_zal4b/<int:praktyka_id>')
@login_required
def weryfikuj_zal4b(praktyka_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
    return render_template('dziekanat/weryfikuj_zal4b.html', praktyka_id=praktyka_id)

@dziekanat_bp.route('/zal4a_lista')
@login_required
def zal4a_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    
    # Lista praktyk, które mają zatwierdzone ZAL4B, więc można do nich stworzyć ZAL4A
    praktyki = Praktyka.query.filter(Praktyka.status == 'ZAL4B_ZATWIERDZONE').all()
    # Dodatkowo te, które już mają ZAL4A w bazie
    praktyki_z_4a = Praktyka.query.join(Dokument).filter(Dokument.typ_zalacznika == 'ZAL4A').all()
    
    wszystkie = set(praktyki + praktyki_z_4a)
    
    do_oceny = []
    zatwierdzone = []
    
    for p in wszystkie:
        doc = Dokument.query.filter_by(praktyka_id=p.id, typ_zalacznika='ZAL4A').first()
        item = {
            'student_id': p.student.id,
            'imie': p.student.uzytkownik.imie,
            'nazwisko': p.student.uzytkownik.nazwisko,
            'nr_albumu': p.student.nr_albumu,
            'status': doc.status if doc and doc.status != 'Draft' else ('Szkic decyzji' if doc and doc.status == 'Draft' else 'Oczekuje na decyzję'),
            'data': doc.updated_at.strftime('%Y-%m-%d %H:%M') if doc else '-'
        }
        if doc and doc.status == 'Zatwierdzony':
            zatwierdzone.append(item)
        else:
            do_oceny.append(item)
            
    return render_template('dziekanat/zal4a_lista.html', do_oceny=do_oceny, zatwierdzone=zatwierdzone)

@dziekanat_bp.route('/weryfikuj_zal4a/<int:student_id>', methods=['GET', 'POST'])
@login_required
def weryfikuj_zal4a(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4A').first() if praktyka else None
    
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL4A', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()
    
    from models import EfektUczenia, DecyzjaZal4a
    from datetime import date
    
    decyzja = DecyzjaZal4a.query.filter_by(dokument_id=dokument.id).first()
    if not decyzja:
        decyzja = DecyzjaZal4a(dokument_id=dokument.id)
        db.session.add(decyzja)
        db.session.commit()
    
    if request.method == 'POST':
        akcja = request.form.get('akcja')
        komentarz = request.form.get('komentarz')
        dokument.komentarz = komentarz
        
        decyzja.rodzaj_zaliczenia = request.form.get('rodzaj_zaliczenia')
        wymiar_godzin = request.form.get('wymiar_godzin')
        if wymiar_godzin:
            decyzja.wymiar_godzin = int(wymiar_godzin)
        decyzja.ogolny_wynik = request.form.get('ogolny_wynik')
            
        podpis = request.form.get('podpis_dyrektora')
        if podpis == '1' and current_user.rola == 'dyrektor':
            decyzja.podpis_dyrektora = f"{current_user.imie} {current_user.nazwisko}"
            decyzja.data_podpisania = date.today()
        
        from blueprints.student import lista_wymaganych_efektow
        for i, efekt in enumerate(lista_wymaganych_efektow):
            kod = f"{i+1:02d}"
            ocena = request.form.get(f'ocena_{kod}')
            if ocena:
                efekt_obj = EfektUczenia.query.filter_by(dokument_id=dokument.id, kod_efektu=kod).first()
                if not efekt_obj:
                    efekt_obj = EfektUczenia(dokument_id=dokument.id, kod_efektu=kod, opis_efektu=efekt)
                    db.session.add(efekt_obj)
                efekt_obj.uzyskany = int(ocena)
        
        if akcja == 'zatwierdz' and current_user.rola == 'dyrektor':
            dokument.status = 'Zatwierdzony'
            dokument.uwagi_opiekuna = f"Podpisano przez: {current_user.imie} {current_user.nazwisko}"
            
            if decyzja.ogolny_wynik == 'nie uzyskał/a':
                zal4b = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4B').first()
                if zal4b:
                    zal4b.status = 'Rejected'
                    zal4b.komentarz = "Dyrektor wydał decyzję negatywną (nie uzyskał/a). Ścieżka zaliczenia na podstawie pracy została odrzucona."
                
                praktyka.status = 'BRAK_ZGŁOSZENIA'
                
                from models import Powiadomienie
                notif_s = Powiadomienie(
                    uzytkownik_id=student.uzytkownik.id,
                    tresc="Dyrektor wydał decyzję NEGATYWNĄ (Zał. 4a). Twoja ścieżka zawodowa została odrzucona. Wybierz ścieżkę od nowa na pulpicie.",
                    link=f"/student/dashboard"
                )
                db.session.add(notif_s)
                flash('Decyzja została zatwierdzona. Z powodu oceny "nie uzyskał/a", wniosek został automatycznie odrzucony, a student cofnięty do wyboru ścieżki.', 'success')
            else:
                flash('Decyzja została zatwierdzona.', 'success')
        elif akcja == 'zwroc_do_uzupelnienia':
            dokument.status = 'Returned'
            zal4b = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4B').first()
            if zal4b:
                zal4b.status = 'Returned'
                zal4b.komentarz = komentarz
            
            from models import Powiadomienie
            notif = Powiadomienie(
                uzytkownik_id=student.uzytkownik_id,
                tresc=f"Decyzja Dyrektora (Zał. 4a) wymaga uzupełnień w Załączniku 4b.",
                link=f"/student/zal4b_wniosek"
            )
            db.session.add(notif)
            flash('Zwrócono wniosek do uzupełnienia przez studenta.', 'warning')
        else:
            dokument.status = 'Draft'
            flash('Zmiany zostały zapisane.', 'info')
            
        db.session.commit()
        return redirect(url_for('dziekanat.weryfikuj_zal4a', student_id=student.id))
        
    efekty = EfektUczenia.query.filter_by(dokument_id=dokument.id).order_by(EfektUczenia.kod_efektu).all() if dokument else []
    
    from blueprints.student import lista_wymaganych_efektow
    
    return render_template('dziekanat/weryfikuj_zal4a.html', 
                           student=student, 
                           praktyka=praktyka, 
                           dokument=dokument, 
                           efekty=efekty, 
                           decyzja=decyzja,
                           lista_statyczna=lista_wymaganych_efektow)


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

@dziekanat_bp.route('/ankiety')
@login_required
def ankiety_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    from models import Ankieta
    import json
    ankiety_z_bazy = Ankieta.query.order_by(Ankieta.data_utworzenia.desc()).all()
    
    ankiety_parsed = []
    for a in ankiety_z_bazy:
        odp = []
        try:
            odp = json.loads(a.odpowiedzi)
        except:
            pass
            
        suma = 0
        ilosc = 0
        for o in odp:
            if o > 0:
                suma += o
                ilosc += 1
        srednia = round(suma/ilosc, 2) if ilosc > 0 else 0
        
        ankiety_parsed.append({
            'id': a.id,
            'rok': a.rok_akademicki,
            'semestr': a.semestr,
            'forma': a.forma_studiow,
            'srednia': srednia,
            'uwagi': a.uwagi,
            'data': a.data_utworzenia.strftime('%Y-%m-%d %H:%M')
        })
        
    return render_template('dziekanat/ankiety_lista.html', ankiety=ankiety_parsed)

@dziekanat_bp.route('/ankiety/<int:id>')
@login_required
def ankieta_szczegoly(id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
        
    from models import Ankieta
    import json
    
    ankieta = Ankieta.query.get_or_404(id)
    odpowiedzi = []
    try:
        odpowiedzi = json.loads(ankieta.odpowiedzi)
    except:
        pass
        
    pytania = [
        "Poznałam/poznałem zasady funkcjonowania instytucji, w której odbywałam/odbywałem praktyki zawodowe.",
        "Poznałam/poznałem strukturę oraz regulamin organizacyjny instytucji, w której odbywałam/odbywałem praktyki zawodowe.",
        "Praktyki zawodowe umożliwiły mi pełną realizację ramowego programu praktyk zawodowych przewidzianego w ramach mojego kierunku studiów.",
        "Podczas praktyk zawodowych zwracano uwagę na przestrzeganie zasad etyki i tajemnicy zawodowej.",
        "Podczas praktyk miałam/miałem możliwość praktycznego zastosowania wiedzy teoretycznej zdobytej na zajęciach.",
        "Praktyki zawodowe przyczyniły się do pogłębienia mojej wiedzy i umiejętności zdobytych w trakcie studiów.",
        "Mogłem liczyć na wsparcie merytoryczne Opiekuna zakładowego praktyk.",
        "Mogłem liczyć na wsparcie merytoryczne Opiekuna uczelnianego praktyk.",
        "Opiekun zakładowy odpowiedzialny za praktyki zawodowe w miejscu ich odbywania potrafił prawidłowo zorganizować ich przebieg.",
        "Podczas praktyk zawodowych miałam/miałem możliwość pozyskiwania materiałów niezbędnych do przygotowania mojej pracy dyplomowej.",
        "Praktyki zawodowe rozwinęły moje umiejętności skutecznego komunikowania się w sytuacjach zawodowych i pracy w zespole.",
        "Praktyki zawodowe nauczyły mnie samodzielności i odpowiedzialności podczas wykonywania pracy.",
        "Liczba godzin realizowana w ramach praktyk zawodowych jest wystarczająca.",
        "Czy po zakończeniu praktyki zawodowej chciałaby/chciałby Pani/Pan współpracować z instytucją, w której Pani/Pan zrealizowała/zrealizował praktykę?"
    ]
    
    wyniki = []
    for idx, pyt in enumerate(pytania):
        odp_val = odpowiedzi[idx] if idx < len(odpowiedzi) else 0
        wyniki.append({
            'numer': idx + 1,
            'pytanie': pyt,
            'ocena': odp_val
        })
        
    return render_template('dziekanat/ankieta_szczegoly.html', ankieta=ankieta, wyniki=wyniki)

@dziekanat_bp.route('/zal8_lista')
@login_required
def zal8_lista():
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    from models import Student
    studenci = Student.query.all()
    return render_template('dziekanat/zal8_lista.html', studenci=studenci)

@dziekanat_bp.route('/zal8_protokol/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal8_protokol(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    from models import Student, Praktyka, Dokument, KartaPraktyki, Protokol, Uzytkownik
    from datetime import datetime
    
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka:
        flash('Student nie ma przypisanej praktyki.', 'warning')
        return redirect(url_for('dziekanat.zal8_lista'))

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
                
        protokol.przewodniczacy = request.form.get('przewodniczacy')
        protokol.komisja_2 = request.form.get('komisja_2')
        protokol.komisja_3 = request.form.get('komisja_3')
        protokol.rola_3 = request.form.get('rola_3')
        protokol.komisja_4 = request.form.get('komisja_4')
        protokol.rola_4 = request.form.get('rola_4')
        
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
            
        return redirect(url_for('dziekanat.zal8_protokol', student_id=student.id))
        
    return render_template('dokumenty/zal8_protokol.html', student=student, karta=karta, pracownicy=pracownicy, protokol=protokol)

@dziekanat_bp.route('/zal8a_protokol/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal8a_protokol(student_id):
    if current_user.rola not in ['dziekanat', 'dyrektor']:
        return redirect(url_for('index'))
    from models import Student, Praktyka, Protokol, Uzytkownik, Powiadomienie
    from datetime import datetime
    
    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka:
        flash('Student nie ma przypisanej praktyki.', 'warning')
        return redirect(url_for('dziekanat.zal8_lista'))

    pracownicy = Uzytkownik.query.filter(Uzytkownik.rola.in_(['pracownik', 'uopz', 'dziekanat', 'dyrektor'])).all()
    protokol = Protokol.query.filter_by(praktyka_id=praktyka.id).first()

    if request.method == 'POST':
        akcja = request.form.get('akcja')
        if not protokol:
            protokol = Protokol(praktyka_id=praktyka.id)
            db.session.add(protokol)
            
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
        protokol.podpis_opiekuna_s = request.form.get('podpis_opiekuna_s')
        
        data_egz = request.form.get('data_egzaminu')
        if data_egz:
            try:
                protokol.data_egzaminu = datetime.strptime(data_egz, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        protokol.przewodniczacy = request.form.get('przewodniczacy')
        protokol.komisja_2 = request.form.get('komisja_2')
        protokol.komisja_3 = request.form.get('komisja_3')
        protokol.rola_3 = request.form.get('rola_3')
        protokol.komisja_4 = request.form.get('komisja_4')
        protokol.rola_4 = request.form.get('rola_4')
        
        protokol.pytanie_1 = request.form.get('pytanie_1')
        protokol.ocena_czastkowa_1 = safe_float(request.form.get('ocena_czastkowa_1'))
        protokol.pytanie_2 = request.form.get('pytanie_2')
        protokol.ocena_czastkowa_2 = safe_float(request.form.get('ocena_czastkowa_2'))
        protokol.pytanie_3 = request.form.get('pytanie_3')
        protokol.ocena_czastkowa_3 = safe_float(request.form.get('ocena_czastkowa_3'))
        
        protokol.ocena_e = safe_float(request.form.get('ocena_e_manual'))
        protokol.ocena_koncowa = safe_float(request.form.get('ocena_k'))
        protokol.ocena_k_slownie = request.form.get('ocena_k_slownie')
        
        if request.form.get('generateSignatureDyrektor'):
            protokol.podpis_przewodniczacego = f"[Podpis elektroniczny Przewodniczący: {current_user.tytul_naukowy or ''} {current_user.imie} {current_user.nazwisko}, Data: {datetime.today().strftime('%d.%m.%Y')}]"
        elif request.form.get('podpis_przewodniczacego') is not None:
            protokol.podpis_przewodniczacego = request.form.get('podpis_przewodniczacego')
        
        try:
            if akcja == 'zakoncz':
                if not protokol.podpis_opiekuna_s:
                    flash('Nie można zatwierdzić: Brak podpisu UOPZ na protokole.', 'danger')
                    return redirect(url_for('dziekanat.zal8a_protokol', student_id=student.id))
                if protokol.ocena_koncowa is None or protokol.ocena_e is None or protokol.ocena_s is None:
                    flash('Nie można zatwierdzić: Wszystkie oceny (S, E, Końcowa) muszą być wystawione.', 'danger')
                    return redirect(url_for('dziekanat.zal8a_protokol', student_id=student.id))
                if not protokol.podpis_przewodniczacego:
                    flash('Nie można zatwierdzić: Brak podpisu Przewodniczącego Komisji.', 'danger')
                    return redirect(url_for('dziekanat.zal8a_protokol', student_id=student.id))

                praktyka.status = 'ZALICZONA'
                notif = Powiadomienie(
                    uzytkownik_id=student.uzytkownik_id,
                    tresc="Gratulacje! Twoja praktyka została ostatecznie ZALICZONA na podstawie protokołu komisji egzaminacyjnej.",
                    link=url_for('student.dashboard')
                )
                db.session.add(notif)
                flash('Praktyka została pomyślnie zaliczona i zakończona!', 'success')
            else:
                flash('Zapisano protokół (szkic) pomyślnie.', 'success')
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd podczas zapisywania: {str(e)}', 'danger')
            
        return redirect(url_for('dziekanat.zal8a_protokol', student_id=student.id))
        
    instytucja_1 = praktyka.zaklad.nazwa if praktyka.zaklad else ''
    okres_1 = ''
    from models import Dokument, DecyzjaZal4a
    zal4a_doc = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4A').first()
    if zal4a_doc:
        d4a = DecyzjaZal4a.query.filter_by(dokument_id=zal4a_doc.id).first()
        if d4a and d4a.wymiar_godzin:
            okres_1 = f"{d4a.wymiar_godzin} godz."

    return render_template('dokumenty/zal8a_protokol.html', student=student, pracownicy=pracownicy, protokol=protokol, instytucja_1=instytucja_1, okres_1=okres_1)
