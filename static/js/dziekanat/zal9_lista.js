document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/dziekanat/zal9')
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
            
            const doWeryfikacji = data.do_weryfikacji || [];
            const zatwierdzone = data.zatwierdzone || [];
            
            const badge = document.getElementById('do-weryfikacji-badge');
            if (doWeryfikacji.length > 0) {
                badge.textContent = doWeryfikacji.length;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
            
            const weryfTable = document.getElementById('do-weryfikacji-table');
            weryfTable.innerHTML = '';
            if (doWeryfikacji.length > 0) {
                doWeryfikacji.forEach(o => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="ps-4">
                            <strong>${o.student_imie} ${o.student_nazwisko}</strong><br>
                            <small class="text-muted">Album: ${o.nr_albumu}</small>
                        </td>
                        <td>${o.data_zlozenia || 'Brak danych'}</td>
                        <td class="text-center">
                            <a href="/dziekanat/weryfikuj_zal9/${o.id}" class="btn btn-sm btn-primary">
                                <i class="bi bi-search"></i> Sprawdź
                            </a>
                        </td>
                    `;
                    weryfTable.appendChild(tr);
                });
            } else {
                weryfTable.innerHTML = `
                    <tr>
                        <td colspan="3" class="text-center py-5 text-muted">
                            <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                            Brak nowych oświadczeń do weryfikacji.
                        </td>
                    </tr>
                `;
            }
            
            const histTable = document.getElementById('zatwierdzone-table');
            histTable.innerHTML = '';
            if (zatwierdzone.length > 0) {
                zatwierdzone.forEach(o => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="ps-4">
                            <strong>${o.student_imie} ${o.student_nazwisko}</strong><br>
                            <small class="text-muted">Album: ${o.nr_albumu}</small>
                        </td>
                        <td>${o.data_zlozenia || 'Brak danych'}</td>
                        <td class="text-center">
                            <span class="badge bg-secondary">${o.status}</span>
                        </td>
                        <td class="text-center">
                            <a href="/dziekanat/weryfikuj_zal9/${o.id}" class="btn btn-sm btn-outline-secondary">
                                <i class="bi bi-eye"></i> Podgląd
                            </a>
                        </td>
                    `;
                    histTable.appendChild(tr);
                });
            } else {
                histTable.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-5 text-muted">
                            <i class="bi bi-archive fs-1 d-block mb-2"></i>
                            Brak zatwierdzonych oświadczeń w historii.
                        </td>
                    </tr>
                `;
            }
        })
        .catch(err => console.error(err));
});
