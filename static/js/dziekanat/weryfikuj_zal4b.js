document.addEventListener('DOMContentLoaded', function() {
    loadWniosekData();
});

function loadWniosekData() {
    fetch(`/api/dziekanat/weryfikuj_zal4b/${PRAKTYKA_ID}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            // Wypełnianie danych
            const studentInfo = `${data.uzytkownik.imie} ${data.uzytkownik.nazwisko}`;
            document.getElementById('student-info').textContent = studentInfo;
            document.getElementById('student-album').textContent = data.student.nr_albumu;
            
            const kier = data.student.kierunek || 'Informatyka';
            document.getElementById('student-kierunek1').textContent = kier;
            document.getElementById('student-kierunek2').textContent = kier;
            document.getElementById('specjalnosc').value = data.student.specjalnosc || '';
            
            if (data.dokument && data.dokument.created_at) {
                document.getElementById('data-wypelnienia').textContent = new Date(data.dokument.created_at).toLocaleDateString('pl-PL');
            }

            if (data.wniosek) {
                document.getElementById('okres-od').value = data.wniosek.okres_zatrudnienia_od || '';
                document.getElementById('okres-do').value = data.wniosek.okres_zatrudnienia_do || '';
                document.getElementById('stanowisko').value = data.wniosek.stanowisko || '';
                document.getElementById('zakres-obowiazkow').value = data.wniosek.zakres_obowiazkow || '';
                document.getElementById('uzasadnienie').value = data.wniosek.uzasadnienie || '';
                
                if (data.wniosek.podpis_studenta) {
                    const dataPod = data.wniosek.data_podpisu || new Date().toISOString().split('T')[0];
                    const dzisiajFormat = new Date(dataPod).toLocaleDateString('pl-PL');
                    const safePodpis = data.wniosek.podpis_studenta.split('(')[0].trim();
                    document.getElementById('podpis-student').innerHTML = `<span style="font-family: sans-serif; color: #000; font-size: 14px; margin-right: 10px;">${dzisiajFormat}</span>${safePodpis}`;
                }
            }

            // Załączniki
            const zalList = document.getElementById('zalaczniki-list');
            if (data.zalaczniki && data.zalaczniki.length > 0) {
                zalList.innerHTML = '';
                data.zalaczniki.forEach((zal, idx) => {
                    const nazwa = zal.path.split('/').pop();
                    const opis = zal.opis || 'Brak opisu';
                    const linkHtml = `
                        <a href="/static/${zal.path}" target="_blank" class="list-group-item list-group-item-action">
                            <div class="d-flex w-100 justify-content-between">
                                <h6 class="mb-1"><i class="bi bi-file-earmark-pdf text-danger"></i> ${nazwa}</h6>
                            </div>
                            <p class="mb-1 text-muted small">${opis}</p>
                        </a>
                    `;
                    zalList.insertAdjacentHTML('beforeend', linkHtml);
                });
            }

            // Decyzja
            renderDecyzja(data.dokument.status, data.dokument.komentarz);
        })
        .catch(error => {
            console.error('Błąd:', error);
            alert('Wystąpił błąd podczas ładowania danych wniosku.');
        });
}

function renderDecyzja(status, komentarz) {
    const container = document.getElementById('decyzja-container');
    
    if (status === 'Approved') {
        container.innerHTML = `
            <div class="alert alert-success mb-0">
                <i class="bi bi-check-circle-fill"></i> Wniosek został zatwierdzony.
            </div>
        `;
    } else if (status === 'Returned') {
        container.innerHTML = `
            <div class="alert alert-warning mb-0">
                <i class="bi bi-exclamation-triangle-fill"></i> Wniosek odrzucony do poprawy.
                ${komentarz ? `<hr><small>Uwagi: ${komentarz}</small>` : ''}
            </div>
        `;
    } else if (status === 'Submitted') {
        container.innerHTML = `
            <div class="mb-3">
                <label class="form-label small fw-bold text-muted">Uwagi do poprawy/odrzucenia (wymagane)</label>
                <textarea id="komentarz-dziekanatu" class="form-control mb-3" rows="3" placeholder="Wpisz uwagi..."></textarea>
            </div>
            <div class="d-grid gap-2">
                <button class="btn btn-success" onclick="zmienStatus('zatwierdz')">
                    <i class="bi bi-check-lg"></i> Zatwierdź wniosek
                </button>
                <button class="btn btn-outline-warning" onclick="zmienStatus('odrzuc')">
                    <i class="bi bi-arrow-counterclockwise"></i> Zwróć do poprawy
                </button>
                <hr>
                <button class="btn btn-danger" onclick="zmienStatus('odrzuc_calkowicie')">
                    <i class="bi bi-x-octagon-fill"></i> Odrzuć całkowicie ścieżkę
                </button>
                <small class="text-danger text-center mt-1" style="font-size: 0.75rem;">Ta opcja cofa studenta na sam początek (Brak zgłoszenia)</small>
            </div>
        `;
    } else {
        container.innerHTML = `
            <div class="alert alert-secondary mb-0">
                Wniosek jest w trakcie edycji przez studenta (status: ${status}).
            </div>
        `;
    }
}

function zmienStatus(akcja) {
    if (akcja === 'odrzuc' || akcja === 'odrzuc_calkowicie') {
        const komentarz = document.getElementById('komentarz-dziekanatu').value;
        if (!komentarz.trim()) {
            alert("Podaj powód odrzucenia/zwrotu wniosku w polu uwag.");
            return;
        }
    }
    
    let msg = "";
    if (akcja === 'zatwierdz') msg = "Czy na pewno chcesz OSTATECZNIE ZATWIERDZIĆ ten wniosek?";
    else if (akcja === 'odrzuc') msg = "Zwrócić wniosek do poprawy przez studenta?";
    else if (akcja === 'odrzuc_calkowicie') msg = "UWAGA: Odrzucenie całkowite zablokuje ten wniosek i cofnie studenta do ekranu wyboru ścieżki. Czy kontynuować?";
    
    if (!confirm(msg)) {
        return;
    }

    const payload = { akcja: akcja };
    if (akcja === 'odrzuc' || akcja === 'odrzuc_calkowicie') {
        payload.komentarz_dziekanatu = document.getElementById('komentarz-dziekanatu').value;
    }

    fetch(`/api/dziekanat/weryfikuj_zal4b/${PRAKTYKA_ID}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            window.location.reload();
        } else {
            alert(data.error || 'Wystąpił błąd.');
        }
    })
    .catch(error => {
        console.error('Błąd:', error);
        alert('Błąd sieci.');
    });
}
