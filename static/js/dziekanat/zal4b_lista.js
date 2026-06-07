document.addEventListener('DOMContentLoaded', function() {
    loadZal4bLista();
});

function loadZal4bLista() {
    fetch('/api/dziekanat/zal4b')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            renderTable('table-do-weryfikacji', data.do_weryfikacji, true);
            renderTable('table-w-trakcie', data.w_trakcie, false);
            renderTable('table-zatwierdzone', data.zatwierdzone, false);

            const badge = document.getElementById('badge-do-weryfikacji');
            if (data.do_weryfikacji.length > 0) {
                badge.textContent = data.do_weryfikacji.length;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Błąd:', error);
            document.querySelectorAll('tbody').forEach(tbody => {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">Wystąpił błąd podczas ładowania danych.</td></tr>';
            });
        });
}

function renderTable(tableId, items, isActionable) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    tbody.innerHTML = '';

    if (!items || items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Brak dokumentów</td></tr>';
        return;
    }

    items.forEach(item => {
        const tr = document.createElement('tr');
        
        const actionBtnClass = isActionable ? 'btn-primary' : 'btn-outline-primary';
        const actionBtnText = isActionable ? 'Weryfikuj' : 'Podgląd';
        const actionBtnIcon = isActionable ? 'bi-search' : 'bi-eye';
        
        const actionHtml = `
            <a href="/dziekanat/weryfikuj_zal4b/${item.praktyka_id}" class="btn ${actionBtnClass} btn-sm">
                <i class="bi ${actionBtnIcon}"></i> ${actionBtnText}
            </a>
        `;

        tr.innerHTML = `
            <td><strong>${item.student_imie} ${item.student_nazwisko}</strong></td>
            <td>${item.nr_albumu}</td>
            <td>${item.data_zlozenia}</td>
            <td>${actionHtml}</td>
        `;
        tbody.appendChild(tr);
    });
}
