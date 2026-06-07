document.addEventListener('DOMContentLoaded', function () {
    const pathParts = window.location.pathname.split('/');
    const studentId = pathParts[pathParts.length - 1];
    document.getElementById('back-link').href = `/uopz/teczka/${studentId}`;

    function loadData() {
        fetch(`/api/uopz/zal3_karta/${studentId}`)
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
                    window.location.href = '/uopz/dashboard';
                    return;
                }

                document.getElementById('student-name-header').textContent = `${data.student.nr_albumu} - ${data.uzytkownik.imie} ${data.uzytkownik.nazwisko}`;

                if (data.dokument) {
                    document.getElementById('doc-status-badge').textContent = data.dokument.status;
                }

                // Wypełnianie danych studenta
                const imieNazwisko = `${data.uzytkownik.imie} ${data.uzytkownik.nazwisko.split(' (')[0]}`;
                document.getElementById('val-student-imienazwisko').textContent = imieNazwisko;
                document.getElementById('val-student-imienazwisko2').textContent = imieNazwisko;
                document.getElementById('val-student-album').textContent = data.student.nr_albumu;
                document.getElementById('val-student-studia').textContent = `inżynierskie ${data.student.tryb_studiow}`;
                document.getElementById('val-student-kierunek').textContent = data.student.kierunek;
                if(data.student.specjalnosc) document.getElementById('val-student-specjalnosc').textContent = data.student.specjalnosc;

                // Wypełnianie danych UOPZ
                const uopzDane = `${data.uopz.imie} ${data.uopz.nazwisko}`;
                document.getElementById('val-uopz-dane').textContent = uopzDane;

                // Wypełnianie danych zakładu i praktyki
                if (data.praktyka.zaklad) {
                    const adres = `${data.praktyka.zaklad.ulica || ''} ${data.praktyka.zaklad.nr_budynku || ''}${data.praktyka.zaklad.nr_lokalu ? '/' + data.praktyka.zaklad.nr_lokalu : ''}, ${data.praktyka.zaklad.miasto || ''}`;
                    document.getElementById('val-zaklad-nazwa').textContent = data.praktyka.zaklad.nazwa;
                    document.getElementById('val-zaklad-adres').textContent = adres;
                    document.getElementById('val-zaklad-nazwa2').textContent = data.praktyka.zaklad.nazwa;
                    document.getElementById('val-zaklad-adres2').textContent = adres;
                }
                document.getElementById('val-data-start').textContent = data.praktyka.data_start || 'Brak';
                document.getElementById('val-data-end').textContent = data.praktyka.data_end || 'Brak';
                document.getElementById('val-data-start2').textContent = data.praktyka.data_start || 'Brak';
                document.getElementById('val-data-end2').textContent = data.praktyka.data_end || 'Brak';

                // Porozumienie
                if (data.porozumienie) {
                    const year = data.porozumienie.data_podpisania ? data.porozumienie.data_podpisania.split('-')[0] : new Date().getFullYear();
                    document.getElementById('val-porozumienie-id').textContent = `Porozumienie Nr ${data.porozumienie.id}/${year}`;
                    document.getElementById('val-porozumienie-data').textContent = data.porozumienie.data_podpisania || 'Brak';
                }

                // ZOPZ Dane
                if (data.zopz) {
                    document.getElementById('val-zopz-dane').textContent = `${data.zopz.imie} ${data.zopz.nazwisko}`;
                }

                const skierowanieActions = document.getElementById('skierowanie-actions');

                if (data.karta && data.karta.podpis_dyrektora) {
                    skierowanieActions.style.display = 'none';
                    document.getElementById('val-skierowanie-podpis').innerHTML = `${data.karta.podpis_dyrektora}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.skierowanie_data}</span>`;
                } else {
                    skierowanieActions.style.display = 'block';
                }

                if (data.karta) {
                    if(data.karta.podpis_zgloszenie) document.getElementById('val-zgloszenie-podpis').innerHTML = `${data.karta.podpis_zgloszenie}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.data_zgloszenia}</span>`;
                    if(data.karta.podpis_bhp) document.getElementById('val-bhp-podpis').innerHTML = `${data.karta.podpis_bhp}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.data_bhp}</span>`;
                    
                    if(data.karta.zaswiadczenie_uwagi) document.getElementById('val-zaswiadczenie-uwagi').textContent = data.karta.zaswiadczenie_uwagi;
                    if(data.karta.podpis_zopz) document.getElementById('val-zaswiadczenie-podpis').innerHTML = `${data.karta.podpis_zopz}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.zaswiadczenie_data}</span>`;

                    if (data.karta.ocena_zopz_param) {
                        document.getElementById('val-zopz-ocena-param').textContent = data.karta.ocena_zopz_param;
                        document.getElementById('val-zopz-ocena-opis').textContent = data.karta.ocena_zopz_opis || 'Brak wpisu';
                        if(data.karta.podpis_zopz) document.getElementById('val-zopz-podpis').innerHTML = `${data.karta.podpis_zopz}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.ocena_zopz_data}</span>`;
                    }
                }

                const formOceny = document.getElementById('form-oceny');

                if (data.karta && data.karta.podpis_uopz) {
                    formOceny.style.display = 'none';
                    document.getElementById('uopz-form-actions').style.display = 'none';

                    document.getElementById('ocena-uopz-param-input').style.display = 'none';
                    document.getElementById('uopz-ocena-param-view').style.display = 'block';
                    document.getElementById('uopz-ocena-param-view').textContent = data.karta.ocena_uopz_param;

                    document.getElementById('ocena-sprawozdania-input').style.display = 'none';
                    document.getElementById('uopz-ocena-sprawozdania-view').style.display = 'block';
                    document.getElementById('uopz-ocena-sprawozdania-view').textContent = data.karta.ocena_sprawozdania;

                    document.getElementById('ocena-uopz-opis-input').style.display = 'none';
                    document.getElementById('uopz-ocena-opis-view').style.display = 'block';
                    document.getElementById('uopz-ocena-opis-view').textContent = data.karta.ocena_uopz_opis || 'Brak wpisu';

                    document.getElementById('uopz-podpis-container').style.setProperty('display', 'flex', 'important');
                    const podpisHtml = `${data.karta.podpis_uopz}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.ocena_uopz_data}</span>`;
                    document.getElementById('val-uopz-podpis').innerHTML = podpisHtml;
                } else if (data.karta && data.karta.ocena_zopz_param && !data.karta.podpis_uopz) {
                    formOceny.style.display = 'block';
                    document.getElementById('uopz-form-actions').style.display = 'block';
                    
                    if (data.karta.ocena_uopz_param) document.getElementById('ocena-uopz-param-input').value = data.karta.ocena_uopz_param;
                    if (data.karta.ocena_sprawozdania) document.getElementById('ocena-sprawozdania-input').value = data.karta.ocena_sprawozdania;
                    if (data.karta.ocena_uopz_opis) document.getElementById('ocena-uopz-opis-input').value = data.karta.ocena_uopz_opis;
                } else {
                    formOceny.style.display = 'none';
                }
            })
            .catch(err => console.error(err));
    }

    loadData();

    function sendAction(actionData) {
        fetch(`/api/uopz/zal3_karta/${studentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(actionData)
        })
            .then(response => response.json())
            .then(data => {
                const alerts = document.getElementById('alerts-container');
                if (data.success) {
                    alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    loadData();
                } else {
                    alerts.innerHTML = `<div class="alert alert-danger">${data.message || 'Wystąpił błąd'}</div>`;
                }
                window.scrollTo(0, 0);
            })
            .catch(err => console.error(err));
    }

    const btnWydaj = document.getElementById('btn-wydaj');
    const chkSkierowanie = document.getElementById('zloz-podpis-skierowanie');
    
    if (chkSkierowanie) {
        chkSkierowanie.addEventListener('change', function() {
            const podpisDiv = document.getElementById('val-skierowanie-podpis');
            if (this.checked) {
                podpisDiv.textContent = this.getAttribute('data-imienazwisko');
            } else {
                podpisDiv.textContent = '';
            }
        });
    }

    if(btnWydaj) {
        btnWydaj.addEventListener('click', function (e) {
            e.preventDefault();
            if (!chkSkierowanie || !chkSkierowanie.checked) {
                alert('Musisz złożyć podpis elektroniczny pod skierowaniem, aby je wystawić i wysłać do zakładu (ZOPZ).');
                return;
            }
            if (confirm("Czy na pewno chcesz wystawić i podpisać skierowanie na praktykę? Zostanie ono przekazane do ZOPZ.")) {
                sendAction({ akcja: 'wydaj_skierowanie' });
            }
        });
    }

    const btnPopros = document.getElementById('btn-popros');
    if(btnPopros) {
        btnPopros.addEventListener('click', function (e) {
            e.preventDefault();
            if (confirm("Czy chcesz wysłać prośbę o podpis do Dyrektora?")) {
                sendAction({ akcja: 'popros_dyrektora' });
            }
        });
    }

    const formOceny = document.getElementById('form-oceny');
    if(formOceny) {
        const checkboxPodpis = document.getElementById('zloz-podpis-uopz');
        const btnZapisz = document.getElementById('btn-zapisz-ocene');
        
        if (checkboxPodpis && btnZapisz) {
            checkboxPodpis.addEventListener('change', function() {
                const podpisDiv = document.getElementById('val-uopz-podpis');
                if (this.checked) {
                    btnZapisz.innerHTML = '<i class="bi bi-send"></i> Wyślij do Dziekanatu';
                    btnZapisz.className = 'btn btn-success';
                    document.getElementById('uopz-podpis-container').style.setProperty('display', 'flex', 'important');
                    podpisDiv.textContent = this.getAttribute('data-imienazwisko');
                } else {
                    btnZapisz.innerHTML = '<i class="bi bi-save"></i> Zapisz Kartę';
                    btnZapisz.className = 'btn btn-primary';
                    document.getElementById('uopz-podpis-container').style.setProperty('display', 'none', 'important');
                    podpisDiv.textContent = '';
                }
            });
        }

        formOceny.addEventListener('submit', function (e) {
            e.preventDefault();
            const zloz_podpis = document.getElementById('zloz-podpis-uopz').checked;

            if (zloz_podpis) {
                if (!confirm("Złożenie podpisu zatwierdzi oceny i prześle dokument do Dziekanatu. Kontynuować?")) return;
            }

            const data = {
                akcja: 'zapisz_ocene',
                ocena_uopz_param: document.getElementById('ocena-uopz-param-input').value,
                ocena_sprawozdania: document.getElementById('ocena-sprawozdania-input').value,
                ocena_uopz_opis: document.getElementById('ocena-uopz-opis-input').value,
                zloz_podpis: zloz_podpis
            };
            sendAction(data);
        });
    }
});
