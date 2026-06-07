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
            
            // Uzytkownicy
            const uzytkownicy = data.uzytkownicy || [];
            const tableUzytkownicy = document.getElementById('uzytkownicy-table');
            tableUzytkownicy.innerHTML = '';
            if (uzytkownicy.length > 0) {
                uzytkownicy.forEach(u => {
                    const statusBadge = u.aktywny === 1 ? '<span class="badge bg-success">Aktywny</span>' : '<span class="badge bg-danger">Zablokowany</span>';
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${u.imie} ${u.nazwisko}</td>
                        <td>${u.email}</td>
                        <td><span class="badge bg-secondary">${u.rola}</span></td>
                        <td>${statusBadge}</td>
                        <td>
                            <button type="button" class="btn btn-sm btn-primary" onclick="otworzModalEdycjiUzytkownika(${u.id}, '${u.imie}', '${u.nazwisko}', '${u.email}', '${u.rola}', ${u.aktywny}, ${u.is_me})">Edytuj</button>
                        </td>
                    `;
                    tableUzytkownicy.appendChild(tr);
                });
            } else {
                tableUzytkownicy.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Brak użytkowników.</td></tr>';
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

function otworzModalEdycjiUzytkownika(id, imie, nazwisko, email, rola, aktywny, is_me) {
    document.getElementById('editUserId').value = id;
    document.getElementById('editUserImie').value = imie;
    document.getElementById('editUserNazwisko').value = nazwisko;
    document.getElementById('editUserEmail').value = email;
    document.getElementById('editUserRola').value = rola;
    document.getElementById('editUserAktywny').value = aktywny;
    document.getElementById('editUserHaslo').value = '';
    
    // Jeśli to moje konto, nie mogę odebrać sobie uprawnień ani się zablokować
    document.getElementById('editUserRola').disabled = is_me;
    document.getElementById('editUserAktywny').disabled = is_me;
    
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    modal.show();
}

function zapiszEdycjeUzytkownika() {
    const id = document.getElementById('editUserId').value;
    const data = {
        imie: document.getElementById('editUserImie').value,
        nazwisko: document.getElementById('editUserNazwisko').value,
        email: document.getElementById('editUserEmail').value,
        rola: document.getElementById('editUserRola').value,
        aktywny: parseInt(document.getElementById('editUserAktywny').value)
    };
    
    const haslo = document.getElementById('editUserHaslo').value;
    if (haslo) {
        data.haslo = haslo;
    }
    
    fetch(`/api/admin/uzytkownik/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
        modal.hide();
        
        const alerts = document.getElementById('alerts-container');
        if (data.success) {
            alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            loadDashboard();
        } else {
            alerts.innerHTML = `<div class="alert alert-danger">${data.error || data.message}</div>`;
        }
        window.scrollTo(0,0);
    })
    .catch(err => console.error(err));
}
