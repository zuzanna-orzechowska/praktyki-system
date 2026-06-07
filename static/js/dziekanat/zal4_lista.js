document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/dziekanat/zal4_lista')
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

            renderTable('w-toku-table', data.w_toku);
            renderTable('zatwierdzone-table', data.zatwierdzone);
        })
        .catch(err => console.error(err));

    function renderTable(tbodyId, items) {
        const tbody = document.getElementById(tbodyId);
        tbody.innerHTML = '';

        if (!items || items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Brak dokumentów w tej kategorii</td></tr>';
            return;
        }

        items.forEach(doc => {
            const tr = document.createElement('tr');
            
            let statusBadge = `<span class="badge bg-secondary">${doc.status}</span>`;
            if (doc.status === 'Weryfikacja UOPZ') {
                statusBadge = `<span class="badge bg-warning text-dark">Oczekuje na UOPZ</span>`;
            } else if (doc.status === 'Draft' || doc.status === 'Weryfikacja ZOPZ') {
                statusBadge = `<span class="badge bg-info text-dark">U Studenta/ZOPZ</span>`;
            } else if (doc.status === 'Zatwierdzone') {
                statusBadge = `<span class="badge bg-success">Zatwierdzone</span>`;
            }

            const btnClass = 'btn-outline-secondary';
            const btnText = 'Podgląd';
            const btnIcon = 'bi-eye';

            tr.innerHTML = `
                <td class="fw-bold">${doc.student_imie} ${doc.student_nazwisko}</td>
                <td>${doc.nr_albumu}</td>
                <td>${doc.data_zlozenia}</td>
                <td>${statusBadge}</td>
                <td class="text-end">
                    <a href="/dziekanat/zal4_efekty/${doc.student_id}" class="btn btn-sm ${btnClass}">
                        <i class="bi ${btnIcon}"></i> ${btnText}
                    </a>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
});
