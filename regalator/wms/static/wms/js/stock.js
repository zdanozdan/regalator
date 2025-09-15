function addStockRow() {
    const prefix = 'stock';
    const totalFormsInput = document.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);
    if (!totalFormsInput) return;
    const index = parseInt(totalFormsInput.value, 10);
    const tmpl = document.getElementById('stock-empty-form');
    if (!tmpl) return;
    const html = tmpl.innerHTML.replace(/__prefix__/g, index);
    document.getElementById('stock-formset-rows').insertAdjacentHTML('beforeend', html);
    totalFormsInput.value = index + 1;
}

function markDelete(button) {
    const row = button.closest('[data-form-row]');
    if (!row) return;
    const delInput = row.querySelector('input[id$="-DELETE"]');
    if (delInput) {
        delInput.checked = true;
        row.style.display = 'none';
    }
}