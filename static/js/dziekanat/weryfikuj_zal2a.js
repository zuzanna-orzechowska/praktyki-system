document.addEventListener('DOMContentLoaded', function () {
    const pathParts = window.location.pathname.split('/');
    const praktykaId = pathParts[pathParts.length - 1];

    if (!praktykaId) return;

    fetch(`/api/dziekanat/weryfikuj_zal2a/${praktykaId}`)
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                throw new Error('Unauthorized');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                document.getElementById('alerts-container').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }

            document.getElementById('student-name').textContent = `${data.uzytkownik.imie} ${data.uzytkownik.nazwisko}`;
            document.getElementById('student-album').textContent = data.student.nr_albumu;
            document.getElementById('student-kierunek').textContent = data.student.kierunek || 'Informatyka';
            document.getElementById('student-specjalnosc').textContent = data.student.specjalnosc || '-';

            const statusEl = document.getElementById('dokument-status');
            const status = data.dokument.status;
            statusEl.textContent = status;
            if (status === 'Submitted') {
                statusEl.className = 'badge bg-warning text-dark';
                statusEl.textContent = 'Oczekuje na weryfikację Dziekanatu';
                document.getElementById('dziekanat-actions').classList.remove('d-none');
            } else if (status === 'Approved') {
                statusEl.className = 'badge bg-success';
                statusEl.textContent = 'Zatwierdzony';
            } else {
                statusEl.className = 'badge bg-secondary';
            }

            const programyTbody = document.querySelector('#tabela-program tbody');
            programyTbody.innerHTML = '';
            const programy = data.zapisane_programy || {};
            for (const [kod, prace] of Object.entries(programy)) {
                programyTbody.innerHTML += `
                    <tr>
                        <td class="fw-bold">${kod}</td>
                        <td>${prace}</td>
                    </tr>
                `;
            }
            if (Object.keys(programy).length === 0) {
                programyTbody.innerHTML = '<tr><td colspan="2" class="text-center text-muted">Brak programu</td></tr>';
            }

            const harmTbody = document.querySelector('#tabela-harmonogram tbody');
            harmTbody.innerHTML = '';
            let sumaDni = 0;
            if (data.pozycje && data.pozycje.length > 0) {
                data.pozycje.forEach(p => {
                    sumaDni += p.planowana_liczba_dni;
                    harmTbody.innerHTML += `
                        <tr>
                            <td class="text-center">${p.lp}</td>
                            <td>${p.dzial_komorka}</td>
                            <td class="text-center">${p.planowana_liczba_dni}</td>
                        </tr>
                    `;
                });
            } else {
                harmTbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Brak wpisów w harmonogramie</td></tr>';
            }
            document.getElementById('suma-dni').textContent = sumaDni;

            if (data.podpisy) {
                if (data.podpisy.podpis_uopz) {
                    document.getElementById('podpis-uopz').textContent = data.podpisy.podpis_uopz;
                    document.getElementById('data-uopz').textContent = data.podpisy.data_uopz;
                }
                if (data.podpisy.podpis_zopz) {
                    document.getElementById('podpis-zopz').textContent = data.podpisy.podpis_zopz;
                    document.getElementById('data-zopz').textContent = data.podpisy.data_zopz;
                }
                if (data.podpisy.podpis_student) {
                    document.getElementById('podpis-student').textContent = data.podpisy.podpis_student;
                    document.getElementById('data-student').textContent = data.podpisy.data_student;
                }
            }
        })
        .catch(err => console.error('Błąd pobierania danych Zal 2a:', err));

    window.toggleOdrzuc = function () {
        const komContainer = document.getElementById('komentarz-container');
        const dActions = document.getElementById('dziekanat-actions');
        const podActions = document.getElementById('potwierdz-odrzuc-actions');

        if (komContainer.style.display === 'none') {
            komContainer.style.display = 'block';
            dActions.classList.add('d-none');
            podActions.classList.remove('d-none');
        } else {
            komContainer.style.display = 'none';
            document.getElementById('komentarz-dziekanatu').value = '';
            dActions.classList.remove('d-none');
            podActions.classList.add('d-none');
        }
    };

    window.zapiszDecyzje = function (akcja) {
        let payload = { akcja: akcja };

        if (akcja === 'odrzuc') {
            const komentarz = document.getElementById('komentarz-dziekanatu').value.trim();
            if (!komentarz) {
                alert('Proszę wpisać powód odrzucenia dokumentu w polu komentarza.');
                return;
            }
            payload.komentarz_dziekanatu = komentarz;
        }

        fetch(`/api/dziekanat/weryfikuj_zal2a/${praktykaId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(data => {
                const alerts = document.getElementById('alerts-container');
                if (data.success) {
                    alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    setTimeout(() => window.location.href = '/dziekanat/zal2a', 2500);
                } else {
                    alerts.innerHTML = `<div class="alert alert-danger">${data.message || 'Błąd zapisu'}</div>`;
                }
                window.scrollTo(0, 0);
            })
            .catch(err => console.error(err));
    };
});
