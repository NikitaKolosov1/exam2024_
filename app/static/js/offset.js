    document.getElementById('toggleRegistration').addEventListener('click', function() {
        let loginForm = document.getElementById('loginForm');
        let registrationForm = document.getElementById('registrationForm');

        let toggleRegistrationForm = document.getElementById('toggleRegistration');
        let toggleLoginForm = document.getElementById('toggleLogin');
        
        toggleRegistrationForm.style.display = 'none';
        toggleLoginForm.style.display = 'block';

        loginForm.style.display = 'none';
        registrationForm.style.display = 'block';
    });
    document.getElementById('toggleLogin').addEventListener('click', function() {
        var loginForm = document.getElementById('loginForm');
        var registrationForm = document.getElementById('registrationForm');
        
        let toggleRegistrationForm = document.getElementById('toggleRegistration');
        let toggleLoginForm = document.getElementById('toggleLogin');
        
        toggleRegistrationForm.style.display = 'block';
        toggleLoginForm.style.display = 'none';

        loginForm.style.display = 'block';
        registrationForm.style.display = 'none';
    });