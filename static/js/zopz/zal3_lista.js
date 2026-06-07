document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/zopz/zal3_lista')
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

            renderTable('do-akcji-table', data.do_akcji, true);
            renderTable('w-toku-table', data.w_toku, false);
            renderTable('zatwierdzone-table', data.zatwierdzone, false);
        })
        .catch(err => console.error(err));

    function renderTable(tbodyId, items, isActionable) {
        const tbody = document.getElementById(tbodyId);
        tbody.innerHTML = '';

        if (!items || items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Brak dokumentów w tej kategorii</td></tr>';
            return;
        }

        items.forEach(doc => {
            const tr = document.createElement('tr');
            
            let statusBadge = `<span class="badge bg-secondary">${doc.status}</span>`;
            if (doc.status === 'Draft_UOPZ' || doc.status === 'Weryfikacja_Uczelni') {
                statusBadge = `<span class="badge bg-info text-dark">W uczelni</span>`;
            } else if (doc.status === 'Skierowanie_Wydane') {
                statusBadge = `<span class="badge bg-warning text-dark">Wydano Skierowanie</span>`;
            } else if (doc.status === 'Weryfikacja_ZOPZ') {
                statusBadge = `<span class="badge bg-primary">Wypełnianie Oceny</span>`;
            } else if (doc.status === 'Zatwierdzone') {
                statusBadge = `<span class="badge bg-success">Zatwierdzone</span>`;
            }

            const btnClass = isActionable ? 'btn-primary' : 'btn-outline-secondary';
            const btnText = isActionable ? 'Rozpatrz' : 'Podgląd';
            const btnIcon = isActionable ? 'bi-pencil-square' : 'bi-eye';

            tr.innerHTML = `
                <td class="fw-bold">${doc.student_imie} ${doc.student_nazwisko}</td>
                <td>${doc.nr_albumu}</td>
                <td>${doc.data_zlozenia}</td>
                <td>${statusBadge}</td>
                <td class="text-end">
                    <a href="/zopz/zal3_karta/${doc.student_id}" class="btn btn-sm ${btnClass}">
                        <i class="bi ${btnIcon}"></i> ${btnText}
                    </a>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
});
