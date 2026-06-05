import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from flask import current_app

def _init_styles():
    fonts_dir = os.path.join(current_app.root_path, 'static', 'fonts')
    pdfmetrics.registerFont(TTFont('DejaVuSerif', os.path.join(fonts_dir, 'DejaVuSerif.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', os.path.join(fonts_dir, 'DejaVuSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSerif-Italic', os.path.join(fonts_dir, 'DejaVuSerif-Italic.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuSerif-BoldItalic', os.path.join(fonts_dir, 'DejaVuSerif-BoldItalic.ttf')))
    
    pdfmetrics.registerFontFamily('DejaVuSerif',
                                  normal='DejaVuSerif',
                                  bold='DejaVuSerif-Bold',
                                  italic='DejaVuSerif-Italic',
                                  boldItalic='DejaVuSerif-BoldItalic')

    styles = getSampleStyleSheet()
    
    base_style = ParagraphStyle(
        'BaseStyle',
        fontName='DejaVuSerif',
        fontSize=11,
        leading=15,
    )
    
    return {
        'base': base_style,
        'right': ParagraphStyle('RightStyle', parent=base_style, alignment=2),
        'center': ParagraphStyle('CenterStyle', parent=base_style, alignment=1),
        'header_bold': ParagraphStyle('HeaderBold', parent=base_style, fontName='DejaVuSerif-Bold', fontSize=12, leading=14),
        'title': ParagraphStyle('TitleStyle', parent=base_style, fontName='DejaVuSerif-Bold', fontSize=12, alignment=1, spaceBefore=25, spaceAfter=20, leading=16),
        'section_title': ParagraphStyle('SectionTitle', parent=base_style, fontName='DejaVuSerif-Bold', fontSize=11, spaceBefore=15, spaceAfter=0),
        'italic_desc': ParagraphStyle('ItalicDesc', parent=base_style, fontName='DejaVuSerif-Italic', fontSize=11, spaceBefore=0, spaceAfter=15, leftIndent=15)
    }

class PDFDocumentBuilder:
    """Klasa pomocnicza do znacznego uproszczenia tworzenia dokumentów PDF"""
    def __init__(self, title, zalacznik_nr, student, skip_header=False):
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(self.buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50, title=title)
        self.styles = _init_styles()
        self.elements = []
        if not skip_header:
            self._build_header(zalacznik_nr, student)

    def _build_header(self, z_nr, student):
        self.elements.append(Paragraph(f"Załącznik nr {z_nr}", self.styles['right']))
        self.elements.append(Spacer(1, 15))
        self.elements.append(Paragraph("<b>Akademia Nauk Stosowanych<br/>w Elblągu</b>", self.styles['header_bold']))
        self.elements.append(Spacer(1, 15))
        self.elements.append(Paragraph("<b>Instytut Informatyki Stosowanej</b><br/><i>im. Krzysztofa Brzeskiego</i>", self.styles['base']))
        self.elements.append(Spacer(1, 25))

        imie_nazwisko = f"{student.uzytkownik.imie} {student.uzytkownik.nazwisko.split('(')[0].strip()}" if student and student.uzytkownik else ".................."
        album = student.nr_albumu or ".................."
        kierunek = student.kierunek or "informatyka"
        specjalnosc = student.specjalnosc or "..................................................."
        tryb = "inżynierskie niestacjonarne"
        rok = student.rok_akademicki or "........................"
        
        data_table = [
            [Paragraph(f"Student: <b>{imie_nazwisko}</b>", self.styles['base']), Paragraph(f"Nr albumu: <b>{album}</b>", self.styles['base'])],
            [Paragraph(f"Kierunek: <b>{kierunek}</b>", self.styles['base']), ""],
            [Paragraph(f"Specjalność: <b>{specjalnosc}</b>", self.styles['base']), ""],
            [Paragraph(f"Studia: <b>{tryb}</b>", self.styles['base']), ""],
            [Paragraph(f"Rok ak.: <b>{rok}</b>", self.styles['base']), ""]
        ]
        
        t = Table(data_table, colWidths=[350, 150])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('SPAN', (0,1), (1,1)), ('SPAN', (0,2), (1,2)), ('SPAN', (0,3), (1,3)), ('SPAN', (0,4), (1,4)),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('TOPPADDING', (0,0), (-1,-1), 4), ('LEFTPADDING', (0,0), (-1,-1), 20),
        ]))
        self.elements.append(t)

    def add_title(self, text):
        self.elements.append(Paragraph(text, self.styles['title']))

    def add_paragraph(self, text, style='base'):
        self.elements.append(Paragraph(text, self.styles[style]))
        
    def add_spacer(self, height):
        self.elements.append(Spacer(1, height))
        
    def add_signature(self, podpis_text, description, align='right'):
        podpis_text = podpis_text or "........................................................................"
        if "...." not in podpis_text:
            sig_val = Paragraph(f"<font fontName='DejaVuSerif-Italic' color='#004a99'>{podpis_text}</font>", self.styles['center'])
        else:
            sig_val = podpis_text

        desc_val = Paragraph(f"<small>{description}</small>", self.styles['center'])
        
        if align == 'right':
            t = Table([["", sig_val], ["", desc_val]], colWidths=[200, 280])
            t.setStyle(TableStyle([('ALIGN', (1,0), (1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        else:
            t = Table([["", sig_val], ["", desc_val]], colWidths=[280, 200])
            t.setStyle(TableStyle([('ALIGN', (1,0), (1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            
        self.elements.append(t)

    def build(self):
        self.doc.build(self.elements)
        self.buffer.seek(0)
        return self.buffer


def generate_zal7a_pdf(student, praktyka, sprawozdanie):
    pdf = PDFDocumentBuilder(f"Zalacznik_7a_{student.nr_albumu}", "7a", student)
    pdf.add_title("SPRAWOZDANIE STUDENTA<br/>Z PRAKTYKI ZAWODOWEJ REALIZOWANEJ<br/>NA PODSTAWIE PRACY ZAWODOWEJ LUB DZIAŁALNOŚCI GOSPODARCZEJ")

    miejsce = praktyka.zaklad.nazwa if praktyka and praktyka.zaklad else ("." * 80)
    pdf.add_paragraph(f"odbytej w <b>{miejsce}</b>")
    pdf.add_spacer(25)

    pdf.add_paragraph("I.&nbsp;&nbsp; CHARAKTERYSTYKA MIEJSCA PRACY", 'section_title')
    pdf.add_paragraph("(Krótki opis instytucji)", 'italic_desc')
    if sprawozdanie and sprawozdanie.charakterystyka:
        pdf.add_paragraph(sprawozdanie.charakterystyka.replace(chr(10), '<br/>'))
    pdf.add_spacer(20)

    pdf.add_paragraph("II. OPIS I ANALIZA WYKONYWANYCH PRAC", 'section_title')
    pdf.add_paragraph("(Syntetyczny opis wykonanych prac)", 'italic_desc')
    if sprawozdanie and sprawozdanie.opis_prac:
        pdf.add_paragraph(sprawozdanie.opis_prac.replace(chr(10), '<br/>'))
    pdf.add_spacer(20)

    pdf.add_paragraph("III. WIEDZA I UMIEJĘTNOŚCI UZYSKANE W TRAKCIE PRACY ZAWODOWEJ LUB DZIAŁALNOŚCI GOSPODARCZEJ", 'section_title')
    pdf.add_paragraph("(Samoocena w zakresie nabytych kompetencji oraz osiągniętych efektów uczenia się)", 'italic_desc')
    if sprawozdanie and sprawozdanie.wiedza_umiejetnosci:
        pdf.add_paragraph(sprawozdanie.wiedza_umiejetnosci.replace(chr(10), '<br/>'))
    pdf.add_spacer(50)

    podpis = sprawozdanie.podpis_studenta if sprawozdanie else None
    pdf.add_signature(podpis, "data i podpis studenta", align='left')
    pdf.add_spacer(30)
    pdf.add_signature(None, "data i podpis bezpośredniego przełożonego<br/>lub uczelnianego opiekuna praktyk", align='right')

    return pdf.build()

def generate_zal4b_pdf(student, praktyka, wniosek):
    pdf = PDFDocumentBuilder(f"Zalacznik_4b_{student.nr_albumu}", "4b", student, skip_header=True)
    
    pdf.add_paragraph("Załącznik nr 4b", 'right')
    data = wniosek.data_podpisu.strftime('%d.%m.%Y') if wniosek and wniosek.data_podpisu else "......................."
    pdf.add_paragraph(f"Elbląg dnia {data}", 'right')
    pdf.add_spacer(15)
    
    kierunek = student.kierunek or "Informatyka"
    imie_nazwisko = f"{student.uzytkownik.imie} {student.uzytkownik.nazwisko.split('(')[0].strip()}" if student and student.uzytkownik else "..............................."
    album = student.nr_albumu or "..................."
    specjalnosc = student.specjalnosc or "..................................................."
    
    pdf.add_paragraph(f"Kierunek studiów: <b>{kierunek}</b>", 'base')
    pdf.add_paragraph(f"Student / ka: {imie_nazwisko}", 'base')
    pdf.add_paragraph(f"Nr albumu: {album}", 'base')
    pdf.add_paragraph(f"Kierunek studiów: <b>{kierunek}</b>", 'base')
    pdf.add_paragraph(f"Specjalność: {specjalnosc}", 'base')
    pdf.add_spacer(20)

    pdf.add_paragraph("<b>Dyrektor Instytutu Informatyki Stosowanej<br/>im. Krzysztofa Brzeskiego<br/>Za pośrednictwem Komisji do spraw praktyki zawodowej<br/>dla kierunku studiów informatyka</b>", 'center')
    pdf.add_spacer(20)

    pdf.add_title("WNIOSEK O UBIEGANIE SIĘ ZALICZENIA EFEKTÓW UCZENIA SIĘ<br/>PRZEWIDZIANYCH DLA PRAKTYKI ZAWODOWEJ NA PODSTAWIE PRACY<br/>ZAWODOWEJ/STAŻU/ DZIAŁALNOŚCI GOSPODARCZEJ*")
    
    pdf.add_paragraph("<u><b>Wniosek</b></u>", 'center')
    pdf.add_spacer(15)

    pdf.add_paragraph("Na podstawie § 4, ustęp 1 i 2 Regulaminu praktyk zawodowych w Instytucie Informatyki Stosowanej im. Krzysztofa Brzeskiego ANS w Elblągu proszę o uznanie efektów uczenia się przewidzianych dla praktyki zawodowej na podstawie pracy zawodowej/stażu/działalności gospodarczej*.")
    pdf.add_spacer(15)
    
    pdf.add_paragraph("Uzasadnienie:")
    if wniosek and wniosek.uzasadnienie:
        pdf.add_paragraph(wniosek.uzasadnienie.replace(chr(10), '<br/>'))
    else:
        pdf.add_paragraph("........................................................................................................................................................................<br/>........................................................................................................................................................................<br/>........................................................................................................................................................................")
    pdf.add_spacer(15)

    pdf.add_paragraph("Dla potwierdzenia uzyskania zakładanych dla praktyki zawodowej efektów uczenia się załączam n/w dokumenty potwierdzające zakres realizowanych czynności zawodowych oraz czas ich realizacji w tym w szczególności :")
    pdf.add_paragraph("1. Umowę o pracę, zaświadczenie o odbyciu stażu lub wolontariatu")
    pdf.add_paragraph("2. Opis zajmowanego stanowiska pracy/kartę stanowiskową")
    pdf.add_paragraph("3. Zakres obowiązków realizowany w ramach stażu/wolontariatu")
    pdf.add_paragraph("4. Zaświadczenie z CEIDG lub KRS")
    pdf.add_paragraph("5. Inne dokumenty potwierdzające uzyskanie efektów uczenia się przewidzianych dla praktyki zawodowej")
    pdf.add_spacer(30)

    podpis = wniosek.podpis_studenta if wniosek else None
    pdf.add_signature(podpis, "Data i podpis studenta/ki", align='right')
    
    pdf.elements.append(Spacer(1, 30))
    
    pdf.add_paragraph("Opinia Komisji ds. praktyk zawodowych")
    pdf.add_spacer(10)
    pdf.add_paragraph("........................................................................................................................................................................<br/>........................................................................................................................................................................<br/>........................................................................................................................................................................")
    pdf.add_spacer(20)
    pdf.add_signature(None, "data i podpis Przewodniczącego Komisji ds. praktyk<br/>zawodowych", align='right')
    pdf.add_spacer(30)

    pdf.add_paragraph("<b>Decyzja Dyrektora Instytutu Informatyki Stosowanej im. Krzysztofa Brzeskiego:</b>")
    pdf.add_spacer(10)
    pdf.add_paragraph("Wyrażam zgodę na uznanie efektów uczenia się przewidzianych dla praktyki zawodowej*")
    pdf.add_spacer(5)
    pdf.add_paragraph("Wyrażam zgodę na częściowe zaliczenie efektów uczenia się przewidzianych dla praktyki zawodowej i wskazuję na konieczność dodatkowego zaliczenia n/w efektów uczenia się*")
    pdf.add_paragraph("........................................................................................................................................................................<br/>........................................................................................................................................................................<br/>........................................................................................................................................................................")
    pdf.add_spacer(5)
    pdf.add_paragraph("Nie wyrażam zgody na zaliczenie efektów uczenia się przewidzianych dla praktyki zawodowej.")
    pdf.add_spacer(30)

    pdf.add_signature(None, "data i podpis Dyrektora IIS im. K. Brzeskiego", align='right')

    return pdf.build()

def generate_zal8a_pdf(student, praktyka, protokol):
    pdf = PDFDocumentBuilder(f"Zalacznik_8a_{student.nr_albumu}", "8/8a", student)
    pdf.add_title("PROTOKÓŁ ZALICZENIA PRAKTYKI<br/>ZAWODOWEJ/STAŻU")

    przewodniczacy = protokol.komisja_przewodniczacy if protokol else '........................'
    czl1 = protokol.komisja_czlonek_1 if protokol else '........................'
    czl2 = protokol.komisja_czlonek_2 if protokol else '........................'
    
    pdf.add_paragraph(f"Komisja w składzie:<br/>Przewodniczący: <b>{przewodniczacy}</b><br/>Członek komisji: <b>{czl1}</b><br/>Członek komisji: <b>{czl2}</b>")
    pdf.add_spacer(15)
    
    pdf.add_paragraph("po przeanalizowaniu dokumentacji z przebiegu praktyki:")
    pdf.add_paragraph("- wniosek o zaliczenie praktyki na podstawie pracy / działalności")
    pdf.add_paragraph("- sprawozdanie studenta z praktyki")
    pdf.add_spacer(15)

    godziny = protokol.zaliczone_godziny if protokol else '...'
    ou = protokol.ocena_u if protokol else '...'
    oz = protokol.ocena_z if protokol else '...'
    oe = protokol.ocena_e if protokol else '...'

    pdf.add_paragraph(f"1. Zalicza praktykę w wymiarze: <b>{godziny} godz.</b>")
    pdf.add_paragraph(f"2. Decyzja dyrektora IIN (Ocena U): <b>{ou}</b>")
    pdf.add_paragraph(f"3. Ocena ze sprawozdania (Ocena Z): <b>{oz}</b>")
    pdf.add_paragraph(f"4. Ostateczna ocena z praktyki (Ocena E): <b>{oe}</b>")
    pdf.add_spacer(40)

    podpis = protokol.podpis_uczelnianego if protokol else None
    pdf.add_signature(podpis, "Podpis uczelnianego opiekuna praktyk<br/>w imieniu Komisji", align='right')

    return pdf.build()

def generate_zal4a_pdf(student, praktyka, decyzja):
    pdf = PDFDocumentBuilder(f"Zalacznik_4a_{student.nr_albumu}", "4a", student)
    pdf.add_title("POTWIERDZENIE UZYSKANIA<br/>EFEKTÓW UCZENIA SIĘ W RAMACH PRAKTYKI ZAWODOWEJ NA PODSTAWIE<br/>ZATRUDNIENIA/STAŻU/DZIAŁALNOŚCI GOSPODARCZEJ*")

    rodzaj = decyzja.rodzaj_zaliczenia if decyzja and decyzja.rodzaj_zaliczenia else "pracy zawodowej/stażu/działalności gospodarczej*"
    wymiar = decyzja.wymiar_godzin if decyzja and decyzja.wymiar_godzin else "........."
    wynik = decyzja.ogolny_wynik if decyzja and decyzja.ogolny_wynik else "uzyskał/a /nie uzyskał/a*"
    
    pdf.add_paragraph(f"W ramach {rodzaj} w wymiarze <b>{wymiar}</b> godzin <b>{wynik}</b> zakładane dla praktyki zawodowej efekty uczenia się:")
    pdf.add_spacer(15)

    from models import EfektUczenia
    efekty = EfektUczenia.query.filter_by(dokument_id=decyzja.dokument_id).order_by(EfektUczenia.kod_efektu).all() if decyzja else []
    
    table_data = [
        [Paragraph("Efekty uczenia się", pdf.styles['center']), "", Paragraph("Potwierdzenie uzyskania efektów", pdf.styles['center'])]
    ]
    
    for efekt in efekty:
        kod = efekt.kod_efektu
        opis = efekt.opis_efektu
        
        u1 = "<b>uzyskał/a *</b>" if efekt.uzyskany == 1 else "uzyskał/a *"
        u2 = "<b>uzyskał/a częściowo*</b>" if efekt.uzyskany == 2 else "uzyskał/a częściowo*"
        u3 = "<b>nie uzyskał/a*</b>" if efekt.uzyskany == 3 else "nie uzyskał/a*"
        
        opcje = Paragraph(f"{u1}<br/><br/>{u2}<br/><br/>{u3}", pdf.styles['center'])
        
        table_data.append([
            Paragraph(kod, pdf.styles['center']),
            Paragraph(opis, pdf.styles['base']),
            opcje
        ])
        
    if not efekty:
        table_data.append(["", Paragraph("Brak zdefiniowanych efektów uczenia się.", pdf.styles['base']), ""])

    t = Table(table_data, colWidths=[30, 260, 190])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN', (0,0), (1,0)),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    
    pdf.elements.append(t)
    pdf.add_spacer(25)

    pdf.add_paragraph("Potwierdzenie merytorycznej oceny dokumentacji złożonej przez studenta ze wskazaniem jakie elementy efektów uczenia się zaliczonych częściowo powinny zostać uzupełnione:")
    pdf.add_spacer(30)
    pdf.add_paragraph("........................................................................................................................................................................")
    pdf.add_spacer(40)

    podpis = decyzja.podpis_dyrektora if decyzja else None
    pdf.add_signature(podpis, "data, podpis Przewodniczącego Komisji do spraw praktyk", align='right')

    return pdf.build()
