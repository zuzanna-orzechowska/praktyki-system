document.addEventListener('DOMContentLoaded', function () {
    const pathParts = window.location.pathname.split('/');
    const studentId = pathParts[pathParts.length - 1];

    fetch(`/api/zopz/teczka/${studentId}`)
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
                window.location.href = '/zopz/dashboard';
                return;
            }

            document.getElementById('student-name').textContent = `Teczka Studenta: ${data.uzytkownik.imie} ${data.uzytkownik.nazwisko} (${data.student.nr_albumu})`;
            document.getElementById('student-info').textContent = `${data.student.nr_albumu} / ${data.student.kierunek}`;
            document.getElementById('miejsce-praktyki').textContent = data.zaklad_nazwa || 'Brak przypisanego zakładu';
            
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
            const mappedStatus = statusMap[data.praktyka.status] || { text: data.praktyka.status, color: 'secondary' };
            const statusBadge = document.getElementById('praktyka-status');
            statusBadge.textContent = mappedStatus.text;
            statusBadge.className = `badge bg-${mappedStatus.color}`;

            if (data.porozumienie && data.porozumienie.id) {
                document.getElementById('btn-zal1').href = `/zopz/porozumienie/${data.porozumienie.id}`;
                if (data.porozumienie.status === 'OczekujeZOPZ') {
                    document.getElementById('badge-zal1').style.display = 'inline-block';
                }
            } else {
                document.getElementById('btn-zal1').classList.add('disabled');
                document.getElementById('btn-zal1').textContent = 'Brak porozumienia';
            }

            document.getElementById('btn-zal2a').href = `/zopz/zal2a_harmonogram/${studentId}`;

            const btnZal3 = document.getElementById('btn-zal3');
            if (btnZal3) {
                btnZal3.href = `/zopz/zal3_karta/${studentId}`;
            }
        })
        .catch(err => console.error(err));
});
