document.addEventListener('DOMContentLoaded', () => {
    // Password Visibility Toggle (Show / Hide Password with professional SVGs)
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

    // -------------------------------------------------------------------------
    // 4. Side Navigation Drawer Controller (Mobile & Desktop)
    // -------------------------------------------------------------------------
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarDrawer = document.getElementById('momcare-sidebar');
    const sidebarBackdrop = document.getElementById('sidebar-backdrop');
    const sidebarClose = document.getElementById('sidebar-close');

    function openSidebar() {
        if (!sidebarDrawer) return;
        sidebarDrawer.classList.add('open');
        sidebarDrawer.setAttribute('aria-hidden', 'false');
        if (sidebarBackdrop) sidebarBackdrop.classList.add('active');
        if (sidebarToggle) sidebarToggle.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (!sidebarDrawer) return;
        sidebarDrawer.classList.remove('open');
        sidebarDrawer.setAttribute('aria-hidden', 'true');
        if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
        if (sidebarToggle) sidebarToggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            if (sidebarDrawer && sidebarDrawer.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }

    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', closeSidebar);
    }

    // Outside click fallback: Close if clicking anywhere outside sidebar drawer
    document.addEventListener('click', (e) => {
        if (sidebarDrawer && sidebarDrawer.classList.contains('open')) {
            if (!sidebarDrawer.contains(e.target) && sidebarToggle && !sidebarToggle.contains(e.target)) {
                closeSidebar();
            }
        }
    });

    // Keyboard support: Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebarDrawer && sidebarDrawer.classList.contains('open')) {
            closeSidebar();
        }
    });

    // -------------------------------------------------------------------------
    // 5. Mother Dashboard View Navigation (Section switching without scroll)
    // -------------------------------------------------------------------------
    window.switchDashboardView = function(viewKey) {
        const overviewSection = document.getElementById('dashboard-overview-container');
        const childrenSection = document.getElementById('registered-children-section');
        const vaccinationSection = document.getElementById('vaccination-management-section');
        const growthSection = document.getElementById('growth-monitoring-section');
        const wellnessSection = document.getElementById('wellness-section');
        const communitySection = document.getElementById('community-section');
        const consultationSection = document.getElementById('consultation-section');
        const infoContainer = document.getElementById('information-panels-container');
        const viewBar = document.getElementById('dashboard-view-bar');
        const viewTitle = document.getElementById('dashboard-view-title');

        if (!overviewSection) {
            return;
        }

        const sections = [
            overviewSection,
            childrenSection,
            vaccinationSection,
            growthSection,
            infoContainer
        ].filter(Boolean);

        // Update active highlight in sidebar
        document.querySelectorAll('.sidebar-nav-item').forEach(el => {
            const sec = el.getAttribute('data-section');
            if (sec) {
                el.classList.toggle('active', sec === viewKey || (viewKey === 'all' && sec === 'overview'));
            }
        });

        if (viewKey === 'overview') {
            // Show overview banner & stats, hide detailed lists
            sections.forEach(s => s.style.display = 'none');
            overviewSection.style.display = 'block';
            if (infoContainer) {
                infoContainer.style.display = 'grid';
                if (wellnessSection) wellnessSection.style.display = 'block';
                if (communitySection) communitySection.style.display = 'block';
            }
            if (viewBar) viewBar.style.display = 'none';
            if (history.replaceState) history.replaceState(null, null, ' ');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else if (viewKey === 'all') {
            // Show all sections
            sections.forEach(s => s.style.display = 'block');
            if (infoContainer) {
                infoContainer.style.display = 'grid';
                if (wellnessSection) wellnessSection.style.display = 'block';
                if (communitySection) communitySection.style.display = 'block';
            }
            if (viewBar) {
                viewBar.style.display = 'flex';
                if (viewTitle) viewTitle.textContent = 'All Sections';
            }
            if (history.replaceState) history.replaceState(null, null, '#all');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            // Focus on the specific section
            sections.forEach(s => s.style.display = 'none');
            if (viewBar) viewBar.style.display = 'flex';

            let titleText = '';

            if (viewKey === 'children' && childrenSection) {
                childrenSection.style.display = 'block';
                titleText = 'Registered Children';
            } else if (viewKey === 'vaccination' && vaccinationSection) {
                vaccinationSection.style.display = 'block';
                titleText = 'Child Immunization Schedule & Records';
            } else if (viewKey === 'growth' && growthSection) {
                growthSection.style.display = 'block';
                titleText = 'Child Growth & Development Monitoring';
            } else if (viewKey === 'wellness' && wellnessSection) {
                if (infoContainer) infoContainer.style.display = 'block';
                wellnessSection.style.display = 'block';
                if (communitySection) communitySection.style.display = 'none';
                titleText = 'Maternal Wellness & Nutrition';
            } else if (viewKey === 'community' && communitySection) {
                if (infoContainer) infoContainer.style.display = 'block';
                if (wellnessSection) wellnessSection.style.display = 'none';
                communitySection.style.display = 'block';
                titleText = 'Healthcare Worker / Community Care';
            } else if (viewKey === 'consultation' && communitySection) {
                if (infoContainer) infoContainer.style.display = 'block';
                if (wellnessSection) wellnessSection.style.display = 'none';
                communitySection.style.display = 'block';
                titleText = 'Health Consultation';
                if (consultationSection) {
                    consultationSection.scrollIntoView({ behavior: 'smooth' });
                }
            }

            if (viewTitle) viewTitle.textContent = titleText;
            if (history.replaceState) history.replaceState(null, null, '#' + viewKey);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        // Close sidebar drawer if open
        closeSidebar();
    };

    // Attach click listeners to sidebar links with data-section
    document.querySelectorAll('.sidebar-nav-item[data-section]').forEach(link => {
        link.addEventListener('click', (e) => {
            const sec = link.getAttribute('data-section');
            if (sec && document.getElementById('dashboard-overview-container')) {
                e.preventDefault();
                window.switchDashboardView(sec);
            }
        });
    });

    // Check hash on page load (or default to overview)
    if (document.getElementById('dashboard-overview-container')) {
        const hash = window.location.hash.replace('#', '');
        if (hash) {
            if (['children', 'vaccination', 'growth', 'wellness', 'community', 'consultation', 'all', 'overview'].includes(hash)) {
                window.switchDashboardView(hash);
            } else if (hash === 'registered-children-section') {
                window.switchDashboardView('children');
            } else if (hash === 'vaccination-management-section') {
                window.switchDashboardView('vaccination');
            } else if (hash === 'growth-monitoring-section') {
                window.switchDashboardView('growth');
            } else if (hash === 'wellness-section') {
                window.switchDashboardView('wellness');
            } else if (hash === 'community-section') {
                window.switchDashboardView('community');
            } else if (hash === 'consultation-section') {
                window.switchDashboardView('consultation');
            } else {
                window.switchDashboardView('overview');
            }
        } else {
            window.switchDashboardView('overview');
        }
    }
});
