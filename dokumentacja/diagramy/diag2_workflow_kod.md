flowchart TD
    START([Student szuka miejsca praktyki])

    START --> PRACA{Pracuje zawodowo\nlub prowadzi\ndziałalność gosp.?}

    PRACA -->|TAK| E1["Wypełnia Zał. 4b\nWniosek o zaliczenie\npracy / stażu / dział. gosp."]
    E1 --> E2["Komisja ds. praktyk\nwypełnia Zał. 4a\nMerytoryczna ocena wniosku"]
    E2 --> E3{Decyzja\nDyrektora\nInstytutu}
    E3 -->|Negatywna - wraca\ndo ścieżki standardowej| Z9
    E3 -->|Pozytywna| USOS

    PRACA -->|NIE| Z9["Student dostarcza Zał. 9 do Dziekanatu\nOświadczenie instytucji o przyjęciu na praktykę\n– przed rozpoczęciem praktyki"]
    Z9 --> ZAL1["Dziekanat / Uczelnia podpisuje Zał. 1\nPorozumienie z Zakładem Pracy\nUczelnia wysyła też Regulamin + Zał. 2"]
    ZAL1 --> PROGRAM["UOPZ + ZOPZ + Student uzgadniają Zał. 2a\nProgram i harmonogram praktyki zawodowej"]
    PROGRAM --> SIER["UOPZ wydaje Skierowanie\n– wchodzi w skład Zał. 3 – Karta praktyki"]
    SIER --> REALIZ["Student rozpoczyna praktykę\n960h / 120 dni roboczych / 6 miesięcy\nSemestr 7 – koniec do połowy lutego"]

    subgraph TRAKCIE["W trakcie praktyki"]
        T1["Student wypełnia codziennie\nZał. 6 Dziennik praktyki\n– opis prac + nr efektów uczenia się"]
        T2["ZOPZ potwierdza podpisem\nwykonanie zadań w Dzienniku"]
        T3["UOPZ przeprowadza\nmin. 1 hospitację\nw zakładzie pracy"]
        T1 --> T2
    end

    REALIZ --> TRAKCIE

    TRAKCIE --> DO7["Do 7 dni po zakończeniu\nStudent składa komplet dokumentów do UOPZ"]

    subgraph DOCS["Dokumenty końcowe składane do UOPZ"]
        D1["Zał. 6 – Dziennik praktyki\npodpisany przez ZOPZ"]
        D2["Zał. 7 lub 7a – Sprawozdanie\nstacjonarne lub niestacjonarne\npodpisane przez ZOPZ / przełożonego"]
        D3["Zał. 3 – Karta praktyki\nzaświadczenie odbycia + opinia zakładu\npodpisana przez ZOPZ"]
        D4["Zał. 4 – Potwierdzenie\nuzyskania efektów uczenia się\nwypełnione przez ZOPZ"]
        D5["Zał. 5 – Kwestionariusz ankiety\nwypełniony przez studenta"]
    end

    DO7 --> DOCS

    DOCS --> EGZAM["Egzamin ustny z oceną\nprzed Komisją egzaminacyjną\nPrzewodniczący + Opiekunowie praktyk"]
    EGZAM --> PROT["Komisja sporządza Zał. 8\nProtokoł zaliczenia praktyki\nS = ocena sprawozdania\nU = ocena UOPZ\nZ = ocena ZOPZ"]
    PROT --> USOS(["UOPZ wpisuje ocenę do USOS\nZał. 8 trafia do akt studenta\n✅ Praktyka zaliczona"])