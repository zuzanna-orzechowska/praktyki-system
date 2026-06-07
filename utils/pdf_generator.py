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

def generate_zal3_pdf(student, praktyka, karta, porozumienie, zopz, uopz):
    pdf = PDFDocumentBuilder(f"Zalacznik_3_{student.nr_albumu}", "3", student, skip_header=True)
    
    # KARTA PRAKTYKI ZAWODOWEJ
    pdf.add_title("KARTA PRAKTYKI ZAWODOWEJ")
    
    # SKIEROWANIE NA PRAKTYKĘ
    pdf.add_paragraph("SKIEROWANIE NA PRAKTYKĘ", 'center')
    pdf.add_spacer(10)
    
    porozumienie_nr = f"Porozumienie Nr {porozumienie.id}/{porozumienie.data_podpisania.strftime('%Y') if porozumienie.data_podpisania else '2026'}" if porozumienie and porozumienie.id else "Brak"
    data_zawarcia = porozumienie.data_podpisania if porozumienie and porozumienie.data_podpisania else (porozumienie.data_zawarcia if porozumienie and porozumienie.data_zawarcia else "Brak")
    pdf.add_paragraph(f"Na podstawie porozumienia nr <b>{porozumienie_nr}</b> z dnia <b>{data_zawarcia}</b> r., kieruję niżej wymienionego studenta na praktykę zawodową do zakładu pracy:")
    pdf.add_spacer(10)
    
    nazwa_zakladu = praktyka.zaklad.nazwa if praktyka and praktyka.zaklad else "Brak zakładu"
    adres_zakladu = f"{praktyka.zaklad.ulica} {praktyka.zaklad.nr_budynku}" + (f"/{praktyka.zaklad.nr_lokalu}" if praktyka.zaklad.nr_lokalu else "") + f", {praktyka.zaklad.miasto}" if praktyka and praktyka.zaklad else "Brak adresu"
    
    pdf.add_paragraph(f"<b>{nazwa_zakladu}</b>", 'center')
    pdf.add_paragraph(f"{adres_zakladu}", 'center')
    pdf.add_spacer(20)
    
    imie_nazwisko = f"{student.uzytkownik.imie} {student.uzytkownik.nazwisko.split('(')[0].strip()}" if student and student.uzytkownik else "Brak danych"
    uopz_dane = f"{uopz.imie} {uopz.nazwisko}" if uopz else "Brak danych"
    data_start = praktyka.data_start if praktyka else "Brak"
    data_end = praktyka.data_end if praktyka else "Brak"
    
    pdf.add_paragraph(f"1. Imię i nazwisko: <b>{imie_nazwisko}</b>")
    pdf.add_paragraph(f"2. Numer albumu: <b>{student.nr_albumu}</b>")
    pdf.add_paragraph(f"3. Studia: <b>inżynierskie {'stacjonarne' if student.tryb_studiow == 'stacjonarne' else 'niestacjonarne'}*</b>")
    pdf.add_paragraph(f"4. Kierunek: <b>{student.kierunek}</b>")
    pdf.add_paragraph(f"&nbsp;&nbsp;&nbsp;specjalność: <b>{student.specjalnosc or 'Brak'}</b>")
    pdf.add_paragraph(f"5. Czas trwania praktyki: <b>6 miesięcy (120 dni roboczych)</b>")
    pdf.add_paragraph(f"6. Uczelniany opiekun praktyki zawodowej: <b>{uopz_dane}</b>")
    pdf.add_paragraph(f"7. Termin praktyki: od <b>{data_start}</b> do <b>{data_end}</b>")
    pdf.add_spacer(30)
    
    podpis_dyrektora = karta.podpis_dyrektora if karta else None
    data_skierowania = str(karta.skierowanie_data) if karta and karta.skierowanie_data else ""
    pdf.add_signature(podpis_dyrektora, f"Dyrektor Instytutu<br/>lub osoba upoważniona<br/>{data_skierowania}", align='right')
    
    pdf.add_spacer(30)
    
    # POTWIERDZENIA Z ZAKŁADU PRACY
    pdf.add_paragraph("POTWIERDZENIA Z ZAKŁADU PRACY", 'center')
    pdf.add_spacer(10)
    zopz_dane = f"{zopz.imie} {zopz.nazwisko}" if zopz else "Brak danych"
    pdf.add_paragraph(f"Zakładowy opiekun praktyki zawodowej: <b>{zopz_dane}</b>")
    pdf.add_spacer(20)
    
    podpis_zgloszenie = karta.podpis_zgloszenie if karta else None
    data_zgloszenia = str(karta.data_zgloszenia) if karta and karta.data_zgloszenia else ""
    pdf.add_paragraph("Potwierdzam zgłoszenie się studenta na praktykę:")
    pdf.add_signature(podpis_zgloszenie, f"(data, pieczęć i podpis zakładowego opiekuna praktyki)<br/>{data_zgloszenia}", align='right')
    pdf.add_spacer(15)
    
    podpis_bhp = karta.podpis_bhp if karta else None
    data_bhp = str(karta.data_bhp) if karta and karta.data_bhp else ""
    pdf.add_paragraph("Potwierdzam odbycie szkolenia BHP:")
    pdf.add_signature(podpis_bhp, f"(data, pieczęć i podpis upoważnionego pracownika zakładu)<br/>{data_bhp}", align='right')
    pdf.add_spacer(30)
    
    # ZAŚWIADCZENIE
    pdf.add_paragraph("Zaświadczenie odbycia praktyki zawodowej", 'center')
    pdf.add_spacer(10)
    pdf.add_paragraph(f"Zaświadczam, że student <b>{imie_nazwisko}</b> odbył praktykę zawodową w:")
    pdf.add_paragraph(f"<b>{nazwa_zakladu}</b>, {adres_zakladu}", 'center')
    pdf.add_paragraph(f"w okresie (okresach) od <b>{data_start}</b> do <b>{data_end}</b> zgodnie z przyjętym programem.")
    pdf.add_spacer(10)
    
    uwagi_zopz = karta.zaswiadczenie_uwagi if karta and karta.zaswiadczenie_uwagi else "Brak uwag"
    pdf.add_paragraph(f"Uwagi: <b>{uwagi_zopz}</b>")
    pdf.add_spacer(30)
    
    podpis_zopz = karta.podpis_zopz if karta else None
    data_zaswiadczenie = str(karta.zaswiadczenie_data) if karta and karta.zaswiadczenie_data else ""
    pdf.add_signature(podpis_zopz, f"(miejscowość i data, pieczęć i podpis kierownika zakładu)<br/>{data_zaswiadczenie}", align='right')
    pdf.add_spacer(30)
    
    # OCENA PRZEBIEGU PRAKTYKI
    pdf.add_paragraph("Ocena przebiegu praktyki zawodowej", 'center')
    pdf.add_spacer(15)
    
    pdf.add_paragraph("Ocena z zakładu pracy (ZOPZ)", 'center')
    ocena_zopz_param = str(karta.ocena_zopz_param) if karta and karta.ocena_zopz_param else "........"
    ocena_zopz_opis = karta.ocena_zopz_opis if karta and karta.ocena_zopz_opis else "........"
    data_ocena_zopz = str(karta.ocena_zopz_data) if karta and karta.ocena_zopz_data else ""
    pdf.add_paragraph(f"Ocena parametryczna (w skali 2 do 5): <b>{ocena_zopz_param}</b>")
    pdf.add_paragraph(f"Ocena opisowa: <i>{ocena_zopz_opis}</i>")
    pdf.add_spacer(20)
    pdf.add_signature(podpis_zopz, f"Zakładowy opiekun praktyki zawodowej<br/>{data_ocena_zopz}", align='right')
    pdf.add_spacer(20)
    
    pdf.add_paragraph("Ocena Uczelnianego Opiekuna Praktyki Zawodowej (UOPZ)", 'center')
    ocena_uopz_param = str(karta.ocena_uopz_param) if karta and karta.ocena_uopz_param else "........"
    ocena_uopz_opis = karta.ocena_uopz_opis if karta and karta.ocena_uopz_opis else "........"
    data_ocena_uopz = str(karta.ocena_uopz_data) if karta and karta.ocena_uopz_data else ""
    podpis_uopz = karta.podpis_uopz if karta else None
    pdf.add_paragraph(f"Ocena parametryczna (w skali 2 do 5): <b>{ocena_uopz_param}</b>")
    pdf.add_paragraph(f"Ocena opisowa: <i>{ocena_uopz_opis}</i>")
    pdf.add_spacer(20)
    pdf.add_signature(podpis_uopz, f"Uczelniany opiekun praktyki zawodowej<br/>{data_ocena_uopz}", align='right')
    pdf.add_spacer(20)
    
    ocena_sprawozdania = str(karta.ocena_sprawozdania) if karta and karta.ocena_sprawozdania else "........"
    pdf.add_paragraph(f"Ocena sprawozdania z praktyki (w skali 2 do 5): <b>{ocena_sprawozdania}</b>")
    pdf.add_spacer(20)
    pdf.add_signature(podpis_uopz, f"(data i podpis uczelnianego opiekuna praktyki)<br/>{data_ocena_uopz}", align='right')

    return pdf.build()


