let efektyListaGlobal = [];

document.addEventListener('DOMContentLoaded', function() {
    window.loadDziennik = function() {
        fetch(`/api/uopz/dziennik/${STUDENT_ID}`)
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
                
                document.getElementById('student-imie-nazwisko').textContent = `${student.imie} ${student.nazwisko}`;
                document.getElementById('student-nr-albumu').textContent = profil.nr_albumu || 'Brak';
                document.getElementById('rok-akademicki-text').textContent = profil.rok_akademicki || 'Brak';
                
                document.getElementById('miejsce-praktyk').textContent = praktyka.zaklad_nazwa || 'Brak przypisanej firmy';
                
                // Status Badge
                const badge = document.getElementById('dokument-status-badge');
                badge.textContent = dokument.status;
                badge.className = 'badge';
                if (dokument.status === 'Weryfikacja UOPZ') badge.classList.add('bg-warning', 'text-dark');
                else if (dokument.status === 'Zatwierdzone') badge.classList.add('bg-success');
                else badge.classList.add('bg-secondary');
                
                // Show actions only if Weryfikacja UOPZ
                const akcjeContainer = document.getElementById('uopz-akcje-container');
                if (dokument.status === 'Weryfikacja UOPZ') {
                    akcjeContainer.classList.remove('d-none');
                } else {
                    akcjeContainer.classList.add('d-none');
                }
                
                // Wpisy
                const tbody = document.getElementById('dziennikBody');
                tbody.innerHTML = '';
                
                if (data.wpisy && data.wpisy.length > 0) {
                    data.wpisy.forEach((wpis, index) => {
                        appendRow(tbody, index + 1, wpis);
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted fst-italic">Brak wpisów do wyświetlenia.</td></tr>';
                }
            })
            .catch(err => console.error(err));
    };

    window.loadDziennik();
});

function appendRow(tbody, dayNumber, wpis) {
    const tr = document.createElement('tr');
    
    let decyzjaHtml = '';
    if (wpis.potwierdzony_zopz === 1) {
        decyzjaHtml = '<span class="text-success fw-bold"><i class="bi bi-check-circle"></i> Potwierdzone</span>';
    } else if (wpis.potwierdzony_zopz === -1) {
        decyzjaHtml = `<span class="text-danger fw-bold"><i class="bi bi-x-circle"></i> Odrzucone</span>
                       <div class="mt-1 small text-danger text-start"><i class="bi bi-chat-left-text me-1"></i>${wpis.komentarz_zopz}</div>`;
    } else {
        decyzjaHtml = '<span class="text-muted small">Oczekuje</span>';
    }
    
    tr.innerHTML = `
        <td class="text-center fw-bold">${dayNumber}</td>
        <td>
            <div class="form-control form-control-sm" style="background-color: #f8f9fa; cursor: not-allowed;">${wpis.data_wpisu}</div>
        </td>
        <td>
            <div class="form-control form-control-sm" style="background-color: #f8f9fa; cursor: not-allowed; min-height: 50px; white-space: pre-wrap; word-break: break-word; overflow-wrap: break-word;">${wpis.opis_prac}</div>
        </td>
        <td>
            <div class="form-control form-control-sm" style="background-color: #f8f9fa; cursor: not-allowed;">${wpis.nr_efektu || '-'}</div>
        </td>
        <td class="text-center align-middle">
            ${decyzjaHtml}
        </td>
    `;
    tbody.appendChild(tr);
}

window.zatwierdzDziennik = function() {
    if (!confirm('Czy na pewno chcesz zatwierdzić ostatecznie Dziennik Praktyk? Po tej akcji dokument otrzyma status "Zatwierdzone".')) {
        return;
    }
    
    fetch(`/api/uopz/dziennik/${STUDENT_ID}/zatwierdz`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById('alerts-container').innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                loadDziennik();
                window.scrollTo(0, 0);
            } else {
                alert(data.error || 'Błąd');
            }
        });
};

window.cofnijDziennik = function() {
    const komentarz = document.getElementById('komentarz-uopz').value.trim();
    if (!komentarz) {
        alert('Podaj uwagi (powód cofnięcia) przed odrzuceniem dokumentu.');
        return;
    }
    
    if (!confirm('Czy na pewno chcesz zwrócić Dziennik do studenta (z ponowną weryfikacją przez ZOPZ)?')) {
        return;
    }
    
    fetch(`/api/uopz/dziennik/${STUDENT_ID}/odrzuc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ komentarz: komentarz })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            document.getElementById('alerts-container').innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
            loadDziennik();
            window.scrollTo(0, 0);
        } else {
            alert(data.error || 'Błąd');
        }
    });
};
