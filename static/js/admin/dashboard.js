document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();

    document.getElementById('stworz-zopz-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const data = {
            imie: document.getElementById('zopz-imie').value,
            nazwisko: document.getElementById('zopz-nazwisko').value,
            email: document.getElementById('zopz-email').value
        };
        
        fetch('/api/admin/stworz_zopz', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            const alerts = document.getElementById('alerts-container');
            if (data.success) {
                alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                document.getElementById('stworz-zopz-form').reset();
                loadDashboard();
            } else {
                alerts.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            }
            window.scrollTo(0,0);
        })
        .catch(err => console.error(err));
    });
});

function loadDashboard() {
    fetch('/api/admin/dashboard')
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
                return;
            }
            
            // Oczekujacy
            const oczekujacy = data.oczekujacy || [];
            const zgloszenia = data.zgloszenia_zopz || [];
            
            const badge = document.getElementById('oczekujacy-badge');
            const navBadge = document.getElementById('nav-admin-badge');
            const totalOczekujacy = oczekujacy.length + zgloszenia.length;
            
            if (totalOczekujacy > 0) {
                badge.textContent = totalOczekujacy;
                badge.style.display = 'inline-block';
                if (navBadge) {
                    navBadge.textContent = totalOczekujacy;
                    navBadge.style.display = 'inline-block';
                }
            } else {
                badge.style.display = 'none';
                if (navBadge) navBadge.style.display = 'none';
            }
            
            const tableOczekujacy = document.getElementById('oczekujacy-table');
            tableOczekujacy.innerHTML = '';
            if (oczekujacy.length > 0) {
                oczekujacy.forEach(u => {
                    tableOczekujacy.innerHTML += `
                        <tr>
                            <td>${u.imie} ${u.nazwisko}</td>
                            <td>${u.email}</td>
                            <td>
                                <select id="rola-${u.id}" class="form-select form-select-sm d-inline-block w-auto me-2">
                                    <option value="" selected disabled>Wybierz rolę...</option>
                                    <option value="dziekanat">Dziekanat</option>
                                    <option value="uopz">UOPZ</option>
                                    <option value="dyrektor">Dyrektor</option>
                                    <option value="pracownik">Pracownik</option>
                                </select>
                                <button type="button" class="btn btn-sm btn-success" onclick="akceptujPracownika(${u.id})">Akceptuj</button>
                            </td>
                        </tr>
                    `;
                });
            } else {
                tableOczekujacy.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Brak oczekujących pracowników.</td></tr>';
            }
            
            // Zgloszenia ZOPZ
            const zgloszeniaContainer = document.getElementById('zgloszenia-zopz-container');
            const zgloszeniaTable = document.getElementById('zgloszenia-zopz-table');
            if (zgloszenia.length > 0) {
                zgloszeniaContainer.style.display = 'block';
                zgloszeniaTable.innerHTML = '';
                zgloszenia.forEach(z => {
                    zgloszeniaTable.innerHTML += `
                        <tr>
                            <td>${z.opiekun_imie} ${z.opiekun_nazwisko}</td>
                            <td>${z.nazwa_instytucji}</td>
                            <td>${z.opiekun_email}</td>
                            <td>
                                <button type="button" class="btn btn-sm btn-success" onclick="akceptujZgloszenieZopz(${z.id})">Generuj konto i wyślij e-mail</button>
                            </td>
                        </tr>
                    `;
                });
            } else {
                zgloszeniaContainer.style.display = 'none';
            }
            
            // Pracownicy
            const pracownicy = data.pracownicy || [];
            const tablePracownicy = document.getElementById('pracownicy-table');
            tablePracownicy.innerHTML = '';
            if (pracownicy.length > 0) {
                pracownicy.forEach(u => {
                    tablePracownicy.innerHTML += `
                        <tr>
                            <td>${u.imie} ${u.nazwisko}</td>
                            <td>${u.email}</td>
                            <td><span class="badge bg-secondary">${u.rola}</span></td>
                            <td>${u.data_utworzenia}</td>
                        </tr>
                    `;
                });
            } else {
                tablePracownicy.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Brak pracowników.</td></tr>';
            }
            
            // ZOPZ
            const opiekunowie = data.opiekunowie || [];
            const tableZopz = document.getElementById('zopz-table');
            tableZopz.innerHTML = '';
            if (opiekunowie.length > 0) {
                opiekunowie.forEach(z => {
                    tableZopz.innerHTML += `
                        <tr>
                            <td>${z.imie} ${z.nazwisko}</td>
                            <td>${z.email}</td>
                            <td><span class="badge bg-info text-dark">${z.auth_provider.toUpperCase()}</span></td>
                        </tr>
                    `;
                });
            } else {
                tableZopz.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Brak opiekunów ZOPZ.</td></tr>';
            }
        })
        .catch(err => console.error(err));
}

function akceptujPracownika(id) {
    const rola = document.getElementById(`rola-${id}`).value;
    if (!rola) {
        alert('Proszę najpierw wybrać rolę z listy.');
        return;
    }
    
    fetch(`/api/admin/akceptuj_pracownika/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rola: rola })
    })
    .then(response => response.json())
    .then(data => {
        const alerts = document.getElementById('alerts-container');
        if (data.success) {
            alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            loadDashboard();
        } else {
            alerts.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
        }
        window.scrollTo(0,0);
    })
    .catch(err => console.error(err));
}

function akceptujZgloszenieZopz(oswiadczenie_id) {
    fetch(`/api/admin/stworz_zopz_z_zal9/${oswiadczenie_id}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        const alerts = document.getElementById('alerts-container');
        if (data.success) {
            alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            loadDashboard();
        } else {
            alerts.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            // Jeśli nie powiodło się, bo np. już istnieje, nadal przeładujmy by zniknęło
            loadDashboard();
        }
        window.scrollTo(0,0);
    })
    .catch(err => console.error(err));
}
