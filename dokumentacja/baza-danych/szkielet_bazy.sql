-- ============================================================
-- Szkielet bazy danych – SQLite (faza I) / PostgreSQL (faza II)
-- ============================================================

PRAGMA foreign_keys = ON;  -- wymagane w SQLite

-- ------------------------------------------------------------
-- 1. UŻYTKOWNICY I ROLE
-- ------------------------------------------------------------
CREATE TABLE uzytkownik (
    id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    email       TEXT        NOT NULL UNIQUE,
    haslo_hash  TEXT        NOT NULL,
    imie        TEXT        NOT NULL,
    nazwisko    TEXT        NOT NULL,
    rola        TEXT        NOT NULL CHECK (rola IN ('student', 'uopz', 'zopz', 'dziekanat', 'admin')),
    aktywny     INTEGER     NOT NULL DEFAULT 1,  -- 1 = aktywny, 0 = zablokowany
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 2. PROFIL STUDENTA
-- ------------------------------------------------------------
CREATE TABLE student (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    uzytkownik_id   INTEGER     NOT NULL UNIQUE,
    nr_albumu       TEXT        NOT NULL UNIQUE,
    kierunek        TEXT        NOT NULL DEFAULT 'informatyka',
    specjalnosc     TEXT,
    tryb_studiow    TEXT        NOT NULL CHECK (tryb_studiow IN ('stacjonarne', 'niestacjonarne')),
    rok_studiow     INTEGER     NOT NULL,
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (uzytkownik_id) REFERENCES uzytkownik(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 3. ZAKŁAD PRACY
-- ------------------------------------------------------------
CREATE TABLE zaklad_pracy (
    id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    nazwa       TEXT        NOT NULL,
    nip         TEXT        UNIQUE,
    adres       TEXT,
    miasto      TEXT,
    email       TEXT,
    telefon     TEXT,
    zopz_id     INTEGER,
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (zopz_id) REFERENCES uzytkownik(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- 4. PRAKTYKA ZAWODOWA (encja główna)
-- ------------------------------------------------------------
CREATE TABLE praktyka (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER     NOT NULL,
    zaklad_id       INTEGER     NOT NULL,
    uopz_id         INTEGER     NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'OCZEKUJE_NA_ZAL9'
                                CHECK (status IN (
                                    'OCZEKUJE_NA_ZAL9',
                                    'ZAL9_PRZYJETY',
                                    'POROZUMIENIE_PODPISANE',
                                    'PROGRAM_UZGODNIONY',
                                    'SKIEROWANIE_WYDANE',
                                    'PRAKTYKA_W_TOKU',
                                    'DOKUMENTY_ZLOZONE',
                                    'EGZAMIN',
                                    'PROTOKOL_SPORZADZONY',
                                    'ZALICZONA',
                                    'ODRZUCONA',
                                    'PRZEDLUZONA'
                                )),
    data_start      DATE,
    data_end        DATE,
    liczba_godzin   INTEGER     DEFAULT 960,
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)    REFERENCES student(id)      ON DELETE RESTRICT,
    FOREIGN KEY (zaklad_id)     REFERENCES zaklad_pracy(id) ON DELETE RESTRICT,
    FOREIGN KEY (uopz_id)       REFERENCES uzytkownik(id)   ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- 5. DOKUMENT (ogólna tabela dla wszystkich załączników)
-- ------------------------------------------------------------
CREATE TABLE dokument (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER     NOT NULL,
    typ_zalacznika  TEXT        NOT NULL CHECK (typ_zalacznika IN (
                                    'ZAL1', 'ZAL2', 'ZAL2A', 'ZAL3',
                                    'ZAL4', 'ZAL4A', 'ZAL4B',
                                    'ZAL5', 'ZAL6', 'ZAL7', 'ZAL7A',
                                    'ZAL8', 'ZAL9'
                                )),
    status          TEXT        NOT NULL DEFAULT 'Draft'
                                CHECK (status IN (
                                    'Draft', 'Submitted', 'Under_Review',
                                    'Rejected', 'Approved', 'Closed'
                                )),
    plik_path       TEXT,                   -- ścieżka do wygenerowanego PDF
    uwagi_opiekuna  TEXT,                   -- uwagi UOPZ przy odrzuceniu
    utworzony_przez INTEGER     NOT NULL,   -- id użytkownika
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (praktyka_id)     REFERENCES praktyka(id)   ON DELETE CASCADE,
    FOREIGN KEY (utworzony_przez) REFERENCES uzytkownik(id) ON DELETE RESTRICT,

    -- jeden załącznik danego typu na praktykę
    UNIQUE (praktyka_id, typ_zalacznika)
);

-- ------------------------------------------------------------
-- 6. WPISY DZIENNIKA PRAKTYKI (Zał. 6 – tabela dynamiczna)
-- ------------------------------------------------------------
CREATE TABLE wpis_dziennika (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    dokument_id         INTEGER     NOT NULL,
    numer_dnia          INTEGER     NOT NULL,
    data_wpisu          DATE        NOT NULL,
    opis_prac           TEXT        NOT NULL,
    nr_efektu           TEXT,                   -- np. "EK_01, EK_03"
    potwierdzony_zopz   INTEGER     NOT NULL DEFAULT 0,  -- 0 = nie, 1 = tak
    potwierdzono_at     DATETIME,

    FOREIGN KEY (dokument_id) REFERENCES dokument(id) ON DELETE CASCADE,

    UNIQUE (dokument_id, numer_dnia)
);

-- ------------------------------------------------------------
-- 7. EFEKTY UCZENIA SIĘ (Zał. 4)
-- ------------------------------------------------------------
CREATE TABLE efekt_uczenia (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    dokument_id     INTEGER     NOT NULL,
    kod_efektu      TEXT        NOT NULL,   -- np. "EK_01"
    opis_efektu     TEXT        NOT NULL,
    uzyskany        INTEGER     NOT NULL DEFAULT 0,  -- 0 = nie, 1 = tak
    podpis_zopz     TEXT,
    data_podpisu    DATE,

    FOREIGN KEY (dokument_id) REFERENCES dokument(id) ON DELETE CASCADE,

    UNIQUE (dokument_id, kod_efektu)
);

-- ------------------------------------------------------------
-- 8. PROTOKÓŁ EGZAMINU (Zał. 8)
-- ------------------------------------------------------------
CREATE TABLE protokol (
    id              INTEGER     PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER     NOT NULL UNIQUE,
    ocena_s         REAL,                   -- ocena za sprawozdanie
    ocena_u         REAL,                   -- ocena UOPZ
    ocena_z         REAL,                   -- ocena ZOPZ
    ocena_koncowa   REAL,
    data_egzaminu   DATE,
    przewodniczacy  TEXT,
    plik_pdf_path   TEXT,
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (praktyka_id) REFERENCES praktyka(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 9. POROZUMIENIE Z ZAKŁADEM PRACY (Zał. 1)
-- ------------------------------------------------------------
CREATE TABLE porozumienie (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    praktyka_id         INTEGER     NOT NULL UNIQUE,
    zaklad_id           INTEGER     NOT NULL,
    data_podpisania     DATE,
    podpisal_dziekanat  TEXT,
    status              TEXT        NOT NULL DEFAULT 'Draft'
                                    CHECK (status IN ('Draft', 'Podpisane', 'Archiwalne')),
    plik_path           TEXT,
    created_at          DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (praktyka_id) REFERENCES praktyka(id)       ON DELETE CASCADE,
    FOREIGN KEY (zaklad_id)   REFERENCES zaklad_pracy(id)   ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- 10. HISTORIA ZMIAN STATUSU PRAKTYKI
-- ------------------------------------------------------------
CREATE TABLE historia_statusu (
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,
    praktyka_id         INTEGER     NOT NULL,
    status_poprzedni    TEXT,
    status_nowy         TEXT        NOT NULL,
    zmieniony_przez     INTEGER     NOT NULL,
    zmieniono_at        DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    komentarz           TEXT,

    FOREIGN KEY (praktyka_id)    REFERENCES praktyka(id)   ON DELETE CASCADE,
    FOREIGN KEY (zmieniony_przez) REFERENCES uzytkownik(id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- 11. HARMONOGRAM PRAKTYKI
-- ------------------------------------------------------------
CREATE TABLE harmonogram_praktyki (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dokument_id         INTEGER NOT NULL, 
    lp                  INTEGER NOT NULL,
    dzial_komorka       TEXT NOT NULL,
    planowana_liczba_dni INTEGER NOT NULL CHECK (planowana_liczba_dni > 0),
    
    FOREIGN KEY (dokument_id) REFERENCES dokument(id) ON DELETE CASCADE,
    UNIQUE (dokument_id, lp)
);

-- ------------------------------------------------------------
-- 12. SPRAWOZDANIE Z PRAKTYKI (Zał. 7)
-- ------------------------------------------------------------
CREATE TABLE sprawozdanie (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dokument_id         INTEGER NOT NULL UNIQUE,
    charakterystyka     TEXT NOT NULL,
    opis_prac           TEXT NOT NULL,
    wiedza_umiejetnosci TEXT NOT NULL,

    FOREIGN KEY (dokument_id) REFERENCES dokument(id) ON DELETE CASCADE
);

-- ============================================================
-- INDEKSY – przyspieszenie najczęstszych zapytań
-- ============================================================
CREATE INDEX idx_student_uzytkownik  ON student(uzytkownik_id);
CREATE INDEX idx_praktyka_student    ON praktyka(student_id);
CREATE INDEX idx_praktyka_zaklad     ON praktyka(zaklad_id);
CREATE INDEX idx_praktyka_status     ON praktyka(status);
CREATE INDEX idx_dokument_praktyka   ON dokument(praktyka_id);
CREATE INDEX idx_dokument_typ        ON dokument(typ_zalacznika);
CREATE INDEX idx_wpis_dokument       ON wpis_dziennika(dokument_id);
CREATE INDEX idx_efekt_dokument      ON efekt_uczenia(dokument_id);
CREATE INDEX idx_historia_praktyka   ON historia_statusu(praktyka_id);