document.addEventListener('DOMContentLoaded', function() {
    const pathParts = window.location.pathname.split('/');
    const studentId = pathParts[pathParts.length - 1];
    document.getElementById('back-link').href = `/uopz/teczka/${studentId}`;

    function loadData() {
        fetch(`/api/uopz/zal3_karta/${studentId}`)
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

                if (data.praktyka.status === 'SKIEROWANIE_WYDANE') {
                    document.getElementById('btn-wydaj').style.display = 'none';
                    document.getElementById('skierowanie-info').style.display = 'block';
                } else {
                    document.getElementById('btn-wydaj').style.display = 'inline-block';
                    document.getElementById('skierowanie-info').style.display = 'none';
                }

                if (data.protokol) {
                    if (data.protokol.ocena_u) document.getElementById('ocena-u').value = data.protokol.ocena_u;
                    if (data.protokol.ocena_s) document.getElementById('ocena-s').value = data.protokol.ocena_s;
                }
            })
            .catch(err => console.error(err));
    }

    loadData();

    document.getElementById('btn-wydaj').addEventListener('click', function() {
        fetch(`/api/uopz/zal3_karta/${studentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ akcja: 'wydaj_skierowanie' })
        })
        .then(response => response.json())
        .then(data => {
            const alerts = document.getElementById('alerts-container');
            if (data.success) {
                alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                loadData();
            } else {
                alerts.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            }
            window.scrollTo(0,0);
        })
        .catch(err => console.error(err));
    });

    document.getElementById('form-oceny').addEventListener('submit', function(e) {
        e.preventDefault();
        const ocenaU = document.getElementById('ocena-u').value;
        const ocenaS = document.getElementById('ocena-s').value;

        fetch(`/api/uopz/zal3_karta/${studentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ akcja: 'zapisz_ocene', ocena_u: ocenaU, ocena_s: ocenaS })
        })
        .then(response => response.json())
        .then(data => {
            const alerts = document.getElementById('alerts-container');
            if (data.success) {
                alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            } else {
                alerts.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            }
            window.scrollTo(0,0);
        })
        .catch(err => console.error(err));
    });
});
