// Global variable to store Pipedrive fields
let pipedriveFields = {
    organization: [],
    person: [],
    deal: []
};

async function fetchPipedriveFields() {
    try {
        const response = await fetch('/pipedrive-fields?company=' + company);
        if (response.ok) {
            pipedriveFields = await response.json();
            // Load existing mappings after fields are fetched
            loadExistingMappings();
        } else {
            console.error('Failed to fetch Pipedrive fields');
            alert('Failed to fetch Pipedrive fields');
        }
    } catch (error) {
        console.error('Error fetching Pipedrive fields:', error);
        alert('Error fetching Pipedrive fields');
    }
}

function createMappingRow(mapping = null) {
    const row = document.createElement('div');
    row.className = 'mapping-row row g-3 align-items-center mb-3';

    const sourceFieldSelect = `<select class="form-select source-field">
                <option value="">Select Source Field</option>
            </select>`;


    row.innerHTML = `
        <div class="col-md-3">
            ${sourceFieldSelect}
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
    const sourceSelect = row.querySelector('.source-field');

    entitySelect.addEventListener('change', () => {
        updateTargetFields(targetSelect, entitySelect.value);
    });

    row.querySelector('.remove-mapping').addEventListener('click', () => {
        row.remove();
    });

    // If mapping data is provided, set the values
    if (mapping) {
        sourceSelect.value = mapping.source;
        row.querySelector('.entity-type').value = mapping.entity;
        updateTargetFields(targetSelect, mapping.entity);
        setTimeout(() => {
            targetSelect.value = mapping.target;
        }, 100);
    }

    //Populate source field options dynamically
    populateSourceFields(sourceSelect);

    return row;
}

function populateSourceFields(selectElement){
    for (const entityType in pipedriveFields) {
        pipedriveFields[entityType].forEach(field => {
            const option = document.createElement('option');
            option.value = field.key;
            option.textContent = field.name;
            selectElement.appendChild(option);
        });
    }
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

async function saveMappings() {
    const mappings = Array.from(document.querySelectorAll('.mapping-row')).map(row => ({
        source: row.querySelector('.source-field').value,
        target: row.querySelector('.target-field').value,
        entity: row.querySelector('.entity-type').value
    })).filter(mapping => mapping.source && mapping.target && mapping.entity);

    try {
        const response = await fetch(`/${company}/field-mappings`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(mappings)
        });

        if (response.ok) {
            alert('Mappings saved successfully');
        } else {
            alert('Failed to save mappings');
        }
    } catch (error) {
        console.error('Error saving mappings:', error);
        alert('Error saving mappings');
    }
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', () => {
    fetchPipedriveFields();

    // Add event listeners
    document.getElementById('addMapping').addEventListener('click', () => {
        document.getElementById('fieldMappings').appendChild(createMappingRow());
    });

    document.getElementById('saveMapping').addEventListener('click', saveMappings);
});