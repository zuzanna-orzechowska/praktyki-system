sequenceDiagram
    participant S as Student
    participant B as Backend (Flask)
    participant J as JSON Database
    participant O as Opiekun Uczelniany (UOPZ)

    S->>B: Wyślij dziennik do weryfikacji (POST /student/zal6)
    B->>B: Walidacja danych (Flask-WTF)

    alt dane niekompletne (brak wpisów / pustych pól)
        B-->>S: Zwróć błąd walidacji (flash message)
    else dane poprawne
        B->>J: Zapisz wpisy dziennika do zal6_dziennik/{nr_albumu}.json
        B->>J: Zmień status praktyki na 'Under_Review'
        B->>O: Powiadom e-mailem o nowym dokumencie (Flask-Mail)

        alt UOPZ odrzuca z uwagami
            O->>B: POST /uopz/dziennik/<id> – dodaj uwagi i odrzuć
            B->>J: Zapisz uwagi, zmień status na 'Rejected'
            B-->>S: Powiadom studenta o konieczności poprawy
        else UOPZ zatwierdza
            O->>B: POST /uopz/dziennik/<id> – zatwierdź
            B->>J: Zmień status na 'Approved'
            B-->>S: Powiadom studenta o zatwierdzeniu
        end
    end