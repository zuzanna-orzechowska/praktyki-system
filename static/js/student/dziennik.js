let hasUnsavedChanges = false;
let isSubmitting = false;
let efektyListaGlobal = [];
let praktykaStartGlobal = '';
let maxDateGlobal = '';

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('dziennik-form');

    form.addEventListener('change', function () {
        hasUnsavedChanges = true;
    });

    form.addEventListener('input', function () {
        hasUnsavedChanges = true;
    });

    form.addEventListener('submit', function (e) {
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

    window.loadDziennik = function () {
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

                const rok = praktyka.rok_akademicki || '';
                const textEl = document.getElementById('rok-akademicki-text');
                const btnEl = document.getElementById('rok-akademicki-edit-btn');
                const contEl = document.getElementById('rok-akademicki-edit-container');
                const inputEl = document.getElementById('rok-akademicki-input');

                if (rok && textEl && btnEl && contEl && inputEl) {
                    textEl.textContent = rok;
                    textEl.style.display = 'inline';
                    btnEl.style.display = 'inline';
                    contEl.style.display = 'none';
                    inputEl.value = rok;
                } else if (textEl && btnEl && contEl && inputEl) {
                    textEl.style.display = 'none';
                    btnEl.style.display = 'none';
                    contEl.style.display = 'inline-flex';
                    inputEl.value = '';
                }

                // Render efekty list
                const efektyUl = document.getElementById('efekty-list');
                efektyUl.innerHTML = '';
                efektyListaGlobal.forEach(efekt => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item mb-1';
                    li.innerHTML = `<strong>${efekt.kod}</strong>: ${efekt.opis}`;
                    efektyUl.appendChild(li);
                });

                const statusDokumentu = data.status_dokumentu || 'Draft';

                // Render table
                const tbody = document.getElementById('dziennikBody');
                tbody.innerHTML = '';

                if (data.wpisy && data.wpisy.length > 0) {
                    data.wpisy.forEach((wpis, index) => {
                        appendRow(tbody, index + 1, wpis, statusDokumentu);
                    });
                } else {
                    appendRow(tbody, 1, null, statusDokumentu);
                }
                renderZalaczniki(data.zalaczniki || []);
                updateDeleteButtons(statusDokumentu);
                renderStatusAndActions(statusDokumentu, data.wpisy ? data.wpisy.length : 0);
            })
            .catch(err => console.error(err));
    };

    // Inicjalne ładowanie
    window.loadDziennik();
});

