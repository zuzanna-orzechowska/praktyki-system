from extensions import db
from flask_login import UserMixin
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash


class DictSerializable:
    def to_dict(self):
        result = {}
        for c in self.__table__.columns:
            val = getattr(self, c.name)
            if isinstance(val, (date, datetime)):
                val = val.isoformat()
            result[c.name] = val
        return result

class Uzytkownik(db.Model, UserMixin, DictSerializable):
    __tablename__ = 'uzytkownik'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    haslo_hash = db.Column(db.String(255), nullable=True) 
    tytul_naukowy = db.Column(db.String(50), nullable=True)
    imie = db.Column(db.String(50), nullable=False)
    nazwisko = db.Column(db.String(50), nullable=False)
    rola = db.Column(db.String(50), nullable=False)
    aktywny = db.Column(db.Integer, default=1)
    wymaga_zmiany_hasla = db.Column(db.Boolean, default=False)
    
    auth_provider = db.Column(db.String(50), default="microsoft")
    external_id = db.Column(db.String(255), unique=True)
    data_utworzenia = db.Column(db.DateTime, default=datetime.utcnow)

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

class Student(db.Model, DictSerializable):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)
    nr_albumu = db.Column(db.String(20), unique=True, nullable=False)
    kierunek = db.Column(db.String(100), default='informatyka')
    specjalnosc = db.Column(db.String(100))
    tryb_studiow = db.Column(db.String(50))
    rok_studiow = db.Column(db.Integer)
    rok_akademicki = db.Column(db.String(20))
    uzytkownik = db.relationship('Uzytkownik', backref=db.backref('student_profil', uselist=False))

class ZakladPracy(db.Model, DictSerializable):
    __tablename__ = 'zaklad_pracy'
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(255), nullable=False)
    nip = db.Column(db.String(20), unique=True)
    # adres = db.Column(db.String(255)) # Deprecated
    ulica = db.Column(db.String(150))
    nr_budynku = db.Column(db.String(20))
    nr_lokalu = db.Column(db.String(20))
    kod_pocztowy = db.Column(db.String(20))
    miasto = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telefon = db.Column(db.String(50))
    zopz_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'))

class Praktyka(db.Model, DictSerializable):
    __tablename__ = 'praktyka'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    zaklad_id = db.Column(db.Integer, db.ForeignKey('zaklad_pracy.id'), nullable=True)
    uopz_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=True)
    status = db.Column(db.String(50), default='OCZEKUJE_NA_ZAL9')
    data_start = db.Column(db.Date)
    data_end = db.Column(db.Date)
    
    liczba_godzin = db.Column(db.Integer, default=960)
    ankieta_wypelniona = db.Column(db.Boolean, default=False)
    
    student = db.relationship('Student', backref='praktyki')
    zaklad = db.relationship('ZakladPracy')

class Dokument(db.Model, DictSerializable):
    __tablename__ = 'dokument'
    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), nullable=False)
    typ_zalacznika = db.Column(db.String(20), nullable=False) # np. 'ZAL6'
    status = db.Column(db.String(50), default='Draft')
    plik_path = db.Column(db.String(255), nullable=True)
    uwagi_opiekuna = db.Column(db.Text, nullable=True)
    utworzony_przez = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)
    komentarz = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    praktyka = db.relationship('Praktyka', backref=db.backref('dokumenty', lazy=True))

class WpisDziennika(db.Model, DictSerializable):
    __tablename__ = 'wpis_dziennika'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False)
    numer_dnia = db.Column(db.Integer, nullable=False)
    data_wpisu = db.Column(db.Date, nullable=False)
    opis_prac = db.Column(db.Text, nullable=False)
    nr_efektu = db.Column(db.String(100))
    potwierdzony_zopz = db.Column(db.Integer, default=0)
    komentarz_zopz = db.Column(db.Text, nullable=True)
    
    dokument = db.relationship('Dokument', backref=db.backref('wpisy', cascade="all, delete-orphan"))

class Porozumienie(db.Model, DictSerializable):
    __tablename__ = 'porozumienie'
    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), unique=True, nullable=False)
    zaklad_id = db.Column(db.Integer, db.ForeignKey('zaklad_pracy.id'), nullable=False)
    data_podpisania = db.Column(db.Date)
    podpisal_dziekanat = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Draft')
    plik_path = db.Column(db.String(255))
    komentarz_zopz = db.Column(db.Text, nullable=True)
    praktyka = db.relationship('Praktyka', backref=db.backref('porozumienie', uselist=False))
    zaklad = db.relationship('ZakladPracy')