def generate_zal4_pdf(student, praktyka, dokument, efekty, podpis_zopz, data_podpisu_zopz, opinia_uopz, podpis_uopz, data_podpisu_uopz):
    pdf = PDFDocumentBuilder(f"Zalacznik_4_{student.nr_albumu}", "4", student)
    
    pdf.add_title("POTWIERDZENIE UZYSKANIA EFEKTÓW UCZENIA SIĘ<br/>W RAMACH PRAKTYKI ZAWODOWEJ")
    
    wymiar = praktyka.liczba_godzin if praktyka else "......."
    pdf.add_paragraph(f"W ramach praktyki zawodowej zrealizowanej w wymiarze <b>{wymiar}</b> godzin student uzyskał/a (nie uzyskał/a)* zakładane dla praktyki zawodowej efekty uczenia się:")
    pdf.add_spacer(15)
    
    table_data = [
        [Paragraph("Lp.", pdf.styles['center']), Paragraph("Efekty uczenia się", pdf.styles['center']), Paragraph("Potwierdzenie ZOPZ", pdf.styles['center'])]
    ]
    
    for i, efekt in enumerate(efekty, 1):
        lp = str(i)
        opis = efekt.opis_efektu
        potwierdzenie = "uzyskał/a" if efekt.uzyskany == 1 else "nie uzyskał/a"
        
        table_data.append([
            Paragraph(lp, pdf.styles['center']),
            Paragraph(opis, pdf.styles['base']),
            Paragraph(potwierdzenie, pdf.styles['center'])
        ])
        
    if not efekty:
        table_data.append(["", Paragraph("Brak zdefiniowanych efektów uczenia się.", pdf.styles['base']), ""])

    t = Table(table_data, colWidths=[30, 260, 190])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    
    pdf.elements.append(t)
    pdf.add_spacer(25)
    
    pdf.add_paragraph("<b>Potwierdzenie bezpośredniego opiekuna zakładowego:</b>")
    pdf.add_spacer(20)
    pdf.add_signature(podpis_zopz, f"Data, podpis i pieczęć zakładu pracy<br/>{data_podpisu_zopz}", align='right')
    pdf.add_spacer(30)
    
    pdf.add_paragraph("<b>Opinia opiekuna uczelnianego:</b>")
    pdf.add_spacer(10)
    if opinia_uopz:
        pdf.add_paragraph(opinia_uopz.replace(chr(10), '<br/>'))
    else:
        pdf.add_paragraph("........................................................................................................................................................................<br/>........................................................................................................................................................................")
    
    pdf.add_spacer(30)
    pdf.add_signature(podpis_uopz, f"Data, podpis opiekuna uczelnianego<br/>{data_podpisu_uopz}", align='right')

    return pdf.build()


