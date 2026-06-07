document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/uopz/dashboard')
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
            
            const praktyki = data.praktyki || [];
            const table = document.getElementById('praktyki-table');
            table.innerHTML = '';
            
            if (praktyki.length > 0) {
                praktyki.forEach(p => {
                    const dataStr = p.data_start && p.data_end ? `${p.data_start} - ${p.data_end}` : '<span class="text-muted">Brak danych</span>';
                    
                    const statusMap = {
                        'BRAK_ZGŁOSZENIA': { text: 'Brak zgłoszenia', color: 'secondary' },
                        'OCZEKUJE_NA_ZAL9': { text: 'Oczekuje na zał. 9', color: 'warning text-dark' },
                        'ZAL9_ZATWIERDZONE': { text: 'Zał. 9 zatwierdzony', color: 'success' },
                        'SCIEZKA_PRACA': { text: 'Zaliczenie z pracy', color: 'info text-dark' },
                        'PROGRAM_UZGODNIONY': { text: 'Program uzgodniony', color: 'primary' },
                        'SKIEROWANIE_WYDANE': { text: 'Skierowanie wydane', color: 'success' },
                        'PRAKTYKA_W_TOKU': { text: 'Praktyka w toku', color: 'warning text-dark' },
                        'DOKUMENTY_ZLOZONE': { text: 'Dokumenty złożone', color: 'info text-dark' },
                        'EGZAMIN': { text: 'Egzamin', color: 'info text-dark' },
                        'ZALICZONA': { text: 'Praktyka zaliczona', color: 'success' }
                    };
                    const mappedStatus = statusMap[p.status] || { text: p.status, color: 'secondary' };
                    
                    table.innerHTML += `
                        <tr>
                            <td class="ps-4 fw-bold">
                                ${p.student_imie} ${p.student_nazwisko}
                                ${p.oczekujace_akcje > 0 ? `<span class="badge bg-danger ms-1">${p.oczekujace_akcje}</span>` : ''}
                            </td>
                            <td>${p.nr_albumu}</td>
                            <td>${p.kierunek || 'Brak danych'}</td>
                            <td>${dataStr}</td>
                            <td><span class="badge bg-${mappedStatus.color}">${mappedStatus.text}</span></td>
                            <td class="text-end pe-4">
                                <a href="/uopz/teczka/${p.student_id}" class="btn btn-sm btn-outline-secondary mb-1 position-relative">
                                    <i class="bi bi-folder2-open"></i> Teczka
                                    ${p.oczekujace_akcje > 0 ? `<span class="position-absolute top-0 start-100 translate-middle p-1 bg-danger border border-light rounded-circle"><span class="visually-hidden">Nowe dokumenty</span></span>` : ''}
                                </a>
                            </td>
                        </tr>
                    `;
                });
            } else {
                table.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center py-4 text-muted">Nie masz jeszcze przypisanych żadnych studentów.</td>
                    </tr>
                `;
            }
        })
        .catch(err => console.error(err));
});
