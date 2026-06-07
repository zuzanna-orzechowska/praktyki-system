document.addEventListener('DOMContentLoaded', function() {
    function loadData() {
        fetch('/api/dziekanat/zal3')
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

                // Do Weryfikacji
                const doWeryfikacjiTbody = document.getElementById('do-weryfikacji-tbody');
                document.getElementById('badge-do-weryfikacji').textContent = data.do_weryfikacji.length;
                
                if (data.do_weryfikacji.length === 0) {
                    doWeryfikacjiTbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Brak dokumentów do weryfikacji</td></tr>';
                } else {
                    doWeryfikacjiTbody.innerHTML = '';
                    data.do_weryfikacji.forEach(doc => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td class="fw-bold">${doc.student_imie} ${doc.student_nazwisko}</td>
                            <td>${doc.nr_albumu}</td>
                            <td>${doc.data_zlozenia || '-'}</td>
                            <td>
                                <a href="/dziekanat/weryfikuj_zal3/${doc.praktyka_id}" class="btn btn-sm btn-primary">
                                    <i class="bi bi-search"></i> Weryfikuj
                                </a>
                            </td>
                        `;
                        doWeryfikacjiTbody.appendChild(tr);
                    });
                }

                // Zatwierdzone
                const zatwierdzoneTbody = document.getElementById('zatwierdzone-tbody');
                if (data.zatwierdzone.length === 0) {
                    zatwierdzoneTbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Brak zatwierdzonych dokumentów</td></tr>';
                } else {
                    zatwierdzoneTbody.innerHTML = '';
                    data.zatwierdzone.forEach(doc => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td class="fw-bold">${doc.student_imie} ${doc.student_nazwisko}</td>
                            <td>${doc.nr_albumu}</td>
                            <td>${doc.data_zlozenia || '-'}</td>
                            <td>
                                <a href="/dziekanat/weryfikuj_zal3/${doc.praktyka_id}" class="btn btn-sm btn-outline-secondary">
                                    <i class="bi bi-eye"></i> Podgląd
                                </a>
                            </td>
                        `;
                        zatwierdzoneTbody.appendChild(tr);
                    });
                }
            })
            .catch(err => console.error(err));
    }

    loadData();
});
