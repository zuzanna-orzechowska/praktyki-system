--2.4 - reguły walidacji dla poszczególnych formularzy

------------------------------------------
--1.Karta praktyki zawodowej
------------------------------------------

-- Sprawdzanie wartości NULL (brakujące dane studenta lub daty)
SELECT id FROM praktyka 
WHERE student_id IS NULL OR zaklad_id IS NULL OR data_start IS NULL OR data_end IS NULL;

-- Sprawdzanie zakresów liczbowych (oceny w zakresie 2-5)
SELECT praktyka_id, ocena_koncowa FROM protokol 
WHERE ocena_koncowa NOT BETWEEN 2.0 AND 5.0;

-- Sprawdzanie istnienia powiązanych rekordów (brak opiekuna ZOPZ w zakładzie)
SELECT p.id FROM praktyka p 
JOIN zaklad_pracy z ON p.zaklad_id = z.id 
WHERE z.zopz_id IS NULL;

-- Porównanie dat (data zakończenia nie może być przed datą rozpoczęcia)
SELECT id FROM praktyka 
WHERE data_end < data_start;


------------------------------------------
--2.Potwierdzenie efektów uczenia się
------------------------------------------

-- Zliczanie rekordów (musi być dokładnie 13 efektów dla dokumentu)
SELECT dokument_id, COUNT(*) as liczba_efektow 
FROM efekt_uczenia 
GROUP BY dokument_id 
HAVING liczba_efektow <> 13;

-- Kontrola wartości logicznych (czy każdy efekt ma przypisaną decyzję 0 lub 1)
SELECT dokument_id, kod_efektu FROM efekt_uczenia 
WHERE uzyskany IS NULL OR uzyskany NOT IN (0, 1);

------------------------------------------
--3.Dziennik praktyki zawodowej
------------------------------------------
-- Sprawdzanie pustych pól (każdy wpis musi mieć opis pracy)
SELECT id, numer_dnia FROM wpis_dziennika 
WHERE opis_prac IS NULL OR TRIM(opis_prac) = '';

-- Kontrola powiązań z efektami (czy wpis odnosi się do EK)
SELECT id FROM wpis_dziennika 
WHERE nr_efektu IS NULL OR nr_efektu = '';

-- Sprawdzanie podpisów (brak potwierdzenia ZOPZ)
SELECT id, numer_dnia FROM wpis_dziennika 
WHERE potwierdzony_zopz = 0;


------------------------------------------
--4.Sprawozdanie z praktyki zawodowej 
------------------------------------------

-- Wykrywanie sprzeczności: Ocena pozytywna w protokole przy braku zaliczenia efektów w Zał. 4
SELECT pr.praktyka_id 
FROM protokol pr
JOIN dokument d ON pr.praktyka_id = d.praktyka_id
JOIN efekt_uczenia e ON d.id = e.dokument_id
WHERE pr.ocena_koncowa > 2.0 
  AND d.typ_zalacznika = 'ZAL4' 
  AND e.uzyskany = 0;




--2.5 - walidacja między formularzami
------------------------------------------
--1.Spójność studenta we wszystkich formularzach
------------------------------------------
SELECT d.id, d.typ_zalacznika, p.student_id
FROM dokument d
JOIN praktyka p ON d.praktyka_id = p.id
WHERE p.student_id <> (SELECT student_id FROM praktyka WHERE id = d.praktyka_id);

------------------------------------------
--2.zgodność dat praktyki w dokumentach
------------------------------------------
SELECT w.id AS wpis_id, w.data_wpisu, p.data_start, p.data_end
FROM wpis_dziennika w
JOIN dokument d ON w.dokument_id = d.id
JOIN praktyka p ON d.praktyka_id = p.id
WHERE w.data_wpisu < p.data_start OR w.data_wpisu > p.data_end;


------------------------------------------
--3.zgodność liczby dni
------------------------------------------
SELECT 
    p.id AS praktyka_id,
    (SELECT SUM(planowana_liczba_dni) FROM harmonogram_praktyki hp 
     JOIN dokument d1 ON hp.dokument_id = d1.id 
     WHERE d1.praktyka_id = p.id AND d1.typ_zalacznika = 'ZAL2A') AS suma_plan,
    (SELECT COUNT(*) FROM wpis_dziennika wd 
     JOIN dokument d2 ON wd.dokument_id = d2.id 
     WHERE d2.praktyka_id = p.id AND d2.typ_zalacznika = 'ZAL6') AS liczba_wpisow
