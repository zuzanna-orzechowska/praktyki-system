document.addEventListener('DOMContentLoaded', function() {
    const pathParts = window.location.pathname.split('/');
    const studentId = pathParts[pathParts.length - 1];

    fetch(`/api/uopz/teczka/${studentId}`)
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

            document.getElementById('student-name').textContent = `Teczka Studenta: ${data.uzytkownik.imie} ${data.uzytkownik.nazwisko}`;
            document.getElementById('student-info').textContent = `${data.student.nr_albumu} / ${data.student.kierunek}`;
            // we don't return zaklad directly via teczka right now but we can say 'Oczekuje'
            document.getElementById('miejsce-praktyki').textContent = 'Załadowano z API';
            document.getElementById('praktyka-status').textContent = data.praktyka.status;

            // Set hrefs
            document.getElementById('btn-zal2a').href = `/uopz/zal2a_harmonogram/${studentId}`;
            document.getElementById('btn-zal3').href = `/uopz/zal3_karta/${studentId}`;
            document.getElementById('btn-zal4').href = `/uopz/zal4_efekty/${studentId}`;
            document.getElementById('btn-zal7').href = `/uopz/zal7_sprawozdanie/${studentId}`;
            document.getElementById('btn-zal7a').href = `/uopz/zal7a_sprawozdanie/${studentId}`;

            // Optional: badges
            const dokumenty = data.dokumenty || {};
            if (dokumenty['ZAL7'] && dokumenty['ZAL7'].status === 'Submitted') {
                document.getElementById('badge-zal7').style.display = 'inline-block';
            }
        })
        .catch(err => console.error(err));
});
