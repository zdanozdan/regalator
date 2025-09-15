document.addEventListener('_htmx:afterRequest', function(event) {        
    if (event.target.id.includes('location-row')) {

        const barcodeField = document.querySelector('.barcode-field');
        const barcodeInput = barcodeField ? barcodeField.querySelector('input') : null;

        if (!barcodeField || !barcodeInput) return;

        // Focus on barcode field when the content is swapped in
        //barcodeInput.focus();

        // Add event listener for barcode scanned (anonymous)
        document.addEventListener('barcode:scanned', function(e) {
            const code = e.detail && e.detail.code ? e.detail.code : '';
            if (!code) return;
            // Ignore codes that contain Enter characters
            barcodeInput.value = code;
            //barcodeInput.dispatchEvent(new Event('input', { bubbles: true }));
            //barcodeInput.focus();
            // Show green success alert above the input and auto-hide after 5s
            showBootstrapAlert('success', `Zeskanowano: ${code}`);
            setTimeout(function() { removeBootstrapAlert(); }, 5000);
        });
    }
});

document.addEventListener('barcode:scanned', function(event) {        
    const barcodeFields = document.querySelectorAll('.barcode-field');
    if (barcodeFields) {
        barcodeFields.forEach(field => {
            field.value = event.detail.code;
        });
    }
    showBootstrapAlert('success', `Zeskanowano: ${event.detail.code}`);
    setTimeout(function() { removeBootstrapAlert(); }, 5000);
});

// Helper functions for Bootstrap alerts
function showBootstrapAlert(type, message) {
    // Remove any existing alerts first
    removeBootstrapAlert();
    
    // Create the alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.id = 'barcode-alert';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find the barcode field and insert the alert above it
    const barcodeFields = document.querySelectorAll('.barcode-field');
    barcodeFields.forEach(field => {
        field.parentNode.insertBefore(alertDiv, field);
    });
}

function removeBootstrapAlert() {
    const existingAlert = document.getElementById('barcode-alert');
    if (existingAlert) {
        existingAlert.remove();
    }
}

// Helper for Bootstrap 5 toast
function showBsToast(message, delay, variant) {
    try {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        const bgClass = (variant || 'success') === 'success' ? 'text-bg-success' : 'text-bg-dark';
        toast.className = `toast align-items-center ${bgClass} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        container.appendChild(toast);

        if (window.bootstrap && window.bootstrap.Toast) {
            const toastInstance = new window.bootstrap.Toast(toast, { delay: delay || 3000 });
            toastInstance.show();
            toast.addEventListener('hidden.bs.toast', function() { toast.remove(); });
        } else {
            toast.classList.add('show');
            setTimeout(function() { toast.classList.remove('show'); toast.remove(); }, delay || 3000);
        }
    } catch (err) {
        if (console && console.warn) console.warn('Toast error', err);
    }
}

document.addEventListener('barcode:scanned', (e) => {
    const code = e.detail.code;
    showBsToast(`Zeskanowano: ${code}`, 3000, 'success');
});


// Barcode scanner detection utility
// Buffers characters until Enter is received, then dispatches a custom event with the barcode
// Usage: window.initBarcodeScanner({ eventName: 'barcode:scanned', timeoutMs: 300 })
(function() {
    function initBarcodeScanner(options) {
        const settings = {
            eventName: (options && options.eventName) || 'barcode:scanned',
            timeoutMs: (options && options.timeoutMs) || 300,
            allowWhileTypingInInputs: (options && options.allowWhileTypingInInputs) || true
        };

        let buffer = '';
        let lastKeyTime = 0;
        let clearTimer = null;

        function clearBuffer() {
            buffer = '';
            lastKeyTime = 0;
            if (clearTimer) {
                clearTimeout(clearTimer);
                clearTimer = null;
            }
        }

        function scheduleClear() {
            if (clearTimer) {
                clearTimeout(clearTimer);
            }
            clearTimer = setTimeout(clearBuffer, settings.timeoutMs);
        }

        document.addEventListener('keydown', function(e) {
            // Ignore modifier keys
            if (e.ctrlKey || e.metaKey || e.altKey) return;

            // Optionally ignore keystrokes when typing in inputs/textareas/contenteditable
            const target = e.target;
            const isEditable = target && (
                target.tagName === 'INPUT' ||
                target.tagName === 'TEXTAREA' ||
                target.isContentEditable === true
            );
            // If not allowed during typing and user is in an editable element, skip buffering
            if (!settings.allowWhileTypingInInputs && isEditable) {
                return;
            }

            const now = Date.now();
            if (lastKeyTime && now - lastKeyTime > settings.timeoutMs) {
                // Too much time passed, reset the buffer
                clearBuffer();
            }
            lastKeyTime = now;

            if (e.key === 'Enter') {
                if (buffer.length > 0) {
                    const code = buffer;
                    clearBuffer();
                    const event = new CustomEvent(settings.eventName, { detail: { code } });
                    document.dispatchEvent(event);
                }
                return; // Do not add Enter to buffer
            }

            // Only buffer visible single-character keys
            if (e.key && e.key.length === 1) {
                buffer += e.key;
                scheduleClear();
            }
        });
    }

    // Expose globally
    window.initBarcodeScanner = initBarcodeScanner;
})();

document.addEventListener('DOMContentLoaded', function() {
    if (window && window.initBarcodeScanner) {
        window.initBarcodeScanner({ eventName: 'barcode:scanned', timeoutMs: 200 });
    }
});