from extensions import db
from flask_login import UserMixin
from datetime import datetime

class Uzytkownik(db.Model, UserMixin):
    __tablename__ = 'uzytkownik'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    haslo_hash = db.Column(db.String(255), nullable=False)
    imie = db.Column(db.String(50), nullable=False)
    nazwisko = db.Column(db.String(50), nullable=False)
    rola = db.Column(db.String(20), nullable=False)
    aktywny = db.Column(db.Integer, default=1)

    @property
    def is_active(self):
        return bool(self.aktywny)

    def get_id(self):
        return str(self.id)

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)
    nr_albumu = db.Column(db.String(20), unique=True, nullable=False)
    kierunek = db.Column(db.String(100), default='informatyka')
    specjalnosc = db.Column(db.String(100))
    tryb_studiow = db.Column(db.String(50))
    rok_studiow = db.Column(db.Integer)
    uzytkownik = db.relationship('Uzytkownik', backref=db.backref('student_profil', uselist=False))

class ZakladPracy(db.Model):
    __tablename__ = 'zaklad_pracy'
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(255), nullable=False)
    nip = db.Column(db.String(20), unique=True)
    adres = db.Column(db.String(255))
    miasto = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telefon = db.Column(db.String(50))
    zopz_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'))

class Praktyka(db.Model):
    __tablename__ = 'praktyka'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    zaklad_id = db.Column(db.Integer, db.ForeignKey('zaklad_pracy.id'), nullable=False)
    uopz_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)
    status = db.Column(db.String(50), default='OCZEKUJE_NA_ZAL9')
    data_start = db.Column(db.Date)
    data_end = db.Column(db.Date)
    
    liczba_godzin = db.Column(db.Integer, default=960)
    
    student = db.relationship('Student', backref='praktyki')
    zaklad = db.relationship('ZakladPracy')

class Dokument(db.Model):
    __tablename__ = 'dokument'
    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), nullable=False)
    typ_zalacznika = db.Column(db.String(20), nullable=False) # np. 'ZAL6'
    status = db.Column(db.String(50), default='Draft')
    utworzony_przez = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)

class WpisDziennika(db.Model):
    __tablename__ = 'wpis_dziennika'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False)
    numer_dnia = db.Column(db.Integer, nullable=False)
    data_wpisu = db.Column(db.Date, nullable=False)
    opis_prac = db.Column(db.Text, nullable=False)
    nr_efektu = db.Column(db.String(100))
    potwierdzony_zopz = db.Column(db.Integer, default=0)
    
    dokument = db.relationship('Dokument', backref=db.backref('wpisy', cascade="all, delete-orphan"))

class Porozumienie(db.Model):
    __tablename__ = 'porozumienie'
    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), unique=True, nullable=False)
    zaklad_id = db.Column(db.Integer, db.ForeignKey('zaklad_pracy.id'), nullable=False)
    data_podpisania = db.Column(db.Date)
    podpisal_dziekanat = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Draft')
    plik_path = db.Column(db.String(255))
    praktyka = db.relationship('Praktyka', backref=db.backref('porozumienie', uselist=False))
    zaklad = db.relationship('ZakladPracy')

class HarmonogramPraktyki(db.Model):
    __tablename__ = 'harmonogram_praktyki'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False)
    lp = db.Column(db.Integer, nullable=False)
    dzial_komorka = db.Column(db.String(255), nullable=False)
    planowana_liczba_dni = db.Column(db.Integer, nullable=False)
    dokument = db.relationship('Dokument', backref=db.backref('pozycje_harmonogramu', cascade="all, delete-orphan"))

class Protokol(db.Model):
    __tablename__ = 'protokol'
    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), unique=True, nullable=False)
    ocena_s = db.Column(db.Float)  # ocena za sprawozdanie
    ocena_u = db.Column(db.Float)  # ocena UOPZ
    ocena_z = db.Column(db.Float)  # ocena ZOPZ
    ocena_koncowa = db.Column(db.Float)
    data_egzaminu = db.Column(db.Date)
    przewodniczacy = db.Column(db.String(255))
    plik_pdf_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    praktyka = db.relationship('Praktyka', backref=db.backref('protokol', uselist=False))

class Sprawozdanie(db.Model):
    __tablename__ = 'sprawozdanie'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False, unique=True)
    charakterystyka = db.Column(db.Text, nullable=False)
    opis_prac = db.Column(db.Text, nullable=False)
    wiedza_umiejetnosci = db.Column(db.Text, nullable=False)
    
    dokument = db.relationship('Dokument', backref=db.backref('sprawozdanie', uselist=False, cascade="all, delete-orphan"))