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
            const safeNazwisko = (student.nazwisko || '').split('(')[0].trim();
            document.getElementById('student-info').textContent = `${student.imie} ${safeNazwisko}`;
            document.getElementById('student-album').textContent = student.nr_albumu;
            
            if (document.getElementById('student-kierunek1')) document.getElementById('student-kierunek1').textContent = student.kierunek || 'Informatyka';
            if (document.getElementById('student-kierunek2')) document.getElementById('student-kierunek2').textContent = student.kierunek || 'Informatyka';
            
            if (document.getElementById('data-wypelnienia')) {
                const dzisiaj = new Date().toLocaleDateString('pl-PL');
                document.getElementById('data-wypelnienia').textContent = dzisiaj;
            }
            
            const checkbox = document.getElementById('zloz_podpis');
            if (checkbox) {
                checkbox.addEventListener('change', function() {
                    if (this.checked) {
                        const dzisiajFormat = new Date().toLocaleDateString('pl-PL');
                        document.getElementById('podpis-student').innerHTML = `<span style="font-family: sans-serif; color: #000; font-size: 14px; margin-right: 10px;">${dzisiajFormat}</span>${student.imie} ${safeNazwisko}`;
                    } else {
                        document.getElementById('podpis-student').innerHTML = '';
                    }
                });
            }
            
            const updateCounters = function() {
                const uza = document.getElementById('uzasadnienie');
                const uzaCounter = document.getElementById('uzasadnienie_counter');
                if (uza && uzaCounter) {
                    const len = uza.value.trim().length;
                    uzaCounter.textContent = `Znaków: ${len} / min. 400`;
                    uzaCounter.className = len >= 400 ? 'text-success small fw-bold' : 'text-danger small fw-bold';
                }
                
                const zak = document.getElementById('zakres_obowiazkow');
                const zakCounter = document.getElementById('zakres_obowiazkow_counter');
                if (zak && zakCounter) {
                    const len = zak.value.trim().length;
                    zakCounter.textContent = `Znaków: ${len} / min. 200`;
                    zakCounter.className = len >= 200 ? 'text-success small fw-bold' : 'text-danger small fw-bold';
                }
            };
            
            const uzaInput = document.getElementById('uzasadnienie');
            if (uzaInput) uzaInput.addEventListener('input', updateCounters);
            
            const zakInput = document.getElementById('zakres_obowiazkow');
            if (zakInput) zakInput.addEventListener('input', updateCounters);
            
            // Populate form fields
            if (wniosek) {
                setValue('data_od', wniosek.okres_zatrudnienia_od);
                setValue('data_do', wniosek.okres_zatrudnienia_do);
                setValue('stanowisko', wniosek.stanowisko);
                setValue('zakres_obowiazkow', wniosek.zakres_obowiazkow);
                setValue('uzasadnienie', wniosek.uzasadnienie);
                
                if (wniosek.zalaczniki_paths) {
                    let zalaczniki = [];
                    try {
                        zalaczniki = JSON.parse(wniosek.zalaczniki_paths);
                    } catch (e) {
                        if (wniosek.zalaczniki_paths.length > 5) {
                            zalaczniki = [{path: wniosek.zalaczniki_paths, opis: 'Załącznik'}];
                        }
                    }
                    
                    const skanContainer = document.getElementById('skan-container');
                    if (zalaczniki.length > 0) {
                        skanContainer.innerHTML = '';
                        zalaczniki.forEach((zal, idx) => {
                            const filename = zal.path.split('/').pop();
                            skanContainer.innerHTML += `
                                <div class="alert alert-secondary d-flex justify-content-between align-items-center p-2 mb-2">
                                    <div>
                                        <i class="bi bi-file-earmark-check text-success"></i> 
                                        <strong>${zal.opis || 'Brak opisu'}</strong> <small class="text-muted">(${filename})</small>
                                    </div>
                                    ${dokument && dokument.status !== 'Draft' ? '' : `<button type="button" class="btn btn-sm btn-outline-danger" onclick="usunZalacznik(${idx})"><i class="bi bi-trash"></i></button>`}
                                </div>
                            `;
                        });
                    }
                }
            }
            
            setValue('specjalnosc', student.specjalnosc);
            updateCounters();
            
            // Handle statuses and readonly fields
            if (dokument && dokument.status !== 'Draft' && dokument.status !== 'Rejected') {
                const inputs = document.querySelectorAll('input, textarea');
                inputs.forEach(input => input.setAttribute('readonly', 'readonly'));
                
                const uploadContainer = document.getElementById('upload-new-container');
                if(uploadContainer) uploadContainer.style.display = 'none';
                
                if (checkbox) {
                    checkbox.checked = true;
                    checkbox.disabled = true;
                    const dzisiajFormat = new Date(dokument.data_utworzenia || new Date()).toLocaleDateString('pl-PL');
                    document.getElementById('podpis-student').innerHTML = `<span style="font-family: sans-serif; color: #000; font-size: 14px; margin-right: 10px;">${dzisiajFormat}</span>${student.imie} ${safeNazwisko}`;
                }
                
                const actionBtns = document.getElementById('action-buttons');
                if(actionBtns) actionBtns.style.display = 'none';
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
    
    if (akcjaValue === 'zapisz' || akcjaValue === 'wyslij') {
        const uza = document.getElementById('uzasadnienie').value;
        const zak = document.getElementById('zakres_obowiazkow').value;
        if (uza.trim().length < 400) {
            alert('Uzasadnienie jest zbyt krótkie (min. 400 znaków). Aktualnie: ' + uza.trim().length);
            return;
        }
        if (zak.trim().length < 200) {
            alert('Zakres obowiązków jest zbyt krótki (min. 200 znaków). Aktualnie: ' + zak.trim().length);
            return;
        }
    }
    
    if (akcjaValue === 'wyslij') {
        if (!form.reportValidity()) {
            return;
        }
        const checkbox = document.getElementById('zloz_podpis');
        if (checkbox && !checkbox.checked) {
            alert('Musisz złożyć podpis cyfrowy pod dokumentem przed jego formalnym wysłaniem.');
            return;
        }
        
        const skanContainer = document.getElementById('skan-container');
        const hasUploads = skanContainer.querySelectorAll('.alert').length > 0;
        
        if (!hasUploads) {
            alert('Musisz dodać wymagane załączniki z odpowiednimi opisami by móc wysłać wniosek.');
            return;
        }
    }
    
    const buttons = document.querySelectorAll('#action-buttons button');
    buttons.forEach(btn => btn.disabled = true);
    
    const formData = new FormData(form);
    formData.append('akcja', akcjaValue);
    
    fetch('/api/student/zal4b_wniosek', {
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
            alertContainer.innerHTML = `<div class="alert alert-danger">${data.message || data.error}</div>`;
            buttons.forEach(btn => btn.disabled = false);
        }
        window.scrollTo(0, 0);
    })
    .catch(err => {
        console.error(err);
        buttons.forEach(btn => btn.disabled = false);
    });
}

function dodajZalacznik() {
    const plikInput = document.getElementById('nowy_plik');
    const opisInput = document.getElementById('nowy_plik_opis');
    if (!plikInput.files.length) {
        alert('Najpierw wybierz plik.');
        return;
    }
    
    const formData = new FormData();
    formData.append('akcja', 'dodaj_zalacznik');
    formData.append('nowy_plik', plikInput.files[0]);
    formData.append('opis', opisInput.value.trim());
    
    fetch('/api/student/zal4b_wniosek', { method: 'POST', body: formData })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert(data.error || data.message);
        }
    });
}

function usunZalacznik(idx) {
    if (!confirm('Na pewno usunąć ten załącznik?')) return;
    const formData = new FormData();
    formData.append('akcja', 'usun_zalacznik');
    formData.append('index', idx);
    fetch('/api/student/zal4b_wniosek', { method: 'POST', body: formData })
    .then(res => res.json())
    .then(data => {
        if (data.success) window.location.reload();
    });
}

document.getElementById('zal4b-form').addEventListener('submit', function(e) {
    e.preventDefault();
});
