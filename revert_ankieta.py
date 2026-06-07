from app import create_app, db
from models import Student, Praktyka, Uzytkownik, Ankieta
app = create_app()
with app.app_context():
    user = Uzytkownik.query.filter_by(imie='Zuzanna').first()
    if user:
        student = Student.query.filter_by(uzytkownik_id=user.id).first()
        if student:
            praktyka = Praktyka.query.filter_by(student_id=student.id).first()
            if praktyka:
                praktyka.ankieta_wypelniona = False
                db.session.commit()
                print("Zaktualizowano praktyke: ankieta_wypelniona=False")
    
    # Delete the last ankieta
    ankieta = Ankieta.query.order_by(Ankieta.id.desc()).first()
    if ankieta:
        db.session.delete(ankieta)
        db.session.commit()
        print("Usunieto ostatnia ankiete.")
