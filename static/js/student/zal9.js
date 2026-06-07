document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');

    fetch('/api/student/zal9_oswiadczenie?t=' + new Date().getTime(), { cache: 'no-store' })
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
            const safeNazwisko = (student.nazwisko || '').split('(')[0].trim();
            document.getElementById('student-info').textContent = `${student.imie} ${safeNazwisko}`;
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
                const fieldset = document.getElementById('form-fieldset');
                if (fieldset) fieldset.setAttribute('disabled', 'disabled');

                const actionBtns = document.getElementById('action-buttons');
                if (actionBtns) {
                    actionBtns.classList.remove('d-flex');
                    actionBtns.classList.add('d-none');
                }

                const skanInput = document.getElementById('skan_dokumentu');
                if (skanInput) skanInput.style.display = 'none';
                const labels = form.querySelectorAll('label[for="skan_dokumentu"]');
                labels.forEach(l => l.style.display = 'none');

                const deleteBtns = document.querySelectorAll('#skan-container button');
                deleteBtns.forEach(b => b.style.display = 'none');

                // Add explicit status message
                let statusText = 'Oczekuje na weryfikację przez Dziekanat';
                let alertType = 'alert-info';

                if (dokument.status === 'Approved') {
                    statusText = 'Zaakceptowane przez Dziekanat';
                    alertType = 'alert-success';
                }

                const existingAlert = document.getElementById('status-alert-banner');
                if (!existingAlert) {
                    const statusBanner = document.createElement('div');
                    statusBanner.id = 'status-alert-banner';
                    statusBanner.className = `alert ${alertType} fw-bold mb-4 shadow-sm`;
                    
                    if (dokument.status === 'Approved') {
                        statusBanner.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i> ${statusText}.`;
                    } else {
                        statusBanner.innerHTML = `<i class="bi bi-info-circle-fill me-2"></i> ${statusText}. Pola formularza zostały zablokowane.`;
                    }
                    
                    form.insertBefore(statusBanner, form.firstChild);
                }
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

    if (akcjaValue === 'zapisz' || akcjaValue === 'wyslij') {
        if (!form.reportValidity()) {
            return;
        }

        const skanContainer = document.getElementById('skan-container');
        const fileInput = document.getElementById('skan_dokumentu');
        const isUploaded = skanContainer.innerHTML.includes('Wgrano plik');
        const isSelected = fileInput && fileInput.files && fileInput.files.length > 0;

        if (!isUploaded && !isSelected) {
            alert('Wgranie skanu dokumentu jest wymagane. Proszę wybrać plik przed zapisaniem.');
            return;
        }
    }

    const buttons = document.querySelectorAll('#action-buttons button');
    buttons.forEach(btn => btn.disabled = true);

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

document.querySelector('form').addEventListener('submit', function (e) {
    e.preventDefault();
});
