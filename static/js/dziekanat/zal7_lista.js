document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/dziekanat/zal7_lista')
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

            renderTable('do-akcji-table', data.do_akcji, true, 'do-akcji-count');
            renderTable('w-toku-table', data.w_toku, false, 'w-toku-count');
            renderTable('zatwierdzone-table', data.zatwierdzone, false, 'zatwierdzone-count');
        })
        .catch(err => console.error(err));

    function renderTable(tbodyId, items, isActionable, countId) {
        const tbody = document.getElementById(tbodyId);
        const countEl = document.getElementById(countId);
        tbody.innerHTML = '';

        if (countEl) {
            if (items && items.length > 0) {
                countEl.textContent = items.length;
                countEl.classList.remove('d-none');
            } else {
                countEl.classList.add('d-none');
            }
        }

        if (!items || items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Brak dokumentów w tej kategorii</td></tr>';
            return;
        }

        items.forEach((doc, index) => {
            const tr = document.createElement('tr');
            
            let statusBadge = `<span class="badge bg-secondary">${doc.status}</span>`;
            if (doc.status === 'Weryfikacja UOPZ' || doc.status === 'Weryfikacja Dziekanatu' || doc.status === 'Weryfikacja Dyrektor') {
                statusBadge = `<span class="badge bg-warning text-dark">Weryfikacja Uczelni</span>`;
            } else if (doc.status === 'Weryfikacja ZOPZ' || doc.status === 'Draft' || doc.status === 'Wrócono do poprawy') {
                statusBadge = `<span class="badge bg-info text-dark">U Studenta/ZOPZ</span>`;
            } else if (doc.status === 'Approved') {
                statusBadge = `<span class="badge bg-success">Zatwierdzone</span>`;
            }

            const btnClass = isActionable ? 'btn-primary' : 'btn-outline-secondary';
            const btnText = isActionable ? 'Weryfikuj' : 'Podgląd';
            const btnIcon = isActionable ? 'bi-pencil-square' : 'bi-eye';

            tr.innerHTML = `
                <td class="text-muted fw-bold">${index + 1}</td>
                <td class="fw-bold">${doc.student_imie} ${doc.student_nazwisko}</td>
                <td>${doc.nr_albumu}</td>
                <td>${doc.data_zlozenia}</td>
                <td>${statusBadge}</td>
                <td class="text-end">
                    <a href="/dziekanat/${doc.typ.toLowerCase()}_sprawozdanie/${doc.student_id}" class="btn btn-sm ${btnClass}">
                        <i class="bi ${btnIcon}"></i> ${btnText}
                    </a>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
});