def generate_zal6_pdf(student, praktyka, wpisy, zopz=None):
    pdf = PDFDocumentBuilder(f"Zalacznik_6_{student.nr_albumu}", "6", student)
    
    pdf.add_title("DZIENNIK PRAKTYK")
    pdf.add_spacer(15)
    
    table_data = [
        [Paragraph("Nr dnia", pdf.styles['center']), Paragraph("Data", pdf.styles['center']), Paragraph("Opis zrealizowanych prac", pdf.styles['center']), Paragraph("Potwierdzenie ZOPZ", pdf.styles['center'])]
    ]
    
    zopz_imie_nazwisko = f"{zopz.imie} {zopz.nazwisko}" if zopz else "........................"
    
    for wpis in wpisy:
        nr = str(wpis.numer_dnia)
        data = wpis.data_wpisu.strftime('%Y-%m-%d') if wpis.data_wpisu else ""
        opis = wpis.opis_prac
        
        if wpis.potwierdzony_zopz == 1:
            potwierdzenie = Paragraph(f"<font color='#004a99'><i>{zopz_imie_nazwisko}</i></font>", pdf.styles['center'])
        else:
            potwierdzenie = Paragraph("Nie zatwierdzony", pdf.styles['center'])
        
        table_data.append([
            Paragraph(nr, pdf.styles['center']),
            Paragraph(data, pdf.styles['center']),
            Paragraph(opis, pdf.styles['base']),
            potwierdzenie
        ])
        
    if not wpisy:
        table_data.append(["", "", Paragraph("Brak wpisów w dzienniku.", pdf.styles['base']), ""])

    t = Table(table_data, colWidths=[40, 70, 260, 110])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    
    pdf.elements.append(t)
    pdf.add_spacer(20)
    
    return pdf.build()


