erDiagram
    UZYTKOWNIK {
        int id PK
        string email UK
        string haslo_hash
        string imie
        string nazwisko
        string rola
        datetime created_at
        datetime updated_at
        bool aktywny
    }

    STUDENT {
        int id PK
        int uzytkownik_id FK
        string nr_albumu UK
        string kierunek
        string specjalnosc
        string tryb_studiow
        int rok_studiow
        datetime created_at
    }

    ZAKLAD_PRACY {
        int id PK
        string nazwa
        string nip UK
        string adres
        string miasto
        string email
        string telefon
        int zopz_id FK
        datetime created_at
    }

    PRAKTYKA {
        int id PK
        int student_id FK
        int zaklad_id FK
        int uopz_id FK
        string status
        date data_start
        date data_end
        int liczba_godzin
        datetime created_at
        datetime updated_at
    }

    DOKUMENT {
        int id PK
        int praktyka_id FK
        string typ_zalacznika
        string status
        string plik_path
        text uwagi_opiekuna
        int utworzony_przez FK
        datetime created_at
        datetime updated_at
    }

    WPIS_DZIENNIKA {
        int id PK
        int dokument_id FK
        int numer_dnia
        date data_wpisu
        text opis_prac
        string nr_efektu
        bool potwierdzony_zopz
        datetime potwierdzono_at
    }

    EFEKT_UCZENIA {
        int id PK
        int dokument_id FK
        string kod_efektu
        text opis_efektu
        bool uzyskany
        string podpis_zopz
        date data_podpisu
    }

    PROTOKOL {
        int id PK
        int praktyka_id FK
        float ocena_s
        float ocena_u
        float ocena_z
        float ocena_koncowa
        date data_egzaminu
        string przewodniczacy
        string plik_pdf_path
        datetime created_at
    }

    POROZUMIENIE {
        int id PK
        int praktyka_id FK
        int zaklad_id FK
        date data_podpisania
        string podpisal_dziekanat
        string status
        string plik_path
        datetime created_at
    }

    HISTORIA_STATUSU {
        int id PK
        int praktyka_id FK
        string status_poprzedni
        string status_nowy
        int zmieniony_przez FK
        datetime zmieniono_at
        text komentarz
    }

    UZYTKOWNIK ||--o| STUDENT : "ma profil"
    UZYTKOWNIK ||--o{ ZAKLAD_PRACY : "jest ZOPZ"
    STUDENT ||--o{ PRAKTYKA : "odbywa"
    ZAKLAD_PRACY ||--o{ PRAKTYKA : "przyjmuje"
    UZYTKOWNIK ||--o{ PRAKTYKA : "nadzoruje jako UOPZ"
    PRAKTYKA ||--|{ DOKUMENT : "zawiera"
    PRAKTYKA ||--o| PROTOKOL : "ma protokol"
    PRAKTYKA ||--o| POROZUMIENIE : "ma porozumienie"
    PRAKTYKA ||--o{ HISTORIA_STATUSU : "ma historie"
    DOKUMENT ||--o{ WPIS_DZIENNIKA : "zawiera wpisy"
    DOKUMENT ||--o{ EFEKT_UCZENIA : "zawiera efekty"
    UZYTKOWNIK ||--o{ HISTORIA_STATUSU : "wprowadzil"