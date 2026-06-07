document.addEventListener('DOMContentLoaded', function() {
    loadData();

    document.getElementById('btn-random-assign').addEventListener('click', function() {
        if (confirm('Czy na pewno chcesz przypisać losowych opiekunów do wszystkich studentów, którzy ich nie mają?')) {
            randomAssign();
        }
    });
});

let globalUopzList = [];

function loadData() {
    fetch('/api/dziekanat/przypisz_uopz')
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                throw new Error('Unauthorized');
            }
            return response.json();
        })
        .then(data => {
            globalUopzList = data.uopz_list || [];
            const praktyki = data.praktyki || [];
            renderTable(praktyki);
        })
        .catch(err => console.error(err));
}

function renderTable(praktyki) {
    const tbody = document.getElementById('students-table');
    tbody.innerHTML = '';

    if (praktyki.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">Brak studentów w systemie.</td></tr>';
        return;
    }

    let uopzOptions = '<option value="">--- Wybierz Opiekuna ---</option>';
    globalUopzList.forEach(u => {
        const title = u.tytul ? u.tytul + ' ' : '';
        uopzOptions += `<option value="${u.id}">${title}${u.imie} ${u.nazwisko}</option>`;
    });

    praktyki.forEach(p => {
        let selectHtml = `<select class="form-select form-select-sm uopz-select" id="select-${p.id}">`;
        selectHtml += uopzOptions;
        selectHtml += `</select>`;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="fw-bold text-primary">${p.student_imie} ${p.student_nazwisko}</td>
            <td>${p.nr_albumu}</td>
            <td>${p.kierunek || 'Brak'}</td>
            <td><span class="badge bg-secondary">${p.status}</span></td>
            <td>${selectHtml}</td>
            <td class="text-center">
                <button class="btn btn-sm btn-success w-100" onclick="zapiszPrzypisanie(${p.id})">Zapisz</button>
            </td>
        `;
        tbody.appendChild(tr);

        if (p.uopz_id) {
            document.getElementById(`select-${p.id}`).value = p.uopz_id;
        }
    });
}

window.zapiszPrzypisanie = function(praktykaId) {
    const w = document.getElementById(`select-${praktykaId}`);
    const uopzId = w.value ? parseInt(w.value) : null;

    fetch('/api/dziekanat/przypisz_uopz', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            praktyka_id: praktykaId,
            uopz_id: uopzId
        })
    })
    .then(response => response.json())
    .then(data => {
        const alerts = document.getElementById('alerts-container');
        if (data.success) {
            alerts.innerHTML = `<div class="alert alert-success alert-dismissible fade show" role="alert">
                ${data.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        } else {
            alerts.innerHTML = `<div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${data.error || 'Błąd'}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        }
        window.scrollTo(0,0);
    })
    .catch(err => console.error(err));
};

function randomAssign() {
    if (globalUopzList.length === 0) {
        alert("Brak zarejestrowanych opiekunów uczelnianych (UOPZ).");
        return;
    }

    const allSelects = document.querySelectorAll('.uopz-select');
    let toAssignCount = 0;

    allSelects.forEach(select => {
        if (!select.value) {
            const randomUopz = globalUopzList[Math.floor(Math.random() * globalUopzList.length)];
            select.value = randomUopz.id;
            
            const praktykaId = select.id.split('-')[1];
            zapiszPrzypisanie(praktykaId);
            toAssignCount++;
        }
    });

    if (toAssignCount === 0) {
        alert("Wszyscy studenci mają już przypisanych opiekunów.");
    }
}
