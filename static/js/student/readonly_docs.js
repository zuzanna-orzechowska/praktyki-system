document.addEventListener('DOMContentLoaded', function () {
    const apiPath = window.location.pathname.replace('/student/', '/api/student/');

    fetch(apiPath)
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
            const praktyka = data.praktyka;
            const dokument = data.dokument;

            const safeNazwisko = (student.nazwisko || '').split('(')[0].trim();
            populateIfExist('student-info', `${student.imie} ${safeNazwisko}`);
            populateIfExist('student-album', student.nr_albumu);
            populateIfExist('student-kierunek', student.kierunek);

            if (praktyka) {
                populateIfExist('praktyka-start', praktyka.data_start);
                populateIfExist('praktyka-end', praktyka.data_end);
            }

            document.querySelectorAll('[data-bind]').forEach(el => {
                const path = el.getAttribute('data-bind').split('.');
                let val = data;
                for (let p of path) {
                    if (val === null || val === undefined) break;
                    val = val[p];
                }
                if (val !== undefined && val !== null) {
                    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                        el.value = val;
                    } else {
                        el.textContent = val;
                    }
                }
            });
        })
        .catch(err => console.error(err));
});

function populateIfExist(id, value) {
    const el = document.getElementById(id);
    if (el && value) {
        if (el.tagName === 'INPUT') el.value = value;
        else el.textContent = value;
    }
}
