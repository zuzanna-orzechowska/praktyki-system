graph TB
    subgraph KLIENT["Klient – Przeglądarka"]
        UI["Szablony Jinja2\nHTML / CSS / Bootstrap / JS"]
    end

    subgraph FLASK["Backend – Flask Application"]
        CONF["config.py\nSECRET_KEY, ENV"]
        AUTH["Flask-Login\nAutoryzacja + Zarządzanie sesją"]
        PERM["Dekoratory uprawnień\n@role_required('uopz', 'admin', ...)"]

        subgraph BP["Blueprints – Routery"]
            direction LR
            BPa["auth\n/login  /logout\n/reset-hasla"]
            BPb["student\n/moje-praktyki\n/dokumenty  /status"]
            BPc["uopz\n/studenci  /skierowania\n/hospitacje  /egzamin"]
            BPd["zopz\n/potwierdzenia\n/opinie  /dziennik"]
            BPe["dziekanat\n/porozumienia  /komisja\n/oswiadczenia  /wnioski"]
            BPf["admin\n/uzytkownicy  /role\n/konfiguracja"]
            BPg["dokumenty\n/generuj  /podgladaj\n/pobierz-pdf  /podpisz"]
        end

        FORMS["Formularze – Flask-WTF / WTForms\nname='pole[]' dla danych listowych\nrequest.form.getlist()"]
        JS["Dynamiczne wiersze – czysty JS\naddRow()  addAfter()  deleteRow()\nmanipulacja drzewem DOM"]
        PDF["Generowanie PDF\nWeasyPrint / ReportLab"]
        MAIL["Powiadomienia e-mail\nFlask-Mail"]
    end

    subgraph DANE["Warstwa Danych – JSON (faza I)"]
        direction LR
        HELPERS["Funkcje pomocnicze\nload_data()\nsave_data()"]
        J1["zal4_efekty/{nr_albumu}.json\nPotwierdzenie efektów uczenia się"]
        J2["zal6_dziennik/{nr_albumu}.json\nDziennik praktyki – wiersze tabeli"]
        J3["users.json\nUżytkownicy i role"]
        J4["praktyki.json\nPraktyki i statusy"]
        HELPERS --> J1
        HELPERS --> J2
        HELPERS --> J3
        HELPERS --> J4
    end

    subgraph MIGRACJA["Faza II – migracja do bazy danych"]
        DB[("PostgreSQL / SQLite\nSQLAlchemy + Flask-Migrate")]
    end

    UI <-->|"HTTP request / response"| FLASK
    AUTH --> PERM
    PERM --> BP
    BP --> FORMS
    FORMS --> JS
    BP --> DANE
    BPg --> PDF
    MAIL --> BP
    DANE -.->|"docelowo zastąpione przez"| MIGRACJA