let hasUnsavedChanges = false;
let isSubmitting = false;
let efektyListaGlobal = [];
let praktykaStartGlobal = '';
let maxDateGlobal = '';

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('dziennik-form');
    
    form.addEventListener('change', function() {
        hasUnsavedChanges = true;
    });
    
    form.addEventListener('input', function() {
        hasUnsavedChanges = true;
    });

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        isSubmitting = true;
        saveDziennik();
    });

    window.addEventListener('beforeunload', function (e) {
        if (hasUnsavedChanges && !isSubmitting) {
            const msg = 'Masz niezapisane zmiany. Czy na pewno chcesz opuścić tę stronę?';
            e.returnValue = msg;
            return msg;
        }
    });

    // Fetch data
    fetch('/api/student/dziennik')
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
            
            const uzytkownik = data.uzytkownik;
            const praktyka = data.praktyka;
            efektyListaGlobal = data.efekty_lista;
            praktykaStartGlobal = praktyka.data_start;
            maxDateGlobal = data.max_date;
            
            document.getElementById('praktyka-zaklad').textContent = praktyka.zaklad_nazwa || 'Brak przypisanej firmy';
            document.getElementById('praktyka-start').textContent = praktyka.data_start || '';
            document.getElementById('praktyka-end').textContent = praktyka.data_end || '';
            
            // Render efekty list
            const efektyUl = document.getElementById('efekty-list');
            efektyUl.innerHTML = '';
            efektyListaGlobal.forEach(efekt => {
                const li = document.createElement('li');
                li.className = 'mb-1';
                li.innerHTML = `<strong>${efekt.kod}</strong>: ${efekt.opis}`;
                efektyUl.appendChild(li);
            });
            
            // Render table
            const tbody = document.getElementById('dziennikBody');
            tbody.innerHTML = '';
            
            if (data.wpisy && data.wpisy.length > 0) {
                data.wpisy.forEach((wpis, index) => {
                    appendRow(tbody, index + 1, wpis);
                });
            } else {
                appendRow(tbody, 1, null);
            }
            updateDeleteButtons();
        })
        .catch(err => console.error(err));
});

function appendRow(tbody, dayNumber, wpis) {
    const tr = document.createElement('tr');
    
    const wid = wpis ? wpis.id : '';
    const dataWpisu = wpis ? wpis.data_wpisu : '';
    const opis = wpis ? wpis.opis_prac : '';
    const nrEfektu = wpis ? wpis.nr_efektu : '';
    const potwierdzony = wpis ? wpis.potwierdzony_zopz : false;
    
    const readonlyAttr = potwierdzony ? 'readonly' : '';
    const disabledAttr = potwierdzony ? 'style="pointer-events: none; opacity: 0.8;" tabindex="-1"' : '';
    const btnDisabledAttr = potwierdzony ? 'disabled data-approved="true" title="Nie można usunąć zatwierdzonego wpisu"' : '';
    
    const statusHtml = potwierdzony 
        ? '<span class="text-success"><i class="bi bi-check-circle"></i> Potwierdzone</span>' 
        : '<small>Oczekuje...</small>';
        
    let efektyOptions = '<option value="" disabled ' + (!nrEfektu ? 'selected' : '') + '>Wybierz...</option>';
    efektyListaGlobal.forEach(e => {
        efektyOptions += `<option value="${e.kod}" ${nrEfektu === e.kod ? 'selected' : ''}>${e.kod}</option>`;
    });
    
    tr.innerHTML = `
        <td class="text-center fw-bold day-number">${dayNumber}</td>
        <td>
            <input type="hidden" name="wpis_id[]" value="${wid}">
            <input type="date" name="data[]" class="form-control form-control-sm"
                value="${dataWpisu}" min="${praktykaStartGlobal}" max="${maxDateGlobal}" required ${readonlyAttr}>
        </td>
        <td><textarea name="opis[]" class="form-control form-control-sm" rows="2" minlength="200"
                placeholder="Szczegółowy opis (min. 200 znaków)..." required ${readonlyAttr}>${opis}</textarea>
        </td>
        <td>
            <select name="efekty[]" class="form-select form-select-sm" required ${disabledAttr}>
                ${efektyOptions}
            </select>
        </td>
        <td class="text-center text-muted">${statusHtml}</td>
        <td class="text-center">
            <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeRow(this)" ${btnDisabledAttr}><i class="bi bi-trash"></i></button>
        </td>
    `;
    
    tbody.appendChild(tr);
}

