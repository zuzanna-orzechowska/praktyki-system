erDiagram
    UZYTKOWNIK {
        int id PK
        string email UK
        string haslo_hash
        string imie
        string nazwisko
        string rola
        int aktywny
        datetime created_at
        datetime updated_at
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
        datetime updated_at
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

    HARMONOGRAM_PRAKTYKI {
        int id PK
        int dokument_id FK
        int lp
        string dzial_komorka
        int planowana_liczba_dni
    }

    WPIS_DZIENNIKA {
        int id PK
        int dokument_id FK
        int numer_dnia
        date data_wpisu
        text opis_prac
        string nr_efektu
        int potwierdzony_zopz
        datetime potwierdzono_at
    }

    EFEKT_UCZENIA {
        int id PK
        int dokument_id FK
        string kod_efektu
        text opis_efektu
        int uzyskany
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
    UZYTKOWNIK ||--o{ ZAKLAD_PRACY : "zarządza jako ZOPZ"
    UZYTKOWNIK ||--o{ PRAKTYKA : "nadzoruje jako UOPZ"
    UZYTKOWNIK ||--o{ DOKUMENT : "tworzy"
    UZYTKOWNIK ||--o{ HISTORIA_STATUSU : "zmienia status"
    STUDENT ||--o{ PRAKTYKA : "odbywa"
    ZAKLAD_PRACY ||--o{ PRAKTYKA : "przyjmuje"
    PRAKTYKA ||--|{ DOKUMENT : "posiada załączniki"
    PRAKTYKA ||--o| PROTOKOL : "kończy się"
    PRAKTYKA ||--o| POROZUMIENIE : "wymaga"
    PRAKTYKA ||--o{ HISTORIA_STATUSU : "rejestruje zmiany"
    DOKUMENT ||--o{ WPIS_DZIENNIKA : "ma wpisy (Zal 6)"
    DOKUMENT ||--o{ EFEKT_UCZENIA : "ma efekty (Zal 4)"
    DOKUMENT ||--o{ HARMONOGRAM_PRAKTYKI : "ma plan (Zal 2a)"