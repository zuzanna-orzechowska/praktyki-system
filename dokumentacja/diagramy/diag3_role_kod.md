graph LR
    subgraph STU["🎓 Student"]
        direction TB
        S1["✏️ Zał. 4b – składa wniosek o zaliczenie pracy/stażu"]
        S2["✏️ Zał. 5  – wypełnia kwestionariusz ankiety"]
        S3["✏️ Zał. 6  – prowadzi dziennik (codzienne wpisy)"]
        S4["✏️ Zał. 7/7a – pisze i podpisuje sprawozdanie"]
        S5["✏️ Zał. 9  – dostarcza oświadczenie instytucji"]
        S6["👁️ Zał. 1, 2, 2a, 3, 4, 8 – tylko podgląd"]
    end

    subgraph UOPZ["🏫 UOPZ – Uczelniany Opiekun Praktyk"]
        direction TB
        U1["✏️ Zał. 2/2a – tworzy program i harmonogram"]
        U2["✏️ Zał. 3   – wydaje skierowanie na praktykę"]
        U3["✏️ Zał. 4/4a – ocenia efekty uczenia się"]
        U4["✏️ Zał. 8   – podpisuje protokół egzaminu"]
        U5["👁️ Zał. 6, 7/7a – przegląda i ocenia dokumenty studenta"]
        U6["👁️ Zał. 1, 5, 9 – tylko podgląd"]
    end

    subgraph ZOPZ["🏢 ZOPZ – Zakładowy Opiekun Praktyk"]
        direction TB
        Z1["✏️ Zał. 3   – podpisuje kartę praktyki i opinię"]
        Z2["✏️ Zał. 4   – potwierdza uzyskanie efektów uczenia się"]
        Z3["✏️ Zał. 6   – potwierdza codzienne wpisy w dzienniku"]
        Z4["✏️ Zał. 7/7a – podpisuje sprawozdanie studenta"]
        Z5["👁️ Zał. 2/2a – tylko podgląd programu praktyki"]
    end

    subgraph DZIEK["🏛️ Dziekanat / Dyrektor Instytutu"]
        direction TB
        D1["✏️ Zał. 1  – podpisuje porozumienie z zakładem pracy"]
        D2["✏️ Zał. 4a – podejmuje ostateczną decyzję o uznaniu efektów"]
        D3["✏️ Zał. 8  – podpisuje protokół egzaminu komisji"]
        D4["✏️ Zał. 9  – przyjmuje oświadczenie instytucji"]
        D5["👁️ Zał. 2, 3, 5, 6, 7 – wgląd do dokumentacji"]
    end

    subgraph ADMIN["⚙️ Administrator Systemu"]
        direction TB
        A1["✏️ Wszystkie załączniki – pełny dostęp"]
        A2["✏️ Zarządzanie użytkownikami i rolami"]
        A3["✏️ Konfiguracja systemu i słowników"]
        A4["👁️ Logi systemowe i historia zmian"]
    end