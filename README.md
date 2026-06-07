# 📋 System Obsługi Praktyk Zawodowych
### Akademia Nauk Stosowanych w Elblągu – Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego

> Aplikacja webowa automatyzująca obieg dokumentów związanych z praktykami zawodowymi na kierunku Informatyka. Zastępuje 9 papierowych załączników cyfrowym systemem z kontrolą dostępu opartą na rolach, generowaniem dokumentów PDF oraz powiadomieniami e-mail.

---

## 📁 Struktura repozytorium

```text
praktyki-system/
│
├── app.py                       # Główny plik aplikacji Flask
├── models.py                    # Modele bazy danych (SQLAlchemy)
├── extensions.py                # Inicjalizacja rozszerzeń (db, login, mail)
├── blueprints/                  # Moduły aplikacji (Blueprints)
│   ├── auth/                    # Logowanie (w tym Google OAuth), rejestracja
│   ├── student/                 # Widoki i panele studenta
│   ├── uopz/                    # Uczelniany opiekun praktyk
│   ├── zopz/                    # Zakładowy opiekun praktyk
│   ├── dziekanat/               # Dziekanat / Dyrektor Instytutu
│   ├── admin/                   # Zarządzanie użytkownikami i rolami
│   ├── api/                     # API powiadomień i inne
│   └── pdf_export/              # Generowanie i eksport dokumentów PDF
│
├── templates/                   # Szablony Jinja2
├── static/                      # CSS, JS, obrazy, pliki do pobrania
├── uploads/                     # Przesłane pliki
│
├── dokumentacja/                # Dokumentacja techniczna i projektowa
├── .env.example                 # Przykładowy plik konfiguracyjny (zmienne środowiskowe)
├── docker-compose.yml           # Konfiguracja Dockera
├── Dockerfile                   # Plik Docker do konteneryzacji
└── requirements.txt             # Zależności Pythona
```

---

## ⚙️ Technologie

| Warstwa | Technologia |
|---|---|
| Backend | Python 3.11+, Flask |
| Autoryzacja | Flask-Login, Google OAuth (Authlib) |
| Formularze | Flask-WTF, WTForms |
| Szablony | Jinja2 |
| Frontend | Bootstrap 5, czysty JavaScript |
| Baza danych | SQLite (dev) / PostgreSQL (prod) – SQLAlchemy |
| Generowanie PDF | WeasyPrint / ReportLab |
| Powiadomienia | Flask-Mail |
| Konteneryzacja | Docker, Docker Compose |

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

```text
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

## 🚀 Uruchomienie projektu

### Z użyciem Dockera (Zalecane)

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/twoj-login/praktyki-system.git
cd praktyki-system

# 2. Skonfiguruj zmienne środowiskowe
cp .env.example .env
# Edytuj plik .env wprowadzając odpowiednie dane (klucze OAuth, dane SMTP, itp.)

# 3. Uruchom kontenery
docker-compose up --build
```
Aplikacja będzie dostępna pod adresem: `http://localhost:5000`

### Środowisko lokalne (bez Dockera)

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

# 4. Skonfiguruj środowisko
cp .env.example .env
# Wypełnij .env swoimi danymi (SECRET_KEY, MAIL_*, klucze Google OAuth)

# 5. Uruchom aplikację
python app.py
```
Aplikacja będzie dostępna pod adresem: `http://127.0.0.1:5000`

---

## 📌 Status projektu

Projekt jest w zaawansowanej fazie rozwoju z wdrożonymi kluczowymi funkcjonalnościami:

- [x] Struktura projektu Flask i konfiguracja środowisk
- [x] Baza danych oparta o SQLAlchemy (SQLite/PostgreSQL)
- [x] System logowania, autoryzacji (w tym Google OAuth) i zarządzania rolami
- [x] Obsługa kluczowych ról: Student, UOPZ, ZOPZ, Dziekanat, Admin
- [x] Obsługa poszczególnych formularzy i załączników (m.in. Zał. 4, Zał. 6, Zał. 9, Porozumienia)
- [x] Dynamiczne śledzenie statusów praktyki
- [x] Powiadomienia mailowe (Flask-Mail) i system notyfikacji API
- [x] Generowanie dokumentów PDF (WeasyPrint)
- [x] Konteneryzacja za pomocą Docker i Docker Compose

---

## 📬 Kontakt

Projekt realizowany w ramach przedmiotu **Aplikacje Internetowe II**
e-mail: 21284@student.ans-elblag.pl
