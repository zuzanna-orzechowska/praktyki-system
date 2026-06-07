from flask import Blueprint, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Student, Praktyka, KartaPraktyki, Porozumienie, Uzytkownik, Dokument
from utils.pdf_generator import generate_zal3_pdf
from io import BytesIO

pdf_export_bp = Blueprint('pdf_export', __name__, url_prefix='/dokumenty/pobierz_pdf')

@pdf_export_bp.route('/zal3/<int:student_id>', methods=['GET'])
@login_required
def pobierz_zal3(student_id):
    student = Student.query.get_or_404(student_id)
    
    if current_user.rola == 'student' and current_user.id != student.uzytkownik_id:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
        
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Brak praktyki.', 'warning')
        return redirect(url_for('index'))
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL3').first()
    if not dokument:
        flash('Brak wygenerowanej Karty Praktyki.', 'warning')
        return redirect(url_for('index'))
        
    karta = KartaPraktyki.query.filter_by(dokument_id=dokument.id).first()
    porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
    
    zopz = Uzytkownik.query.get(praktyka.zaklad.zopz_id) if praktyka.zaklad and praktyka.zaklad.zopz_id else None
    uopz = Uzytkownik.query.get(praktyka.uopz_id) if praktyka.uopz_id else None
    
    pdf_buffer = generate_zal3_pdf(student, praktyka, karta, porozumienie, zopz, uopz)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Karta_Praktyki_Zal3_{student.nr_albumu}.pdf",
        mimetype='application/pdf'
    )

from models import EfektUczenia
from utils.pdf_generator import generate_zal4_pdf
import re

@pdf_export_bp.route('/zal4/<int:student_id>', methods=['GET'])
@login_required
def pobierz_zal4(student_id):
    student = Student.query.get_or_404(student_id)
    
    if current_user.rola == 'student' and current_user.id != student.uzytkownik_id:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
        
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Brak praktyki.', 'warning')
        return redirect(url_for('index'))
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4').first()
    if not dokument:
        flash('Brak wygenerowanego Załącznika 4.', 'warning')
        return redirect(url_for('index'))
        
    efekty = EfektUczenia.query.filter_by(dokument_id=dokument.id).order_by(EfektUczenia.id).all()
    
    podpis_zopz = efekty[0].podpis_zopz if efekty and efekty[0].podpis_zopz else None
    data_podpisu_zopz = str(efekty[0].data_podpisu) if efekty and efekty[0].data_podpisu else ""
    
    opinia_text = dokument.uwagi_opiekuna or ""
    podpis_uopz = None
    data_podpisu_uopz = ""
    
    match = re.search(r'\[PODPIS_UOPZ:(.+?)\|DATA:(.+?)\]', opinia_text)
    if match:
        podpis_uopz = match.group(1).strip()
        data_podpisu_uopz = match.group(2).strip()
        opinia_text = opinia_text[:match.start()].strip()
        
    pdf_buffer = generate_zal4_pdf(student, praktyka, dokument, efekty, podpis_zopz, data_podpisu_zopz, opinia_text, podpis_uopz, data_podpisu_uopz)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Efekty_Uczenia_Zal4_{student.nr_albumu}.pdf",
        mimetype='application/pdf'
    )


from models import WpisDziennika
from utils.pdf_generator import generate_zal6_pdf

@pdf_export_bp.route('/zal6/<int:student_id>', methods=['GET'])
@login_required
def pobierz_zal6(student_id):
    student = Student.query.get_or_404(student_id)
    
    if current_user.rola == 'student' and current_user.id != student.uzytkownik_id:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
        
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Brak praktyki.', 'warning')
        return redirect(url_for('index'))
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL6').first()
    if not dokument:
        flash('Brak wygenerowanego Dziennika Praktyk.', 'warning')
        return redirect(url_for('index'))
        
    wpisy = WpisDziennika.query.filter_by(dokument_id=dokument.id).order_by(WpisDziennika.numer_dnia).all()
        
    zopz = Uzytkownik.query.get(praktyka.zaklad.zopz_id) if praktyka.zaklad and praktyka.zaklad.zopz_id else None
    pdf_buffer = generate_zal6_pdf(student, praktyka, wpisy, zopz)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Dziennik_Praktyk_Zal6_{student.nr_albumu}.pdf",
        mimetype='application/pdf'
    )


from models import Protokol
from utils.pdf_generator import generate_zal8_pdf

@pdf_export_bp.route('/zal8/<int:student_id>', methods=['GET'])
@login_required
def pobierz_zal8(student_id):
    student = Student.query.get_or_404(student_id)
    
    if current_user.rola == 'student' and current_user.id != student.uzytkownik_id:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
        
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Brak praktyki.', 'warning')
        return redirect(url_for('index'))
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL3').first()
    karta = None
    if dokument:
        karta = KartaPraktyki.query.filter_by(dokument_id=dokument.id).first()
        
    protokol = Protokol.query.filter_by(praktyka_id=praktyka.id).first()
    
    pdf_buffer = generate_zal8_pdf(student, praktyka, protokol, karta)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Protokol_Zaliczenia_Zal8_{student.nr_albumu}.pdf",
        mimetype='application/pdf'
    )