def generate_zal8_pdf(student, praktyka, protokol, karta):
    pdf = PDFDocumentBuilder(f"Zalacznik_8_{student.nr_albumu}", "8", student)
    pdf.add_title("PROTOKÓŁ ZALICZENIA PRAKTYKI ZAWODOWEJ (PZ)")
    pdf.add_spacer(15)

    pdf.add_paragraph(f"Miejsce i okres realizacji PZ:")
    
    table_data = [
        [Paragraph("Lp.", pdf.styles['center']), Paragraph("Nazwa instytucji (zakładu pracy)", pdf.styles['center']), Paragraph("Okres / liczba dni", pdf.styles['center'])],
        ["1", Paragraph(protokol.instytucja_1 if protokol and protokol.instytucja_1 else "", pdf.styles['base']), Paragraph(protokol.okres_1 if protokol and protokol.okres_1 else "", pdf.styles['base'])],
        ["2", Paragraph(protokol.instytucja_2 if protokol and protokol.instytucja_2 else "", pdf.styles['base']), Paragraph(protokol.okres_2 if protokol and protokol.okres_2 else "", pdf.styles['base'])]
    ]
    
    t = Table(table_data, colWidths=[30, 290, 180])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
    ]))
    pdf.elements.append(t)
    pdf.add_spacer(15)
    
    os = protokol.ocena_s if protokol and protokol.ocena_s else '...'
    ou = protokol.ocena_u if protokol and protokol.ocena_u else (karta.ocena_uopz_param if karta else '...')
    oz = protokol.ocena_z if protokol and protokol.ocena_z else (karta.ocena_zopz_param if karta else '...')
    
    pdf.add_paragraph(f"<b>Zestawienie Ocen Cząstkowych</b>")
    pdf.add_paragraph(f"Ocena za sprawozdanie (S*) = <b>{os}</b>")
    pdf.add_paragraph(f"Ocena UOPZ (U*) = <b>{ou}</b>")
    pdf.add_paragraph(f"Ocena ZOPZ (Z*) = <b>{oz}</b>")
    pdf.add_spacer(15)

    data_egz = protokol.data_egzaminu.strftime('%Y-%m-%d') if protokol and protokol.data_egzaminu else '..................'
    przewodniczacy = protokol.przewodniczacy if protokol and protokol.przewodniczacy else '..................'
    k2 = protokol.komisja_2 if protokol and protokol.komisja_2 else '..................'
    k3 = protokol.komisja_3 if protokol and protokol.komisja_3 else '..................'
    r3 = protokol.rola_3 if protokol and protokol.rola_3 else '..................'
    k4 = protokol.komisja_4 if protokol and protokol.komisja_4 else '..................'
    r4 = protokol.rola_4 if protokol and protokol.rola_4 else '..................'
    
    pdf.add_paragraph(f"<b>Skład komisji i Pytania Egzaminacyjne</b> (Data zaliczenia: {data_egz})")
    pdf.add_paragraph(f"1. {przewodniczacy} — Przewodniczący Komisji")
    pdf.add_paragraph(f"2. {k2} — Uczelniany opiekun praktyki zawodowej")
    pdf.add_paragraph(f"3. {k3} — {r3}")
    pdf.add_paragraph(f"4. {k4} — {r4}")
    pdf.add_spacer(15)

    pyt1 = protokol.pytanie_1 if protokol and protokol.pytanie_1 else ""
    ocena1 = protokol.ocena_czastkowa_1 if protokol and protokol.ocena_czastkowa_1 else ""
    pyt2 = protokol.pytanie_2 if protokol and protokol.pytanie_2 else ""
    ocena2 = protokol.ocena_czastkowa_2 if protokol and protokol.ocena_czastkowa_2 else ""
    pyt3 = protokol.pytanie_3 if protokol and protokol.pytanie_3 else ""
    ocena3 = protokol.ocena_czastkowa_3 if protokol and protokol.ocena_czastkowa_3 else ""
    
    table_pytania = [
        [Paragraph("Lp.", pdf.styles['center']), Paragraph("Pytania / mini zadania zawodowe", pdf.styles['center']), Paragraph("Oceny cząstkowe", pdf.styles['center'])],
        ["1", Paragraph(pyt1, pdf.styles['base']), ocena1],
        ["2", Paragraph(pyt2, pdf.styles['base']), ocena2],
        ["3", Paragraph(pyt3, pdf.styles['base']), ocena3]
    ]
    t2 = Table(table_pytania, colWidths=[30, 350, 120])
    t2.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
    ]))
    pdf.elements.append(t2)
    
    oe = protokol.ocena_e if protokol and protokol.ocena_e else '...'
    pdf.add_spacer(5)
    pdf.add_paragraph(f"Łączna ocena za mini zadania (średnia arytmetyczna) - E: <b>{oe}</b>", 'right')
    pdf.add_spacer(15)

    ok = protokol.ocena_koncowa if protokol and protokol.ocena_koncowa else '...'
    slownie = protokol.ocena_k_slownie if protokol and protokol.ocena_k_slownie else '........................'
    
    pdf.add_paragraph("Algorytm wyliczania oceny końcowej: 0,4·E + 0,1·S + 0,2·U + 0,3·Z = K")
    pdf.add_paragraph(f"Ocena Końcowa (K): <b>{ok}</b>")
    pdf.add_paragraph(f"Zaliczam praktykę zawodową na ocenę (K): <b>{slownie}</b>")
    pdf.add_spacer(40)

    pdf.add_signature(None, "Przewodniczący Komisji", align='right')

    return pdf.build()


