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

            const safeNazwisko = (uzytkownik.nazwisko || '').split('(')[0].trim();
            document.getElementById('student-greeting').textContent = `Witaj, ${uzytkownik.imie} ${safeNazwisko}!`;

            const status = praktyka ? praktyka.status : null;

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
                let tilesHtml = ``;

                if (status === 'SCIEZKA_PRACA' || status === 'ZAL4B_ZATWIERDZONE') {
                    tilesHtml += `
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/zal4b_wniosek" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-briefcase"></i></div>
                            <div class="usos-tile-content">
                                <h5>Wniosek o zaliczenie (Zał. 4b)</h5>
                                <p>Twój wniosek o zaliczenie praktyki na podstawie pracy.</p>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/zal7a_sprawozdanie" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-journal-check"></i></div>
                            <div class="usos-tile-content">
                                <h5>Sprawozdanie z pracy (Zał. 7a)</h5>
                                <p>Twoje sprawozdanie podsumowujące wykonaną pracę.</p>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/zal4a_decyzja" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-file-earmark-check"></i></div>
                            <div class="usos-tile-content">
                                <h5>Decyzja (Zał. 4a)</h5>
                                <p>Decyzja w sprawie zaliczenia praktyki zawodowej.</p>
                            </div>
                        </a>
                    </div>
                    `;
                } else {
                    tilesHtml += `
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/dziennik" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-journal-text"></i></div>
                            <div class="usos-tile-content">
                                <h5>Dziennik Praktyki (Zał. 6)</h5>
                                <p>Uzupełniaj wpisy w dzienniku praktyki każdego dnia pracy.</p>
                            </div>
                        </a>
                    </div>
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
                        <a href="/student/sprawozdanie" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-file-text"></i></div>
                            <div class="usos-tile-content">
                                <h5>Sprawozdanie (Zał. 7)</h5>
                                <p>Sprawozdanie z przebiegu praktyki zawodowej.</p>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-6 col-lg-6">
                        <a href="/student/zal5_ankieta" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-ui-radios"></i></div>
                            <div class="usos-tile-content">
                                <h5>Ankieta (Zał. 5)</h5>
                                <p>Anonimowa ankieta oceniająca przebieg praktyk zawodowych.</p>
                            </div>
                        </a>
                    </div>
                    `;
                }

                tilesHtml += `
                    <div class="col-md-12 col-lg-12 mb-3">
                        <a href="/dokumenty" class="usos-tile">
                            <div class="usos-tile-icon"><i class="bi bi-folder2-open"></i></div>
                            <div class="usos-tile-content">
                                <h5>Wszystkie dokumenty</h5>
                                <p>Przeglądaj niezbędne regulaminy oraz pobieraj wzory formularzy.</p>
                            </div>
                        </a>
                    </div>
                `;

                tilesContainer.innerHTML = tilesHtml;
            }
        })
        .catch(err => console.error(err));
});