from models import HarmonogramPraktyki
from utils.pdf_generator import generate_zal2a_pdf

@pdf_export_bp.route('/zal2a/<int:student_id>', methods=['GET'])
@login_required
def pobierz_zal2a(student_id):
    student = Student.query.get_or_404(student_id)
    
    if current_user.rola == 'student' and current_user.id != student.uzytkownik_id:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
        
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Brak praktyki.', 'warning')
        return redirect(url_for('index'))
        
    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL2A').first()
    if not dokument:
        flash('Brak wygenerowanego Harmonogramu.', 'warning')
        return redirect(url_for('index'))
        
    harmonogram = HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).order_by(HarmonogramPraktyki.lp).all()
    from models import ProgramPraktyki, Zal2aPodpisy
    program = ProgramPraktyki.query.filter_by(dokument_id=dokument.id).all()
    podpisy = Zal2aPodpisy.query.filter_by(dokument_id=dokument.id).first()
        
    pdf_buffer = generate_zal2a_pdf(student, praktyka, dokument, harmonogram, program, podpisy)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Harmonogram_Zal2a_{student.nr_albumu}.pdf",
        mimetype='application/pdf'
    )


from utils.pdf_generator import (
    generate_zal1_pdf,
    generate_zal2_pdf,
    generate_zal7_pdf,
    generate_zal9_pdf,
    generate_zal7a_pdf,
    generate_zal4b_pdf,
    generate_zal8a_pdf,
    generate_zal4a_pdf
)

@pdf_export_bp.route('/dokument/<typ_dokumentu>/<int:student_id>', methods=['GET'])
@login_required
def pobierz_dokument(typ_dokumentu, student_id):
    student = Student.query.get_or_404(student_id)
    
    if current_user.rola == 'student' and current_user.id != student.uzytkownik_id:
        flash('Brak dostępu.', 'danger')
        return redirect(url_for('index'))
        
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka:
        flash('Brak praktyki.', 'warning')
        return redirect(url_for('index'))
        
    pdf_buffer = None
    file_prefix = "Dokument"
    
    if typ_dokumentu == 'ZAL1':
        from models import Oswiadczenie
        porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
        dokument_zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
        oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument_zal9.id).first() if dokument_zal9 else None
        pdf_buffer = generate_zal1_pdf(student, praktyka, porozumienie, oswiadczenie)
        file_prefix = "Porozumienie_Zal1"
        
    elif typ_dokumentu == 'ZAL2':
        from models import Oswiadczenie
        porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
        dokument_zal9 = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
        oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument_zal9.id).first() if dokument_zal9 else None
        pdf_buffer = generate_zal2_pdf(student, praktyka, porozumienie, oswiadczenie)
        file_prefix = "Program_Zal2"
        
    elif typ_dokumentu == 'ZAL9':
        from models import Oswiadczenie
        dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL9').first()
        oswiadczenie = Oswiadczenie.query.filter_by(dokument_id=dokument.id).first() if dokument else None
        pdf_buffer = generate_zal9_pdf(student, praktyka, oswiadczenie)
        file_prefix = "Oswiadczenie_Zal9"
        
    elif typ_dokumentu in ['ZAL4A', 'ZAL4B', 'ZAL7', 'ZAL7A', 'ZAL8A']:
        dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika=typ_dokumentu).first()
        
        if typ_dokumentu == 'ZAL7':
            from models import Sprawozdanie
            sprawozdanie = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first() if dokument else None
            pdf_buffer = generate_zal7_pdf(student, praktyka, sprawozdanie)
            file_prefix = "Sprawozdanie_Zal7"
            
        elif typ_dokumentu == 'ZAL7A':
            from models import Sprawozdanie
            sprawozdanie = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first() if dokument else None
            pdf_buffer = generate_zal7a_pdf(student, praktyka, sprawozdanie)
            file_prefix = "Sprawozdanie_Zal7a"
            
        elif typ_dokumentu == 'ZAL4B':
            from models import WniosekZaliczeniePraktyki
            wniosek = WniosekZaliczeniePraktyki.query.filter_by(dokument_id=dokument.id).first() if dokument else None
            pdf_buffer = generate_zal4b_pdf(student, praktyka, wniosek)
            file_prefix = "Wniosek_Zal4b"
            
        elif typ_dokumentu == 'ZAL8A':
            from models import Protokol
            protokol = Protokol.query.filter_by(dokument_id=dokument.id).first() if dokument else None
            pdf_buffer = generate_zal8a_pdf(student, praktyka, protokol)
            file_prefix = "Protokol_Zal8a"
            
        elif typ_dokumentu == 'ZAL4A':
            from models import DecyzjaZal4a
            decyzja = DecyzjaZal4a.query.filter_by(dokument_id=dokument.id).first() if dokument else None
            pdf_buffer = generate_zal4a_pdf(student, praktyka, decyzja)
            file_prefix = "Decyzja_Zal4a"
    
    if not pdf_buffer:
        flash(f'Eksport PDF nie jest obsługiwany dla tego dokumentu.', 'danger')
        return redirect(url_for('index'))
        
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"{file_prefix}_{student.nr_albumu}.pdf",
        mimetype='application/pdf'
    )
