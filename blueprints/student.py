from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Student, Praktyka, Dokument, Porozumienie, HarmonogramPraktyki, Uzytkownik, Protokol, Sprawozdanie, EfektUczenia, Ankieta, Oswiadczenie, KartaPraktyki, Powiadomienie
from datetime import datetime
from werkzeug.utils import secure_filename
import re
import json
import os

lista_wymaganych_efektow = [
    "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych",
    "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce",
    "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy",
    "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka",
    "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania, posługując się rozmaitymi źródłami literaturowymi i zasobami publikowanymi w języku polskim jak i angielskim",
    "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje, wiedzę i umiejętności, co najmniej z dwóch zakresów: zadania dotyczące sprzętu i oprogramowania: np.: programowania, administrowanie siecią komputerową, konserwacja sprzętu i oprogramowania, bieżące usuwanie usterek, administrowanie zasobami informatycznymi, zakładu pracy / instytucji, (e)-usługami.",
    "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia",
    "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy / instytucji, opisać go, przedstawić koncepcję rozwiązania i ją zrealizować.",
    "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności informatycznej zakładu pracy/instytucji stosując normy i standardy stosowane w informatyce oraz biorąc pod uwagę aspekty środowiskowe i etyczne.",
    "Pracuje w zespole zajmującym się zawodowo branżą IT,",
    "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów",
    "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje do realizacji planowanego zadania, jak i przekazać im w sposób zrozumiały informacje i opinie z zakresu informatyki",
    "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki działalności informatyków w szczególności ekonomiczne i społeczne"
]
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
    
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL3').first()
    karta = KartaPraktyki.query.filter_by(dokument_id=dokument.id).first() if dokument else None
    
    zopz = Uzytkownik.query.get(praktyka.zaklad.zopz_id) if praktyka.zaklad and praktyka.zaklad.zopz_id else None

    return render_template(
        'dokumenty/zal3_karta.html', 
        student=student, 
        praktyka=praktyka, 
        uopz=uopz, 
        zopz=zopz,
        porozumienie=porozumienie, 
        karta=karta,
        dokument=dokument
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
        akcja = request.form.get('akcja', 'wyslij')
        charakterystyka = request.form.get('charakterystyka', '').strip()
        opis = request.form.get('opis', '').strip()
        wiedza = request.form.get('wiedza', '').strip()

        if akcja == 'wyslij':
            if len(charakterystyka) < 150 or len(opis) < 300 or len(wiedza) < 300:
                flash('Błąd wysyłania! Niektóre sekcje są zbyt krótkie. Uzupełnij sprawozdanie przed wysłaniem.', 'danger')
                return redirect(url_for('student.sprawozdanie'))

        if not sprawozdanie_doc:
            sprawozdanie_doc = Sprawozdanie(dokument_id=dokument.id)
            db.session.add(sprawozdanie_doc)

        sprawozdanie_doc.charakterystyka = charakterystyka
        sprawozdanie_doc.opis_prac = opis
        sprawozdanie_doc.wiedza_umiejetnosci = wiedza
        
        if akcja == 'wyslij':
            dokument.status = 'OczekujeZOPZ'
            db.session.commit()
            
            if praktyka.zaklad and praktyka.zaklad.zopz_id:
                powiadomienie_zopz = Powiadomienie(
                    uzytkownik_id=praktyka.zaklad.zopz_id,
                    tresc=f"Student {current_user.imie} {current_user.nazwisko} przesłał Sprawozdanie (Zał. 7) do weryfikacji.",
                    link=url_for('zopz.teczka', student_id=student.id)
                )
                db.session.add(powiadomienie_zopz)
                
            if praktyka.uopz_id:
                powiadomienie_uopz = Powiadomienie(
                    uzytkownik_id=praktyka.uopz_id,
                    tresc=f"Student {current_user.imie} {current_user.nazwisko} przesłał Sprawozdanie (Zał. 7) do ZOPZ.",
                    link=url_for('uopz.teczka', student_id=student.id)
                )
                db.session.add(powiadomienie_uopz)
                
            db.session.commit()
            
            flash('Sprawozdanie zapisano i przesłano do weryfikacji ZOPZ!', 'success')
        else:
            dokument.status = 'Draft'
            db.session.commit()
            flash('Szkic sprawozdania został zapisany.', 'info')
            
        return redirect(url_for('student.sprawozdanie'))

    return render_template(
        'dokumenty/zal7_sprawozdanie.html', 
        student=student, 
        praktyka=praktyka, 
        sprawozdanie=sprawozdanie_doc,
        dokument=dokument
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

    # Oznacz powiadomienia jako przeczytane
    Powiadomienie.query.filter_by(uzytkownik_id=current_user.id, link=request.path, przeczytane=False).update({'przeczytane': True})
    db.session.commit()

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4').first()
    efekty = []
    
    if dokument:
        efekty = EfektUczenia.query.filter_by(dokument_id=dokument.id).order_by(EfektUczenia.kod_efektu).all()

    opinia_text = dokument.uwagi_opiekuna if dokument and dokument.uwagi_opiekuna else ''
    podpis_uopz = None
    data_podpisu_uopz = None
    
    if opinia_text:
        match = re.search(r'\[Podpis elektroniczny UOPZ:\s*(.*?),\s*Data:\s*(.*?)\]', opinia_text)
        if match:
            podpis_uopz = match.group(1).strip()
            data_podpisu_uopz = match.group(2).strip()
            opinia_text = opinia_text[:match.start()].strip()

    return render_template(
        'dokumenty/zal4_efekty.html', 
        student=student, 
        praktyka=praktyka, 
        dokument=dokument,
        efekty=efekty,
        lista_statyczna=lista_wymaganych_efektow,
        opinia_text=opinia_text,
        podpis_uopz=podpis_uopz,
        data_podpisu_uopz=data_podpisu_uopz
    )

@student_bp.route('/zal4a_decyzja')
@login_required
def zal4a_decyzja():
    if current_user.rola != 'student': return redirect(url_for('index'))
    return render_template('dokumenty/zal4a_decyzja_student.html', lista_statyczna=lista_wymaganych_efektow)

@student_bp.route('/zal4b_wniosek', methods=['GET'])
@login_required
def zal4b_wniosek():
    if current_user.rola != 'student':
        return redirect(url_for('index'))
    return render_template('dokumenty/zal4b_wniosek_student.html')

@student_bp.route('/zal7a_pdf', methods=['GET'])
@login_required
def zal7a_pdf():
    if current_user.rola != 'student': return redirect(url_for('index'))
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A').first()
    if not dokument:
        flash('Nie znaleziono dokumentu.', 'danger')
        return redirect(url_for('student.zal7a_sprawozdanie'))
        
    sprawozdanie = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first()
    
    from utils.pdf_generator import generate_zal7a_pdf
    from flask import send_file
    
    pdf_buffer = generate_zal7a_pdf(student, praktyka, sprawozdanie)
    
    return send_file(
        pdf_buffer,
        as_attachment=False,
        download_name=f'Zalacznik_7a_{student.nr_albumu}.pdf',
        mimetype='application/pdf'
    )

@student_bp.route('/zal7a_sprawozdanie', methods=['GET', 'POST'])
@login_required
def zal7a_sprawozdanie():
    if current_user.rola != 'student': return redirect(url_for('index'))
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()
        
    sprawozdanie = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first()
    
    if request.method == 'POST':
        akcja = request.form.get('akcja')
        charakterystyka = request.form.get('charakterystyka', '').strip()
        opis = request.form.get('opis', '').strip()
        wiedza = request.form.get('wiedza', '').strip()
        rok_akademicki = request.form.get('rok_akademicki', '').strip()
        miejsce_pracy = request.form.get('miejsce_pracy', '').strip()
        
        if not sprawozdanie:
            sprawozdanie = Sprawozdanie(dokument_id=dokument.id)
            db.session.add(sprawozdanie)
            
        sprawozdanie.charakterystyka = charakterystyka
        sprawozdanie.opis_prac = opis
        sprawozdanie.wiedza_umiejetnosci = wiedza
        
        generate_signature = request.form.get('generateSignature')
        if generate_signature:
            import datetime
            imie_nazwisko = f"{current_user.imie} {current_user.nazwisko.split('(')[0].strip()}"
            dzisiaj = datetime.date.today().strftime('%d.%m.%Y')
            sprawozdanie.podpis_studenta = f"{dzisiaj}   {imie_nazwisko}"
        else:
            sprawozdanie.podpis_studenta = None
        
        if rok_akademicki:
            student.rok_akademicki = rok_akademicki
            
        if miejsce_pracy:
            if not praktyka.zaklad:
                from models import ZakladPracy
                nowy_zaklad = ZakladPracy(nazwa=miejsce_pracy)
                db.session.add(nowy_zaklad)
                db.session.flush()
                praktyka.zaklad_id = nowy_zaklad.id
            else:
                praktyka.zaklad.nazwa = miejsce_pracy
        
        if akcja == 'wyslij':
            if len(charakterystyka) < 50 or len(opis) < 50 or len(wiedza) < 50:
                flash('Błąd wysyłania! Niektóre sekcje są zbyt krótkie.', 'danger')
            else:
                import os
                from werkzeug.utils import secure_filename
                
                plik = request.files.get('skan_pdf')
                if plik and plik.filename != '':
                    filename = secure_filename(f"zal7a_skan_{student.nr_albumu}_{plik.filename}")
                    from flask import current_app
                    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    plik.save(save_path)
                    dokument.plik_path = f"uploads/{filename}"
                
                if not dokument.plik_path:
                    flash('Musisz wgrać zeskanowany dokument z podpisem, aby wysłać go do weryfikacji!', 'danger')
                    return redirect(url_for('student.zal7a_sprawozdanie'))

                dokument.status = 'Weryfikacja Dyrektor'
                db.session.commit()
                
                from models import Uzytkownik, Powiadomienie
                dyrektor = Uzytkownik.query.filter_by(rola='dyrektor').first()
                if dyrektor:
                    notif = Powiadomienie(
                        uzytkownik_id=dyrektor.id,
                        tresc=f"Student {current_user.imie} {current_user.nazwisko} przesłał skan Sprawozdania (Zał. 7a) do oceny.",
                        link=url_for('dziekanat.zal7_lista')
                    )
                    db.session.add(notif)
                    db.session.commit()
                flash('Sprawozdanie przesłane do Dyrektora!', 'success')
                return redirect(url_for('student.dashboard'))
        else:
            import os
            from werkzeug.utils import secure_filename
            plik = request.files.get('skan_pdf')
            if plik and plik.filename != '':
                filename = secure_filename(f"zal7a_skan_{student.nr_albumu}_{plik.filename}")
                from flask import current_app
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                plik.save(save_path)
                dokument.plik_path = f"uploads/{filename}"

            dokument.status = 'Draft'
            db.session.commit()
            flash('Szkic sprawozdania został zapisany.', 'info')
            
    return render_template('dokumenty/zal7a_sprawozdanie_student.html', student=student, praktyka=praktyka, dokument=dokument, sprawozdanie=sprawozdanie)

@student_bp.route('/zal8_protokol')
@login_required
def zal8_protokol():
    if current_user.rola != 'student': return redirect(url_for('index'))
    
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))
        
    zal7 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7').first()
    zal7a = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A').first()
    
    if (not zal7 or zal7.status != 'Approved') and (not zal7a or zal7a.status != 'Approved'):
        flash('Sprawozdanie musi zostać najpierw zatwierdzone przez Dyrektora Instytutu.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    return render_template('dokumenty/zal8_protokol_student.html')

@student_bp.route('/zal8a_protokol')
@login_required
def zal8a_protokol():
    if current_user.rola != 'student': return redirect(url_for('index'))
    
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Brak przypisanej praktyki.', 'warning')
        return redirect(url_for('student.dashboard'))
        
    zal7a = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL7A').first()
    
    if not zal7a or zal7a.status != 'Approved':
        flash('Sprawozdanie (Zał. 7a) musi zostać najpierw zatwierdzone przez Dyrektora Instytutu.', 'danger')
        return redirect(url_for('student.dashboard'))
        
    return render_template('dokumenty/zal8a_protokol_student.html', student=student, protokol=praktyka.protokol, praktyka=praktyka)


@student_bp.route('/zal9_oswiadczenie', methods=['GET'])
@login_required
def zal9_oswiadczenie():
    if current_user.rola != 'student':
        return redirect(url_for('index'))
    return render_template('dokumenty/zal9_oswiadczenie_student.html')

@student_bp.route('/zal5_ankieta', methods=['GET', 'POST'])
@login_required
def zal5_ankieta():
    if current_user.rola != 'student':
        return redirect(url_for('index'))
        
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    
    if not praktyka:
        flash('Nie posiadasz przypisanej praktyki w systemie.', 'warning')
        return redirect(url_for('student.dashboard'))
        
    if praktyka.ankieta_wypelniona:
        flash('Wysłałeś już anonimową ankietę dla tej praktyki. Dziękujemy!', 'info')
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        
        odpowiedzi = []
        for i in range(1, 15):
            val = request.form.get(f'pytanie_{i}', '0')
            odpowiedzi.append(int(val))
            
        nowa_ankieta = Ankieta(
            odpowiedzi=json.dumps(odpowiedzi),
            uwagi=request.form.get('uwagi', ''),
            rok_akademicki=request.form.get('rok_akademicki', ''),
            kierunek=request.form.get('kierunek', ''),
            forma_studiow=request.form.get('forma_studiow', ''),
            semestr=int(request.form.get('semestr', 0)),
            liczba_godzin=int(request.form.get('liczba_godzin', 0))
        )
        db.session.add(nowa_ankieta)
        
        # Powiadomienia dla dziekanatu
        pracownicy_dziekanatu = Uzytkownik.query.filter_by(rola='dziekanat').all()
        for pracownik in pracownicy_dziekanatu:
            powiadomienie = Powiadomienie(
                uzytkownik_id=pracownik.id,
                tresc="Wpłynęła nowa, anonimowa ankieta od studenta (Zał. 5).",
                link=url_for('dziekanat.ankiety_lista')
            )
            db.session.add(powiadomienie)
            
        # Oznacz ankietę jako wypełnioną dla praktyki studenta (zachowując anonimowość wpisu Ankiety)
        praktyka.ankieta_wypelniona = True
        db.session.commit()
        
        flash('Ankieta została wysłana anonimowo do Dziekanatu. Dziękujemy!', 'success')
        return redirect(url_for('student.dashboard'))
    return render_template('dokumenty/zal5_ankieta.html')