def generate_zal2a_pdf(student, praktyka, dokument, harmonogram, program, podpisy):
    pdf = PDFDocumentBuilder(f"Zalacznik_2a_{student.nr_albumu}", "2a", student)
    
    pdf.add_title("SZCZEGÓŁOWY HARMONOGRAM PRAKTYKI ZAWODOWEJ<br/>(załącznik do Porozumienia)")
    pdf.add_spacer(15)
    
    pdf.add_paragraph("Kierunek studiów: <b>informatyka</b>")
    pdf.add_paragraph(f"Zakład pracy: <b>{praktyka.zaklad.nazwa if praktyka and praktyka.zaklad else '........................'}</b>")
    pdf.add_spacer(15)
    
    # 1. PROGRAM PRAKTYKI ZAWODOWEJ
    pdf.add_paragraph("<b>PROGRAM PRAKTYKI ZAWODOWEJ</b>", style='center')
    pdf.add_spacer(10)
    
    efekty_definicje = [
        ("01", "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych."),
        ("02", "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce."),
        ("03", "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy."),
        ("04", "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka."),
        ("05", "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania, posługując się rozmaitymi źródłami literaturowymi i zasobami."),
        ("06", "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje zawodowe."),
        ("07", "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia."),
        ("08", "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy i zaproponować jego rozwiązanie."),
        ("09", "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności IT, stosując odpowiednie normy i standardy."),
        ("10", "Pracuje w zespole zajmującym się zawodowo branżą IT."),
        ("11", "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów."),
        ("12", "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje do realizacji zadania, jak i przekazać im w sposób zrozumiały opinie z zakresu informatyki."),
        ("13", "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki działalności informatyków, szczególnie te ekonomiczne i społeczne.")
    ]
    
    zapisane_programy = {p.kod_efektu: p.dzial_prace for p in program} if program else {}
    
    prog_data = [
        [Paragraph("<b>Kod</b>", pdf.styles['center']),
         Paragraph("<b>Efekty kształcenia</b>", pdf.styles['center']),
         Paragraph("<b>Dział (komórka) / przykładowe prace wykonywane przez praktykanta</b>", pdf.styles['center'])]
    ]
    
    for kod, definicja in efekty_definicje:
        prace = zapisane_programy.get(kod, "Brak wpisu")
        prog_data.append([
            Paragraph(f"<b>{kod}</b>", pdf.styles['center']),
            Paragraph(f"<small>{definicja}</small>", pdf.styles['base']),
            Paragraph(prace, pdf.styles['base'])
        ])
        
    t_prog = Table(prog_data, colWidths=[40, 210, 250], repeatRows=1)
    t_prog.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    pdf.elements.append(t_prog)
    pdf.add_spacer(30)
    
    # 2. HARMONOGRAM PRAKTYKI ZAWODOWEJ
    pdf.add_paragraph("<b>HARMONOGRAM PRAKTYKI ZAWODOWEJ</b>", style='center')
    pdf.add_spacer(10)
    
    harm_data = [
        [Paragraph("<b>L.p.</b>", pdf.styles['center']),
         Paragraph("<b>Dział/komórka organizacyjna zakładu pracy, w której praktyka będzie realizowana</b>", pdf.styles['center']),
         Paragraph("<b>Planowana liczba dni</b>", pdf.styles['center'])]
    ]
    
    for item in harmonogram:
        harm_data.append([
            Paragraph(str(item.lp), pdf.styles['center']),
            Paragraph(item.dzial_komorka, pdf.styles['base']),
            Paragraph(f"{item.planowana_liczba_dni} dni", pdf.styles['center'])
        ])
        
    if not harmonogram:
        harm_data.append(["", Paragraph("Brak pozycji harmonogramu.", pdf.styles['base']), ""])

    t_harm = Table(harm_data, colWidths=[40, 310, 150])
    t_harm.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    pdf.elements.append(t_harm)
    pdf.add_spacer(40)
    
    # 3. PODPISY (3 kolumny)
    def format_sig(text):
        text = text or "..........................................................."
        if "...." not in text:
            return Paragraph(f"<font fontName='DejaVuSerif-Italic' color='#004a99'>{text}</font>", pdf.styles['center'])
        return Paragraph(text, pdf.styles['center'])
        
    p_uopz = podpisy.podpis_uopz if podpisy else None
    p_zopz = podpisy.podpis_zopz if podpisy else None
    p_stud = podpisy.podpis_student if podpisy else None
    
    t_sig = Table([
        [format_sig(p_uopz), format_sig(p_zopz), format_sig(p_stud)],
        [Paragraph("<small>podpis uczelnianego opiekuna<br/>praktyki</small>", pdf.styles['center']),
         Paragraph("<small>podpis zakładowego opiekuna<br/>praktyki</small>", pdf.styles['center']),
         Paragraph("<small>podpis studenta</small>", pdf.styles['center'])]
    ], colWidths=[160, 160, 160])
    pdf.elements.append(t_sig)
    
    return pdf.build()


