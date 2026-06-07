document.addEventListener('DOMContentLoaded', function () {
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
            document.getElementById('miejsce-praktyki').textContent = data.zaklad_nazwa || 'Załadowano z API';
            document.getElementById('praktyka-status').textContent = data.praktyka.status;

            document.getElementById('btn-zal2a').href = `/uopz/zal2a_harmonogram/${studentId}`;
            document.getElementById('btn-zal3').href = `/uopz/zal3_karta/${studentId}`;
            document.getElementById('btn-zal4').href = `/uopz/zal4_efekty/${studentId}`;
            document.getElementById('btn-zal7').href = `/uopz/zal7_sprawozdanie/${studentId}`;
            document.getElementById('btn-zal7a').href = `/uopz/zal7a_sprawozdanie/${studentId}`;
            
            if (data.dokumenty && data.dokumenty['ZAL4B']) {
                document.getElementById('btn-zal8').href = `/uopz/zal8a_protokol/${studentId}`;
                document.getElementById('btn-zal8').textContent = 'Wypełnij Protokół (Zał. 8a)';
            } else {
                document.getElementById('btn-zal8').href = `/uopz/zal8_protokol/${studentId}`;
            }

            const btnZal8a = document.getElementById('btn-zal8a');
            if (btnZal8a) {
                btnZal8a.href = `/uopz/zal8a_protokol/${studentId}`;
            }
            
            const btnZal6 = document.getElementById('btn-zal6');
            if (btnZal6) {
                btnZal6.href = `/uopz/dziennik/${studentId}`;
                btnZal6.classList.remove('disabled');
                btnZal6.textContent = 'Podgląd Dziennika';
            }

            const dokumenty = data.dokumenty || {};
            if (dokumenty['ZAL7'] && dokumenty['ZAL7'].status === 'Submitted') {
                document.getElementById('badge-zal7').style.display = 'inline-block';
            }
            if (dokumenty['ZAL6'] && dokumenty['ZAL6'].status === 'Weryfikacja UOPZ') {
                const badgeZal6 = document.getElementById('badge-zal6');
                if (badgeZal6) badgeZal6.style.display = 'inline-block';
            }

            // Hiding logic based on path
            const isProfessionalPath = (data.praktyka.status === 'SCIEZKA_PRACA' || data.praktyka.status === 'ZAL4B_ZATWIERDZONE' || (data.praktyka.status === 'ZALICZONA' && dokumenty['ZAL4B']));
            
            if (isProfessionalPath) {
                document.getElementById('card-zal2a').style.display = 'none';
                document.getElementById('card-zal3').style.display = 'none';
                document.getElementById('card-zal4').style.display = 'none';
                document.getElementById('card-zal6').style.display = 'none';
                document.getElementById('card-zal7').style.display = 'none';
                document.getElementById('card-zal8').style.display = 'none';
            } else {
                document.getElementById('card-zal7a').style.display = 'none';
                document.getElementById('card-zal8a').style.display = 'none';
            }
        })
        .catch(err => console.error(err));
});
