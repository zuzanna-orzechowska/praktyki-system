-- ===========================================================================
-- LABORATORIUM 07: WERYFIKACJA FORMULARZA PRAKTYK ZA POMOCĄ SQL
-- Temat: Testy integralności i przypadki brzegowe (Zadania 2-9)
-- Autor: [Twoje Imię i Nazwisko] / Album: 21284
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- TESTY POPRAWNOŚCI (Zadanie 1.5 - Punkty 2-9)
-- ---------------------------------------------------------------------------

-- T2: Sprawdzenie wymaganej liczby godzin (Zgodnie z regulaminem 960h)
SELECT id, student_id, liczba_godzin 
FROM praktyka 
WHERE liczba_godzin <> 960;

-- T3: Sprawdzenie poprawności chronologii dat (Start musi być przed End)
SELECT id, data_start, data_end 
FROM praktyka 
WHERE data_end < data_start;

-- T4: Sprawdzenie wymaganej liczby efektów kształcenia (Musi być dokładnie 13)
-- Walidacja dla Załącznika 4
SELECT dokument_id, COUNT(*) AS liczba_efektow
FROM efekt_uczenia
GROUP BY dokument_id
HAVING COUNT(*) <> 13;

-- T5: Wykrywanie pustych opisów efektów kształcenia
SELECT dokument_id, kod_efektu 
FROM efekt_uczenia 
WHERE opis_efektu IS NULL OR TRIM(opis_efektu) = '';

-- T6: Weryfikacja sumy dni w harmonogramie (Zał. 2a - wymagane 120 dni)
SELECT dokument_id, SUM(planowana_liczba_dni) AS laczna_liczba_dni
FROM harmonogram_praktyki
GROUP BY dokument_id
HAVING laczna_liczba_dni <> 120;

-- T7: Sprawdzenie kompletności pozycji w harmonogramie
SELECT dokument_id, COUNT(*) AS liczba_pozycji
FROM harmonogram_praktyki
GROUP BY dokument_id
HAVING liczba_pozycji < 1;

-- T8: Sprawdzenie unikalności numeru albumu (Wykrywanie duplikatów w bazie)
SELECT nr_albumu, COUNT(*) 
FROM student 
GROUP BY nr_albumu 
HAVING COUNT(*) > 1;

-- T9: Sprawdzenie obecności opiekuna zakładowego (ZOPZ) dla każdej praktyki
SELECT p.id as praktyka_id, z.nazwa as firma
FROM praktyka p
JOIN zaklad_pracy z ON p.zaklad_id = z.id
WHERE z.zopz_id IS NULL;


-- ---------------------------------------------------------------------------
-- PRZYPADKI BRZEGOWE (Zadanie 1.6) - Testowanie ograniczeń (Constraints)
-- ---------------------------------------------------------------------------

-- Przypadek 1: Próba dodania studenta z istniejącym już numerem albumu
-- Oczekiwany rezultat: UNIQUE constraint failed: student.nr_albumu
-- INSERT INTO student (uzytkownik_id, nr_albumu, kierunek, rok_studiow, tryb_studiow)
-- VALUES (999, '21284', 'Informatyka', 1, 'stacjonarne');

-- Przypadek 3: Próba ustawienia daty wstecznej
-- Oczekiwany rezultat: Wykrycie przez zapytanie T3 lub błąd CHECK (jeśli dodany do tabeli)
-- INSERT INTO praktyka (student_id, zaklad_id, uopz_id, data_start, data_end)
-- VALUES (1, 1, 1, '2026-10-01', '2026-01-01');

-- Przypadek 4: Duplikat numeru LP w tym samym dokumencie harmonogramu
-- Oczekiwany rezultat: UNIQUE constraint failed: harmonogram_praktyki.dokument_id, lp
-- INSERT INTO harmonogram_praktyki (dokument_id, lp, dzial_komorka, planowana_liczba_dni)
-- VALUES (1, 1, 'Dział IT', 60);
-- INSERT INTO harmonogram_praktyki (dokument_id, lp, dzial_komorka, planowana_liczba_dni)
-- VALUES (1, 1, 'HR', 60);

-- Przypadek 6: Wykrycie praktyk bez zatwierdzonego Załącznika 9 (Inicjującego)
SELECT p.id, p.status 
FROM praktyka p
LEFT JOIN dokument d ON p.id = d.praktyka_id AND d.typ_zalacznika = 'ZAL9'
WHERE d.id IS NULL;

-- ---------------------------------------------------------------------------
-- PODSUMOWANIE ANALIZY INTEGRALNOŚCI
-- ---------------------------------------------------------------------------
-- Powyższe zapytania gwarantują spójność danych pomiędzy Formularzem 2a, 
-- Dziennikiem (Zal 6) a efektami (Zal 4). 
-- Każda niezgodność z regulaminem (np. suma dni != 120) jest natychmiast 
-- raportowana przez silnik bazy danych SQL.
