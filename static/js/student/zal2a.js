document.addEventListener('DOMContentLoaded', function() {
    const efekty_definicje = [
        {kod: "01", desc: "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych."},
        {kod: "02", desc: "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce."},
        {kod: "03", desc: "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy."},
        {kod: "04", desc: "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka."},
        {kod: "05", desc: "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania, posługując się rozmaitymi źródłami literaturowymi i zasobami."},
        {kod: "06", desc: "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje zawodowe."},
        {kod: "07", desc: "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia."},
        {kod: "08", desc: "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy i zaproponować jego rozwiązanie."},
        {kod: "09", desc: "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności IT, stosując odpowiednie normy i standardy."},
        {kod: "10", desc: "Pracuje w zespole zajmującym się zawodowo branżą IT."},
        {kod: "11", desc: "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów."},
        {kod: "12", desc: "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje do realizacji zadania, jak i przekazać im w sposób zrozumiały opinie z zakresu informatyki."},
        {kod: "13", desc: "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki działalności informatyków, szczególnie te ekonomiczne i społeczne."}
    ];

    fetch('/api/student/zal2a_harmonogram')
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
                window.location.href = '/student/teczka';
                return;
            }

            // Header
            document.getElementById('header-kierunek1').textContent = data.student.kierunek || 'Informatyka';
            document.getElementById('header-kierunek2').textContent = data.student.kierunek || 'Informatyka';
            const safeNazwisko = (data.student.nazwisko || '').split('(')[0].trim();
            document.getElementById('header-student').textContent = (data.student.imie || '') + ' ' + safeNazwisko;
            document.getElementById('header-album').textContent = data.student.nr_albumu || '';
            
            const specInput = document.getElementById('input-specjalnosc');
            const btnSaveSpec = document.getElementById('btn-save-spec');
            if(specInput) {
                specInput.value = data.student.specjalnosc || '';
                if(data.dokument.status === 'Submitted' || data.dokument.status === 'Approved') {
                    specInput.disabled = true;
                    if(btnSaveSpec) btnSaveSpec.disabled = true;
                }
            }
            
            document.getElementById('header-zaklad').textContent = data.praktyka.zaklad_nazwa || '';
            document.getElementById('header-od').textContent = data.praktyka.data_start || '';
            document.getElementById('header-do').textContent = data.praktyka.data_end || '';

            // Programy
            const progContainer = document.getElementById('programy-container');
            progContainer.innerHTML = '';
            efekty_definicje.forEach(ef => {
                const val = data.zapisane_programy[ef.kod] || '';
                progContainer.innerHTML += `
                    <tr>
                        <td class="bg-white border-dark p-3">
                            <div class="d-flex">
                                <div class="me-3">${ef.kod}</div>
                                <div>${ef.desc}</div>
                            </div>
                        </td>
                        <td class="bg-white border-dark p-3">${val}</td>
                    </tr>
                `;
            });

            // Harmonogram
            const tbody = document.querySelector('#tabela-harmonogram tbody');
            tbody.innerHTML = '';
            const pozycje = data.pozycje || [];
            if (pozycje.length > 0) {
                pozycje.forEach(p => {
                    tbody.innerHTML += `
                        <tr>
                            <td class="align-middle text-center bg-white border-dark p-3">${p.lp}</td>
                            <td class="bg-white border-dark p-3">${p.dzial_komorka}</td>
                            <td class="text-center align-middle bg-white border-dark p-3">${p.planowana_liczba_dni}</td>
                        </tr>
                    `;
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted bg-white border-dark">Brak wpisów w harmonogramie.</td></tr>';
            }
            document.getElementById('total-days').textContent = data.suma_dni || 0;

            // Podpisy
            if (data.podpisy) {
                if (data.podpisy.podpis_uopz) {
                    document.getElementById('podpis-uopz').textContent = data.podpisy.podpis_uopz;
                    document.getElementById('data-uzgodnienia').textContent = data.podpisy.data_uopz || '';
                }
                if (data.podpisy.podpis_zopz) {
                    document.getElementById('podpis-zopz').textContent = data.podpisy.podpis_zopz;
                }
                if (data.podpisy.podpis_student) {
                    document.getElementById('podpis-student').textContent = data.podpisy.podpis_student;
                    document.getElementById('zloz_podpis').checked = true;
                    document.getElementById('zloz_podpis').disabled = true;
                }
            }

            // Komentarze
            if (data.dokument.komentarz) {
                document.getElementById('komentarz').value = data.dokument.komentarz;
            }
            if (data.dokument.uwagi_opiekuna) {
                document.getElementById('uwagi-container').classList.remove('d-none');
                document.getElementById('uwagi-text').textContent = data.dokument.uwagi_opiekuna;
            }

            // Status i Decyzja
            const statusBadge = document.getElementById('status-badge');
            let badgeClass = 'bg-secondary';
            let statusText = data.dokument.status;
            
            if (statusText === 'Student_Review') { 
                badgeClass = 'bg-warning text-dark'; 
                statusText = 'Oczekuje na Twoją akceptację'; 
                document.getElementById('decyzja-panel').classList.remove('d-none');
            }
            else if (statusText === 'Draft_UOPZ' || statusText === 'Sent_to_ZOPZ' || statusText === 'Sent_back_to_UOPZ' || statusText === 'Draft') {
                badgeClass = 'bg-secondary';
                statusText = 'W przygotowaniu przez uczelnię/zakład pracy';
            }
            else if (statusText === 'Submitted') { 
                badgeClass = 'bg-info text-dark'; 
                statusText = 'Przesłane do Dziekanatu';
                document.getElementById('komentarz').disabled = true;
            }
            else if (statusText === 'Approved') {
                badgeClass = 'bg-success';
                statusText = 'Zatwierdzony przez Dziekanat';
                document.getElementById('komentarz').disabled = true;
            }
            else if (statusText === 'Rejected') {
                badgeClass = 'bg-danger';
                statusText = 'Odrzucony';
                document.getElementById('komentarz').disabled = true;
            }
            
            statusBadge.innerHTML = `<span class="badge ${badgeClass} fs-6">Status: ${statusText}</span>`;
        })
        .catch(err => console.error(err));

    const checkboxPodpis = document.getElementById('zloz_podpis');
    if (checkboxPodpis) {
        checkboxPodpis.addEventListener('change', function() {
            const podpisDiv = document.getElementById('podpis-student');
            if (this.checked) {
                podpisDiv.textContent = this.getAttribute('data-imienazwisko');
            } else {
                podpisDiv.textContent = 'Brak podpisu';
            }
        });
    }
});