FROM praktyka p
WHERE suma_plan <> liczba_wpisow;



------------------------------------------
--4.zgodność efektów kształcenia
------------------------------------------
SELECT wd.id, wd.nr_efektu
FROM wpis_dziennika wd
JOIN dokument d ON wd.dokument_id = d.id
WHERE wd.nr_efektu NOT IN (
    SELECT eu.kod_efektu 
    FROM efekt_uczenia eu 
    JOIN dokument d2 ON eu.dokument_id = d2.id 
    WHERE d2.praktyka_id = d.praktyka_id AND d2.typ_zalacznika = 'ZAL4'
);

------------------------------------------
--5.zgodność oceny z osiągniętymi efektami
------------------------------------------
SELECT pr.praktyka_id, pr.ocena_koncowa
FROM protokol pr
JOIN dokument d ON pr.praktyka_id = d.praktyka_id
JOIN efekt_uczenia eu ON d.id = eu.dokument_id
WHERE d.typ_zalacznika = 'ZAL4' 
  AND eu.uzyskany = 0 
  AND pr.ocena_koncowa > 2.0;




--2.6 przypadki brzegowe

------------------------------------------
--1.różne daty praktyki w różncyh formularzach
------------------------------------------
SELECT d.id, d.typ_zalacznika, p.data_start, p.data_end
FROM dokument d
JOIN praktyka p ON d.praktyka_id = p.id
WHERE (p.data_start <> (SELECT data_start FROM praktyka WHERE id = d.praktyka_id))
   OR (p.data_end <> (SELECT data_end FROM praktyka WHERE id = d.praktyka_id));


------------------------------------------
--2.brak wpisów w dzienniku
------------------------------------------
SELECT p.id, p.status
FROM praktyka p
JOIN dokument d ON p.id = d.praktyka_id
WHERE d.typ_zalacznika = 'ZAL6'
  AND p.status IN ('PRAKTYKA_W_TOKU', 'DOKUMENTY_ZLOZONE')
  AND NOT EXISTS (SELECT 1 FROM wpis_dziennika WHERE dokument_id = d.id);


------------------------------------------
--3.brak efektów w jednym z dokumntów
------------------------------------------
SELECT p.id
FROM praktyka p
JOIN dokument d ON p.id = d.praktyka_id
WHERE d.typ_zalacznika = 'ZAL4'
  AND NOT EXISTS (SELECT 1 FROM efekt_uczenia WHERE dokument_id = d.id);


------------------------------------------
--4.niespójne dane studenta
------------------------------------------
SELECT s.id, s.nr_albumu, u.imie, u.nazwisko
FROM student s
JOIN uzytkownik u ON s.uzytkownik_id = u.id
WHERE s.uzytkownik_id IS NULL OR u.rola <> 'student';

------------------------------------------
--5.ocena pozytywna przy braku zaliczenia efektów
------------------------------------------
SELECT pr.praktyka_id, pr.ocena_koncowa
FROM protokol pr
JOIN dokument d ON pr.praktyka_id = d.praktyka_id
JOIN efekt_uczenia eu ON d.id = eu.dokument_id
WHERE pr.ocena_koncowa >= 3.0 
  AND d.typ_zalacznika = 'ZAL4' 
  AND eu.uzyskany = 0;


------------------------------------------
--6. brak podpisów
------------------------------------------
SELECT wd.dokument_id, wd.numer_dnia
FROM wpis_dziennika wd
JOIN dokument d ON wd.dokument_id = d.id
WHERE d.status = 'Submitted' 
  AND wd.potwierdzony_zopz = 0;


------------------------------------------
--7.Sprzeczne informacje (Praktyka zakończona, ale brak potwierdzenia)
------------------------------------------
SELECT p.id, p.status
FROM praktyka p
WHERE p.status = 'ZALICZONA'
  AND NOT EXISTS (SELECT 1 FROM protokol pr WHERE pr.praktyka_id = p.id);