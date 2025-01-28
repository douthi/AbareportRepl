
const sourceFields = [
    'ProjNr',
    'ProjName',
    'NAME',
    'VORNAME',
    'EMAIL',
    'TEL',
    'LAND',
    'PLZ',
    'ORT',
    'STREET',
    'HOUSE_NUMBER',
    'KDatum',
    'KSumme',
    'ADatum',
    'ASumme',
    'Status',
    'KdINR',
    'RootProj',
    'Name2',
    'Name3', 
    'ISOCode',
    'Status1',
    'Status2',
    'Status3',
    'Status4',
    'NDatum',
    'NSumme',
    'Person1',
    'INR',
    'KURZNA',
    'ZEILE1',
    'ZEILE2',
    'STAAT',
    'ANR_NR',
    'TEL2',
    'TELEX',
    'TELEFAX',
    'SPRACHE',
    'ASI_INR',
    'AKP_NR',
    'WWW',
    'AddressAddition',
    'StreetAddition',
    'PostOfficeBoxText',
    'PostOfficeBoxNumber',
    'ANR_GROUP'
];

function createMappingRow(existingMapping = null) {
    const row = document.createElement('div');
    row.className = 'mapping-row row g-3 align-items-center mb-2';

    row.innerHTML = `
        <div class="col-md-4">
            <select class="form-select source-field" required>
                <option value="">Select Source Field</option>
                ${sourceFields.map(field =>
                    `<option value="${field}" ${existingMapping && existingMapping.source === field ? 'selected' : ''}>${field}</option>`
                ).join('')}
            </select>
        </div>
        <div class="col-md-4">
            <select class="form-select target-field" required>
                <option value="">Select Pipedrive Field</option>
            </select>
        </div>
        <div class="col-md-3">
            <select class="form-select entity-type" required>
                <option value="organization" ${existingMapping && existingMapping.entity === 'organization' ? 'selected' : ''}>Organization</option>
                <option value="person" ${existingMapping && existingMapping.entity === 'person' ? 'selected' : ''}>Person</option>
                <option value="deal" ${existingMapping && existingMapping.entity === 'deal' ? 'selected' : ''}>Deal</option>
            </select>
        </div>
        <div class="col-md-1">
            <button type="button" class="btn btn-danger remove-mapping">×</button>
        </div>
    `;
    
    return row;
}

async function fetchPipedriveFields(company = 'uniska') {
    const response = await fetch(`/pipedrive-fields?company=${company}`);
    const fields = await response.json();
    pipedriveFields = fields;
    return fields;
}

function updateTargetFields(entityType, targetSelect) {
    targetSelect.innerHTML = '<option value="">Select Pipedrive Field</option>';
    const fields = pipedriveFields[entityType] || [];
    fields.forEach(field => {
        const option = document.createElement('option');
        option.value = field.key;
        option.textContent = field.name;
        targetSelect.appendChild(option);
    });
}

document.addEventListener('DOMContentLoaded', async function() {
    const container = document.getElementById('mappingContainer');
    const addButton = document.createElement('button');
    addButton.className = 'btn btn-primary mb-3';
    addButton.textContent = 'Add Mapping';
    container.parentElement.insertBefore(addButton, container);

    await fetchPipedriveFields();

    const mappingsResponse = await fetch('/uniska/field-mappings');
    const existingMappings = await mappingsResponse.json();
    
    if (existingMappings && existingMappings.length > 0) {
        existingMappings.forEach(mapping => {
            container.appendChild(createMappingRow(mapping));
            const row = container.lastElementChild;
            updateTargetFields(mapping.entity, row.querySelector('.target-field'));
            row.querySelector('.target-field').value = mapping.target;
        });
    } else {
        container.appendChild(createMappingRow());
    }

    container.addEventListener('change', (e) => {
        if (e.target.classList.contains('entity-type')) {
            const row = e.target.closest('.mapping-row');
            const targetSelect = row.querySelector('.target-field');
            updateTargetFields(e.target.value, targetSelect);
        }
    });

    addButton.addEventListener('click', () => {
        container.appendChild(createMappingRow());
    });

    container.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-mapping')) {
            e.target.closest('.mapping-row').remove();
        }
    });

    const saveButton = document.getElementById('saveMapping');
    saveButton.addEventListener('click', async () => {
        const mappings = Array.from(container.getElementsByClassName('mapping-row')).map(row => ({
            source: row.querySelector('.source-field').value,
            target: row.querySelector('.target-field').value,
            entity: row.querySelector('.entity-type').value
        }));

        const response = await fetch('/uniska/field-mappings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(mappings)
        });

        if (response.ok) {
            alert('Mappings saved successfully!');
        } else {
            alert('Error saving mappings');
        }
    });
});
