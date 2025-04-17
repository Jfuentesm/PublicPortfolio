// Enhanced responsive navigation for AIRisk

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Toggle - Enhanced version
    const mobileToggle = document.querySelector('.mobile-toggle');
    const navMenu = document.querySelector('nav ul');
    const body = document.body;
    
    if (mobileToggle && navMenu) {
        // Improved toggle functionality
        mobileToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            navMenu.classList.toggle('active');
            
            // Add overlay when menu is open
            if (navMenu.classList.contains('active')) {
                const overlay = document.createElement('div');
                overlay.className = 'mobile-nav-overlay';
                document.body.appendChild(overlay);
                
                // Prevent body scrolling when menu is open
                body.style.overflow = 'hidden';
                
                // Close menu when clicking outside
                overlay.addEventListener('click', function() {
                    navMenu.classList.remove('active');
                    body.style.overflow = '';
                    this.remove();
                });
            } else {
                // Remove overlay and restore scrolling
                const overlay = document.querySelector('.mobile-nav-overlay');
                if (overlay) overlay.remove();
                body.style.overflow = '';
            }
        });
        
        // Close menu when clicking on a link
        const navLinks = navMenu.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                navMenu.classList.remove('active');
                body.style.overflow = '';
                
                const overlay = document.querySelector('.mobile-nav-overlay');
                if (overlay) overlay.remove();
            });
        });
        
        // Close menu when pressing Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                body.style.overflow = '';
                
                const overlay = document.querySelector('.mobile-nav-overlay');
                if (overlay) overlay.remove();
            }
        });
    }
    
    // Responsive Sidebar Toggle for app pages
    const sidebarToggle = document.createElement('div');
    sidebarToggle.className = 'sidebar-toggle';
    sidebarToggle.innerHTML = '<i class="fas fa-bars"></i>';
    
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebar && mainContent) {
        // Add toggle button to the DOM
        const appHeader = document.querySelector('.app-header-container');
        if (appHeader) {
            appHeader.insertBefore(sidebarToggle, appHeader.firstChild);
        }
        
        // Toggle sidebar on mobile
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            
            // Add overlay when sidebar is open on mobile
            if (sidebar.classList.contains('active')) {
                const overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                document.body.appendChild(overlay);
                
                // Prevent body scrolling
                body.style.overflow = 'hidden';
                
                // Close sidebar when clicking outside
                overlay.addEventListener('click', function() {
                    sidebar.classList.remove('active');
                    body.style.overflow = '';
                    this.remove();
                });
            } else {
                // Remove overlay and restore scrolling
                const overlay = document.querySelector('.sidebar-overlay');
                if (overlay) overlay.remove();
                body.style.overflow = '';
            }
        });
        
        // Close sidebar when clicking on a link (on mobile)
        const sidebarLinks = sidebar.querySelectorAll('a');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 768) {
                    sidebar.classList.remove('active');
                    body.style.overflow = '';
                    
                    const overlay = document.querySelector('.sidebar-overlay');
                    if (overlay) overlay.remove();
                }
            });
        });
    }
    
    // Handle window resize events
    window.addEventListener('resize', function() {
        // Remove active classes and overlays when resizing to desktop
        if (window.innerWidth >= 768) {
            // For main navigation
            if (navMenu && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                body.style.overflow = '';
                
                const navOverlay = document.querySelector('.mobile-nav-overlay');
                if (navOverlay) navOverlay.remove();
            }
            
            // For sidebar
            if (sidebar && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
                body.style.overflow = '';
                
                const sidebarOverlay = document.querySelector('.sidebar-overlay');
                if (sidebarOverlay) sidebarOverlay.remove();
            }
        }
    });
});