def generate_zal1_pdf(student, praktyka, porozumienie, oswiadczenie):
    pdf = PDFDocumentBuilder(f"Zalacznik_1_{student.nr_albumu}", "1", student)
    
    pdf.add_title("POROZUMIENIE W SPRAWIE ORGANIZACJI PRAKTYKI ZAWODOWEJ")
    pdf.add_spacer(15)
    
    data_podpisu = porozumienie.data_podpisania.strftime('%Y-%m-%d') if porozumienie and porozumienie.data_podpisania else "........................"
    
    pdf.add_paragraph(f"Zawarte w dniu <b>{data_podpisu}</b> pomiędzy:")
    pdf.add_paragraph("Akademią Nauk Stosowanych w Elblągu")
    pdf.add_paragraph(f"a Zakładem Pracy: <b>{praktyka.zaklad.nazwa if praktyka and praktyka.zaklad else '........................'}</b>")
    adres = "........................"
    if praktyka and praktyka.zaklad:
        adres = f"{praktyka.zaklad.ulica} {praktyka.zaklad.nr_budynku}"
        if praktyka.zaklad.nr_lokalu:
            adres += f"/{praktyka.zaklad.nr_lokalu}"
        adres += f", {praktyka.zaklad.kod_pocztowy} {praktyka.zaklad.miasto}"
    
    pdf.add_paragraph(f"z siedzibą w: <b>{adres}</b>")
    pdf.add_spacer(15)
    
    pdf.add_paragraph("<b>1.</b> Przedmiotem porozumienia jest organizacja praktyki zawodowej dla studenta:")
    pdf.add_spacer(10)
    
    # Tabela ze studentem
    data_start = praktyka.data_start.strftime('%Y-%m-%d') if praktyka.data_start else "........"
    data_end = praktyka.data_end.strftime('%Y-%m-%d') if praktyka.data_end else "........"
    godziny = f"{praktyka.liczba_godzin} godz." if praktyka.liczba_godzin else "........ godz."
    
    table_data = [
        [Paragraph("<b>Lp.</b>", pdf.styles['center']),
         Paragraph("<b>Imię i nazwisko studenta</b>", pdf.styles['center']),
         Paragraph("<b>Termin praktyki</b>", pdf.styles['center']),
         Paragraph("<b>Liczba godz.</b>", pdf.styles['center'])],
        [Paragraph("1.", pdf.styles['center']),
         Paragraph(f"{student.uzytkownik.imie} {student.uzytkownik.nazwisko}", pdf.styles['center']),
         Paragraph(f"{data_start} – {data_end}", pdf.styles['center']),
         Paragraph(godziny, pdf.styles['center'])]
    ]
    t = Table(table_data, colWidths=[30, 180, 150, 80])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    pdf.elements.append(t)
    pdf.add_spacer(15)
    
    pdf.add_paragraph("<b>2. Obowiązki Zakładu pracy:</b>")
    pdf.add_paragraph("Zakład pracy zobowiązuje się do sprawowania nadzoru nad studentami odbywającymi praktykę oraz zapewnienia warunków niezbędnych do jej przeprowadzenia zgodnie z porozumieniem zawartym z Uczelnią, a w szczególności do:")
    pdf.add_paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1) zapewnienia odpowiednich stanowisk pracy, urządzeń, pomieszczeń, zgodnie z programem praktyki,")
    pdf.add_paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2) zapoznania studentów z zakładowym regulaminem pracy, z przepisami o bezpieczeństwie i higienie pracy oraz o ochronie tajemnicy państwowej i służbowej,")
    pdf.add_paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3) sprawowania nadzoru nad właściwym wykonaniem przez studentów programu praktyki,")
    pdf.add_paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4) umożliwienia studentom korzystania z zaplecza socjalnego jakie posiada zakład pracy.")
    pdf.add_spacer(10)
    
    pdf.add_paragraph("<b>3. Obowiązki Uczelni:</b>")
    pdf.add_paragraph("Uczelnia zobowiązana jest do:")
    pdf.add_paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1) opracowania w porozumieniu z Zakładem pracy i ze studentami szczegółowych programów praktyk,")
    pdf.add_paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2) sprawowania nadzoru dydaktyczno – wychowawczego oraz organizacyjnego nad przebiegiem praktyk.")
    pdf.add_spacer(10)
    
    pdf.add_paragraph("<b>4. Obowiązki studenta:</b>")
    pdf.add_paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1) stosowanie się do ustaleń Zakładu pracy w zakresie porządku i dyscypliny pracy,")
    pdf.add_paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2) przestrzeganie zasad BHP i ochrony przeciwpożarowej,")
    pdf.add_paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3) przestrzeganie zasad odbywania praktyk określonych przez Uczelnię,")
    pdf.add_paragraph("&nbsp;&nbsp;&nbsp;&nbsp;4) student odbywający praktykę zawodową jest zobowiązany ubezpieczyć się indywidualnie od następstw nieszczęśliwych wypadków na czas trwania praktyki.")
    pdf.add_spacer(10)
    
    pdf.add_paragraph("<b>5.</b> Upoważnionym do rozstrzygania, wspólnie z kierownikiem Zakładu pracy, spraw związanych z przebiegiem praktyki jest opiekun ds. praktyk powołany przez Rektora Akademii Nauk Stosowanych w Elblągu.")
    pdf.add_paragraph("<b>6.</b> Porozumienie zostaje zawarte na czas trwania praktyki.")
    pdf.add_paragraph("<b>7.</b> Wszelkie zmiany porozumienia wymagają formy pisemnej pod rygorem nieważności.")
    pdf.add_paragraph("<b>8.</b> Porozumienie niniejsze sporządzone zostało w dwóch jednobrzmiących egzemplarzach po jednym dla każdej ze stron.")
    
    pdf.add_spacer(40)
    
    podpis_zopz = f"{oswiadczenie.osoba_upowazniona_imie} {oswiadczenie.osoba_upowazniona_nazwisko}" if oswiadczenie and porozumienie and porozumienie.status in ['ZatwierdzoneZOPZ', 'Podpisane'] else None
    podpis_dyrektora = porozumienie.podpisal_dziekanat if porozumienie else None
    
    def format_sig(text):
        text = text or "........................................................................"
        if "...." not in text:
            return Paragraph(f"<font fontName='DejaVuSerif-Italic' color='#004a99'>{text}</font>", pdf.styles['center'])
        return text
        
    t_sig = Table([
        [format_sig(podpis_dyrektora), format_sig(podpis_zopz)],
        [Paragraph("<small>data i podpis Dyrektora Instytutu</small>", pdf.styles['center']),
         Paragraph("<small>podpis osoby uprawnionej do reprezentacji<br/>w imieniu Zakładu pracy</small>", pdf.styles['center'])]
    ], colWidths=[240, 240])
    pdf.elements.append(t_sig)
    
    return pdf.build()

