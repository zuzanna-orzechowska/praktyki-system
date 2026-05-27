document.addEventListener('DOMContentLoaded', function () {
    const pathParts = window.location.pathname.split('/');
    const docId = pathParts[pathParts.length - 1];

    fetch(`/api/dziekanat/weryfikuj_zal9/${docId}`)
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

            const student = data.student;
            const uzytkownik = data.uzytkownik;
            const praktyka = data.praktyka;
            const oswiadczenie = data.oswiadczenie;
            const dokument = data.dokument;

            document.getElementById('status-badge').textContent = dokument.status;

            if (uzytkownik) {
                document.getElementById('student-info').textContent = `${uzytkownik.imie} ${uzytkownik.nazwisko}`;
            }
            if (student) {
                document.getElementById('student-album').textContent = student.nr_albumu;
                document.getElementById('student-kierunek').textContent = student.kierunek;
            }

            if (oswiadczenie) {
                const keys = ['miejscowosc', 'data_oswiadczenia', 'nazwa_instytucji',
                    'opiekun_imie', 'opiekun_nazwisko', 'opiekun_stanowisko',
                    'opiekun_telefon', 'opiekun_email',
                    'osoba_upowazniona_imie', 'osoba_upowazniona_nazwisko',
                    'osoba_upowazniona_stanowisko', 'rok_studiow'];

                keys.forEach(k => {
                    const el = document.getElementById(`val-${k}`);
                    if (el) el.textContent = oswiadczenie[k] || '';
                });

                if (oswiadczenie.skan_path) {
                    const filename = oswiadczenie.skan_path.split('/').pop();
                    document.getElementById('skan-container').innerHTML = `
                        <div class="alert alert-success py-2 mb-0">
                            <i class="bi bi-check-circle-fill me-2"></i>
                            <a href="/static/${oswiadczenie.skan_path}" target="_blank" class="alert-link">
                                <i class="bi bi-file-earmark-text"></i> ${filename}
                            </a>
                        </div>
                    `;
                }
            }

            if (praktyka) {
                document.getElementById('val-data_start').textContent = praktyka.data_start || '';
                document.getElementById('val-data_end').textContent = praktyka.data_end || '';
            }

            if (dokument && dokument.status === 'Submitted') {
                document.getElementById('action-panel').style.display = 'block';
            } else if (dokument && ['Approved', 'AwaitingAccount', 'AccountCreated'].includes(dokument.status)) {
                document.getElementById('approved-panel').style.display = 'block';

            }

        })
        .catch(err => console.error(err));
});

function submitDecision(action) {
    const pathParts = window.location.pathname.split('/');
    const docId = pathParts[pathParts.length - 1];
    const komentarz = document.getElementById('komentarz_dziekanatu') ? document.getElementById('komentarz_dziekanatu').value : '';

    if (action === 'odrzuc' && !komentarz) {
        if (!confirm('Czy na pewno chcesz odrzucić bez komentarza?')) return;
    }

    if (action === 'zatwierdz') {
        if (!confirm('Zatwierdzić oświadczenie i przekazać dane do działu IT w celu weryfikacji/założenia konta ZOPZ?')) return;
    }

    fetch(`/api/dziekanat/weryfikuj_zal9/${docId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ akcja: action, komentarz_dziekanatu: komentarz })
    })
        .then(response => response.json())
        .then(data => {
            const alerts = document.getElementById('alerts-container');
            if (data.success) {
                alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                setTimeout(() => {
                    window.location.href = '/dziekanat/zal9';
                }, 1500);
            } else {
                alerts.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            }
            window.scrollTo(0, 0);
        })
        .catch(err => console.error(err));
}


