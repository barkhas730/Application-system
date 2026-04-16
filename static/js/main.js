// Diplom App - Main JavaScript

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss alerts
    setTimeout(function () {
        document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
            if (alert && bootstrap && bootstrap.Alert) {
                var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) bsAlert.close();
            }
        });
    }, 5000);

    // Confirm dialogs for dangerous actions
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Restore theme on load
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', saved);
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.className = saved === 'dark' ? 'bi bi-sun me-2' : 'bi bi-moon-stars me-2';
    }
});

// Toast helper
function showToast(message, type) {
    type = type || 'success';
    var container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    var toastEl = document.createElement('div');
    toastEl.className = 'toast align-items-center text-bg-' + type + ' border-0 show';
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML =
        '<div class="d-flex"><div class="toast-body">' + message + '</div>' +
        '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
    container.appendChild(toastEl);
    setTimeout(function () { toastEl.remove(); }, 4000);
}
