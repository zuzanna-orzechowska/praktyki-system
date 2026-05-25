document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/student/zal4b_wniosek')
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
            const wniosek = data.wniosek;
            const dokument = data.dokument;
            
            // Populate text elements
            document.getElementById('student-info').textContent = `${student.imie} ${student.nazwisko}`;
            document.getElementById('student-album').textContent = student.nr_albumu;
            
            // Populate form fields
            if (wniosek) {
                setValue('data_od', wniosek.okres_zatrudnienia_od);
                setValue('data_do', wniosek.okres_zatrudnienia_do);
                setValue('stanowisko', wniosek.stanowisko);
                setValue('zakres_obowiazkow', wniosek.zakres_obowiazkow);
                setValue('uzasadnienie', wniosek.uzasadnienie);
            }
            
            setValue('specjalnosc', student.specjalnosc);
            
            // Handle statuses and readonly fields
            if (dokument && dokument.status !== 'Draft' && dokument.status !== 'Rejected') {
                const inputs = document.querySelectorAll('input, textarea');
                inputs.forEach(input => input.setAttribute('readonly', 'readonly'));
                document.getElementById('action-buttons').style.display = 'none';
            }
        })
        .catch(err => console.error(err));
});

function setValue(name, value) {
    const el = document.querySelector(`[name="${name}"]`);
    if (el && value !== null && value !== undefined) {
        el.value = value;
    }
}

function submitForm(akcjaValue) {
    const form = document.getElementById('zal4b-form');
    
    const data = {
        data_od: form.querySelector('[name="data_od"]').value,
        data_do: form.querySelector('[name="data_do"]').value,
        stanowisko: form.querySelector('[name="stanowisko"]').value,
        zakres_obowiazkow: form.querySelector('[name="zakres_obowiazkow"]').value,
        uzasadnienie: form.querySelector('[name="uzasadnienie"]').value,
        specjalnosc: form.querySelector('[name="specjalnosc"]').value,
        akcja: akcjaValue
    };
    
    fetch('/api/student/zal4b_wniosek', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        const alertContainer = document.getElementById('alerts-container');
        if (data.success) {
            alertContainer.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            setTimeout(() => { window.location.reload(); }, 1500);
        } else {
            alertContainer.innerHTML = `<div class="alert alert-danger">${data.message || data.error}</div>`;
        }
        window.scrollTo(0, 0);
    })
    .catch(err => console.error(err));
}

document.getElementById('zal4b-form').addEventListener('submit', function(e) {
    e.preventDefault();
});
