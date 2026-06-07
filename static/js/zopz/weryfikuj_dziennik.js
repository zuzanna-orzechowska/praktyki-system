let efektyListaGlobal = [];

document.addEventListener('DOMContentLoaded', function () {
    window.loadDziennik = function () {
        fetch(`/api/zopz/dziennik/${STUDENT_ID}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('alerts-container').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    return;
                }

                const student = data.student;
                const profil = data.student_profil;
                const praktyka = data.praktyka;
                const dokument = data.dokument;
                efektyListaGlobal = data.efekty_lista;

                document.getElementById('student-imie-nazwisko').textContent = `${student.imie} ${student.nazwisko}`;
                document.getElementById('student-nr-albumu').textContent = profil.nr_albumu || 'Brak';
                document.getElementById('student-specjalnosc').textContent = profil.specjalnosc || 'Brak';
                document.getElementById('student-studia').textContent = `inżynierskie, ${profil.tryb_studiow || 'stacjonarne'}`;
                document.getElementById('rok-akademicki-text').textContent = profil.rok_akademicki || 'Brak';

                document.getElementById('praktyka-zaklad').textContent = praktyka.zaklad_nazwa || 'Brak przypisanej firmy';
                document.getElementById('praktyka-start').textContent = praktyka.data_start || '';
                document.getElementById('praktyka-end').textContent = praktyka.data_end || '';

                // Status Badge
                const badge = document.getElementById('dokument-status-badge');
                badge.textContent = dokument.status;
                badge.className = 'badge';
                if (dokument.status === 'Draft') {
                    badge.classList.add('bg-secondary');
                    document.getElementById('alerts-container').innerHTML = `
                        <div class="alert alert-info shadow-sm mb-4 border-0">
                            <i class="bi bi-info-circle me-2"></i> 
                            Dziennik jest w fazie roboczej (Draft). Opcje weryfikacji i oceny (przyciski) pojawią się dopiero, gdy student wyśle dziennik do ZOPZ.
                        </div>`;
                }
                else if (dokument.status === 'Weryfikacja ZOPZ' || dokument.status === 'Weryfikacja UOPZ') badge.classList.add('bg-warning', 'text-dark');
                else if (dokument.status === 'Zatwierdzone przez ZOPZ') badge.classList.add('bg-success');
                else if (dokument.status === 'Wrócono do poprawy' || dokument.status === 'Odrzucone') badge.classList.add('bg-danger');
                else badge.classList.add('bg-info');

                const btnZatwierdz = document.getElementById('btn-zatwierdz-wszystko');
                if (dokument.status === 'Weryfikacja ZOPZ') {
                    btnZatwierdz.classList.remove('d-none');
                } else {
                    btnZatwierdz.classList.add('d-none');
                }

                const efektyUl = document.getElementById('efekty-list');
                efektyUl.innerHTML = '';
                efektyListaGlobal.forEach(efekt => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item mb-1';
                    li.innerHTML = `<strong>${efekt.kod}</strong>: ${efekt.opis}`;
                    efektyUl.appendChild(li);
                });

                const zalBody = document.getElementById('zalacznikiBody');
                zalBody.innerHTML = '';
                if (data.zalaczniki && data.zalaczniki.length > 0) {
                    data.zalaczniki.forEach((zal, idx) => {
                        const plikName = zal.plik_path ? zal.plik_path.split('/').pop() : 'Brak pliku';
                        zalBody.innerHTML += `
                            <tr>
                                <td class="text-center align-middle">${idx + 1}</td>
                                <td class="align-middle fw-bold">${zal.opis}</td>
                                <td class="align-middle text-break" style="font-size: 11px;">
                                    <a href="/static/${zal.plik_path}" target="_blank" class="text-decoration-none">
                                        <i class="bi bi-file-earmark-text"></i> ${plikName}
                                    </a>
                                </td>
                            </tr>
                        `;
                    });
                } else {
                    zalBody.innerHTML = '<tr><td colspan="3" class="text-center py-2 text-muted fst-italic">Brak załączników</td></tr>';
                }

                const tbody = document.getElementById('dziennikBody');
                tbody.innerHTML = '';

                if (data.wpisy && data.wpisy.length > 0) {
                    data.wpisy.forEach((wpis, index) => {
                        appendRow(tbody, index + 1, wpis, dokument.status);
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted fst-italic">Brak wpisów do wyświetlenia.</td></tr>';
                }
            })
            .catch(err => console.error(err));
    };

    window.loadDziennik();
});

function appendRow(tbody, dayNumber, wpis, statusDokumentu) {
    const tr = document.createElement('tr');

    let decyzjaHtml = '';
    let opisKlasa = '';

    if (wpis.potwierdzony_zopz === 1) {
        decyzjaHtml = '<span class="text-success fw-bold"><i class="bi bi-check-circle"></i> Potwierdzone</span>';
    } else if (wpis.potwierdzony_zopz === -1) {
        decyzjaHtml = `<span class="text-danger fw-bold"><i class="bi bi-x-circle"></i> Odrzucone</span>
                       <div class="mt-1 small text-danger text-start"><i class="bi bi-chat-left-text me-1"></i>${wpis.komentarz_zopz}</div>`;
        opisKlasa = 'bg-light border-danger text-danger';
    } else {
        if (statusDokumentu === 'Weryfikacja ZOPZ') {
            decyzjaHtml = `
                <button class="btn btn-sm btn-outline-danger" onclick="otworzModalOdrzucenia(${wpis.id}, ${dayNumber})">
                    <i class="bi bi-x-circle me-1"></i> Odrzuć dzień
                </button>
            `;
        } else {
            decyzjaHtml = '<span class="text-muted small">Oczekuje na weryfikację</span>';
        }
    }

    tr.innerHTML = `
        <td class="text-center fw-bold day-number">${dayNumber}</td>
        <td>
            <div class="form-control form-control-sm ${opisKlasa}" style="background-color: #f8f9fa; cursor: not-allowed;">${wpis.data_wpisu}</div>
        </td>
        <td>
            <div class="form-control form-control-sm ${opisKlasa}" style="background-color: #f8f9fa; cursor: not-allowed; min-height: 50px; white-space: pre-wrap; word-break: break-word; overflow-wrap: break-word;">${wpis.opis_prac}</div>
        </td>
        <td>
            <div class="form-control form-control-sm ${opisKlasa}" style="background-color: #f8f9fa; cursor: not-allowed;">${wpis.nr_efektu || '-'}</div>
        </td>
        <td class="text-center align-middle">
            ${decyzjaHtml}
        </td>
    `;

    tbody.appendChild(tr);
}

let currentOdrzucWpisId = null;

function otworzModalOdrzucenia(wpisId, nrDnia) {
    currentOdrzucWpisId = wpisId;
    document.getElementById('modal-dzien-nr').textContent = nrDnia;
    document.getElementById('modal-komentarz').value = '';
    const modal = new bootstrap.Modal(document.getElementById('odrzucModal'));
    modal.show();
}

window.zapiszOdrzucenie = function () {
    const komentarz = document.getElementById('modal-komentarz').value.trim();
    if (!komentarz) {
        alert('Musisz wpisać powód odrzucenia/uwagi dla studenta.');
        return;
    }

    fetch(`/api/zopz/dziennik/${STUDENT_ID}/odrzuc_wpis/${currentOdrzucWpisId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ komentarz: komentarz })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('odrzucModal')).hide();
                loadDziennik();
            } else {
                alert(data.error || 'Wystąpił błąd');
            }
        });
};

window.zatwierdzDziennik = function () {
    if (!confirm('Czy na pewno chcesz zakończyć weryfikację całego dziennika?\nWszystkie nieodrzucone dni zostaną ZATWIERDZONE.\n\nJeśli jakikolwiek dzień został przez Ciebie odrzucony (czerwony status), dziennik wróci do studenta do poprawy. Jeśli żaden nie został odrzucony, cały dziennik przejdzie na zielono i student będzie mógł go wysłać do Dziekanatu.')) {
        return;
    }

    const btn = document.getElementById('btn-zatwierdz-wszystko');
    const orgHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Przetwarzanie...';

    fetch(`/api/zopz/dziennik/${STUDENT_ID}/zatwierdz_dziennik`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById('alerts-container').innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                loadDziennik();
                window.scrollTo(0, 0);
            } else {
                document.getElementById('alerts-container').innerHTML = `<div class="alert alert-danger">${data.error || 'Błąd'}</div>`;
                btn.disabled = false;
                btn.innerHTML = orgHtml;
            }
        });
};
