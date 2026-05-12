from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Uzytkownik(db.Model, UserMixin):
    __tablename__ = 'uzytkownik'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    haslo_hash = db.Column(db.String(255), nullable=True) 
    imie = db.Column(db.String(50), nullable=False)
    nazwisko = db.Column(db.String(50), nullable=False)
    rola = db.Column(db.String(50), nullable=False)
    aktywny = db.Column(db.Integer, default=1)
    
    auth_provider = db.Column(db.String(50), default="microsoft")
    external_id = db.Column(db.String(255), unique=True)

    @property
    def is_active(self):
        return bool(self.aktywny)

    def get_id(self):
        return str(self.id)
    
    def set_password(self, password):
        self.haslo_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.haslo_hash:
            return False
        return check_password_hash(self.haslo_hash, password)

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
    zaklad_id = db.Column(db.Integer, db.ForeignKey('zaklad_pracy.id'), nullable=True)
    uopz_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=True)
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
    komentarz = db.Column(db.Text, nullable=True)
    
    praktyka = db.relationship('Praktyka', backref=db.backref('dokumenty', lazy=True))

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

class EfektUczenia(db.Model):
    __tablename__ = 'efekt_uczenia'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False)
    kod_efektu = db.Column(db.String(20), nullable=False)
    opis_efektu = db.Column(db.Text, nullable=False)
    uzyskany = db.Column(db.Integer, default=0)  # 1 = uzyskał, 0 = nie uzyskał / oczekuje
    podpis_zopz = db.Column(db.String(255))
    data_podpisu = db.Column(db.Date)
    
    dokument = db.relationship('Dokument', backref=db.backref('efekty', cascade="all, delete-orphan"))

class WniosekZaliczeniePraktyki(db.Model):
    __tablename__ = 'wniosek_zaliczenie_praktyki'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False, unique=True)
    uzasadnienie = db.Column(db.Text, nullable=False)
    okres_zatrudnienia_od = db.Column(db.Date, nullable=False)
    okres_zatrudnienia_do = db.Column(db.Date, nullable=False)
    stanowisko = db.Column(db.String(255), nullable=False)
    zakres_obowiazkow = db.Column(db.Text, nullable=True)

    
    #lista ścieżek do załączonych plików
    zalaczniki_paths = db.Column(db.Text) 
    
    dokument = db.relationship('Dokument', backref=db.backref('wniosek_zaliczenie', uselist=False, cascade="all, delete-orphan"))

class Oswiadczenie(db.Model):
    __tablename__ = 'oswiadczenie'
    
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False, unique=True)
    miejscowosc = db.Column(db.String(100), nullable=False)
    data_oswiadczenia = db.Column(db.Date, nullable=False)
    nazwa_instytucji = db.Column(db.String(255), nullable=False)
    opiekun_imie_nazwisko = db.Column(db.String(255), nullable=False)
    opiekun_stanowisko = db.Column(db.String(255), nullable=False)
    opiekun_telefon = db.Column(db.String(50), nullable=False)
    opiekun_email = db.Column(db.String(120), nullable=False)
    osoba_upowazniona = db.Column(db.String(255), nullable=False)

    skan_path = db.Column(db.String(255), nullable=False) 
    
    dokument = db.relationship('Dokument', backref=db.backref('oswiadczenie', uselist=False, cascade="all, delete-orphan"))

class ProgramPraktyki(db.Model):
    __tablename__ = 'program_praktyki'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False)
    kod_efektu = db.Column(db.String(10), nullable=False) # np. '01', '02'
    dzial_prace = db.Column(db.Text)
    
    dokument = db.relationship('Dokument', backref=db.backref('programy', cascade="all, delete-orphan"))