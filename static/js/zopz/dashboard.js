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

            const contAction = document.getElementById('students-action-needed');
            const contInProgress = document.getElementById('students-in-progress');
            const contApproved = document.getElementById('students-approved');

            let countAction = 0;
            let countInProgress = 0;
            let countApproved = 0;

            const alertsContainer = document.getElementById('alerts-container');
            if (alertsContainer) alertsContainer.innerHTML = '';

            if (praktykanci.length > 0) {
                praktykanci.forEach(p => {
                    let akcjeBtn = `<button class="btn btn-sm btn-outline-primary disabled w-100 text-start"><i class="bi bi-file-earmark-text"></i> Dokumenty niedostępne</button>`;
                    let isActionNeeded = false;
                    let isApproved = false;

                    if (p.porozumienie_id) {
                        let btnClass = 'btn-outline-primary';
                        let icon = 'bi-file-earmark-text';
                        let text = 'Porozumienie (Zał. 1)';

                        if (p.porozumienie_status === 'OczekujeZOPZ') {
                            btnClass = 'btn-primary';
                            icon = 'bi-exclamation-circle';
                            text = 'Do zatwierdzenia (Zał. 1)';
                            isActionNeeded = true;
                        } else if (p.porozumienie_status === 'UwagiZOPZ') {
                            btnClass = 'btn-warning text-dark';
                            text = 'Odesłano z uwagami (Zał. 1)';
                        } else if (p.porozumienie_status === 'ZatwierdzoneZOPZ' || p.porozumienie_status === 'Podpisane') {
                            btnClass = 'btn-success';
                            icon = 'bi-check-circle';
                            text = 'Zatwierdzone (Zał. 1)';
                            isApproved = true;
                        }

                        akcjeBtn = `<a href="/zopz/porozumienie/${p.porozumienie_id}" class="btn btn-sm ${btnClass} w-100 text-start"><i class="bi ${icon}"></i> ${text}</a>`;
                    }

                    const zal2aBtn = `<a href="/zopz/zal2a_harmonogram/${p.student_id}" class="btn btn-sm btn-outline-secondary w-100 text-start"><i class="bi bi-calendar-check"></i> Harmonogram (Zał. 2a)</a>`;

                    const cardHtml = `
                        <div class="col-md-6 col-lg-4">
                            <div class="card shadow-sm border-0 h-100 ${isActionNeeded ? 'border-start border-warning border-4' : (isApproved ? 'border-start border-success border-4' : '')}">
                                <div class="card-body d-flex flex-column">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <h6 class="card-title fw-bold mb-0 text-primary"><i class="bi bi-person-fill"></i> ${p.student_imie} ${p.student_nazwisko}</h6>
                                    </div>
                                    <p class="text-muted small mb-1">Album: ${p.nr_albumu} | ${p.kierunek}</p>
                                    <p class="text-muted small mb-3">Status: <span class="badge bg-secondary">${p.status}</span></p>
                                    
                                    <div class="mt-auto d-flex flex-column gap-2">
                                        ${akcjeBtn}
                                        ${zal2aBtn}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

                    if (isActionNeeded) {
                        contAction.insertAdjacentHTML('beforeend', cardHtml);
                        countAction++;
                    } else if (isApproved) {
                        contApproved.insertAdjacentHTML('beforeend', cardHtml);
                        countApproved++;
                    } else {
                        contInProgress.insertAdjacentHTML('beforeend', cardHtml);
                        countInProgress++;
                    }
                });

                if (countAction > 0) document.getElementById('empty-action-needed').style.display = 'none';
                if (countInProgress > 0) document.getElementById('empty-in-progress').style.display = 'none';
                if (countApproved > 0) document.getElementById('empty-approved').style.display = 'none';

                if (countAction > 0 && alertsContainer) {
                    alertsContainer.innerHTML = `
                        <div class="alert alert-warning alert-dismissible fade show shadow-sm mb-4" role="alert">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>Masz <strong>${countAction}</strong> studentów wymagających Twojej akcji. Sprawdź odpowiednią sekcję poniżej.
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        </div>
                    `;
                }
            }
        })
        .catch(err => console.error(err));
});
