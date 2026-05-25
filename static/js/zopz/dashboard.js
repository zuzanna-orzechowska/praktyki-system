document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/zopz/dashboard')
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
            
            const zaklad = data.zaklad;
            if (zaklad) {
                document.getElementById('zaklad-container').style.display = 'block';
                document.getElementById('zaklad-nazwa').textContent = zaklad.nazwa;
                document.getElementById('zaklad-adres').textContent = zaklad.adres;
            } else {
                document.getElementById('zaklad-warning').style.display = 'block';
            }
            
            const praktykanci = data.praktyki || [];
            const table = document.getElementById('praktykanci-table');
            table.innerHTML = '';
            
            if (praktykanci.length > 0) {
                praktykanci.forEach(p => {
                    const dataStr = p.data_start && p.data_end ? `${p.data_start} - ${p.data_end}` : '<span class="text-muted">Brak danych</span>';
                    
                    table.innerHTML += `
                        <tr>
                            <td class="ps-4">
                                <strong>${p.student_imie} ${p.student_nazwisko}</strong><br>
                                <small class="text-muted">Album: ${p.nr_albumu}</small>
                            </td>
                            <td>${p.kierunek}</td>
                            <td>${dataStr}</td>
                            <td><span class="badge bg-secondary">${p.status}</span></td>
                            <td class="text-center">
                                <button class="btn btn-sm btn-outline-primary disabled" title="Dokumenty pojawią się wkrótce">
                                    <i class="bi bi-file-earmark-text"></i> Dokumenty i Regulamin
                                </button>
                            </td>
                        </tr>
                    `;
                });
            } else {
                table.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center py-5 text-muted">
                            <i class="bi bi-person-x fs-1 d-block mb-2"></i>
                            Brak przypisanych studentów do Twojej firmy.
                        </td>
                    </tr>
                `;
            }
        })
        .catch(err => console.error(err));
});
