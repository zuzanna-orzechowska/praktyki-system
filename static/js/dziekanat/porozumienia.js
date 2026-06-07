document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/dziekanat/porozumienia')
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
            
            const wszystkie = data.porozumienia || [];
            const wToku = wszystkie.filter(p => p.status_porozumienia !== 'Podpisane');
            const podpisane = wszystkie.filter(p => p.status_porozumienia === 'Podpisane');
            
            const wTokuTable = document.getElementById('w-toku-table');
            wTokuTable.innerHTML = '';
            
            if (wToku.length > 0) {
                wToku.forEach(p => {
                    let badgeClass = 'secondary';
                    if (p.status_porozumienia === 'OczekujeZOPZ') badgeClass = 'primary';
                    else if (p.status_porozumienia === 'ZatwierdzoneZOPZ') badgeClass = 'info';
                    else if (p.status_porozumienia === 'UwagiZOPZ') badgeClass = 'warning text-dark';
                    
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="fw-bold">${p.student_imie} ${p.student_nazwisko}</td>
                        <td>${p.nr_albumu}</td>
                        <td>${p.data_zlozenia || 'Brak'}</td>
                        <td class="text-center">
                            <a href="/dziekanat/weryfikuj_porozumienie/${p.praktyka_id}" class="btn btn-sm btn-primary">
                                <i class="bi bi-search"></i> Zarządzaj
                            </a>
                        </td>
                    `;
                    wTokuTable.appendChild(tr);
                });
            } else {
                wTokuTable.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-5 text-muted">
                            <i class="bi bi-check2-circle fs-1 d-block mb-2"></i>
                            Brak porozumień w toku.
                        </td>
                    </tr>
                `;
            }
            
            const podpisaneTable = document.getElementById('podpisane-table');
            podpisaneTable.innerHTML = '';
            
            if (podpisane.length > 0) {
                podpisane.forEach(p => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="fw-bold">${p.student_imie} ${p.student_nazwisko}</td>
                        <td>${p.nr_albumu}</td>
                        <td>${p.data_zlozenia || 'Brak'}</td>
                        <td class="text-center">
                            <a href="/dziekanat/weryfikuj_porozumienie/${p.praktyka_id}" class="btn btn-sm btn-outline-secondary">
                                <i class="bi bi-eye"></i> Podgląd
                            </a>
                        </td>
                    `;
                    podpisaneTable.appendChild(tr);
                });
            } else {
                podpisaneTable.innerHTML = `
                    <tr>
                        <td colspan="3" class="text-center py-5 text-muted">
                            <i class="bi bi-archive fs-1 d-block mb-2"></i>
                            Brak podpisanych porozumień w historii.
                        </td>
                    </tr>
                `;
            }
        })
        .catch(err => console.error(err));
});
