document.addEventListener('DOMContentLoaded', function () {
    const pathParts = window.location.pathname.split('/');
    const studentId = pathParts[pathParts.length - 1];
    document.getElementById('back-link').href = `/zopz/teczka/${studentId}`;

    function loadData() {
        fetch(`/api/zopz/zal3_karta/${studentId}`)
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
                    window.location.href = '/zopz/dashboard';
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
                if (data.student.specjalnosc) document.getElementById('val-student-specjalnosc').textContent = data.student.specjalnosc;

                // Wypełnianie danych UOPZ
                if (data.uopz) {
                    const uopzDane = `${data.uopz.imie} ${data.uopz.nazwisko}`;
                    document.getElementById('val-uopz-dane').textContent = uopzDane;
                }

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

                if (data.karta) {
                    if (data.karta.podpis_dyrektora) {
                        document.getElementById('val-skierowanie-podpis').innerHTML = `${data.karta.podpis_dyrektora}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.skierowanie_data}</span>`;
                    }

                    // Zgłoszenie
                    if (data.karta.podpis_zgloszenie) {
                        const zgActions = document.getElementById('zgloszenie-actions');
                        if (zgActions) zgActions.style.display = 'none';
                        document.getElementById('val-zgloszenie-podpis').innerHTML = `${data.karta.podpis_zgloszenie}`;
                    } else {
                        const zgActions = document.getElementById('zgloszenie-actions');
                        if (zgActions) zgActions.style.display = 'block';
                    }

                    // BHP
                    if (data.karta.podpis_bhp) {
                        const bhpActions = document.getElementById('bhp-actions');
                        if (bhpActions) bhpActions.style.display = 'none';
                        document.getElementById('val-bhp-podpis').innerHTML = `${data.karta.podpis_bhp}`;
                    } else {
                        const bhpActions = document.getElementById('bhp-actions');
                        if (bhpActions) bhpActions.style.display = 'block';
                    }

                    if (data.karta.ocena_uopz_param) {
                        document.getElementById('val-uopz-ocena-param').textContent = data.karta.ocena_uopz_param;
                        document.getElementById('val-uopz-ocena-opis').textContent = data.karta.ocena_uopz_opis || 'Brak wpisu';
                        document.getElementById('val-ocena-sprawozdania').textContent = data.karta.ocena_sprawozdania || 'Brak wpisu';
                        if (data.karta.podpis_uopz) {
                            const podpisUopz = `${data.karta.podpis_uopz}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.ocena_uopz_data}</span>`;
                            document.getElementById('val-uopz-podpis').innerHTML = podpisUopz;
                        }
                    }

                    // Ocena ZOPZ i formularz
                    if (data.karta.podpis_zopz) {
                        document.getElementById('zopz-form-actions').style.display = 'none';

                        document.getElementById('val-zaswiadczenie-podpis').innerHTML = `${data.karta.podpis_zopz}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.zaswiadczenie_data}</span>`;

                        document.getElementById('ocena-zopz-param-input').style.display = 'none';
                        document.getElementById('ocena-zopz-param-view').style.display = 'block';
                        document.getElementById('ocena-zopz-param-view').textContent = data.karta.ocena_zopz_param;

                        document.getElementById('ocena-zopz-opis-input').style.display = 'none';
                        document.getElementById('ocena-zopz-opis-view').style.display = 'block';
                        document.getElementById('ocena-zopz-opis-view').textContent = data.karta.ocena_zopz_opis || 'Brak wpisu';

                        document.getElementById('zaswiadczenie-uwagi-input').style.display = 'none';
                        document.getElementById('zaswiadczenie-uwagi-view').style.display = 'block';
                        document.getElementById('zaswiadczenie-uwagi-view').textContent = data.karta.zaswiadczenie_uwagi || 'Brak uwag';

                        document.getElementById('zopz-podpis-container').style.setProperty('display', 'flex', 'important');
                        document.getElementById('val-zopz-podpis').innerHTML = `${data.karta.podpis_zopz}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.ocena_zopz_data}</span>`;
                    } else {
                        document.getElementById('zopz-form-actions').style.display = 'block';

                        if (data.karta.ocena_zopz_param) document.getElementById('ocena-zopz-param-input').value = data.karta.ocena_zopz_param;
                        if (data.karta.ocena_zopz_opis) document.getElementById('ocena-zopz-opis-input').value = data.karta.ocena_zopz_opis;
                        if (data.karta.zaswiadczenie_uwagi) document.getElementById('zaswiadczenie-uwagi-input').value = data.karta.zaswiadczenie_uwagi;
                    }
                }
            })
            .catch(err => console.error(err));
    }

    loadData();

    function sendAction(actionData) {
        fetch(`/api/zopz/zal3_karta/${studentId}`, {
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

    window.zal3Zopz = {
        potwierdzZgloszenie: function () {
            const chk = document.getElementById('chk-podpis-zgloszenie');
            if (!chk || !chk.checked) {
                alert("Musisz złożyć podpis elektroniczny, aby zatwierdzić zgłoszenie.");
                return;
            }
            if (confirm("Potwierdzasz zgłoszenie się studenta?")) {
                sendAction({ akcja: 'potwierdz_zgloszenie', zloz_podpis: true });
            }
        },
        potwierdzBhp: function () {
            const chk = document.getElementById('chk-podpis-bhp');
            if (!chk || !chk.checked) {
                alert("Musisz złożyć podpis elektroniczny, aby zatwierdzić BHP.");
                return;
            }
            if (confirm("Potwierdzasz odbycie szkolenia BHP przez studenta?")) {
                sendAction({ akcja: 'potwierdz_bhp', zloz_podpis: true });
            }
        }
    };

    const chkZgloszenie = document.getElementById('chk-podpis-zgloszenie');
    if (chkZgloszenie) {
        chkZgloszenie.addEventListener('change', function () {
            const podpisDiv = document.getElementById('val-zgloszenie-podpis');
            if (this.checked) {
                podpisDiv.textContent = this.getAttribute('data-imienazwisko');
            } else {
                podpisDiv.textContent = 'Brak podpisu';
            }
        });
    }

    const chkBhp = document.getElementById('chk-podpis-bhp');
    if (chkBhp) {
        chkBhp.addEventListener('change', function () {
            const podpisDiv = document.getElementById('val-bhp-podpis');
            if (this.checked) {
                podpisDiv.textContent = this.getAttribute('data-imienazwisko');
            } else {
                podpisDiv.textContent = 'Brak podpisu';
            }
        });
    }

    const formOceny = document.getElementById('form-oceny-zopz');
    if (formOceny) {
        const checkboxPodpis = document.getElementById('zloz-podpis-zopz');
        const btnZapisz = document.getElementById('btn-zapisz-ocene');

        if (checkboxPodpis && btnZapisz) {
            checkboxPodpis.addEventListener('change', function () {
                const podpisDiv = document.getElementById('val-zopz-podpis');
                const zaswiadczeniePodpisDiv = document.getElementById('val-zaswiadczenie-podpis');
                if (this.checked) {
                    btnZapisz.innerHTML = '<i class="bi bi-send"></i> Wyślij do Uczelni';
                    btnZapisz.className = 'btn btn-success';
                    document.getElementById('zopz-podpis-container').style.setProperty('display', 'flex', 'important');
                    const imienazwisko = this.getAttribute('data-imienazwisko');
                    podpisDiv.textContent = imienazwisko;
                    if (zaswiadczeniePodpisDiv) zaswiadczeniePodpisDiv.textContent = imienazwisko;
                } else {
                    btnZapisz.innerHTML = '<i class="bi bi-save"></i> Zapisz Kartę';
                    btnZapisz.className = 'btn btn-primary';
                    document.getElementById('zopz-podpis-container').style.setProperty('display', 'none', 'important');
                    podpisDiv.textContent = '';
                    if (zaswiadczeniePodpisDiv) zaswiadczeniePodpisDiv.textContent = '';
                }
            });
        }

        formOceny.addEventListener('submit', function (e) {
            e.preventDefault();
            const zloz_podpis = document.getElementById('zloz-podpis-zopz').checked;

            let akcja = 'zapisz_ocene';
            if (zloz_podpis) {
                if (!confirm("Zaznaczono e-podpis. Dokument zostanie ostatecznie zatwierdzony przez Zakład Pracy i odesłany na Uczelnię. Kontynuować?")) return;
                akcja = 'wyslij_do_uczelni';
            }

            const zaswiadczenieUwagiInput = document.getElementById('zaswiadczenie-uwagi-input');

            const data = {
                akcja: akcja,
                ocena_zopz_param: document.getElementById('ocena-zopz-param-input').value,
                ocena_zopz_opis: document.getElementById('ocena-zopz-opis-input').value,
                zaswiadczenie_uwagi: zaswiadczenieUwagiInput ? zaswiadczenieUwagiInput.value : ''
            };
            sendAction(data);
        });
    }
});