function addRow() {
    hasUnsavedChanges = true;
    const tbody = document.getElementById('dziennikBody');
    const rowCount = tbody.getElementsByTagName('tr').length;

    if (rowCount >= 120) {
        alert("Osiągnięto limit 120 dni roboczych praktyki.");
        return;
    }

    appendRow(tbody, rowCount + 1, null);
    updateDeleteButtons();
}

function removeRow(button) {
    if (!confirm("Czy na pewno chcesz usunąć ten wpis? Zmiany zostaną zachowane po kliknięciu 'Zapisz wpisy'.")) {
        return;
    }
    hasUnsavedChanges = true;
    const row = button.closest('tr');
    row.remove();
    updateRowNumbers();
    updateDeleteButtons();
}

function updateRowNumbers() {
    const rows = document.getElementById('dziennikBody').getElementsByTagName('tr');
    for (let i = 0; i < rows.length; i++) {
        rows[i].querySelector('.day-number').innerText = i + 1;
    }
}

function updateDeleteButtons() {
    const rows = document.getElementById('dziennikBody').getElementsByTagName('tr');
    if (rows.length === 1) {
        const btn = rows[0].querySelector('.btn-outline-danger');
        if (btn) btn.disabled = true;
    } else {
        for (let i = 0; i < rows.length; i++) {
            const btn = rows[i].querySelector('.btn-outline-danger');
            if (btn && btn.getAttribute('data-approved') !== 'true') {
                btn.disabled = false;
            }
        }
    }
}

function addMultipleRows() {
    const countInput = document.getElementById('bulkAddCount');
    let count = parseInt(countInput.value);
    if (isNaN(count) || count < 1) return;
    
    if (count > 20) {
        alert("Jednorazowo możesz dodać maksymalnie 20 dni. Zmniejsz wartość i spróbuj ponownie.");
        return;
    }
    
    for (let i = 0; i < count; i++) {
        const tbody = document.getElementById('dziennikBody');
        const rowCount = tbody.getElementsByTagName('tr').length;
        if (rowCount >= 120) {
            alert("Osiągnięto limit 120 dni roboczych praktyki.");
            break;
        }
        addRow();
    }
}

function saveDziennik() {
    const tbody = document.getElementById('dziennikBody');
    const rows = tbody.getElementsByTagName('tr');
    const wpisy = [];
    
    for (let i = 0; i < rows.length; i++) {
        const idInput = rows[i].querySelector('input[name="wpis_id[]"]');
        const dateInput = rows[i].querySelector('input[name="data[]"]');
        const opisInput = rows[i].querySelector('textarea[name="opis[]"]');
        const efektInput = rows[i].querySelector('select[name="efekty[]"]');
        
        wpisy.push({
            wpis_id: idInput ? idInput.value : '',
            data: dateInput ? dateInput.value : '',
            opis: opisInput ? opisInput.value : '',
            efekt: efektInput ? efektInput.value : ''
        });
    }
    
    fetch('/api/student/dziennik', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ wpisy: wpisy })
    })
    .then(response => response.json())
    .then(data => {
        isSubmitting = false;
        hasUnsavedChanges = false;
        
        const alertContainer = document.getElementById('alerts-container');
        alertContainer.innerHTML = '';
        
        if (data.success) {
            alertContainer.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            setTimeout(() => { window.location.reload(); }, 1500);
        } else {
            data.errors.forEach(err => {
                alertContainer.innerHTML += `<div class="alert alert-danger">${err}</div>`;
            });
        }
    })
    .catch(err => {
        console.error(err);
        isSubmitting = false;
    });
}
