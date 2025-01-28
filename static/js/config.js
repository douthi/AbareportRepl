
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
            updateAllTargetFields();
        }
    } catch (error) {
        console.error('Error fetching Pipedrive fields:', error);
    }
}

function createMappingRow() {
    const template = document.querySelector('.mapping-row');
    const newRow = template.cloneNode(true);
    newRow.querySelector('.target-field').disabled = true;
    return newRow;
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

function updateAllTargetFields() {
    document.querySelectorAll('.mapping-row').forEach(row => {
        const entitySelect = row.querySelector('.entity-type');
        const targetSelect = row.querySelector('.target-field');
        updateTargetFields(targetSelect, entitySelect.value);
    });
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('fieldMappings');
    
    // Add new mapping row
    document.getElementById('addMapping').addEventListener('click', () => {
        container.appendChild(createMappingRow());
    });
    
    // Remove mapping row
    container.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-mapping') || e.target.closest('.remove-mapping')) {
            const row = e.target.closest('.mapping-row');
            if (container.querySelectorAll('.mapping-row').length > 1) {
                row.remove();
            }
        }
    });
    
    // Update target fields when entity type changes
    container.addEventListener('change', (e) => {
        if (e.target.classList.contains('entity-type')) {
            const row = e.target.closest('.mapping-row');
            const targetSelect = row.querySelector('.target-field');
            updateTargetFields(targetSelect, e.target.value);
        }
    });
});
