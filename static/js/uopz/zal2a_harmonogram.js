document.addEventListener('DOMContentLoaded', function () {
    const pathParts = window.location.pathname.split('/');
    const studentId = pathParts[pathParts.length - 1];
    document.getElementById('back-link').href = `/uopz/teczka/${studentId}`;

    const efekty_definicje = [
        { kod: "01", desc: "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych." },
        { kod: "02", desc: "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce." },
        { kod: "03", desc: "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy." },
        { kod: "04", desc: "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka." },
        { kod: "05", desc: "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania, posługując się rozmaitymi źródłami literaturowymi i zasobami." },
        { kod: "06", desc: "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje zawodowe." },
        { kod: "07", desc: "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia." },
        { kod: "08", desc: "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy i zaproponować jego rozwiązanie." },
        { kod: "09", desc: "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności IT, stosując odpowiednie normy i standardy." },
        { kod: "10", desc: "Pracuje w zespole zajmującym się zawodowo branżą IT." },
        { kod: "11", desc: "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów." },
        { kod: "12", desc: "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje do realizacji zadania, jak i przekazać im w sposób zrozumiały opinie z zakresu informatyki." },
        { kod: "13", desc: "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki działalności informatyków, szczególnie te ekonomiczne i społeczne." }
    ];

    let rowCount = 0;

    function addHarmonogramRow(dzial = '', dni = '') {
        if (rowCount >= 13) {
            alert('Możesz dodać maksymalnie 13 wierszy (po jednym dla każdego z 13 efektów kształcenia).');
            return;
        }
        rowCount++;
        const tbody = document.querySelector('#tabela-harmonogram tbody');
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="align-middle">${rowCount}</td>
            <td><input type="text" class="form-control dzial-input" value="${dzial}" required></td>
            <td><input type="number" class="form-control dni-input" value="${dni}" min="1" required></td>
            <td><button type="button" class="btn btn-sm btn-outline-danger btn-remove"><i class="bi bi-trash"></i></button></td>
        `;
        tbody.appendChild(tr);

        tr.querySelector('.btn-remove').addEventListener('click', function () {
            tr.remove();
            rowCount--;
            updateTotal();
            document.getElementById('btn-add-row').style.display = 'inline-block';
        });
        tr.querySelector('.dni-input').addEventListener('input', updateTotal);
        updateTotal();

        if (rowCount >= 13) {
            document.getElementById('btn-add-row').style.display = 'none';
        }
    }

    function updateTotal() {
        let sum = 0;
        document.querySelectorAll('.dni-input').forEach(input => {
            sum += parseInt(input.value) || 0;
        });
        document.getElementById('total-days').textContent = sum;
    }

    document.getElementById('btn-add-row').addEventListener('click', () => addHarmonogramRow());

    const checkboxPodpis = document.getElementById('zloz_podpis');
    if (checkboxPodpis) {
        checkboxPodpis.addEventListener('change', function() {
            const podpisDiv = document.getElementById('podpis-uopz');
            if (this.checked) {
                podpisDiv.textContent = this.getAttribute('data-imienazwisko');
            } else {
                podpisDiv.textContent = 'Brak podpisu';
            }
        });
    }

    fetch(`/api/uopz/zal2a_harmonogram/${studentId}`)
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

            let fullName = `${data.uzytkownik.imie} ${data.uzytkownik.nazwisko}`;
            if (!fullName.includes(data.student.nr_albumu)) {
                fullName += ` (${data.student.nr_albumu})`;
            }
            document.getElementById('student-name').textContent = fullName;

            // Programy
            const progContainer = document.getElementById('programy-container');
            progContainer.innerHTML = '';
            efekty_definicje.forEach(ef => {
                const val = data.zapisane_programy[ef.kod] || '';
                progContainer.innerHTML += `
                    <tr>
                        <td class="bg-white border-dark p-3" style="font-size: 0.85em;">
                            <strong>[Efekt ${ef.kod}]</strong> ${ef.desc}
                        </td>
                        <td class="bg-white border-dark p-2">
                            <textarea class="form-control program-input h-100" style="min-height: 80px;" data-kod="${ef.kod}">${val}</textarea>
                        </td>
                    </tr>
                `;
            });

            // Harmonogram
            const pozycje = data.pozycje || [];
            if (pozycje.length > 0) {
                pozycje.forEach(p => addHarmonogramRow(p.dzial_komorka, p.planowana_liczba_dni));
            } else {
                addHarmonogramRow();
            }

            // Podpisy
            if (data.podpisy) {
                if (data.podpisy.podpis_uopz) {
                    document.getElementById('podpis-uopz').textContent = data.podpisy.podpis_uopz;
                    document.getElementById('data-uopz').textContent = data.podpisy.data_uopz;
                    document.getElementById('zloz_podpis').checked = true;
                    document.getElementById('zloz_podpis').disabled = true;
                }
                if (data.podpisy.podpis_zopz) {
                    document.getElementById('podpis-zopz').textContent = data.podpisy.podpis_zopz;
                    document.getElementById('data-zopz').textContent = data.podpisy.data_zopz;
                }
                if (data.podpisy.podpis_student) {
                    document.getElementById('podpis-student').textContent = data.podpisy.podpis_student;
                    document.getElementById('data-student').textContent = data.podpisy.data_student;
                }
            }

            const status = data.dokument ? data.dokument.status : null;
            const actionsDiv = document.getElementById('uopz-actions');
            actionsDiv.classList.remove('d-none');

            if (status === 'Draft_UOPZ' || status === 'Draft' || !status) {
                document.getElementById('btn-wyslij-zopz').classList.remove('d-none');
            } else if (status === 'Sent_back_to_UOPZ') {
                document.getElementById('btn-wyslij-student').classList.remove('d-none');
            } else {
                actionsDiv.classList.add('d-none');
                document.getElementById('zloz_podpis').disabled = true;
                document.getElementById('btn-add-row').style.display = 'none';
                document.querySelectorAll('.program-input, .dzial-input, .dni-input').forEach(el => el.disabled = true);
                document.querySelectorAll('.btn-remove').forEach(el => el.style.display = 'none');
            }
        })
        .catch(err => console.error(err));

    window.zapiszDecyzje = function (akcja) {
        if ((akcja === 'wyslij_do_studenta' || akcja === 'wyslij_do_zopz') && !document.getElementById('zloz_podpis').checked) {
            alert('Musisz zaznaczyć pole "Złóż podpis cyfrowy", aby wysłać dokument dalej.');
            return;
        }

        const programy = {};
        document.querySelectorAll('.program-input').forEach(el => {
            programy[el.getAttribute('data-kod')] = el.value;
        });

        const harmonogram = [];
        document.querySelectorAll('#tabela-harmonogram tbody tr').forEach(tr => {
            const dzial = tr.querySelector('.dzial-input').value;
            const dni = tr.querySelector('.dni-input').value;
            if (dzial && dni) {
                harmonogram.push({ dzial: dzial, dni: dni });
            }
        });

        fetch(`/api/uopz/zal2a_harmonogram/${studentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                akcja: akcja,
                programy: programy,
                harmonogram: harmonogram,
                zloz_podpis: document.getElementById('zloz_podpis') ? document.getElementById('zloz_podpis').checked : false
            })
        })
            .then(response => response.json())
            .then(data => {
                const alerts = document.getElementById('alerts-container');
                if (data.success) {
                    alerts.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    setTimeout(() => window.location.reload(), 2500);
                } else {
                    alerts.innerHTML = `<div class="alert alert-danger">${data.message || 'Błąd zapisu'}</div>`;
                }
                window.scrollTo(0, 0);
            })
            .catch(err => console.error(err));
    };
});