def generate_zal2_pdf(student, praktyka, porozumienie, oswiadczenie):
    pdf = PDFDocumentBuilder(f"Zalacznik_2_{student.nr_albumu}", "2", student)
    
    pdf.add_title("PROGRAM PRAKTYKI ZAWODOWEJ")
    pdf.add_spacer(15)
    
    pdf.add_paragraph("<b>A. Etap pierwszy – rozpoczęcie praktyki</b>")
    pdf.add_paragraph("1. Czynności organizacyjne, szkolenie BHP i ppoż.")
    pdf.add_paragraph("2. Zapoznanie się z zakresem działania zakładu pracy ze szczególnym uwzględnieniem stanowisk informatycznych.")
    pdf.add_paragraph("3. Zapoznanie z projektami realizowanymi przez firmę, stosowanymi technologiami informatycznymi z podkreśleniem narzędzi softwareowych i sieci komputerowych.")
    pdf.add_spacer(10)
    
    pdf.add_paragraph("<b>B. Etap drugi</b>")
    pdf.add_paragraph("1. Praca na ostatecznym stanowisku pracy, wykonywanie prac i projektów informatycznych tak aby osiągnąć wymagane programem studiów, efekty uczenia się:")
    pdf.add_paragraph("   a) ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki;")
    pdf.add_paragraph("   b) zna technologie, narzędzia, metody oraz sprzęt stosowane w informatyce;")
    pdf.add_paragraph("   c) rozwiązuje praktyczne problemy informatyczne osadzone w środowisku IT;")
    pdf.add_paragraph("   d) opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki;")
    pdf.add_paragraph("   e) pracuje w zespole zajmującym się zawodowo branżą IT;")
    pdf.add_paragraph("2. Planowany czas realizacji praktyki: 6 miesięcy tj. 120 dni (960 godz.).")
    pdf.add_spacer(10)
    
    pdf.add_paragraph("<b>C. Etap trzeci - zakończenie praktyki</b>")
    pdf.add_paragraph("1. W trakcie praktyki student prowadzi „Dzienniczek praktyki”. Wpisy potwierdza zakładowy opiekun.")
    pdf.add_paragraph("2. Na „Karcie praktyki” kierownik potwierdza odbycie praktyki, a opiekun wystawia ocenę.")
    pdf.add_paragraph("3. ZOPZ wystawia potwierdzenie osiągnięcia efektów uczenia się (Zał. 4).")
    
    pdf.add_spacer(40)
    podpis_zopz = f"{oswiadczenie.osoba_upowazniona_imie} {oswiadczenie.osoba_upowazniona_nazwisko}" if oswiadczenie and porozumienie and porozumienie.status in ['ZatwierdzoneZOPZ', 'Podpisane'] else None
    podpis_dyrektora = porozumienie.podpisal_dziekanat if porozumienie else None
    
    def format_sig(text):
        text = text or "........................................................................"
        if "...." not in text:
            return Paragraph(f"<font fontName='DejaVuSerif-Italic' color='#004a99'>{text}</font>", pdf.styles['center'])
        return text
        
    t = Table([
        [format_sig(podpis_zopz), format_sig(podpis_dyrektora)],
        [Paragraph("<small>podpis osoby reprezentującej zakład pracy</small>", pdf.styles['center']),
         Paragraph("<small>data i podpis Dyrektora Instytutu</small>", pdf.styles['center'])]
    ], colWidths=[240, 240])
    pdf.elements.append(t)
    
    return pdf.build()

def generate_zal7_pdf(student, praktyka, sprawozdanie):
    pdf = PDFDocumentBuilder(f"Zalacznik_7_{student.nr_albumu}", "7", student)
    
    pdf.add_title("SPRAWOZDANIE Z PRAKTYKI ZAWODOWEJ")
    pdf.add_spacer(15)
    
    pdf.add_paragraph("<b>1. Ogólna charakterystyka zakładu pracy:</b>")
    pdf.add_paragraph(sprawozdanie.charakterystyka if sprawozdanie else "........................")
    pdf.add_spacer(10)
    
    pdf.add_paragraph("<b>2. Opis zrealizowanych prac:</b>")
    pdf.add_paragraph(sprawozdanie.opis_prac if sprawozdanie else "........................")
    pdf.add_spacer(10)
    
    pdf.add_paragraph("<b>3. Ocena zdobytej wiedzy i umiejętności:</b>")
    pdf.add_paragraph(sprawozdanie.wiedza_umiejetnosci if sprawozdanie else "........................")
    pdf.add_spacer(10)
    
    if sprawozdanie and sprawozdanie.uwagi_zopz:
        pdf.add_paragraph("<b>Uwagi Zakładowego Opiekuna Praktyki (ZOPZ):</b>")
        pdf.add_paragraph(sprawozdanie.uwagi_zopz)
        pdf.add_spacer(10)
        
    pdf.add_spacer(40)
    pdf.add_signature(sprawozdanie.podpis_studenta if sprawozdanie else None, "Podpis Studenta", align='left')
    pdf.add_signature(sprawozdanie.podpis_zopz if sprawozdanie else None, "Podpis ZOPZ", align='center')
    pdf.add_signature(sprawozdanie.podpis_uopz if sprawozdanie else None, "Podpis UOPZ", align='right')
    
    return pdf.build()

