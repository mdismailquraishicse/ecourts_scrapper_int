function fetchStates() {
    fetch("/get-states")
        .then(response => response.json())
        .then(data => {
            const stateSelect = document.getElementById("state");
            stateSelect.innerHTML = `<option value="">--Select State--</option>`;
            data.states.forEach(s => {
                stateSelect.innerHTML += `<option value="${s}">${s}</option>`;
            });
        })
        .catch(error => console.error("Error fetching states:", error));
}

function fetchDistricts() {
    const state = document.getElementById("state").value;
    if (!state) return;

    fetch(`/get-districts/${state}`)
        .then(response => response.json())
        .then(data => {
            const districtSelect = document.getElementById("district");
            districtSelect.innerHTML = `<option value="">--Select District--</option>`;
            data.districts.forEach(d => {
                districtSelect.innerHTML += `<option value="${d}">${d}</option>`;
            });
            document.getElementById("complex").innerHTML = `<option value="">--Select Complex--</option>`;
            document.getElementById("court").innerHTML = `<option value="">--Select Court--</option>`;
        });
}

function fetchComplexes() {
    const state = document.getElementById("state").value;
    const district = document.getElementById("district").value;
    if (!state || !district) return;

    fetch(`/get-complexes/${state}/${district}`)
        .then(response => response.json())
        .then(data => {
            const complexSelect = document.getElementById("complex");
            complexSelect.innerHTML = `<option value="">--Select Complex--</option>`;
            data.complexes.forEach(c => {
                complexSelect.innerHTML += `<option value="${c}">${c}</option>`;
            });
            document.getElementById("court").innerHTML = `<option value="">--Select Court--</option>`;
        });
}

function fetchCourts() {
    const state = document.getElementById("state").value;
    const district = document.getElementById("district").value;
    const complexName = document.getElementById("complex").value;
    if (!state || !district || !complexName) return;

    fetch(`/get-courts/${state}/${district}/${complexName}`)
        .then(response => response.json())
        .then(data => {
            const courtSelect = document.getElementById("court");
            courtSelect.innerHTML = `<option value="">--Select Court--</option>`;
            data.courts.forEach(c => {
                courtSelect.innerHTML += `<option value="${c}">${c}</option>`;
            });
        });
}

function setupButtons() {
    const criminalBtn = document.getElementById("criminalBtn");
    const civilBtn = document.getElementById("civilBtn");

    function submitAction(type) {
        const state = document.getElementById("state").value;
        const district = document.getElementById("district").value;
        const complex = document.getElementById("complex").value;
        const court = document.getElementById("court").value;
        const dateInput = document.getElementById("causeDate").value; // YYYY-MM-DD

        if (!state || !district || !complex || !court || !dateInput) {
            alert("Please select all dropdowns and date!");
            return;
        }

        // Reformat date to DD-MM-YYYY
        const parts = dateInput.split("-");
        const date = `${parts[2]}-${parts[1]}-${parts[0]}`;

        fetch(`/submit-${type}/${state}/${district}/${complex}/${court}/${date}`)
            .then(res => res.json())
            .then(data => alert(data.status))
            .catch(err => console.error(err));
    }

    criminalBtn.addEventListener("click", () => submitAction("criminal"));
    civilBtn.addEventListener("click", () => submitAction("civil"));
}

document.addEventListener("DOMContentLoaded", () => {
    fetchStates();
    setupButtons();
});