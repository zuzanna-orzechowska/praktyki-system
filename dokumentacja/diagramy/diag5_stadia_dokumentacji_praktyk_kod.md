stateDiagram-v2
    [*] --> Draft : Student tworzy dokument

    Draft --> Submitted : Student wysyła do weryfikacji

    Submitted --> Under_Review : UOPZ / ZOPZ rozpoczyna przegląd

    Under_Review --> Rejected : Opiekun zgłasza uwagi
    Under_Review --> Approved : Opiekun zatwierdza dokument

    Rejected --> Draft : Student wprowadza poprawki

    Approved --> Closed : Praktyka zaliczona / USOS uzupełniony

    Closed --> [*]

    note right of Draft
        Student może edytować
        i zapisywać zmiany
    end note

    note right of Rejected
        System wysyła e-mail
        z uwagami do studenta
    end note

    note right of Closed
        Protokół (Zał. 8)
        trafia do akt studenta
    end note