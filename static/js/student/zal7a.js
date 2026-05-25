document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/student/zal7a_sprawozdanie')
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
            
            const sprawozdanie = data.sprawozdanie;
            
            if (sprawozdanie) {
                if (document.getElementById('charakterystyka')) document.getElementById('charakterystyka').value = sprawozdanie.charakterystyka;
                if (document.getElementById('opis')) document.getElementById('opis').value = sprawozdanie.opis_prac;
                if (document.getElementById('wiedza')) document.getElementById('wiedza').value = sprawozdanie.wiedza_umiejetnosci;
            }
            
            if (data.dokument && data.dokument.status !== 'Draft' && data.dokument.status !== 'Rejected') {
                document.querySelectorAll('textarea, input').forEach(el => el.setAttribute('readonly', 'readonly'));
                if (document.getElementById('action-buttons')) document.getElementById('action-buttons').style.display = 'none';
            }
        })
        .catch(err => console.error(err));
        
    const form = document.getElementById('zal7a-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const data = {
                charakterystyka: document.getElementById('charakterystyka').value,
                opis: document.getElementById('opis').value,
                wiedza: document.getElementById('wiedza').value
            };
            
            fetch('/api/student/zal7a_sprawozdanie', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                const alerts = document.getElementById('alerts-container');
                if (data.success) {
                    alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    alerts.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                }
                window.scrollTo(0,0);
            })
            .catch(err => console.error(err));
        });
    }
});
