document.addEventListener('DOMContentLoaded', function () {
    loadNotifications();
});

function loadNotifications() {
    fetch('/api/notifications')
        .then(res => res.json())
        .then(data => {
            if (data.error) return;
            const notifs = data.powiadomienia || [];

            const badge = document.getElementById('notif-badge');
            const unreadCount = notifs.filter(n => !n.przeczytane).length;

            if (unreadCount > 0) {
                badge.style.display = 'inline-block';
                badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
            } else {
                badge.style.display = 'none';
            }

            const content = document.getElementById('notif-content');
            if (notifs.length === 0) {
                content.innerHTML = '<li><span class="dropdown-item text-muted text-center small py-3">Brak nowych powiadomień</span></li>';
                return;
            }

            content.innerHTML = '';
            notifs.forEach(n => {
                const bgClass = n.przeczytane ? '' : 'bg-light';
                const fwClass = n.przeczytane ? 'text-muted' : 'fw-bold';
                const icon = !n.przeczytane ? '<i class="bi bi-circle-fill text-primary" style="font-size: 0.5rem; margin-right: 5px;"></i>' : '';

                content.innerHTML += `
                    <li>
                        <a class="dropdown-item py-2 ${bgClass}" href="#" onclick="handleNotificationClick(event, ${n.id}, '${n.link}')" style="white-space: normal; font-size: 0.85rem; border-bottom: 1px solid #f1f1f1;">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    ${icon}<span class="${fwClass}">${n.tresc}</span>
                                </div>
                            </div>
                            <div class="text-end text-muted mt-1" style="font-size: 0.7rem;">${n.data_utworzenia}</div>
                        </a>
                    </li>
                `;
            });

            if (unreadCount > 0) {
                content.innerHTML += `
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item text-center text-primary py-2" href="#" onclick="markAllRead(event)" style="font-size: 0.85rem;">Oznacz wszystkie jako przeczytane</a></li>
                `;
            }
        })
        .catch(err => console.error('Błąd pobierania powiadomień:', err));
}

function handleNotificationClick(e, id, link) {
    e.preventDefault();

    fetch(`/api/notifications/mark_read/${id}`, { method: 'POST' })
        .then(() => {
            if (link && link !== 'null') {
                window.location.href = link;
            } else {
                loadNotifications();
            }
        });
}

function markAllRead(e) {
    e.preventDefault();
    fetch('/api/notifications/mark_all_read', { method: 'POST' })
        .then(() => loadNotifications());
}
