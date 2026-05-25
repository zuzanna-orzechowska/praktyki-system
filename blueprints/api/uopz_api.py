from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import Uzytkownik, Student, Praktyka, Dokument, Protokol, HarmonogramPraktyki, ProgramPraktyki, Porozumienie, EfektUczenia, Sprawozdanie

uopz_api_bp = Blueprint('uopz_api', __name__, url_prefix='/uopz')

@uopz_api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.rola != 'uopz':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    praktyki = Praktyka.query.filter_by(uopz_id=current_user.id).all()
    
    def format_praktyka(p):
        student = p.student
        return {
            'id': p.id,
            'student_id': student.id,
            'student_imie': student.uzytkownik.imie,
            'student_nazwisko': student.uzytkownik.nazwisko,
            'nr_albumu': student.nr_albumu,
            'kierunek': student.kierunek,
            'data_start': str(p.data_start) if p.data_start else '',
            'data_end': str(p.data_end) if p.data_end else '',
            'status': p.status
        }
        
    return jsonify({
        'praktyki': [format_praktyka(p) for p in praktyki]
    })

@uopz_api_bp.route('/teczka/<int:student_id>', methods=['GET'])
@login_required
def teczka(student_id):
    if current_user.rola != 'uopz':
        return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id, uopz_id=current_user.id).first()

    if not praktyka:
        return jsonify({'error': 'Brak dostępu do tego studenta lub brak przypisanej praktyki.'}), 403

    dokumenty = Dokument.query.filter_by(praktyka_id=praktyka.id).all()
    dok_dict = {d.typ_zalacznika: d.to_dict() for d in dokumenty}

    return jsonify({
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokumenty': dok_dict
    })