function renderStatusAndActions(status, wpisyCount) {
    const badge = document.getElementById('dokument-status-badge');

    // Status Badge
    badge.textContent = status;
    badge.className = 'badge';
    if (status === 'Draft') badge.classList.add('bg-secondary');
    else if (status === 'Weryfikacja ZOPZ' || status === 'Weryfikacja UOPZ') badge.classList.add('bg-warning', 'text-dark');
    else if (status === 'Zatwierdzone przez ZOPZ') badge.classList.add('bg-success');
    else if (status === 'Wrócono do poprawy' || status === 'Odrzucone') badge.classList.add('bg-danger');
    else badge.classList.add('bg-info');

    // Bottom Actions
    const mainSaveBtn = document.getElementById('btnZapiszDziennik');
    const bulkAddContainer = document.getElementById('bulkAddContainer');
    const btnBottomZopz = document.getElementById('btnBottomZopz');
    const btnBottomUopz = document.getElementById('btnBottomUopz');

    // Reset defaults
    if (btnBottomZopz) {
        btnBottomZopz.classList.remove('d-none');
        btnBottomZopz.disabled = true;
        btnBottomZopz.onclick = null;
    }
    if (btnBottomUopz) {
        btnBottomUopz.classList.add('d-none');
        btnBottomUopz.onclick = null;
    }

    if (status === 'Draft' || status === 'Wrócono do poprawy') {
        if (mainSaveBtn) mainSaveBtn.style.display = 'inline-block';
        if (bulkAddContainer) bulkAddContainer.style.display = 'flex';

        // Blokada dodawania jeśli nie ma daty rozpoczęcia praktyki
        if (bulkAddContainer && !praktykaStartGlobal) {
            bulkAddContainer.style.display = 'none';
            document.getElementById('alerts-container').innerHTML = `
                <div class="alert alert-warning mb-4">
                    <i class="bi bi-exclamation-triangle me-2"></i> Nie masz jeszcze ustalonej daty rozpoczęcia praktyki. Uzupełnianie dziennika zostało tymczasowo zablokowane.
                </div>
            `;
        }

        // Przycisk "Wyślij do ZOPZ" na dole
        if (btnBottomZopz) {
            if (wpisyCount < 5) {
                btnBottomZopz.disabled = true;
                btnBottomZopz.title = `Wymagane minimum 5 wpisów (obecnie ${wpisyCount})`;
            } else {
                btnBottomZopz.disabled = false;
                btnBottomZopz.title = '';
                btnBottomZopz.onclick = wyslijDoZopz;
            }
        }
    } else {
        // Zablokuj edycję
        if (mainSaveBtn) mainSaveBtn.style.display = 'none';
        if (bulkAddContainer) bulkAddContainer.style.display = 'none';
        if (btnBottomZopz) btnBottomZopz.classList.add('d-none');

        if (status === 'Zatwierdzone przez ZOPZ') {
            // Przycisk "Wyślij do UOPZ" na dole
            if (btnBottomUopz) {
                btnBottomUopz.classList.remove('d-none');
                btnBottomUopz.onclick = wyslijDoUopz;
            }
        }
    }
}

function wyslijDoZopz() {
    if (hasUnsavedChanges) {
        alert("Masz niezapisane zmiany (np. poprawione wpisy)! Zapisz dziennik najpierw, klikając zielony przycisk 'Zapisz Dziennik (Szkic)', zanim wyślesz go do weryfikacji.");
        return;
    }

    if (!confirm('Czy na pewno chcesz przesłać dziennik do weryfikacji ZOPZ? Po przesłaniu nie będziesz mógł go edytować!')) return;
    fetch('/api/student/dziennik/wyslij_do_zopz', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
                loadDziennik();
            } else {
                showAlert(data.error || 'Błąd', 'danger');
            }
        });
}

function wyslijDoUopz() {
    if (!confirm('Czy na pewno chcesz przesłać dziennik do Dziekanatu?')) return;
    fetch('/api/student/dziennik/wyslij_do_uopz', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
                loadDziennik();
            } else {
                showAlert(data.error || 'Błąd', 'danger');
            }
        });
}