class HarmonogramPraktyki(db.Model, DictSerializable):
    __tablename__ = 'harmonogram_praktyki'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False)
    lp = db.Column(db.Integer, nullable=False)
    dzial_komorka = db.Column(db.String(255), nullable=False)
    planowana_liczba_dni = db.Column(db.Integer, nullable=False)
    dokument = db.relationship('Dokument', backref=db.backref('pozycje_harmonogramu', cascade="all, delete-orphan"))

class Protokol(db.Model, DictSerializable):
    __tablename__ = 'protokol'
    id = db.Column(db.Integer, primary_key=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), unique=True, nullable=False)
    ocena_s = db.Column(db.Float)  # ocena za sprawozdanie
    ocena_u = db.Column(db.Float)  # ocena UOPZ
    ocena_z = db.Column(db.Float)  # ocena ZOPZ
    ocena_koncowa = db.Column(db.Float)
    data_egzaminu = db.Column(db.Date)
    przewodniczacy = db.Column(db.String(255))
    
    instytucja_1 = db.Column(db.String(255))
    okres_1 = db.Column(db.String(100))
    instytucja_2 = db.Column(db.String(255))
    okres_2 = db.Column(db.String(100))
    
    komisja_2 = db.Column(db.String(255))
    komisja_3 = db.Column(db.String(255))
    rola_3 = db.Column(db.String(255))
    komisja_4 = db.Column(db.String(255))
    rola_4 = db.Column(db.String(255))
    
    pytanie_1 = db.Column(db.Text)
    ocena_czastkowa_1 = db.Column(db.Float)
    pytanie_2 = db.Column(db.Text)
    ocena_czastkowa_2 = db.Column(db.Float)
    pytanie_3 = db.Column(db.Text)
    ocena_czastkowa_3 = db.Column(db.Float)
    
    ocena_e = db.Column(db.Float)
    ocena_k_slownie = db.Column(db.String(255))
    
    plik_pdf_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    praktyka = db.relationship('Praktyka', backref=db.backref('protokol', uselist=False))

class Sprawozdanie(db.Model, DictSerializable):
    __tablename__ = 'sprawozdanie'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False, unique=True)
    charakterystyka = db.Column(db.Text, nullable=False)
    opis_prac = db.Column(db.Text, nullable=False)
    wiedza_umiejetnosci = db.Column(db.Text, nullable=False)
    uwagi_zopz = db.Column(db.Text, nullable=True)
    podpis_zopz = db.Column(db.String(255), nullable=True)
    podpis_uopz = db.Column(db.String(255), nullable=True)
    
    dokument = db.relationship('Dokument', backref=db.backref('sprawozdanie', uselist=False, cascade="all, delete-orphan"))

class ZalacznikDziennika(db.Model, DictSerializable):
    __tablename__ = 'zalacznik_dziennika'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id', ondelete='CASCADE'), nullable=False)
    opis = db.Column(db.Text, nullable=False)
    plik_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EfektUczenia(db.Model, DictSerializable):
    __tablename__ = 'efekt_uczenia'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False)
    kod_efektu = db.Column(db.String(20), nullable=False)
    opis_efektu = db.Column(db.Text, nullable=False)
    uzyskany = db.Column(db.Integer, default=0)  # 1 = uzyskał, 0 = nie uzyskał / oczekuje
    podpis_zopz = db.Column(db.String(255))
    data_podpisu = db.Column(db.Date)
    
    dokument = db.relationship('Dokument', backref=db.backref('efekty', cascade="all, delete-orphan"))

class WniosekZaliczeniePraktyki(db.Model, DictSerializable):
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

class Oswiadczenie(db.Model, DictSerializable):
    __tablename__ = 'oswiadczenie'
    
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False, unique=True)
    termin_od = db.Column(db.Date)
    termin_do = db.Column(db.Date)
    rok_studiow = db.Column(db.Integer)
    kierunek = db.Column(db.String(100))
    miejscowosc = db.Column(db.String(100), nullable=False)
    data_oswiadczenia = db.Column(db.Date, nullable=False)
    nazwa_instytucji = db.Column(db.String(255), nullable=False)
    opiekun_imie = db.Column(db.String(100), nullable=False)
    opiekun_nazwisko = db.Column(db.String(150), nullable=False)
    opiekun_stanowisko = db.Column(db.String(255), nullable=False)
    opiekun_telefon = db.Column(db.String(50), nullable=False)
    opiekun_email = db.Column(db.String(120), nullable=False)
    osoba_upowazniona_imie = db.Column(db.String(100), nullable=False)
    osoba_upowazniona_nazwisko = db.Column(db.String(150), nullable=False)
    osoba_upowazniona_stanowisko = db.Column(db.String(255), nullable=False)

    skan_path = db.Column(db.String(255), nullable=False) 
    
    dokument = db.relationship('Dokument', backref=db.backref('oswiadczenie', uselist=False, cascade="all, delete-orphan"))

