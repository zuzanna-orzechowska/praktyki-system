document.addEventListener('DOMContentLoaded', function() {
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
                
                // Pre-fill modal
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
                saveBtn.addEventListener('click', function() {
                    const nipValue = document.getElementById('form-nip').value.replace(/[\s-]/g, '');
                    
                    // NIP validation function
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
                        if(resData.success) {
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
            const table = document.getElementById('praktykanci-table');
            table.innerHTML = '';
            
            if (praktykanci.length > 0) {
                praktykanci.forEach(p => {
                    const dataStr = p.data_start && p.data_end ? `${p.data_start} - ${p.data_end}` : '<span class="text-muted">Brak danych</span>';
                    
                    let akcjeBtn = `<button class="btn btn-sm btn-outline-primary disabled" title="Dokumenty pojawią się wkrótce"><i class="bi bi-file-earmark-text"></i> Dokumenty</button>`;
                    
                    if (p.porozumienie_id) {
                        let btnClass = 'btn-outline-primary';
                        let icon = 'bi-file-earmark-text';
                        let text = 'Porozumienie (Zał. 1)';
                        
                        if (p.porozumienie_status === 'OczekujeZOPZ') {
                            btnClass = 'btn-primary';
                            icon = 'bi-exclamation-circle';
                            text = 'Do zatwierdzenia (Zał. 1)';
                        } else if (p.porozumienie_status === 'UwagiZOPZ') {
                            btnClass = 'btn-warning';
                            text = 'Odesłano z uwagami';
                        } else if (p.porozumienie_status === 'ZatwierdzoneZOPZ' || p.porozumienie_status === 'Podpisane') {
                            btnClass = 'btn-success';
                            icon = 'bi-check-circle';
                            text = 'Zatwierdzone';
                        }
                        
                        akcjeBtn = `<a href="/zopz/porozumienie/${p.porozumienie_id}" class="btn btn-sm ${btnClass}"><i class="bi ${icon}"></i> ${text}</a>`;
                    }
                    
                    table.innerHTML += `
                        <tr>
                            <td class="ps-4">
                                <strong>${p.student_imie} ${p.student_nazwisko}</strong><br>
                                <small class="text-muted">Album: ${p.nr_albumu}</small>
                            </td>
                            <td>${p.kierunek}</td>
                            <td>${dataStr}</td>
                            <td><span class="badge bg-secondary">${p.status}</span></td>
                            <td class="text-center">
                                ${akcjeBtn}
                            </td>
                        </tr>
                    `;
                });
            } else {
                table.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center py-5 text-muted">
                            <i class="bi bi-person-x fs-1 d-block mb-2"></i>
                            Brak przypisanych studentów do Twojej firmy.
                        </td>
                    </tr>
                `;
            }
        })
        .catch(err => console.error(err));
});