function submitDecision(action) {
    const komentarz = document.getElementById('komentarz').value;
    const zloz_podpis = document.getElementById('zloz_podpis').checked;
    
    let specjalnosc = "";
    const specInput = document.getElementById('input-specjalnosc');
    if(specInput) {
        specjalnosc = specInput.value;
        if (specjalnosc.includes(' (')) {
            specjalnosc = specjalnosc.split(' (')[0].trim();
        } else if (specjalnosc.includes(' / ')) {
            specjalnosc = specjalnosc.split(' / ')[0].trim();
        }
    }
    
    if (action === 'odrzuc' && !komentarz) {
        if (!confirm('Czy na pewno chcesz odrzucić bez komentarza?')) return;
    }
    
    if (action === 'akceptuj' && !zloz_podpis) {
        alert('Musisz zaznaczyć pole "Złóż podpis cyfrowy", aby zatwierdzić dokument.');
        return;
    }
    
    fetch('/api/student/zal2a_harmonogram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            akcja: action, 
            komentarz: komentarz,
            zloz_podpis: zloz_podpis,
            specjalnosc: specjalnosc
        })
    })
    .then(response => response.json())
    .then(data => {
        const alerts = document.getElementById('alerts-container');
        if (data.success) {
            alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            setTimeout(() => window.location.reload(), 1500);
        } else {
            alerts.innerHTML = `<div class="alert alert-danger">${data.message || 'Wystąpił błąd'}</div>`;
        }
        window.scrollTo(0,0);
    })
    .catch(err => console.error(err));
}

window.zapiszSpecjalnosc = function() {
    const specInput = document.getElementById('input-specjalnosc');
    if (!specInput) return;
    
    let specjalnosc = specInput.value;
    if (specjalnosc.includes(' (')) {
        specjalnosc = specjalnosc.split(' (')[0].trim();
    } else if (specjalnosc.includes(' / ')) {
        specjalnosc = specjalnosc.split(' / ')[0].trim();
    }
    
    fetch('/api/student/zal2a_harmonogram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            akcja: 'zapisz_specjalnosc', 
            specjalnosc: specjalnosc 
        })
    })
    .then(r => r.json())
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
};
