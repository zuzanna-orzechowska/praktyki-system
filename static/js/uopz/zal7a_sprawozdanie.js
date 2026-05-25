document.addEventListener('DOMContentLoaded', function() {
    const pathParts = window.location.pathname.split('/');
    const studentId = pathParts[pathParts.length - 1];
    document.getElementById('back-link').href = `/uopz/teczka/${studentId}`;

    function loadData() {
        fetch(`/api/uopz/zal7a_sprawozdanie/${studentId}`)
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
                    window.location.href = '/uopz/dashboard';
                    return;
                }

                document.getElementById('student-name').textContent = `${data.student.nr_albumu} - ${data.uzytkownik.imie} ${data.uzytkownik.nazwisko}`;

                if (data.sprawozdanie) {
                    document.getElementById('charakterystyka').textContent = data.sprawozdanie.charakterystyka_zakladu || 'Brak danych';
                    document.getElementById('przebieg').textContent = data.sprawozdanie.przebieg_praktyki || 'Brak danych';
                    document.getElementById('wnioski').textContent = data.sprawozdanie.wnioski || 'Brak danych';
                } else {
                    document.getElementById('charakterystyka').innerHTML = '<i class="text-muted">Sprawozdanie nie zostało jeszcze wygenerowane przez studenta.</i>';
                    document.getElementById('przebieg').innerHTML = '';
                    document.getElementById('wnioski').innerHTML = '';
                    document.getElementById('btn-zatwierdz').disabled = true;
                    document.getElementById('btn-odrzuc').disabled = true;
                }

                if (data.dokument) {
                    document.getElementById('uwagi_opiekuna').value = data.dokument.uwagi_opiekuna || '';
                    const alertBox = document.getElementById('status-alert');
                    alertBox.style.display = 'block';
                    if (data.dokument.status === 'Approved') {
                        alertBox.className = 'alert alert-success mt-3';
                        alertBox.innerHTML = '<i class="bi bi-check-circle"></i> Sprawozdanie zostało zatwierdzone.';
                    } else if (data.dokument.status === 'Rejected') {
                        alertBox.className = 'alert alert-danger mt-3';
                        alertBox.innerHTML = '<i class="bi bi-x-circle"></i> Sprawozdanie zostało odrzucone (odesłane do poprawy).';
                    } else if (data.dokument.status === 'Submitted') {
                        alertBox.className = 'alert alert-warning mt-3';
                        alertBox.innerHTML = '<i class="bi bi-info-circle"></i> Sprawozdanie oczekuje na Twoją decyzję.';
                    } else {
                        alertBox.style.display = 'none';
                    }
                }
            })
            .catch(err => console.error(err));
    }

    loadData();

    function sendDecision(akcja) {
        const uwagi = document.getElementById('uwagi_opiekuna').value;
        fetch(`/api/uopz/zal7a_sprawozdanie/${studentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ akcja: akcja, uwagi_opiekuna: uwagi })
        })
        .then(response => response.json())
        .then(data => {
            const alerts = document.getElementById('alerts-container');
            if (data.success) {
                alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                loadData();
            } else {
                alerts.innerHTML = `<div class="alert alert-danger">${data.message || 'Błąd zapisu'}</div>`;
            }
            window.scrollTo(0,0);
        })
        .catch(err => console.error(err));
    }

    document.getElementById('btn-zatwierdz').addEventListener('click', () => sendDecision('zatwierdz_i_podpisz'));
    document.getElementById('btn-odrzuc').addEventListener('click', () => sendDecision('odrzuc'));
});
