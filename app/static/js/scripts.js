// app/static/js/scripts.js

document.addEventListener('DOMContentLoaded', () => {
    const flashMessages = window.flashMessages || [];

    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            const toastContainer = document.getElementById('toast-container');
            const toastEl = document.createElement('div');
            toastEl.className = 'toast align-items-center text-bg-info border-0';
            toastEl.role = 'alert';
            toastEl.ariaLive = 'assertive';
            toastEl.ariaAtomic = 'true';
            toastEl.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;
            toastContainer.appendChild(toastEl);
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
        });
    }
});
s
