(function() {
    'use strict';
    const loginForm = document.querySelector('.login-form-element');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            if (!loginForm.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            loginForm.classList.add('was-validated');
        }, false);
    }
})();