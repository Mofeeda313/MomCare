document.addEventListener('DOMContentLoaded', () => {
    // 1. Live Health Check Button on Home Page
    const testBtn = document.getElementById('test-connection-btn');
    const healthResult = document.getElementById('health-result');

    if (testBtn && healthResult) {
        testBtn.addEventListener('click', async () => {
            healthResult.textContent = 'Checking connection...';
            healthResult.style.color = '#78857D';

            try {
                const response = await fetch('/health');
                const data = await response.json();

                if (response.ok && data.status === 'healthy') {
                    healthResult.textContent = `[OK] Flask server & SQLite database reachable (${new Date().toLocaleTimeString()})`;
                    healthResult.style.color = '#073528';
                } else {
                    healthResult.textContent = `[Error] ${data.error || 'Unexpected status'}`;
                    healthResult.style.color = '#991B1B';
                }
            } catch (err) {
                healthResult.textContent = `[Error] Connection failed: ${err.message}`;
                healthResult.style.color = '#991B1B';
            }
        });
    }

    // 2. Password Visibility Toggle (Show / Hide Password with professional SVGs)
    const toggleButtons = document.querySelectorAll('.btn-toggle-password');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            if (targetInput) {
                if (targetInput.type === 'password') {
                    targetInput.type = 'text';
                    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
                    btn.setAttribute('title', 'Hide password');
                } else {
                    targetInput.type = 'password';
                    btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
                    btn.setAttribute('title', 'Show password');
                }
            }
        });
    });

    // 3. Client-Side Form Validation (matching passwords)
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            const password = document.getElementById('password')?.value;
            const confirmPassword = document.getElementById('confirm_password')?.value;

            if (password && confirmPassword && password !== confirmPassword) {
                e.preventDefault();
                alert('Passwords do not match. Please ensure both password fields are identical.');
            }
        });
    }
});
