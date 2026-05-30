document.addEventListener('DOMContentLoaded', function () {
    fetch('/api/zopz/dashboard')
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

            const zaklad = data.zaklad;
            if (zaklad) {
                document.getElementById('zaklad-container').style.display = 'block';
                document.getElementById('zaklad-nazwa').textContent = zaklad.nazwa;

                const adresStr = `${zaklad.ulica || ''} ${zaklad.nr_budynku || ''}${zaklad.nr_lokalu ? '/' + zaklad.nr_lokalu : ''}, ${zaklad.kod_pocztowy || ''} ${zaklad.miasto || ''}`.trim();
                document.getElementById('zaklad-adres-pola').textContent = adresStr !== ',' ? adresStr : 'Brak danych adresowych';

                const nipSpan = document.getElementById('zaklad-nip-pole');
                if (zaklad.nip) {
                    nipSpan.textContent = zaklad.nip;
                    nipSpan.className = 'fw-bold text-success';
                } else {
                    nipSpan.textContent = 'Brak (Wymagane uzupełnienie)';
                    nipSpan.className = 'fw-bold text-danger';
                }

                document.getElementById('form-nip').value = zaklad.nip || '';
                document.getElementById('form-telefon').value = zaklad.telefon || '';
                document.getElementById('form-ulica').value = zaklad.ulica || '';
                document.getElementById('form-nr_budynku').value = zaklad.nr_budynku || '';
                document.getElementById('form-nr_lokalu').value = zaklad.nr_lokalu || '';
                document.getElementById('form-kod_pocztowy').value = zaklad.kod_pocztowy || '';
                document.getElementById('form-miasto').value = zaklad.miasto || '';

            } else {
                document.getElementById('zaklad-warning').style.display = 'block';
            }

            const saveBtn = document.getElementById('saveZakladBtn');
            if (saveBtn) {
                saveBtn.addEventListener('click', function () {
                    const nipValue = document.getElementById('form-nip').value.replace(/[\s-]/g, '');

                    function isValidNip(nip) {
                        if (typeof nip !== 'string') return false;
                        if (nip.length !== 10) return false;
                        const weights = [6, 5, 7, 2, 3, 4, 5, 6, 7];
                        let sum = 0;
                        for (let i = 0; i < 9; i++) {
                            sum += parseInt(nip[i], 10) * weights[i];
                        }
                        return (sum % 11) === parseInt(nip[9], 10);
                    }

                    if (!isValidNip(nipValue)) {
                        alert('Wprowadzony NIP jest niepoprawny. Sprawdź, czy zawiera 10 cyfr i jest wpisany poprawnie.');
                        return;
                    }

                    const payload = {
                        nip: nipValue,
                        telefon: document.getElementById('form-telefon').value,
                        ulica: document.getElementById('form-ulica').value,
                        nr_budynku: document.getElementById('form-nr_budynku').value,
                        nr_lokalu: document.getElementById('form-nr_lokalu').value,
                        kod_pocztowy: document.getElementById('form-kod_pocztowy').value,
                        miasto: document.getElementById('form-miasto').value
                    };

                    fetch('/api/zopz/zaklad_pracy', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    })
                        .then(res => res.json())
                        .then(resData => {
                            if (resData.success) {
                                alert(resData.message);
                                window.location.reload();
                            } else {
                                alert(resData.error || 'Wystąpił błąd');
                            }
                        })
                        .catch(e => console.error(e));
                });
            }

            const praktykanci = data.praktyki || [];

            const table = document.getElementById('praktyki-table');
            if (table) table.innerHTML = '';

            let countAction = 0;
            const alertsContainer = document.getElementById('alerts-container');
            if (alertsContainer) alertsContainer.innerHTML = '';

            if (praktykanci.length > 0) {
                praktykanci.forEach(p => {
                    if (p.porozumienie_status === 'OczekujeZOPZ') {
                        countAction++;
                    }

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

                    let teczkaUrl = `/zopz/teczka/${p.student_id}`;
                    
                    if (table) {
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
                                    <a href="${teczkaUrl}" class="btn btn-sm btn-outline-secondary mb-1 position-relative">
                                        <i class="bi bi-folder2-open"></i> Teczka
                                        ${p.oczekujace_akcje > 0 ? `<span class="position-absolute top-0 start-100 translate-middle p-1 bg-danger border border-light rounded-circle"><span class="visually-hidden">Nowe dokumenty</span></span>` : ''}
                                    </a>
                                </td>
                            </tr>
                        `;
                    }
                });

                if (countAction > 0 && alertsContainer) {
                    alertsContainer.innerHTML = `
                        <div class="alert alert-warning alert-dismissible fade show shadow-sm mb-4" role="alert">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>Masz <strong>${countAction}</strong> studentów wymagających Twojej akcji.
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    `;
                }
            } else if (table) {
                table.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center py-4 text-muted">Brak przypisanych praktykantów w systemie.</td>
                    </tr>
                `;
            }
        })
        .catch(err => console.error(err));
});
