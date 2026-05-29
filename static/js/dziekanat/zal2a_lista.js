document.addEventListener('DOMContentLoaded', function () {
    loadZal2aLista();
});

function loadZal2aLista() {
    fetch('/api/dziekanat/zal2a')
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                throw new Error('Unauthorized');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error(data.error);
                return;
            }

            const doWeryfTbody = document.querySelector('#table-do-weryfikacji tbody');
            const badgeDoWeryf = document.getElementById('badge-do-weryfikacji');

            if (data.do_weryfikacji.length > 0) {
                badgeDoWeryf.textContent = data.do_weryfikacji.length;
                badgeDoWeryf.style.display = 'inline-block';

                doWeryfTbody.innerHTML = '';
                data.do_weryfikacji.forEach(d => {
                    doWeryfTbody.innerHTML += `
                        <tr>
                            <td class="fw-bold">${d.student_imie} ${d.student_nazwisko}</td>
                            <td>${d.nr_albumu}</td>
                            <td>${d.data_zlozenia}</td>
                            <td>
                                <a href="/dziekanat/weryfikuj_zal2a/${d.praktyka_id}" class="btn btn-sm btn-primary">
                                    <i class="bi bi-search"></i> Weryfikuj
                                </a>
                            </td>
                        </tr>
                    `;
                });
            } else {
                badgeDoWeryf.style.display = 'none';
                doWeryfTbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Brak dokumentów do weryfikacji</td></tr>';
            }

            // Zatwierdzone
            const zatwTbody = document.querySelector('#table-zatwierdzone tbody');
            if (data.zatwierdzone.length > 0) {
                zatwTbody.innerHTML = '';
                data.zatwierdzone.forEach(d => {
                    zatwTbody.innerHTML += `
                        <tr>
                            <td class="fw-bold">${d.student_imie} ${d.student_nazwisko}</td>
                            <td>${d.nr_albumu}</td>
                            <td>${d.data_zlozenia}</td>
                            <td>
                                <a href="/dziekanat/weryfikuj_zal2a/${d.praktyka_id}" class="btn btn-sm btn-outline-secondary">
                                    <i class="bi bi-eye"></i> Podgląd
                                </a>
                            </td>
                        </tr>
                    `;
                });
            } else {
                zatwTbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Brak zatwierdzonych dokumentów</td></tr>';
            }
        })
        .catch(err => console.error('Błąd pobierania listy Zał 2a:', err));
}
