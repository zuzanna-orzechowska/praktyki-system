document.addEventListener('DOMContentLoaded', function() {
    const pathParts = window.location.pathname.split('/');
    const studentId = pathParts[pathParts.length - 1];
    document.getElementById('back-link').href = `/uopz/teczka/${studentId}`;

    const efekty_definicje = [
        {kod: "01", desc: "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki..."},
        {kod: "02", desc: "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce"},
        {kod: "03", desc: "Zna ekonomiczne, prawne skutki własnych działań..."},
        {kod: "04", desc: "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka"},
        {kod: "05", desc: "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu..."},
        {kod: "06", desc: "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje..."},
        {kod: "07", desc: "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań..."},
        {kod: "08", desc: "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy..."},
        {kod: "09", desc: "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności..."},
        {kod: "10", desc: "Pracuje w zespole zajmującym się zawodowo branżą IT"},
        {kod: "11", desc: "Przestrzega zasad etyki zawodowej..."},
        {kod: "12", desc: "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje..."},
        {kod: "13", desc: "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej..."}
    ];

    let rowCount = 0;

    function addHarmonogramRow(dzial = '', dni = '') {
        rowCount++;
        const tbody = document.querySelector('#tabela-harmonogram tbody');
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="align-middle">${rowCount}</td>
            <td><input type="text" class="form-control dzial-input" value="${dzial}" required></td>
            <td><input type="number" class="form-control dni-input" value="${dni}" min="1" required></td>
            <td><button type="button" class="btn btn-sm btn-outline-danger btn-remove"><i class="bi bi-trash"></i></button></td>
        `;
        tbody.appendChild(tr);

        tr.querySelector('.btn-remove').addEventListener('click', function() {
            tr.remove();
            updateTotal();
        });
        tr.querySelector('.dni-input').addEventListener('input', updateTotal);
        updateTotal();
    }

    function updateTotal() {
        let sum = 0;
        document.querySelectorAll('.dni-input').forEach(input => {
            sum += parseInt(input.value) || 0;
        });
        document.getElementById('total-days').textContent = sum;
    }

    document.getElementById('btn-add-row').addEventListener('click', () => addHarmonogramRow());

    fetch(`/api/uopz/zal2a_harmonogram/${studentId}`)
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

            // Programy
            const progContainer = document.getElementById('programy-container');
            progContainer.innerHTML = '';
            efekty_definicje.forEach(ef => {
                const val = data.zapisane_programy[ef.kod] || '';
                progContainer.innerHTML += `
                    <div class="mb-3">
                        <label class="form-label fw-bold">Efekt ${ef.kod}: ${ef.desc}</label>
                        <textarea class="form-control program-input" data-kod="${ef.kod}" rows="2">${val}</textarea>
                    </div>
                `;
            });

            // Harmonogram
            const pozycje = data.pozycje || [];
            if (pozycje.length > 0) {
                pozycje.forEach(p => addHarmonogramRow(p.dzial_komorka, p.planowana_liczba_dni));
            } else {
                addHarmonogramRow();
            }
        })
        .catch(err => console.error(err));

    document.getElementById('form-harmonogram').addEventListener('submit', function(e) {
        e.preventDefault();

        const programy = {};
        document.querySelectorAll('.program-input').forEach(el => {
            programy[el.getAttribute('data-kod')] = el.value;
        });

        const harmonogram = [];
        document.querySelectorAll('#tabela-harmonogram tbody tr').forEach(tr => {
            const dzial = tr.querySelector('.dzial-input').value;
            const dni = tr.querySelector('.dni-input').value;
            if (dzial && dni) {
                harmonogram.push({ dzial: dzial, dni: dni });
            }
        });

        fetch(`/api/uopz/zal2a_harmonogram/${studentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                akcja: 'zapisz',
                programy: programy,
                harmonogram: harmonogram
            })
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