def generate_zal9_pdf(student, praktyka, oswiadczenie):
    pdf = PDFDocumentBuilder(f"Zalacznik_9_{student.nr_albumu}", "9", student, skip_header=True)
    
    miejscowosc = oswiadczenie.miejscowosc if oswiadczenie else "........................"
    data_osw = oswiadczenie.data_oswiadczenia.strftime('%d.%m.%Y r.') if oswiadczenie and oswiadczenie.data_oswiadczenia else "........................"
    
    pdf.elements.append(Paragraph("Załącznik nr 9", pdf.styles['right']))
    pdf.add_spacer(15)
    
    # Miejscowosc i data (prawa strona)
    t_miejsc = Table([
        ["", Paragraph(f"<u>{miejscowosc}</u>, dnia <u>{data_osw}</u>", pdf.styles['center'])],
        ["", Paragraph("<small>(miejscowość)</small>", pdf.styles['center'])]
    ], colWidths=[240, 240])
    t_miejsc.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('ALIGN', (1, 1), (1, 1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    pdf.elements.append(t_miejsc)
    pdf.add_spacer(15)
    
    # Pieczęć firmy (lewa strona)
    t_pieczec = Table([
        [Paragraph(".............................................................", pdf.styles['center']), ""],
        [Paragraph("<small>Pieczęć firmy</small>", pdf.styles['center']), ""]
    ], colWidths=[200, 280])
    t_pieczec.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (0, 1), (0, 1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    pdf.elements.append(t_pieczec)
    pdf.add_spacer(30)
    
    pdf.add_title("OŚWIADCZENIE INSTYTUCJI")
    pdf.elements.append(Paragraph("<b>w sprawie przyjęcia studenta na praktykę zawodową</b>", pdf.styles['center']))
    pdf.add_spacer(30)
    
    nazwa_inst = oswiadczenie.nazwa_instytucji if oswiadczenie else "................................................................................................................................."
    pdf.elements.append(Paragraph(f"W imieniu {nazwa_inst}", pdf.styles['base']))
    pdf.elements.append(Paragraph("<small>(nazwa instytucji)</small>", pdf.styles['center']))
    pdf.add_spacer(15)
    
    od = oswiadczenie.termin_od.strftime('%d.%m.%Y') if oswiadczenie and oswiadczenie.termin_od else "......................"
    do = oswiadczenie.termin_do.strftime('%d.%m.%Y') if oswiadczenie and oswiadczenie.termin_do else "........................"
    pdf.elements.append(Paragraph(f"oświadczam, że w terminie od {od} do {do} przyjmiemy na praktykę", pdf.styles['base']))
    pdf.elements.append(Paragraph("zawodową studenta Instytutu Informatyki Stosowanej im. Krzysztofa Brzeskiego", pdf.styles['base']))
    pdf.add_spacer(15)
    
    imie_nazw = f"{student.uzytkownik.imie} {student.uzytkownik.nazwisko}"
    pdf.elements.append(Paragraph(f"{imie_nazw}", pdf.styles['center']))
    pdf.elements.append(Paragraph("<small>(imię i nazwisko studenta)</small>", pdf.styles['center']))
    pdf.add_spacer(15)
    
    # Uczelnia
    pdf.elements.append(Paragraph("Akademii Nauk Stosowanych w Elblągu,", pdf.styles['base']))
    pdf.add_spacer(15)
    
    # Kierunek, rok, album
    kierunek = student.kierunek or "informatyka"
    rok_map = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
    rok = rok_map.get(student.rok_studiow, "....") if student.rok_studiow else "...."
    album = student.nr_albumu or "...................."
    pdf.elements.append(Paragraph(f"kierunek: <b><i>{kierunek}</i></b>, &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; rok studiów: <b>{rok}</b>, &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; nr albumu {album}", pdf.styles['base']))
    pdf.add_spacer(20)
    
    # Zakładowym opiekunem...
    pdf.elements.append(Paragraph("Zakładowym opiekunem praktyki będzie:", pdf.styles['base']))
    pdf.add_spacer(15)
    
    zopz_dane = f"{oswiadczenie.opiekun_imie} {oswiadczenie.opiekun_nazwisko}, {oswiadczenie.opiekun_stanowisko}" if oswiadczenie else "................................................................................................................................."
    pdf.elements.append(Paragraph(f"{zopz_dane}", pdf.styles['center']))
    pdf.elements.append(Paragraph("<small>(imię i nazwisko, stanowisko)</small>", pdf.styles['center']))
    pdf.add_spacer(15)
    
    # Telefon, email
    tel = oswiadczenie.opiekun_telefon if oswiadczenie else "...................................."
    email = oswiadczenie.opiekun_email if oswiadczenie else "................................................................................."
    pdf.elements.append(Paragraph(f"Telefon {tel}, e-mail {email}", pdf.styles['base']))
    pdf.add_spacer(20)
    
    pdf.elements.append(Paragraph("Osobą upoważnioną do podpisania porozumienia dotyczącego prowadzenia praktyki", pdf.styles['base']))
    pdf.elements.append(Paragraph("zawodowej jest ze strony naszej instytucji", pdf.styles['base']))
    pdf.add_spacer(15)
    
    osoba_upow = f"{oswiadczenie.osoba_upowazniona_imie} {oswiadczenie.osoba_upowazniona_nazwisko}, {oswiadczenie.osoba_upowazniona_stanowisko}" if oswiadczenie else "................................................................................................................................."
    pdf.elements.append(Paragraph(f"{osoba_upow}", pdf.styles['center']))
    pdf.elements.append(Paragraph("<small>(imię i nazwisko, stanowisko)</small>", pdf.styles['center']))
    pdf.add_spacer(40)
    
    t_podpis = Table([
        ["", Paragraph("..................................................", pdf.styles['center'])],
        ["", Paragraph("<small>Pieczęć imienna i podpis</small>", pdf.styles['center'])]
    ], colWidths=[240, 240])
    t_podpis.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('ALIGN', (1, 1), (1, 1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    pdf.elements.append(t_podpis)
    
    return pdf.build()

