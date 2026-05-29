document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/uopz/zal2a_lista')
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                throw new Error('Unauthorized');
            }
            return response.json();
        })
        .then(data => {
            renderTable('do-akcji-table', data.do_akcji, 'Brak dokumentów wymagających Twojej akcji.');
            renderTable('w-toku-table', data.w_toku, 'Brak dokumentów w trakcie procedowania.');
            renderTable('zatwierdzone-table', data.zatwierdzone, 'Brak zatwierdzonych dokumentów.');
        })
        .catch(err => console.error(err));
});

function renderTable(tbodyId, items, emptyMsg) {
    const tbody = document.getElementById(tbodyId);
    tbody.innerHTML = '';

    if (!items || items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">${emptyMsg}</td></tr>`;
        return;
    }

    items.forEach(d => {
        let badgeClass = 'bg-secondary';
        let statusText = d.status;

        if (d.status === 'Draft_UOPZ' || d.status === 'Draft' || d.status === 'Rejected') {
            badgeClass = 'bg-warning text-dark';
            statusText = 'Szkic / Do uzupełnienia';
        } else if (d.status === 'Sent_back_to_UOPZ') {
            badgeClass = 'bg-danger';
            statusText = 'Odesłane przez Zakład (ZOPZ)';
        } else if (d.status === 'Sent_to_ZOPZ') {
            badgeClass = 'bg-primary';
            statusText = 'W weryfikacji u ZOPZ';
        } else if (d.status === 'Student_Review') {
            badgeClass = 'bg-info text-dark';
            statusText = 'Oczekuje na akceptację studenta';
        } else if (d.status === 'Submitted') {
            badgeClass = 'bg-info';
            statusText = 'Przesłane do Dziekanatu';
        } else if (d.status === 'Approved') {
            badgeClass = 'bg-success';
            statusText = 'Zatwierdzone';
        }

        tbody.innerHTML += `
            <tr>
                <td class="fw-bold">${d.student_imie} ${d.student_nazwisko}</td>
                <td>${d.nr_albumu}</td>
                <td>${d.data_zlozenia || '-'}</td>
                <td><span class="badge ${badgeClass}">${statusText}</span></td>
                <td class="text-end">
                    <a href="/uopz/zal2a_harmonogram/${d.student_id}" class="btn btn-sm btn-outline-primary">
                        <i class="bi bi-calendar-check"></i> Otwórz Harmonogram
                    </a>
                </td>
            </tr>
        `;
    });
}
