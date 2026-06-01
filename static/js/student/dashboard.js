document.addEventListener('DOMContentLoaded', function () {
    fetch('/api/student/dashboard')
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

            const uzytkownik = data.uzytkownik;
            const praktyka = data.praktyka;

            document.getElementById('student-greeting').textContent = `Witaj, ${uzytkownik.imie} ${uzytkownik.nazwisko}!`;

            const statusBadge = document.getElementById('student-status-badge');

            const statusMap = {
                'BRAK_ZGŁOSZENIA': ['Brak zgłoszenia', 'secondary'],
                'OCZEKUJE_NA_ZAL9': ['Oczekuje na załącznik 9', 'warning text-dark'],
                'ZAL9_ZATWIERDZONE': ['Zał. 9 zatwierdzony', 'success'],
                'SCIEZKA_PRACA': ['Zaliczenie z pracy', 'info text-dark'],
                'PROGRAM_UZGODNIONY': ['Program uzgodniony', 'primary'],
                'SKIEROWANIE_WYDANE': ['Skierowanie wydane', 'success'],
                'PRAKTYKA_W_TOKU': ['Praktyka w toku', 'warning text-dark'],
                'DOKUMENTY_ZLOZONE': ['Dokumenty złożone', 'info text-dark'],
                'EGZAMIN': ['Egzamin', 'info text-dark'],
                'ZALICZONA': ['Praktyka zaliczona', 'success']
            };

            const status = praktyka ? praktyka.status : null;
            const [statusText, statusColor] = status && statusMap[status] ? statusMap[status] : ['Brak zgłoszenia', 'secondary'];

            statusBadge.textContent = statusText;
            statusBadge.className = `badge bg-${statusColor}`;

            const alertsContainer = document.getElementById('alerts-container');
            alertsContainer.innerHTML = '';

            const tilesContainer = document.getElementById('dashboard-tiles');
            tilesContainer.innerHTML = '';

            if (!praktyka || status === 'OCZEKUJE_NA_ZAL9' || status === 'BRAK_ZGŁOSZENIA') {
                tilesContainer.innerHTML = `
                    <div class="col-12 mb-2">
                        <h5 class="fw-bold text-center mt-3">Wybierz sposób realizacji praktyki:</h5>
                    </div>
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/zal9_oswiadczenie" class="usos-tile border-success border-2">
                            <div class="usos-tile-icon text-success"><i class="bi bi-building"></i></div>
                            <div class="usos-tile-content">
                                <h5 class="text-success">Ścieżka Standardowa (Zał. 9)</h5>
                                <p>Znalazłem firmę, która przyjmie mnie na praktykę. Wypełnij oświadczenie od firmy, aby wygenerować porozumienie.</p>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/zal4b_wniosek" class="usos-tile border-primary border-2">
                            <div class="usos-tile-icon text-primary"><i class="bi bi-briefcase"></i></div>
                            <div class="usos-tile-content">
                                <h5 class="text-primary">Zaliczenie na podst. Pracy (Zał. 4b)</h5>
                                <p>Pracuję lub prowadzę własną działalność. Złóż wniosek, aby zaliczyć ją jako praktykę studencką.</p>
                            </div>
                        </a>
                    </div>
                `;
            } else {
                let dziennikTile = '';
                if (status !== 'SCIEZKA_PRACA') {
                    dziennikTile = `
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/dziennik" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-journal-text"></i></div>
                            <div class="usos-tile-content">
                                <h5>Dziennik Praktyki (Zał. 6)</h5>
                                <p>Uzupełniaj wpisy w dzienniku praktyki każdego dnia pracy.</p>
                            </div>
                        </a>
                    </div>
                    `;
                }

                tilesContainer.innerHTML = `
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/dashboard" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-person-badge"></i></div>
                            <div class="usos-tile-content">
                                <h5>Panel praktyk</h5>
                                <p>Sprawdź swoje dane oraz szczegóły procesu zaliczania praktyk.</p>
                            </div>
                        </a>
                    </div>
                    ${dziennikTile}
                    <div class="col-md-12 col-lg-12 mb-3">
                        <a href="/student/porozumienie" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-file-earmark-text"></i></div>
                            <div class="usos-tile-content">
                                <h5>Porozumienie i Program (Zał. 1, 2)</h5>
                                <p>Podgląd Twojego porozumienia o organizację praktyki oraz programu praktyki.</p>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/zal2a_harmonogram" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-calendar-check"></i></div>
                            <div class="usos-tile-content">
                                <h5>Harmonogram i Program (Zał. 2a)</h5>
                                <p>Szczegółowy plan i program Twoich praktyk zawodowych.</p>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/zal3_karta" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-card-checklist"></i></div>
                            <div class="usos-tile-content">
                                <h5>Karta Praktyki (Zał. 3)</h5>
                                <p>Podgląd potwierdzenia odbycia praktyki i wystawionych ocen.</p>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/zal4_efekty" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-list-check"></i></div>
                            <div class="usos-tile-content">
                                <h5>Efekty Uczenia (Zał. 4)</h5>
                                <p>Podgląd zatwierdzonych przez zakład efektów uczenia się z Twojej praktyki.</p>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-6 col-lg-6">
                        <a href="/dokumenty" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-folder2-open"></i></div>
                            <div class="usos-tile-content">
                                <h5>Wszystkie dokumenty</h5>
                                <p>Przeglądaj niezbędne regulaminy oraz pobieraj wzory formularzy.</p>
                            </div>
                        </a>
                    </div>
                `;
            }
        })
        .catch(err => console.error(err));
});