class ProgramPraktyki(db.Model, DictSerializable):
    __tablename__ = 'program_praktyki'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False)
    kod_efektu = db.Column(db.String(10), nullable=False) # np. '01', '02'
    dzial_prace = db.Column(db.Text)
    
    dokument = db.relationship('Dokument', backref=db.backref('programy', cascade="all, delete-orphan"))

class Zal2aPodpisy(db.Model, DictSerializable):
    __tablename__ = 'zal2a_podpisy'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False, unique=True)
    podpis_uopz = db.Column(db.String(255))
    data_uopz = db.Column(db.Date)
    podpis_zopz = db.Column(db.String(255))
    data_zopz = db.Column(db.Date)
    podpis_student = db.Column(db.String(255))
    data_student = db.Column(db.Date)
    
    dokument = db.relationship('Dokument', backref=db.backref('zal2a_podpisy', uselist=False, cascade="all, delete-orphan"))

class Powiadomienie(db.Model, DictSerializable):
    __tablename__ = 'powiadomienie'
    id = db.Column(db.Integer, primary_key=True)
    uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)
    tresc = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    przeczytane = db.Column(db.Boolean, default=False)
    data_utworzenia = db.Column(db.DateTime, default=datetime.utcnow)
    
    uzytkownik = db.relationship('Uzytkownik', backref=db.backref('powiadomienia', cascade="all, delete-orphan"))

class KartaPraktyki(db.Model, DictSerializable):
    __tablename__ = 'karta_praktyki'
    id = db.Column(db.Integer, primary_key=True)
    dokument_id = db.Column(db.Integer, db.ForeignKey('dokument.id'), nullable=False, unique=True)
    
    # Skierowanie
    podpis_dyrektora = db.Column(db.String(255))
    skierowanie_data = db.Column(db.Date)
    
    # Zgłoszenie i BHP (ZOPZ)
    data_zgloszenia = db.Column(db.Date)
    podpis_zgloszenie = db.Column(db.String(255))
    data_bhp = db.Column(db.Date)
    podpis_bhp = db.Column(db.String(255))
    
    # Zaświadczenie (ZOPZ)
    zaswiadczenie_uwagi = db.Column(db.Text)
    zaswiadczenie_data = db.Column(db.Date)
    podpis_zaswiadczenie = db.Column(db.String(255))
    
    # Oceny (ZOPZ)
    ocena_zopz_param = db.Column(db.Float)
    ocena_zopz_opis = db.Column(db.Text)
    ocena_zopz_data = db.Column(db.Date)
    podpis_zopz = db.Column(db.String(255))
    
    # Oceny (UOPZ)
    ocena_uopz_param = db.Column(db.Float)
    ocena_uopz_opis = db.Column(db.Text)
    ocena_uopz_data = db.Column(db.Date)
    podpis_uopz = db.Column(db.String(255))
    ocena_sprawozdania = db.Column(db.Float)
    
    # Dziekanat
    akceptacja_dziekanat = db.Column(db.Boolean, default=False)
    akceptacja_dziekanat_data = db.Column(db.Date)
    
    dokument = db.relationship('Dokument', backref=db.backref('karta_praktyki', uselist=False, cascade="all, delete-orphan"))

class Ankieta(db.Model, DictSerializable):
    __tablename__ = 'ankieta'
    id = db.Column(db.Integer, primary_key=True)
    odpowiedzi = db.Column(db.String(255), nullable=False) # Przechowywanie odpowiedzi JSON (lista 1-5 dla 14 pytań)
    uwagi = db.Column(db.Text, nullable=True)
    rok_akademicki = db.Column(db.String(20), nullable=False)
    kierunek = db.Column(db.String(100), nullable=False)
    forma_studiow = db.Column(db.String(50), nullable=False)
    semestr = db.Column(db.Integer, nullable=False)
    liczba_godzin = db.Column(db.Integer, nullable=False)
    data_utworzenia = db.Column(db.DateTime, default=datetime.utcnow)