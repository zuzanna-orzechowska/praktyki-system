erDiagram
    UZYTKOWNIK {
        int id PK
        string email UK
        string haslo_hash
        string imie
        string nazwisko
        string rola
        int aktywny
        boolean wymaga_zmiany_hasla
        string auth_provider
        string external_id UK
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
    }

    DOKUMENT {
        int id PK
        int praktyka_id FK
        string typ_zalacznika
        string status
        string plik_path
        text uwagi_opiekuna
        text komentarz
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

    HARMONOGRAM_PRAKTYKI {
        int id PK
        int dokument_id FK
        int lp
        string dzial_komorka
        int planowana_liczba_dni
    }

    SPRAWOZDANIE {
        int id PK
        int dokument_id FK
        text charakterystyka
        text opis_prac
        text wiedza_umiejetnosci
    }

    WNIOSEK_ZALICZENIE_PRAKTYKI {
        int id PK
        int dokument_id FK
        text uzasadnienie
        date okres_zatrudnienia_od
        date okres_zatrudnienia_do
        string stanowisko
        text zalaczniki_paths
    }

    OSWIADCZENIE {
        int id PK
        int dokument_id FK
        date termin_od
        date termin_do
        int rok_studiow
        string kierunek
        string miejscowosc
        date data_oswiadczenia
        string nazwa_instytucji
        string opiekun_imie
        string opiekun_nazwisko
        string opiekun_stanowisko
        string opiekun_telefon
        string opiekun_email
        string osoba_upowazniona_imie
        string osoba_upowazniona_nazwisko
        string osoba_upowazniona_stanowisko
        string skan_path
    }

    PROGRAM_PRAKTYKI {
        int id PK
        int dokument_id FK
        string kod_efektu
        text dzial_prace
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
    
    DOKUMENT ||--o{ WPIS_DZIENNIKA : "ma wpisy (Zał. 6)"
    DOKUMENT ||--o{ EFEKT_UCZENIA : "ma efekty (Zał. 4)"
    DOKUMENT ||--o{ HARMONOGRAM_PRAKTYKI : "ma plan (Zał. 2a)"
    DOKUMENT ||--o{ PROGRAM_PRAKTYKI : "ma program (Zał. 2a)"
    
    DOKUMENT ||--o| SPRAWOZDANIE : "zawiera (Zał. 7)"
    DOKUMENT ||--o| WNIOSEK_ZALICZENIE_PRAKTYKI : "zawiera (Zał. 4b)"
    DOKUMENT ||--o| OSWIADCZENIE : "zawiera (Zał. 9)"