function appendRow(tbody, dayNumber, wpis, statusDokumentu = 'Draft') {
    const tr = document.createElement('tr');

    const wid = wpis ? wpis.id : '';
    const dataWpisu = wpis ? wpis.data_wpisu : '';
    const opis = wpis ? wpis.opis_prac : '';
    const nrEfektu = wpis ? wpis.nr_efektu : '';
    const potwierdzony = wpis ? wpis.potwierdzony_zopz : 0;
    const komentarz = wpis ? wpis.komentarz_zopz : '';

    // Dokument jest zablokowany jeśli status to nie Draft i nie Wrócono do poprawy
    const isLocked = statusDokumentu !== 'Draft' && statusDokumentu !== 'Wrócono do poprawy';
    const isRowLocked = isLocked || potwierdzony === 1;

    const readonlyAttr = isRowLocked ? 'readonly' : '';
    const disabledAttr = isRowLocked ? 'style="pointer-events: none; opacity: 0.8;" tabindex="-1"' : '';
    const btnDisabledAttr = isRowLocked ? 'disabled data-approved="true" title="Nie można usunąć zablokowanego wpisu"' : '';

    let statusHtml = '<small>Oczekuje...</small>';
    let opisKlasa = '';
    let uwagiHtml = '';

    if (potwierdzony === 1) {
        statusHtml = '<span class="text-success fw-bold"><i class="bi bi-check-circle"></i> Potwierdzone</span>';
    } else if (potwierdzony === -1) {
        statusHtml = '<span class="text-danger fw-bold"><i class="bi bi-x-circle"></i> Odrzucone</span>';
        opisKlasa = 'border-danger bg-light';
        if (komentarz) {
            uwagiHtml = `<div class="mt-1 small text-danger"><i class="bi bi-chat-left-text me-1"></i><strong>Uwagi ZOPZ:</strong> ${komentarz}</div>`;
        }
    }

    let efektyOptions = '<option value="" disabled ' + (!nrEfektu ? 'selected' : '') + '>Wybierz...</option>';
    efektyListaGlobal.forEach(e => {
        efektyOptions += `<option value="${e.kod}" ${nrEfektu === e.kod ? 'selected' : ''}>${e.kod}</option>`;
    });

    tr.innerHTML = `
        <td class="text-center fw-bold day-number">${dayNumber}</td>
        <td>
            <input type="hidden" name="wpis_id[]" value="${wid}">
            <input type="date" name="data[]" class="form-control form-control-sm ${opisKlasa}"
                value="${dataWpisu}" required ${readonlyAttr}>
        </td>
        <td><textarea name="opis[]" class="form-control form-control-sm ${opisKlasa}" rows="2" minlength="200"
                placeholder="Szczegółowy opis (min. 200 znaków)..." required ${readonlyAttr}>${opis}</textarea>
            ${uwagiHtml}
        </td>
        <td>
            <select name="efekty[]" class="form-select form-select-sm ${opisKlasa}" required ${disabledAttr}>
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

function updateDeleteButtons(statusDokumentu = 'Draft') {
    const isLocked = statusDokumentu !== 'Draft' && statusDokumentu !== 'Wrócono do poprawy';
    const rows = document.getElementById('dziennikBody').getElementsByTagName('tr');
    for (let i = 0; i < rows.length; i++) {
        const btn = rows[i].querySelector('.btn-outline-danger');
        if (btn && btn.getAttribute('data-approved') !== 'true' && !isLocked) {
            btn.disabled = false;
        } else if (btn) {
            btn.disabled = true;
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

    const contEl = document.getElementById('rok-akademicki-edit-container');
    const rokInput = document.getElementById('rok-akademicki-input');
    const textEl = document.getElementById('rok-akademicki-text');
    let rokAkademicki = '';
    if (contEl && contEl.style.display !== 'none') {
        rokAkademicki = rokInput ? rokInput.value.trim() : '';
        if (!rokAkademicki) {
            alert('Proszę wypełnić Rok akademicki.');
            return;
        }
    } else {
        rokAkademicki = textEl ? textEl.textContent : '';
    }

    const btn = event.target;

    // Sprawdzenie czy są niezapisane załączniki
    const niezapisane = document.querySelectorAll('.nowy-zalacznik-row');
    if (niezapisane.length > 0) {
        alert('Masz nowo dodane załączniki, które nie zostały zapisane. Zapisz je najpierw, klikając zielony przycisk "Zapisz dodane załączniki" pod tabelą załączników, albo usuń je jeśli z nich rezygnujesz.');
        return;
    }

    const originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Zapisywanie...';

    const formData = new FormData();
    formData.append('dane', JSON.stringify({
        wpisy: wpisy,
        rok_akademicki: rokAkademicki
    }));

    fetch('/api/student/dziennik', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            isSubmitting = false;
            hasUnsavedChanges = false;

            const alertContainer = document.getElementById('alerts-container');
            alertContainer.innerHTML = '';

            if (data.success) {
                alertContainer.innerHTML = `<div class="alert alert-success alert-dismissible fade show" role="alert">
                ${data.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Zamknij"></button>
            </div>`;

                // Dynamiczne przeładowanie dziennika by pobrać wygenerowane nowe ID wpisów, bez mrugania ekranu
                loadDziennik();

                btn.disabled = false;
                btn.innerHTML = originalHtml;
            } else {
                data.errors.forEach(err => {
                    alertContainer.innerHTML += `<div class="alert alert-danger">${err}</div>`;
                });
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        })
        .catch(err => {
            console.error('Fetch error:', err);
            btn.disabled = false;
            btn.innerHTML = originalHtml;
            showAlert('Wystąpił błąd komunikacji z serwerem. Zobacz konsolę w narzędziach deweloperskich.', 'danger');
        });
}

window.editRokAkademicki = function () {
    document.getElementById('rok-akademicki-text').style.display = 'none';
    document.getElementById('rok-akademicki-edit-btn').style.display = 'none';
    document.getElementById('rok-akademicki-edit-container').style.display = 'inline-flex';
    document.getElementById('rok-akademicki-input').focus();
};

function renderZalaczniki(zalaczniki) {
    const tbody = document.getElementById('zalacznikiBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (!zalaczniki || zalaczniki.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-2 text-muted fst-italic">Brak załączników</td></tr>';
        return;
    }

    zalaczniki.forEach((zal, index) => {
        const plikName = zal.plik_path ? zal.plik_path.split('/').pop() : 'Brak pliku';
        tbody.innerHTML += `
            <tr class="istniejacy-zalacznik" data-zalacznik-id="${zal.id}">
                <td class="text-center align-middle zal-index">${index + 1}</td>
                <td class="align-middle fw-bold">${zal.opis}</td>
                <td class="align-middle text-break" style="font-size: 11px;">
                    <a href="/static/${zal.plik_path}" target="_blank" class="text-decoration-none"><i class="bi bi-file-earmark-text"></i> ${plikName}</a>
                </td>
                <td class="text-center align-middle no-print">
                    <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2" onclick="usunIstniejacyZalacznik(${zal.id})" title="Usuń załącznik">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

function dodajWierszZalacznika() {
    const tbody = document.getElementById('zalacznikiBody');
    if (tbody.querySelector('.fst-italic')) {
        tbody.innerHTML = '';
    }

    const rowCount = tbody.querySelectorAll('tr').length;
    const tr = document.createElement('tr');
    tr.className = 'nowy-zalacznik-row bg-light';
    tr.innerHTML = `
        <td class="text-center align-middle new-zal-index">${rowCount + 1}</td>
        <td class="align-middle">
            <input type="text" class="form-control form-control-sm" placeholder="Krótki opis (np. 'Schemat ERD')" required>
        </td>
        <td class="align-middle">
            <input type="file" class="form-control form-control-sm" required>
        </td>
        <td class="text-center align-middle no-print">
            <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2" onclick="usunWierszZalacznika(this)" title="Usuń ten wiersz">
                <i class="bi bi-trash"></i>
            </button>
        </td>
    `;
    tbody.appendChild(tr);

    document.getElementById('zapisz-zalaczniki-container').classList.remove('d-none');
}

function usunWierszZalacznika(btn) {
    const row = btn.closest('tr');
    row.remove();
    updateZalacznikiIndices();

    const niezapisane = document.querySelectorAll('.nowy-zalacznik-row');
    if (niezapisane.length === 0) {
        document.getElementById('zapisz-zalaczniki-container').classList.add('d-none');
    }
}

window.zapiszWszystkieNoweZalaczniki = function (btn) {
    const noweZalaczniki = document.querySelectorAll('.nowy-zalacznik-row');
    if (noweZalaczniki.length === 0) return;

    let hasErrors = false;
    const formData = new FormData();
    let zalCount = 0;

    noweZalaczniki.forEach((row) => {
        const descInput = row.querySelector('input[type="text"]');
        const fileInput = row.querySelector('input[type="file"]');

        if (!descInput.value.trim() || fileInput.files.length === 0) {
            hasErrors = true;
            row.classList.add('table-danger');
        } else {
            row.classList.remove('table-danger');
            formData.append(`zal_opis_${zalCount}`, descInput.value.trim());
            formData.append(`zal_plik_${zalCount}`, fileInput.files[0]);
            zalCount++;
        }
    });

    if (hasErrors) {
        showAlert('Wypełnij opis i wybierz plik dla wszystkich nowych załączników przed zapisem.', 'danger');
        return;
    }

    formData.append('zal_count', zalCount);

    btn.disabled = true;
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Zapisywanie...';

    fetch('/api/student/dziennik/zalacznik', {
        method: 'POST',
        body: formData
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert('Załączniki zapisane pomyślnie.', 'success');

                noweZalaczniki.forEach(r => r.remove());
                document.getElementById('zapisz-zalaczniki-container').classList.add('d-none');

                const tbody = document.getElementById('zalacznikiBody');
                const emptyRow = tbody.querySelector('.fst-italic');
                if (emptyRow) emptyRow.parentElement.innerHTML = '';

                if (data.zalaczniki && data.zalaczniki.length > 0) {
                    data.zalaczniki.forEach((zal) => {
                        const plikName = zal.plik_path ? zal.plik_path.split('/').pop() : 'Brak pliku';
                        const tr = document.createElement('tr');
                        tr.className = 'istniejacy-zalacznik';
                        tr.setAttribute('data-zalacznik-id', zal.id);
                        tr.innerHTML = `
                        <td class="text-center align-middle zal-index"></td>
                        <td class="align-middle fw-bold">${zal.opis}</td>
                        <td class="align-middle text-break" style="font-size: 11px;">
                            <a href="/static/${zal.plik_path}" target="_blank" class="text-decoration-none">
                                <i class="bi bi-file-earmark-text"></i> ${plikName}
                            </a>
                        </td>
                        <td class="text-center align-middle no-print">
                            <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2" onclick="usunIstniejacyZalacznik(${zal.id})" title="Usuń załącznik">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                        tbody.appendChild(tr);
                    });
                    updateZalacznikiIndices();
                }

                btn.disabled = false;
                btn.innerHTML = originalHtml;
            } else {
                showAlert('Błąd: ' + (data.message || 'Nieznany błąd'), 'danger');
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        })
        .catch(err => {
            console.error('Upload error:', err);
            showAlert('Wystąpił błąd komunikacji podczas wgrywania załączników.', 'danger');
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        });
};

function showAlert(message, type) {
    const alertContainer = document.getElementById('alerts-container');
    if (!alertContainer) return;
    alertContainer.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>`;
}

function updateZalacznikiIndices() {
    const tbody = document.getElementById('zalacznikiBody');
    let index = 1;
    tbody.querySelectorAll('tr').forEach(tr => {
        const tdLp = tr.querySelector('td:first-child');
        if (tdLp && !tr.querySelector('.fst-italic')) {
            tdLp.textContent = index++;
        }
    });
    if (tbody.querySelectorAll('tr').length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-2 text-muted fst-italic">Brak załączników</td></tr>';
    }
}

window.usunIstniejacyZalacznik = function (id) {
    if (!confirm('Czy na pewno chcesz usunąć ten załącznik z systemu?')) return;

    fetch(`/api/student/dziennik/zalacznik/${id}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Załącznik usunięty.', 'success');
                const tr = document.querySelector(`tr[data-zalacznik-id="${id}"]`);
                if (tr) {
                    tr.remove();
                    updateZalacznikiIndices();

                    const tbody = document.getElementById('zalacznikiBody');
                    if (tbody.querySelectorAll('tr').length === 0) {
                        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-2 text-muted fst-italic">Brak załączników</td></tr>';
                    }
                }
            } else {
                showAlert(data.error || data.message || 'Wystąpił błąd podczas usuwania', 'danger');
            }
        })
        .catch(err => {
            console.error(err);
            showAlert('Wystąpił błąd komunikacji z serwerem.', 'danger');
        });
};
