document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    
    // Fetch data and populate form
    fetch('/api/student/zal9_oswiadczenie')
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
            const oswiadczenie = data.oswiadczenie;
            const dokument = data.dokument;
            
            // Populate text elements
            document.getElementById('student-info').textContent = `${student.imie} ${student.nazwisko}`;
            document.getElementById('student-album').textContent = student.nr_albumu;
            
            // Populate form fields
            if (oswiadczenie) {
                setValue('miejscowosc', oswiadczenie.miejscowosc);
                setValue('data_oswiadczenia', oswiadczenie.data_oswiadczenia);
                setValue('nazwa_instytucji', oswiadczenie.nazwa_instytucji);
                setValue('opiekun_imie', oswiadczenie.opiekun_imie);
                setValue('opiekun_nazwisko', oswiadczenie.opiekun_nazwisko);
                setValue('opiekun_stanowisko', oswiadczenie.opiekun_stanowisko);
                setValue('opiekun_telefon', oswiadczenie.opiekun_telefon);
                setValue('opiekun_email', oswiadczenie.opiekun_email);
                setValue('osoba_upowazniona_imie', oswiadczenie.osoba_upowazniona_imie);
                setValue('osoba_upowazniona_nazwisko', oswiadczenie.osoba_upowazniona_nazwisko);
                setValue('osoba_upowazniona_stanowisko', oswiadczenie.osoba_upowazniona_stanowisko);
                
                setValue('rok_studiow', oswiadczenie.rok_studiow || student.rok_studiow);
                setValue('kierunek', oswiadczenie.kierunek || student.kierunek);
                
                if (oswiadczenie.skan_path) {
                    const skanContainer = document.getElementById('skan-container');
                    skanContainer.innerHTML = `
                        <div class="alert alert-success d-flex justify-content-between align-items-center p-2 mb-2">
                            <span><i class="bi bi-file-earmark-check"></i> Wgrano plik: ${oswiadczenie.skan_path.split('_').pop()}</span>
                            <button type="button" class="btn btn-sm btn-outline-danger" onclick="submitForm('usun_plik')">Usuń plik</button>
                        </div>
                    `;
                }
            } else {
                setValue('data_oswiadczenia', data.dzisiaj);
                setValue('rok_studiow', student.rok_studiow);
                setValue('kierunek', student.kierunek);
            }
            
            if (praktyka) {
                setValue('data_start', praktyka.data_start);
                setValue('data_end', praktyka.data_end);
            }
            
            // Handle statuses and readonly fields
            if (dokument && dokument.status !== 'Draft' && dokument.status !== 'Rejected') {
                const inputs = form.querySelectorAll('input, select');
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
    const form = document.querySelector('form');
    const formData = new FormData(form);
    formData.append('akcja', akcjaValue);
    
    fetch('/api/student/zal9_oswiadczenie', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const alertContainer = document.getElementById('alerts-container');
        if (data.success) {
            alertContainer.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            setTimeout(() => { window.location.reload(); }, 1500);
        } else {
            alertContainer.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
        }
        window.scrollTo(0, 0);
    })
    .catch(err => console.error(err));
}

document.querySelector('form').addEventListener('submit', function(e) {
    e.preventDefault();
});
