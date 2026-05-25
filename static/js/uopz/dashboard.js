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
                    
                    table.innerHTML += `
                        <tr>
                            <td class="ps-4 fw-bold">${p.student_imie} ${p.student_nazwisko}</td>
                            <td>${p.nr_albumu}</td>
                            <td>${p.kierunek || 'Brak danych'}</td>
                            <td>${dataStr}</td>
                            <td><span class="badge bg-secondary">${p.status}</span></td>
                            <td class="text-end pe-4">
                                <a href="/uopz/teczka/${p.student_id}" class="btn btn-sm btn-outline-primary">
                                    <i class="bi bi-folder2-open"></i> Otwórz teczkę
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
