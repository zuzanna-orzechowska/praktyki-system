-- ===========================================================================
-- LABORATORIUM 07: WERYFIKACJA FORMULARZA PRAKTYK ZA POMOCĄ SQL
-- ===========================================================================

/* ---------------------------------------------------------------------------
2. WSKAZANIE KLUCZY GŁÓWNYCH I OBCYCH
---------------------------------------------------------------------------
W systemie zastosowano relacyjny model danych z następującą strukturą kluczy:

- uzytkownik: PK (id). Tabela bazowa dla wszystkich ról w systemie.
- student: PK (id), FK (uzytkownik_id) -> uzytkownik(id). Relacja 1:1.
- praktyka: PK (id), FK (student_id), FK (zaklad_id), FK (uopz_id). 
  Główna encja łącząca proces.
- dokument: PK (id), FK (praktyka_id). Repozytorium wszystkich 11 załączników.
- harmonogram_praktyki: PK (id), FK (dokument_id). Pozycje planu dla Zał. 2a.
- efekt_uczenia: PK (id), FK (dokument_id). Walidacja efektów kształcenia.
*/

/* ---------------------------------------------------------------------------
3. WYJAŚNIENIE ROZDZIELENIA DANYCH NA KILKA TABEL
---------------------------------------------------------------------------
Dane zostały rozdzielone zgodnie z zasadami normalizacji (3NF):
- Uniknięcie redundancji: Dane studenta (nr albumu, kierunek) są zapisane raz 
  w tabeli 'student', a nie powtarzane w każdym formularzu.
- Elastyczność: Tabela 'harmonogram_praktyki' pozwala na dynamiczne dodawanie 
  dowolnej liczby zadań do Programu Praktyki (Zał. 2a).
- Bezpieczeństwo: Oddzielenie danych logowania (uzytkownik) od danych 
  dydaktycznych (student) ułatwia zarządzanie dostępem opartym na rolach.
*/

-- ---------------------------------------------------------------------------
-- 5. ZAPYTANIA GENERUJĄCE DANE TESTOWE (Walidacja 1.4 i 1.6)
-- ---------------------------------------------------------------------------

-- 5.1. Poprawne dane testowe
INSERT INTO uzytkownik (id, email, haslo_hash, imie, nazwisko, rola) 
VALUES (10, '21284@student.ans-elblag.pl', 'pbkdf2_hash_tutaj', 'Zuzanna', 'O.', 'student');

INSERT INTO student (uzytkownik_id, nr_albumu, kierunek, tryb_studiow, rok_studiow) 
VALUES (10, '21284', 'Informatyka', 'stacjonarne', 3);

INSERT INTO zaklad_pracy (id, nazwa, zopz_id) VALUES (1, 'ABC Software', 1); 

INSERT INTO praktyka (id, student_id, zaklad_id, uopz_id, data_start, data_end, liczba_godzin)
VALUES (1, 10, 1, 1, '2026-07-01', '2026-12-15', 960); 

INSERT INTO dokument (id, praktyka_id, typ_zalacznika, status, utworzony_przez)
VALUES (100, 1, 'ZAL2A', 'Approved', 10);

-- Poprawny harmonogram (Suma = 120 dni roboczych zgodnie z pkt 1.2 i 2.5)
INSERT INTO harmonogram_praktyki (dokument_id, lp, dzial_komorka, planowana_liczba_dni)
VALUES (100, 1, 'Dział IT', 60), (100, 2, 'Dev Ops', 60);    


-- 5.2. Testowanie przypadków brzegowych (Wymagane niepowodzenia)
-- Przypadek 1: Duplikat numeru albumu (Błąd UNIQUE)
-- INSERT INTO student (uzytkownik_id, nr_albumu, kierunek, rok_studiow) VALUES (11, '21284', 'Inf', 1);

-- Przypadek 4: Duplikat LP w harmonogramie (Błąd UNIQUE na LP + dokument_id)
-- INSERT INTO harmonogram_praktyki (dokument_id, lp, dzial_komorka, planowana_liczba_dni) VALUES (100, 1, 'Błąd', 10);


-- ---------------------------------------------------------------------------
-- 6. ZAPYTANIA WYKRYWAJĄCE BŁĘDY FORMULARZA (Zadanie 1.5 i 2.4)
-- ---------------------------------------------------------------------------

-- T2: Sprawdzenie wymaganej liczby godzin (Musi być 960h / 120 dni)
SELECT id, student_id FROM praktyka WHERE liczba_godzin <> 960;

-- T3: Sprawdzenie poprawności zakresu dat (Data zakończenia < rozpoczęcia)
SELECT id, data_start, data_end FROM praktyka WHERE data_end < data_start;

-- T4: Sprawdzenie liczby efektów kształcenia (Wymagane dokładnie 13)
SELECT dokument_id, COUNT(*) FROM efekt_uczenia GROUP BY dokument_id HAVING COUNT(*) <> 13;

-- T5: Wykrywanie pustych opisów efektów kształcenia
SELECT dokument_id, kod_efektu FROM efekt_uczenia WHERE opis_efektu IS NULL OR TRIM(opis_efektu) = '';

-- T6: Weryfikacja sumy dni w harmonogramie (Musi wynosić 120 dni)
SELECT dokument_id, SUM(planowana_liczba_dni) AS suma 
FROM harmonogram_praktyki 
GROUP BY dokument_id 
HAVING suma <> 120;

-- T8: Wykrywanie duplikatów numerów albumu
SELECT nr_albumu, COUNT(*) FROM student GROUP BY nr_albumu HAVING COUNT(*) > 1;

-- T9: Sprawdzenie braku opiekuna zakładowego (ZOPZ) przypisanego do praktyki
SELECT p.id as praktyka_id, z.nazwa as firma
FROM praktyka p
JOIN zaklad_pracy z ON p.zaklad_id = z.id
WHERE z.zopz_id IS NULL;


-- ---------------------------------------------------------------------------
-- 9. PODSUMOWANIE POPRAWNOŚCI FORMULARZA
-- ---------------------------------------------------------------------------
/*
Zastosowany model bazy danych zapewnia pełną weryfikację merytoryczną formularzy  
1. Więzy integralności (FOREIGN KEY) wymuszają spójność danych między 
   dokumentami a profilem studenta.
2. Ograniczenia unikalności (UNIQUE) zapobiegają błędom duplikacji numerów 
   albumów oraz pozycji w harmonogramie.
3. Zapytania agregujące (SUM, COUNT) pozwalają systemowi automatycznie 
   odrzucać dokumenty niepełne lub niezgodne z regulaminem (np. suma dni != 120)   
4. Całość rozwiązania gwarantuje, że proces praktyk przebiega zgodnie 
   z wymaganiami Instytutu Informatyki Stosowanej ANS w Elblągu.
*/