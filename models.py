from extensions import db
from flask_login import UserMixin

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