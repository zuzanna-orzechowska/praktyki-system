document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/student/zal2a_harmonogram')
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
            
            const tbody = document.getElementById('harmonogram-body');
            tbody.innerHTML = '';
            
            if (data.pozycje && data.pozycje.length > 0) {
                data.pozycje.forEach(p => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="text-center fw-bold">${p.lp}</td>
                        <td>${p.komorka_organizacyjna}</td>
                        <td>${p.opis_zadan}</td>
                        <td class="text-center">${p.planowana_liczba_dni}</td>
                        <td class="text-center">${p.uwagi || ''}</td>
                    `;
                    tbody.appendChild(tr);
                });
                
                const trSuma = document.createElement('tr');
                trSuma.className = 'table-light fw-bold';
                trSuma.innerHTML = `
                    <td colspan="3" class="text-end">Suma dni:</td>
                    <td class="text-center text-primary">${data.suma_dni} / 120</td>
                    <td></td>
                `;
                tbody.appendChild(trSuma);
            } else {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Brak pozycji w harmonogramie. Oczekuj na wprowadzenie danych przez UOPZ.</td></tr>';
            }
            
            // Check document status to disable buttons
            if (data.dokument && data.dokument.status !== 'Draft') {
                document.querySelectorAll('button[type="button"]').forEach(btn => btn.style.display = 'none');
            }
        })
        .catch(err => console.error(err));
});

function submitDecision(action) {
    const komentarz = document.getElementById('komentarz') ? document.getElementById('komentarz').value : '';
    
    if (action === 'odrzuc' && !komentarz) {
        if (!confirm('Czy na pewno chcesz odrzucić bez komentarza?')) return;
    }
    
    fetch('/api/student/zal2a_harmonogram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ akcja: action, komentarz: komentarz })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.success) {
            window.location.reload();
        }
    })
    .catch(err => console.error(err));
}