@uopz_api_bp.route('/zal3_karta/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal3_karta(student_id):
    if current_user.rola != 'uopz': return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka: return jsonify({'error': 'Brak praktyki'}), 404

    protokol = Protokol.query.filter_by(praktyka_id=praktyka.id).first()
    porozumienie = Porozumienie.query.filter_by(praktyka_id=praktyka.id).first()
    zopz = Uzytkownik.query.get(praktyka.zaklad.zopz_id) if praktyka.zaklad and praktyka.zaklad.zopz_id else None

    if request.method == 'POST':
        data = request.json
        akcja = data.get('akcja')
        
        if akcja == 'wydaj_skierowanie':
            praktyka.status = 'SKIEROWANIE_WYDANE'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Skierowanie zostało oficjalnie wydane.'})
            
        elif akcja == 'zapisz_ocene':
            if not protokol:
                protokol = Protokol(praktyka_id=praktyka.id)
                db.session.add(protokol)
            
            try:
                if data.get('ocena_u'): protokol.ocena_u = float(data.get('ocena_u'))
                if data.get('ocena_s'): protokol.ocena_s = float(data.get('ocena_s'))
                db.session.commit()
                return jsonify({'success': True, 'message': 'Oceny UOPZ zostały zapisane w Karcie Praktyki.'})
            except ValueError:
                return jsonify({'success': False, 'message': 'Wprowadzono niepoprawny format oceny.'})

    return jsonify({
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'praktyka': praktyka.to_dict(),
        'uopz': current_user.to_dict(),
        'zopz': zopz.to_dict() if zopz else None,
        'porozumienie': porozumienie.to_dict() if porozumienie else None,
        'protokol': protokol.to_dict() if protokol else None
    })

@uopz_api_bp.route('/zal2a_harmonogram/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal2a_harmonogram(student_id):
    if current_user.rola != 'uopz': return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka: return jsonify({'error': 'Brak praktyki'}), 404

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL2A').first()
    if not dokument:
        dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL2A', utworzony_przez=current_user.id)
        db.session.add(dokument)
        db.session.commit()

    if request.method == 'POST':
        data = request.json
        if data.get('akcja') == 'zapisz':
            ProgramPraktyki.query.filter_by(dokument_id=dokument.id).delete()
            programy_data = data.get('programy', {})
            for kod, prace in programy_data.items():
                if prace:
                    nowy_program = ProgramPraktyki(dokument_id=dokument.id, kod_efektu=kod, dzial_prace=prace)
                    db.session.add(nowy_program)

            HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).delete()
            harmonogram_data = data.get('harmonogram', [])
            for i, p in enumerate(harmonogram_data):
                if p['dzial'] and p['dni']:
                    nowa_pozycja = HarmonogramPraktyki(
                        dokument_id=dokument.id, lp=i + 1,
                        dzial_komorka=p['dzial'], planowana_liczba_dni=int(p['dni'])
                    )
                    db.session.add(nowa_pozycja)
            
            dokument.status = 'Under_Review'
            dokument.uwagi_opiekuna = "" 
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Program i Harmonogram został zapisany i wysłany do studenta!'})

    pozycje_harmonogramu = HarmonogramPraktyki.query.filter_by(dokument_id=dokument.id).order_by(HarmonogramPraktyki.lp).all()
    zapisane_programy = {p.kod_efektu: p.dzial_prace for p in ProgramPraktyki.query.filter_by(dokument_id=dokument.id).all()}

    return jsonify({
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict(),
        'pozycje': [p.to_dict() for p in pozycje_harmonogramu],
        'zapisane_programy': zapisane_programy
    })

@uopz_api_bp.route('/zal4_efekty/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal4_efekty(student_id):
    if current_user.rola != 'uopz': return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka: return jsonify({'error': 'Brak praktyki'}), 404

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika='ZAL4').first()
    
    if request.method == 'POST':
        data = request.json
        if not dokument:
            dokument = Dokument(praktyka_id=praktyka.id, typ_zalacznika='ZAL4', utworzony_przez=current_user.id)
            db.session.add(dokument)
        
        dokument.uwagi_opiekuna = data.get('opinia_uopz')
        db.session.commit()
        return jsonify({'success': True, 'message': 'Opinia opiekuna uczelnianego została zapisana.'})

    efekty = EfektUczenia.query.filter_by(dokument_id=dokument.id).order_by(EfektUczenia.kod_efektu).all() if dokument else []
    
    return jsonify({
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict() if dokument else None,
        'efekty': [e.to_dict() for e in efekty]
    })

@uopz_api_bp.route('/zal7_sprawozdanie/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal7_sprawozdanie(student_id):
    return handle_sprawozdanie(student_id, 'ZAL7')

@uopz_api_bp.route('/zal7a_sprawozdanie/<int:student_id>', methods=['GET', 'POST'])
@login_required
def zal7a_sprawozdanie(student_id):
    return handle_sprawozdanie(student_id, 'ZAL7A')

def handle_sprawozdanie(student_id, typ):
    if current_user.rola != 'uopz': return jsonify({'error': 'Odmowa dostępu'}), 403

    student = Student.query.get_or_404(student_id)
    praktyka = Praktyka.query.filter_by(student_id=student.id).first()
    if not praktyka: return jsonify({'error': 'Brak praktyki'}), 404

    dokument = Dokument.query.filter_by(praktyka_id=praktyka.id, typ_zalacznika=typ).first()
    sprawozdanie_doc = Sprawozdanie.query.filter_by(dokument_id=dokument.id).first() if dokument else None

    if request.method == 'POST':
        data = request.json
        akcja = data.get('akcja')
        uwagi = data.get('uwagi_opiekuna', '')

        if dokument:
            dokument.uwagi_opiekuna = uwagi
            if akcja in ['zatwierdz', 'zatwierdz_i_podpisz']:
                dokument.status = 'Approved'
                db.session.commit()
                return jsonify({'success': True, 'message': 'Sprawozdanie zostało zatwierdzone.'})
            elif akcja == 'odrzuc':
                dokument.status = 'Rejected'
                db.session.commit()
                return jsonify({'success': True, 'message': 'Sprawozdanie zostało odrzucone do poprawy.'})
                
    return jsonify({
        'student': student.to_dict(),
        'uzytkownik': student.uzytkownik.to_dict(),
        'praktyka': praktyka.to_dict(),
        'dokument': dokument.to_dict() if dokument else None,
        'sprawozdanie': sprawozdanie_doc.to_dict() if sprawozdanie_doc else None
    })
