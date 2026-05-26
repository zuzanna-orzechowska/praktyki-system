document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/dziekanat/dashboard')
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/auth/login';
                throw new Error('Unauthorized');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error(data.error);
                return;
            }
            
            const badge = document.getElementById('zal9-badge');
            if (data.zal9_count > 0) {
                badge.textContent = data.zal9_count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
            
            const porBadge = document.getElementById('porozumienia-badge');
            if (porBadge) {
                if (data.porozumienia_count > 0) {
                    porBadge.textContent = data.porozumienia_count;
                    porBadge.style.display = 'inline-block';
                } else {
                    porBadge.style.display = 'none';
                }
            }
        })
        .catch(err => console.error(err));
});
