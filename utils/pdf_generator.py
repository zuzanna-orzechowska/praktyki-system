import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from flask import current_app

def generate_zal7a_pdf(student, praktyka, sprawozdanie):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
        title=f"Zalacznik_7a_{student.nr_albumu}"
    )

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
    
    style_right = ParagraphStyle(
        'RightStyle',
        parent=base_style,
        alignment=2 # Right
    )
    
    style_center = ParagraphStyle(
        'CenterStyle',
        parent=base_style,
        alignment=1 # Center
    )
    
    style_header_bold = ParagraphStyle(
        'HeaderBold',
        parent=base_style,
        fontName='DejaVuSerif-Bold',
        fontSize=12,
        leading=14
    )

    style_title = ParagraphStyle(
        'TitleStyle',
        parent=base_style,
        fontName='DejaVuSerif-Bold',
        fontSize=12,
        alignment=1, # Center
        spaceBefore=25,
        spaceAfter=20,
        leading=16
    )
    
    style_section_title = ParagraphStyle(
        'SectionTitle',
        parent=base_style,
        fontName='DejaVuSerif-Bold',
        fontSize=11,
        spaceBefore=15,
        spaceAfter=0
    )
    
    style_italic_desc = ParagraphStyle(
        'ItalicDesc',
        parent=base_style,
        fontName='DejaVuSerif-Italic',
        fontSize=11,
        spaceBefore=0,
        spaceAfter=15,
        leftIndent=15 # Indent to match Roman numeral width
    )

    elements = []

    # Top right
    elements.append(Paragraph("Załącznik nr 7a", style_right))
    elements.append(Spacer(1, 15))

    # Top left
    elements.append(Paragraph("<b>Akademia Nauk Stosowanych<br/>w Elblągu</b>", style_header_bold))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>Instytut Informatyki Stosowanej</b><br/><i>im. Krzysztofa Brzeskiego</i>", base_style))
    elements.append(Spacer(1, 25))

    # Student Data
    imie_nazwisko = f"{student.uzytkownik.imie} {student.uzytkownik.nazwisko.split('(')[0].strip()}"
    album = student.nr_albumu or ("." * 15)
    kierunek = student.kierunek or "informatyka"
    specjalnosc = student.specjalnosc or ("." * 60)
    tryb = "inżynierskie niestacjonarne"
    rok = student.rok_akademicki or ("." * 30)
    
    data_table = [
        [Paragraph(f"Student: <b>{imie_nazwisko}</b>", base_style), Paragraph(f"Nr albumu: <b>{album}</b>", base_style)],
        [Paragraph(f"Kierunek: <b>{kierunek}</b>", base_style), ""],
        [Paragraph(f"Specjalność: <b>{specjalnosc}</b>", base_style), ""],
        [Paragraph(f"Studia: <b>{tryb}</b>", base_style), ""],
        [Paragraph(f"Rok ak.: <b>{rok}</b>", base_style), ""]
    ]
    
    t = Table(data_table, colWidths=[350, 150])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN', (0,1), (1,1)), 
        ('SPAN', (0,2), (1,2)),
        ('SPAN', (0,3), (1,3)),
        ('SPAN', (0,4), (1,4)),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 20),
    ]))
    elements.append(t)

    # Title
    elements.append(Paragraph("SPRAWOZDANIE STUDENTA<br/>Z PRAKTYKI ZAWODOWEJ REALIZOWANEJ<br/>NA PODSTAWIE PRACY ZAWODOWEJ LUB DZIAŁALNOŚCI GOSPODARCZEJ", style_title))

    # Place
    miejsce = praktyka.zaklad.nazwa if praktyka and praktyka.zaklad else ("." * 80)
    elements.append(Paragraph(f"odbytej w <b>{miejsce}</b>", base_style))
    elements.append(Spacer(1, 25))

    # Section I
    elements.append(Paragraph("I.&nbsp;&nbsp; CHARAKTERYSTYKA MIEJSCA PRACY", style_section_title))
    elements.append(Paragraph("(Krótki opis instytucji)", style_italic_desc))
    charakterystyka = sprawozdanie.charakterystyka if sprawozdanie and sprawozdanie.charakterystyka else ""
    if charakterystyka:
        elements.append(Paragraph(f"{charakterystyka.replace(chr(10), '<br/>')}", base_style))
    elements.append(Spacer(1, 20))

    # Section II
    elements.append(Paragraph("II. OPIS I ANALIZA WYKONYWANYCH PRAC", style_section_title))
    elements.append(Paragraph("(Syntetyczny opis wykonanych prac)", style_italic_desc))
    opis = sprawozdanie.opis_prac if sprawozdanie and sprawozdanie.opis_prac else ""
    if opis:
        elements.append(Paragraph(f"{opis.replace(chr(10), '<br/>')}", base_style))
    elements.append(Spacer(1, 20))

    # Section III
    elements.append(Paragraph("III. WIEDZA I UMIEJĘTNOŚCI UZYSKANE W TRAKCIE PRACY ZAWODOWEJ LUB DZIAŁALNOŚCI GOSPODARCZEJ", style_section_title))
    elements.append(Paragraph("(Samoocena w zakresie nabytych kompetencji oraz osiągniętych efektów uczenia się)", style_italic_desc))
    wiedza = sprawozdanie.wiedza_umiejetnosci if sprawozdanie and sprawozdanie.wiedza_umiejetnosci else ""
    if wiedza:
        elements.append(Paragraph(f"{wiedza.replace(chr(10), '<br/>')}", base_style))
    elements.append(Spacer(1, 50))

    # Signatures
    podpis_text = sprawozdanie.podpis_studenta if sprawozdanie and sprawozdanie.podpis_studenta else "........................................................................"
    
    if sprawozdanie and sprawozdanie.podpis_studenta:
        # Use italic and cursive-like font for signature if possible
        sig1_val = Paragraph(f"<font fontName='DejaVuSerif-Italic' color='#004a99'>{podpis_text}</font>", style_center)
    else:
        sig1_val = podpis_text

    sig_table_1 = [
        ["", sig1_val],
        ["", Paragraph("<small>data i podpis studenta</small>", style_center)]
    ]
    t_sig1 = Table(sig_table_1, colWidths=[280, 200])
    t_sig1.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_sig1)
    
    elements.append(Spacer(1, 30))
    
    sig_table_2 = [
        ["", "........................................................................"],
        ["", Paragraph("<small>data i podpis bezpośredniego przełożonego<br/>lub uczelnianego opiekuna praktyk</small>", style_center)]
    ]
    t_sig2 = Table(sig_table_2, colWidths=[200, 280])
    t_sig2.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(t_sig2)

    doc.build(elements)
    
    buffer.seek(0)
    return buffer
