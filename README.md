# 📋 System Obsługi Praktyk Zawodowych
### Akademia Nauk Stosowanych w Elblągu – Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego

> Aplikacja webowa automatyzująca obieg dokumentów związanych z praktykami zawodowymi na kierunku Informatyka. Zastępuje 9 papierowych załączników cyfrowym systemem z kontrolą dostępu opartą na rolach.

---

## 📁 Struktura repozytorium

```
praktyki-system/
│
├── app/
│   ├── __init__.py              # Fabryka aplikacji Flask
│   ├── config.py                # Konfiguracja środowisk (dev/prod)
│   │
│   ├── blueprints/
│   │   ├── auth/                # Logowanie, wylogowanie, reset hasła
│   │   ├── student/             # Widoki i formularze studenta
│   │   ├── uopz/                # Uczelniany opiekun praktyk
│   │   ├── zopz/                # Zakładowy opiekun praktyk
│   │   ├── dziekanat/           # Dziekanat / Dyrektor Instytutu
│   │   ├── admin/               # Zarządzanie użytkownikami i rolami
│   │   └── dokumenty/           # Generowanie i pobieranie PDF
│   │
│   ├── forms/                   # Formularze Flask-WTF / WTForms
│   ├── templates/               # Szablony Jinja2
│   └── static/                  # CSS, JS, Bootstrap
│
├── data/                        # Pliki JSON – faza I (tymczasowe)
│   ├── users.json
│   ├── praktyki.json
│   ├── zal4_efekty/             # Zał. 4 – per student
│   └── zal6_dziennik/           # Zał. 6 – per student
│
├── dokumentacja/
│   ├── README.md                # Ten plik
│   ├── diagramy/
│   │   ├── architektura.md      # Diagram 1 – architektura Flask (Mermaid)
│   │   ├── workflow.md          # Diagram 2 – przepływ procesu (Mermaid)
│   │   └── uprawnienia.md       # Diagram 3 – role i dostęp do dokumentów (Mermaid)
│   └── specyfikacja.md          # Szczegółowa specyfikacja funkcjonalna
│
├── requirements.txt
└── run.py
```

---

## ⚙️ Technologie

| Warstwa | Technologia |
|---|---|
| Backend | Python 3.11+, Flask |
| Autoryzacja | Flask-Login |
| Formularze | Flask-WTF, WTForms |
| Szablony | Jinja2 |
| Frontend | Bootstrap 5, czysty JavaScript |
| Baza danych (faza I) | JSON (load_data / save_data) |
| Baza danych (faza II) | PostgreSQL / SQLite – SQLAlchemy, Flask-Migrate *(planowane)* |
| Generowanie PDF | WeasyPrint / ReportLab |
| Powiadomienia | Flask-Mail |

---

## 👥 Role i uprawnienia

System obsługuje pięć ról użytkowników. Dostęp do każdego dokumentu jest kontrolowany indywidualnie — użytkownik wymieniony w dokumencie może go zobaczyć, ale nie zawsze edytować.

| Rola | Opis |
|---|---|
| 🎓 **Student** | Wypełnia wnioski, prowadzi dziennik, pisze sprawozdanie |
| 🏫 **UOPZ** | Uczelniany opiekun – wydaje skierowania, ocenia, prowadzi egzamin |
| 🏢 **ZOPZ** | Zakładowy opiekun – potwierdza wpisy, podpisuje dokumenty |
| 🏛️ **Dziekanat / Dyrektor** | Podpisuje porozumienia, przyjmuje oświadczenia, decyduje o uznaniu efektów |
| ⚙️ **Administrator** | Pełny dostęp – zarządzanie użytkownikami, rolami i konfiguracją |

---

## 📄 Obsługiwane załączniki

| Nr | Nazwa | Wypełnia | Podpisuje / Potwierdza |
|---|---|---|---|
| Zał. 1 | Porozumienie z zakładem pracy | Dziekanat | Dziekanat |
| Zał. 2 / 2a | Program i harmonogram praktyki | UOPZ | UOPZ, ZOPZ, Student |
| Zał. 3 | Karta praktyki zawodowej + Skierowanie | UOPZ | ZOPZ |
| Zał. 4 | Potwierdzenie uzyskania efektów uczenia się | ZOPZ | ZOPZ |
| Zał. 4a | Merytoryczna ocena wniosku studenta | Komisja / UOPZ | Dyrektor |
| Zał. 4b | Wniosek o zaliczenie pracy/stażu/dział. gosp. | Student | – |
| Zał. 5 | Kwestionariusz ankiety | Student | – |
| Zał. 6 | Dziennik praktyki zawodowej | Student (codziennie) | ZOPZ (każdy wpis) |
| Zał. 7 / 7a | Sprawozdanie z praktyki (stacj. / niestacj.) | Student | ZOPZ |
| Zał. 8 | Protokół zaliczenia praktyki | Komisja egzaminacyjna | UOPZ + Przewodniczący |
| Zał. 9 | Oświadczenie instytucji o przyjęciu studenta | ZOPZ (zewnętrzny) | Dziekanat |

---

## 🔄 Skrócony opis procesu

```
Student znajduje zakład pracy
        │
        ├─► [Ścieżka standardowa]
        │     Zał. 9 → Dziekanat → Porozumienie (Zał. 1)
        │     → Program (Zał. 2a) → Skierowanie (Zał. 3)
        │     → Praktyka (960h / 6 miesięcy)
        │     → Dokumenty końcowe (Zał. 3, 4, 6, 7)
        │     → Egzamin przed komisją → Protokół (Zał. 8) → USOS ✅
        │
        └─► [Ścieżka alternatywna – praca / staż / działalność gosp.]
              Zał. 4b (wniosek studenta)
              → Komisja (Zał. 4a) → Decyzja Dyrektora → USOS ✅
```

---

## 🚀 Uruchomienie projektu (środowisko deweloperskie)

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/twoj-login/praktyki-system.git
cd praktyki-system

# 2. Utwórz wirtualne środowisko
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Uruchom aplikację
flask run
```

Aplikacja dostępna pod adresem: `http://127.0.0.1:5000`

---

## 📌 Status projektu

> 🚧 **W trakcie budowy** — faza I: szkielet aplikacji, obsługa formularzy, zapis do JSON.

- [x] Diagramy architektoniczne i dokumentacja wstępna
- [ ] Struktura projektu Flask i konfiguracja środowisk
- [ ] System logowania i zarządzania rolami
- [ ] Formularz Zał. 4 – Potwierdzenie efektów uczenia się
- [ ] Formularz Zał. 6 – Dziennik praktyki (dynamiczna tabela)
- [ ] Pozostałe załączniki
- [ ] Generowanie PDF
- [ ] Migracja z JSON do bazy danych – SQLAlchemy, Flask-Migrate (faza II)

---

## 📬 Kontakt

Projekt realizowany w ramach przedmiotu **Aplikacje Internetowe**
Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego – ANS Elbląg
