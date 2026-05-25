document.addEventListener('DOMContentLoaded', function() {
    const pathParts = window.location.pathname.split('/');
    const studentId = pathParts[pathParts.length - 1];
    document.getElementById('back-link').href = `/uopz/teczka/${studentId}`;

    const lista_statyczna = [
        "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki...",
        "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce",
        "Zna ekonomiczne, prawne skutki własnych działań...",
        "Zna zasady bezpieczeństwa pracy i ergonomii...",
        "Pozyskuje informacje odnośnie technologii, metod, technik...",
        "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje...",
        "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań...",
        "Potrafi zidentyfikować problem informatyczny...",
        "Potrafi rozwiązać rzeczywiste zadanie inżynierskie...",
        "Pracuje w zespole zajmującym się zawodowo branżą IT",
        "Przestrzega zasad etyki zawodowej...",
        "Kontaktując się z osobami spoza branży potrafi...",
        "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej..."
    ];

    fetch(`/api/uopz/zal4_efekty/${studentId}`)
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                throw new Error('Unauthorized');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert(data.error);
                window.location.href = '/uopz/dashboard';
                return;
            }

            document.getElementById('student-name').textContent = `${data.student.nr_albumu} - ${data.uzytkownik.imie} ${data.uzytkownik.nazwisko}`;

            const efektyMap = {};
            (data.efekty || []).forEach(e => {
                efektyMap[e.kod_efektu] = e.ocena_zopz;
            });

            const tbody = document.querySelector('#tabela-efekty tbody');
            tbody.innerHTML = '';

            lista_statyczna.forEach((desc, i) => {
                const kod = (i + 1).toString().padStart(2, '0');
                const ocena = efektyMap[kod] || '<span class="text-muted">Brak opinii</span>';
                
                tbody.innerHTML += `
                    <tr>
                        <td class="align-middle"><strong>Efekt ${kod}:</strong> ${desc}</td>
                        <td class="align-middle">
                            <span class="fst-italic">${ocena}</span>
                        </td>
                    </tr>
                `;
            });

            if (data.dokument && data.dokument.uwagi_opiekuna) {
                document.getElementById('opinia-uopz').value = data.dokument.uwagi_opiekuna;
            }
        })
        .catch(err => console.error(err));

    document.getElementById('form-opinia').addEventListener('submit', function(e) {
        e.preventDefault();
        const opinia = document.getElementById('opinia-uopz').value;

        fetch(`/api/uopz/zal4_efekty/${studentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ opinia_uopz: opinia })
        })
        .then(response => response.json())
        .then(data => {
            const alerts = document.getElementById('alerts-container');
            if (data.success) {
                alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            } else {
                alerts.innerHTML = `<div class="alert alert-danger">${data.message || 'Błąd zapisu'}</div>`;
            }
            window.scrollTo(0,0);
        })
        .catch(err => console.error(err));
    });
});
