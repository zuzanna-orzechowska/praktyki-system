flowchart TD
    START([Użytkownik próbuje otworzyć dokument]) --> CZY_LOGIN{Czy użytkownik\njest zalogowany?}

    CZY_LOGIN -->|NIE| REDIRECT["Przekieruj na /login\n401 Unauthorized"]
    REDIRECT --> KONIEC1([Koniec])

    CZY_LOGIN -->|TAK| POBIERZ["Pobierz rolę użytkownika\ni status dokumentu z JSON"]

    POBIERZ --> CZY_WYMIENIONY{Czy użytkownik\njest wymieniony\nw dokumencie?}

    CZY_WYMIENIONY -->|NIE| BLOCK["Zablokuj dostęp\n403 Forbidden"]
    BLOCK --> KONIEC2([Koniec])

    CZY_WYMIENIONY -->|TAK| CZY_ADMIN{Rola:\nAdmin?}

    CZY_ADMIN -->|TAK| EDYCJA_PELNA["Udostępnij pełny\nformularz edycji ✏️"]
    EDYCJA_PELNA --> KONIEC3([Koniec])

    CZY_ADMIN -->|NIE| CZY_STUDENT{Rola:\nStudent?}

    CZY_STUDENT -->|TAK| CZY_STATUS_STU{Status dokumentu\nto 'Draft'\nlub 'Rejected'?}
    CZY_STATUS_STU -->|TAK| EDYCJA_STU["Udostępnij\nformularz edycji ✏️"]
    CZY_STATUS_STU -->|NIE| READONLY_STU["Wyświetl podgląd\nRead-only 👁️"]
    EDYCJA_STU --> KONIEC4([Koniec])
    READONLY_STU --> KONIEC5([Koniec])

    CZY_STUDENT -->|NIE| CZY_UOPZ_ZOPZ{Rola:\nUOPZ lub ZOPZ?}

    CZY_UOPZ_ZOPZ -->|TAK| CZY_STATUS_OP{Status dokumentu\nto 'Under_Review'?}
    CZY_STATUS_OP -->|TAK| EDYCJA_OP["Udostępnij\nformularz zatwierdzenia ✏️\n(podpis / uwagi)"]
    CZY_STATUS_OP -->|NIE| READONLY_OP["Wyświetl podgląd\nRead-only 👁️"]
    EDYCJA_OP --> KONIEC6([Koniec])
    READONLY_OP --> KONIEC7([Koniec])

    CZY_UOPZ_ZOPZ -->|NIE – Dziekanat| READONLY_DZ["Wyświetl podgląd\nRead-only 👁️\n(z opcją podpisu Zał. 1 / 9)"]
    READONLY_DZ --> KONIEC8([Koniec])