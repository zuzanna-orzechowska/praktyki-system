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
            
            if (status === 'ZALICZONA') {
                alertsContainer.innerHTML = `
                <div class="alert alert-success border-0 shadow-sm mb-4 d-flex align-items-center">
                    <i class="bi bi-check-circle-fill me-3 fs-3 text-success"></i>
                    <div>
                        <h5 class="mb-1 fw-bold text-success">Gratulacje! Praktyka Zaliczona!</h5>
                        <p class="mb-0">Komisja Egzaminacyjna pozytywnie oceniła Twoją praktykę (Protokół nr 8/8a).</p>
                    </div>
                </div>
                `;
            }

            if (data.zal9_status === 'Draft' && data.zal9_komentarz) {
                alertsContainer.innerHTML += `
                <div class="alert alert-warning border-0 shadow-sm mb-4 d-flex align-items-center">
                    <i class="bi bi-exclamation-triangle-fill me-3 fs-3 text-warning"></i>
                    <div>
                        <h5 class="mb-1 fw-bold text-warning">Oświadczenie (Zał. 9) zostało cofnięte do poprawy</h5>
                        <p class="mb-0"><strong>Komentarz Dziekanatu:</strong> ${data.zal9_komentarz}</p>
                    </div>
                </div>
                `;
            } else if (data.zal9_status === 'Submitted') {
                alertsContainer.innerHTML += `
                <div class="alert alert-info border-0 shadow-sm mb-4 d-flex align-items-center">
                    <i class="bi bi-info-circle-fill me-3 fs-3 text-info"></i>
                    <div>
                        <h5 class="mb-1 fw-bold text-info">Oświadczenie (Zał. 9) przesłane</h5>
                        <p class="mb-0">Oświadczenie zostało przesłane i oczekuje na weryfikację przez Dziekanat.</p>
                    </div>
                </div>
                `;
            } else if (data.zal9_status === 'AwaitingAccount' || status === 'ZAL9_ZATWIERDZONE') {
                alertsContainer.innerHTML += `
                <div class="alert alert-success border-0 shadow-sm mb-4 d-flex align-items-center">
                    <i class="bi bi-check-circle-fill me-3 fs-3 text-success"></i>
                    <div>
                        <h5 class="mb-1 fw-bold text-success">Oświadczenie (Zał. 9) zatwierdzone</h5>
                        <p class="mb-0">Oświadczenie zostało zatwierdzone. Trwa proces organizacji praktyki.</p>
                    </div>
                </div>
                `;
            }

            const tilesContainer = document.getElementById('dashboard-tiles');
            tilesContainer.innerHTML = '';

            if (!praktyka || status === 'BRAK_ZGŁOSZENIA') {
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

                if (status === 'SCIEZKA_PRACA' || status === 'ZAL4B_ZATWIERDZONE' || (status === 'ZALICZONA' && data.dokumenty && data.dokumenty['ZAL4B'])) {
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
                    
                    const zal7a_status = data.zal7a_status;
                    if (zal7a_status === 'Approved') {
                        tilesHtml += `
                        <div class="col-md-6 col-lg-6">
                            <a href="/student/zal8a_protokol" class="usos-tile">
                                <div class="usos-tile-icon"><i class="bi bi-award"></i></div>
                                <div class="usos-tile-content">
                                    <h5>Protokół (Zał. 8a)</h5>
                                    <p>Wygeneruj ostateczny protokół zaliczenia praktyk.</p>
                                </div>
                            </a>
                        </div>
                        `;
                    } else {
                        tilesHtml += `
                        <div class="col-md-6 col-lg-6">
                            <div class="usos-tile" style="opacity: 0.6; cursor: not-allowed;" title="Najpierw uzyskaj zatwierdzenie Sprawozdania (Zał. 7a) od Dyrektora">
                                <div class="usos-tile-icon"><i class="bi bi-lock-fill"></i></div>
                                <div class="usos-tile-content">
                                    <h5>Protokół (Zał. 8a)</h5>
                                    <p>Wymaga zatwierdzenia Sprawozdania (Zał. 7a).</p>
                                </div>
                            </div>
                        </div>
                        `;
                    }
                } else {
                    const etap = data.etap_standardowy || 1;
                    
                    const linkOrDiv = (href, title, icon, p, requiredEtap, sizeClass="col-md-6 col-lg-6 mb-3") => {
                        const isUnlocked = etap >= requiredEtap;
                        
                        let lockedText = "Wymaga zatwierdzenia Oświadczenia (Zał. 9)";
                        if (requiredEtap === 3) {
                            lockedText = "Wymaga zatwierdzenia Porozumienia przez Zakład Pracy";
                        }
                        
                        const lockedStyle = `style="opacity: 0.6; cursor: not-allowed;" title="${lockedText}"`;
                        
                        if (isUnlocked) {
                            return `
                            <div class="${sizeClass}">
                                <a href="${href}" class="usos-tile h-100">
                                    <div class="usos-tile-icon"><i class="bi ${icon}"></i></div>
                                    <div class="usos-tile-content">
                                        <h5>${title}</h5>
                                        <p>${p}</p>
                                    </div>
                                </a>
                            </div>`;
                        } else {
                            return `
                            <div class="${sizeClass}">
                                <div class="usos-tile h-100" ${lockedStyle}>
                                    <div class="usos-tile-icon"><i class="bi bi-lock-fill"></i></div>
                                    <div class="usos-tile-content">
                                        <h5>${title}</h5>
                                        <p>${p}</p>
                                    </div>
                                </div>
                            </div>`;
                        }
                    };

                    tilesHtml += `
                    <div class="col-md-6 col-lg-6 mb-3">
                        <a href="/student/zal9_oswiadczenie" class="usos-tile h-100">
                            <div class="usos-tile-icon"><i class="bi bi-building-check"></i></div>
                            <div class="usos-tile-content">
                                <h5>Oświadczenie (Zał. 9)</h5>
                                <p>Oświadczenie o przyjęciu na praktykę.</p>
                            </div>
                        </a>
                    </div>
                    ${linkOrDiv('/student/dziennik', 'Dziennik Praktyki (Zał. 6)', 'bi-journal-text', 'Uzupełniaj wpisy w dzienniku praktyki każdego dnia pracy.', 3)}
                    ${linkOrDiv('/student/porozumienie', 'Porozumienie i Program (Zał. 1, 2)', 'bi-file-earmark-text', 'Podgląd Twojego porozumienia o organizację praktyki oraz programu praktyki.', 2, 'col-md-12 col-lg-12 mb-3')}
                    ${linkOrDiv('/student/zal2a_harmonogram', 'Harmonogram i Program (Zał. 2a)', 'bi-calendar-check', 'Szczegółowy plan i program Twoich praktyk zawodowych.', 3)}
                    ${linkOrDiv('/student/zal3_karta', 'Karta Praktyki (Zał. 3)', 'bi-card-checklist', 'Podgląd potwierdzenia odbycia praktyki i wystawionych ocen.', 3)}
                    ${linkOrDiv('/student/zal4_efekty', 'Efekty Uczenia (Zał. 4)', 'bi-list-check', 'Podgląd zatwierdzonych przez zakład efektów uczenia się z Twojej praktyki.', 3)}
                    ${linkOrDiv('/student/sprawozdanie', 'Sprawozdanie (Zał. 7)', 'bi-file-text', 'Sprawozdanie z przebiegu praktyki zawodowej.', 3)}
                    ${linkOrDiv('/student/zal5_ankieta', 'Ankieta (Zał. 5)', 'bi-ui-radios', 'Anonimowa ankieta oceniająca przebieg praktyk zawodowych.', 3)}
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
