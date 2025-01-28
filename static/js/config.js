// Global variable to store Pipedrive fields
let pipedriveFields = {
    organization: [],
    person: [],
    deal: []
};

// Function to toggle password visibility
function togglePassword(inputId, iconId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);

    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Function to fetch Pipedrive fields
async function fetchPipedriveFields(company) {
    try {
        const response = await fetch(`/pipedrive-fields?company=${company}`);
        if (!response.ok) {
            throw new Error('Failed to fetch Pipedrive fields');
        }
        const fields = await response.json();
        return fields;
    } catch (error) {
        console.error('Error fetching Pipedrive fields:', error);
        throw error;
    }
}

function createMappingRow(mapping = null) {
    const row = document.createElement('div');
    row.className = 'mapping-row row g-3 align-items-center mb-3';

    row.innerHTML = `
        <div class="col-md-3">
            <select class="form-select source-field">
                <option value="">Select Source Field</option>
                <option value="NAME">NAME</option>
                <option value="VORNAME">VORNAME</option>
                <option value="EMAIL">EMAIL</option>
                <option value="TEL">TEL</option>
                <option value="LAND">LAND</option>
                <option value="PLZ">PLZ</option>
                <option value="ORT">ORT</option>
                <option value="STREET">STREET</option>
                <option value="HOUSE_NUMBER">HOUSE_NUMBER</option>
                <option value="ProjName">ProjName</option>
                <option value="KSumme">KSumme</option>
                <option value="Status">Status</option>
            </select>
        </div>
        <div class="col-md-3">
            <select class="form-select entity-type">
                <option value="">Select Entity Type</option>
                <option value="organization">Organization</option>
                <option value="person">Person</option>
                <option value="deal">Deal</option>
            </select>
        </div>
        <div class="col-md-4">
            <select class="form-select target-field" disabled>
                <option value="">Select Pipedrive Field</option>
            </select>
        </div>
        <div class="col-md-2">
            <button class="btn btn-danger remove-mapping">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;

    // Add event listeners
    const entitySelect = row.querySelector('.entity-type');
    const targetSelect = row.querySelector('.target-field');

    entitySelect.addEventListener('change', () => {
        updateTargetFields(targetSelect, entitySelect.value);
    });

    row.querySelector('.remove-mapping').addEventListener('click', () => {
        row.remove();
    });

    // If mapping data is provided, set the values
    if (mapping) {
        row.querySelector('.source-field').value = mapping.source;
        row.querySelector('.entity-type').value = mapping.entity;
        updateTargetFields(targetSelect, mapping.entity);
        setTimeout(() => {
            targetSelect.value = mapping.target;
        }, 100);
    }

    return row;
}

function updateTargetFields(targetSelect, entityType) {
    targetSelect.disabled = !entityType;
    targetSelect.innerHTML = '<option value="">Select Pipedrive Field</option>';

    if (entityType && pipedriveFields[entityType]) {
        pipedriveFields[entityType].forEach(field => {
            const option = document.createElement('option');
            option.value = field.key;
            option.textContent = field.name;
            targetSelect.appendChild(option);
        });
    }
}

async function loadExistingMappings() {
    try {
        const response = await fetch(`/${company}/field-mappings`);
        const mappings = await response.json();
        const container = document.getElementById('fieldMappings');
        container.innerHTML = '';

        if (mappings && mappings.length) {
            mappings.forEach(mapping => {
                container.appendChild(createMappingRow(mapping));
            });
        } else {
            container.appendChild(createMappingRow());
        }
    } catch (error) {
        console.error('Error loading existing mappings:', error);
    }
}

// Function to save field mappings
async function saveFieldMappings(mappings) {
    try {
        const response = await fetch('/field-mappings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(mappings)
        });
        if (!response.ok) {
            throw new Error('Failed to save field mappings');
        }
        return await response.json();
    } catch (error) {
        console.error('Error saving field mappings:', error);
        throw error;
    }
}


// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', async () => {
    // Add event listeners
    document.getElementById('fetchFields').addEventListener('click', async () => {
        try {
            pipedriveFields = await fetchPipedriveFields(company); // Update to use new function
            loadExistingMappings();
        } catch (error) {
            console.error("Error fetching and loading fields:", error);
            alert("Error fetching and loading fields. Check console for details.");
        }
    });

    document.getElementById('addMapping').addEventListener('click', () => {
        document.getElementById('fieldMappings').appendChild(createMappingRow());
    });

    document.getElementById('saveMapping').addEventListener('click', async () => {
        const mappings = Array.from(document.querySelectorAll('.mapping-row')).map(row => ({
            source: row.querySelector('.source-field').value,
            target: row.querySelector('.target-field').value,
            entity: row.querySelector('.entity-type').value
        })).filter(mapping => mapping.source && mapping.target && mapping.entity);

        try {
            const result = await saveFieldMappings(mappings); // Update to use new function
            alert('Mappings saved successfully');
        } catch (error) {
            console.error('Error saving mappings:', error);
            alert('Error saving mappings. Check console for details.');
        }
    });

    // Add initial mapping row
    document.getElementById('fieldMappings').appendChild(createMappingRow());

    // Add togglePassword functionality (assuming relevant elements exist)
    document.getElementById('showPassword').addEventListener('click', () => togglePassword('passwordInput', 'passwordIcon'));

});