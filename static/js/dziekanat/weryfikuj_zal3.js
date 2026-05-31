document.addEventListener('DOMContentLoaded', function() {
    const pathParts = window.location.pathname.split('/');
    const praktykaId = pathParts[pathParts.length - 1];

    function loadData() {
        fetch(`/api/dziekanat/weryfikuj_zal3/${praktykaId}`)
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
                    window.location.href = '/dziekanat/dashboard';
                    return;
                }

                document.getElementById('student-name').textContent = `${data.student.nr_albumu} - ${data.uzytkownik.imie} ${data.uzytkownik.nazwisko}`;
                
                if (data.dokument) {
                    document.getElementById('doc-status-badge').textContent = data.dokument.status;
                    
                    if(data.dokument.status === 'Zatwierdzone') {
                        document.getElementById('decyzja-actions').style.display = 'none';
                        document.getElementById('decyzja-info').style.display = 'block';
                    } else {
                        document.getElementById('decyzja-actions').style.display = 'block';
                        document.getElementById('decyzja-info').style.display = 'none';
                    }
                }

                // Wypełnianie danych studenta
                const imieNazwisko = `${data.uzytkownik.imie} ${data.uzytkownik.nazwisko.split(' (')[0]}`;
                document.getElementById('val-student-imienazwisko').textContent = imieNazwisko;
                document.getElementById('val-student-imienazwisko2').textContent = imieNazwisko;
                document.getElementById('val-student-album').textContent = data.student.nr_albumu;
                document.getElementById('val-student-studia').textContent = `inżynierskie ${data.student.tryb_studiow}`;
                document.getElementById('val-student-kierunek').textContent = data.student.kierunek;
                if(data.student.specjalnosc) document.getElementById('val-student-specjalnosc').textContent = data.student.specjalnosc;

                // Wypełnianie danych zakładu i praktyki
                if (data.porozumienie) {
                    const year = data.porozumienie.data_podpisania ? data.porozumienie.data_podpisania.split('-')[0] : new Date().getFullYear();
                    document.getElementById('val-porozumienie-id').textContent = `Porozumienie Nr ${data.porozumienie.id}/${year}`;
                    document.getElementById('val-porozumienie-data').textContent = data.porozumienie.data_podpisania || 'Brak';
                }
                
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

                if (data.karta) {
                    // Skierowanie
                    if(data.karta.podpis_dyrektora) document.getElementById('val-skierowanie-podpis').innerHTML = `${data.karta.podpis_dyrektora}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.skierowanie_data}</span>`;
                    
                    // ZOPZ Potwierdzenia
                    if(data.karta.podpis_zgloszenie) document.getElementById('val-zgloszenie-podpis').innerHTML = `${data.karta.podpis_zgloszenie}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.data_zgloszenia}</span>`;
                    if(data.karta.podpis_bhp) document.getElementById('val-bhp-podpis').innerHTML = `${data.karta.podpis_bhp}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.data_bhp}</span>`;
                    if(data.karta.zaswiadczenie_uwagi) document.getElementById('val-zaswiadczenie-uwagi').textContent = data.karta.zaswiadczenie_uwagi;
                    if(data.karta.podpis_zopz) document.getElementById('val-zaswiadczenie-podpis').innerHTML = `${data.karta.podpis_zopz}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.zaswiadczenie_data}</span>`;
                    
                    // Ocena ZOPZ
                    document.getElementById('val-zopz-ocena-param').textContent = data.karta.ocena_zopz_param || 'Brak';
                    document.getElementById('val-zopz-ocena-opis').textContent = data.karta.ocena_zopz_opis || 'Brak wpisu';
                    if(data.karta.podpis_zopz) document.getElementById('val-zopz-podpis').innerHTML = `${data.karta.podpis_zopz}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.ocena_zopz_data}</span>`;
                    
                    // Ocena UOPZ
                    document.getElementById('val-uopz-ocena-param').textContent = data.karta.ocena_uopz_param || 'Brak';
                    document.getElementById('val-uopz-sprawozdania').textContent = data.karta.ocena_sprawozdania || 'Brak';
                    document.getElementById('val-uopz-ocena-opis').textContent = data.karta.ocena_uopz_opis || 'Brak wpisu';
                    if(data.karta.podpis_uopz) document.getElementById('val-uopz-podpis').innerHTML = `${data.karta.podpis_uopz}<br><span style="font-size: 12px; font-family: Arial; color: #6c757d;">${data.karta.ocena_uopz_data}</span>`;
                }
            })
            .catch(err => console.error(err));
    }

    loadData();

    function sendAction(actionData) {
        fetch(`/api/dziekanat/weryfikuj_zal3/${praktykaId}`, {
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
            window.scrollTo(0,0);
        })
        .catch(err => console.error(err));
    }

    window.weryfikacjaZal3 = {
        zatwierdz: function() {
            if(confirm("Czy na pewno chcesz OSTATECZNIE ZATWIERDZIĆ Kartę Praktyk? Ta operacja jest nieodwracalna.")) {
                sendAction({ akcja: 'zatwierdz' });
            }
        },
        odrzuc: function() {
            const komentarz = document.getElementById('komentarz-dziekanatu').value;
            if(!komentarz) {
                alert("Musisz podać powód odrzucenia (uwagi).");
                return;
            }
            if(confirm("Czy cofnąć Kartę Praktyk do UOPZ celem poprawy?")) {
                sendAction({ akcja: 'odrzuc', komentarz_dziekanatu: komentarz });
            }
        }
    };
});
