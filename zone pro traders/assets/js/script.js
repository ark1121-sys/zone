// Authentication & Utility Functions

// Check if user is logged in
function isLoggedIn() {
    return localStorage.getItem('zp_user') !== null;
}

function getCurrentUser() {
    return localStorage.getItem('zp_user');
}

function getCurrentUserName() {
    return localStorage.getItem('zp_name') || 'User';
}

function getCurrentUserId() {
    return localStorage.getItem('zp_uid');
}

// Logout function - Redirect to index page
window.logout = function() {
    console.log('logout() function called');
    
    try {
        // Clear all user data from localStorage
        const keysToRemove = ['zp_user', 'zp_name', 'zp_uid', 'zp_data'];
        keysToRemove.forEach(key => {
            localStorage.removeItem(key);
        });
        
        // Always redirect to index.html using absolute-style path
        // Our custom server will find it correctly
        console.log('Logging out and redirecting to root index.html');
        window.location.replace('/index.html');
    } catch (error) {
        console.error('Logout error:', error);
        window.location.replace('/');
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide Icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // Check if user is logged in
    const userLoggedIn = isLoggedIn();
    const userName = getCurrentUserName();
    const currentPage = window.location.pathname;
    const isIndex = currentPage === '/' || currentPage.indexOf('index.html') !== -1 || currentPage.endsWith('/');

    if (isIndex) {
        // Desktop nav elements
        const navLogin = document.getElementById('nav-login');
        const navDashboard = document.getElementById('nav-dashboard');
        const navLogout = document.getElementById('nav-logout');

        // Mobile nav elements
        const mobileNavLogin = document.getElementById('mobile-nav-login');
        const mobileNavDashboard = document.getElementById('mobile-nav-dashboard');
        const mobileNavLogout = document.getElementById('mobile-nav-logout');

        if (userLoggedIn) {
            // Logged in state
            if (navLogin) navLogin.classList.add('hidden');
            if (navDashboard) navDashboard.classList.remove('hidden');
            if (navLogout) navLogout.classList.remove('hidden');

            if (mobileNavLogin) mobileNavLogin.classList.add('hidden');
            if (mobileNavDashboard) mobileNavDashboard.classList.remove('hidden');
            if (mobileNavLogout) mobileNavLogout.classList.remove('hidden');
            
            // Optional: Show welcome message
            const welcomeSpan = document.createElement('span');
            welcomeSpan.className = 'text-text-heading font-medium text-sm hidden lg:inline-block mr-2 welcome-msg';
            welcomeSpan.textContent = `Welcome, ${userName}!`;
            if (navDashboard && !document.querySelector('.welcome-msg')) {
                navDashboard.parentNode.insertBefore(welcomeSpan, navDashboard);
            }
        } else {
            // Guest state
            if (navLogin) navLogin.classList.remove('hidden');
            if (navDashboard) navDashboard.classList.add('hidden');
            if (navLogout) navLogout.classList.add('hidden');

            if (mobileNavLogin) mobileNavLogin.classList.remove('hidden');
            if (mobileNavDashboard) mobileNavDashboard.classList.add('hidden');
            if (mobileNavLogout) mobileNavLogout.classList.add('hidden');
        }
    }

    // Bind logout buttons
    const logoutHandler = (e) => {
        e.preventDefault();
        logout();
    };

    const logoutBtnDesktop = document.getElementById('nav-logout');
    const logoutBtnMobile = document.getElementById('mobile-nav-logout');
    
    if (logoutBtnDesktop) logoutBtnDesktop.addEventListener('click', logoutHandler);
    if (logoutBtnMobile) logoutBtnMobile.addEventListener('click', logoutHandler);

    // Mobile Menu Toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if(mobileMenuButton && mobileMenu){
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });

        // Close mobile menu when clicking on a link
        const mobileMenuLinks = mobileMenu.querySelectorAll('a');
        mobileMenuLinks.forEach(link => {
            link.addEventListener('click', () => {
                setTimeout(() => {
                    mobileMenu.classList.add('hidden');
                }, 100);
            });
        });
    }
});

// Bind logout button click - using event delegation for reliability
document.addEventListener('click', (e) => {
    const logoutBtn = e.target.closest('#logout-btn');
    if (logoutBtn) {
        e.preventDefault();
        e.stopPropagation();
        
        const currentPath = window.location.pathname;
        const isOnLogoutPage = currentPath.indexOf('logout.html') !== -1;
        
        // If we are already on the logout page, just call the logout function
        if (isOnLogoutPage) {
            window.logout();
            return;
        }
        
        console.log('Logout button clicked - redirecting to confirmation page');
        
        // Always redirect to /logout.html
        // Our custom server will find it in pages/logout.html automatically
        window.location.href = '/logout.html';
    }
}, true);

// Function to open the modal with the correct price
function openPayment_Modal(price) {
    const modal = document.getElementById('paymentModal');
    const priceDisplay = document.getElementById('modalPrice');
    priceDisplay.innerText = price;
    modal.classList.remove('hidden');
}

function closePayment_Modal() {
    document.getElementById('paymentModal').classList.add('hidden');
}


// Update your existing "Join Now" buttons to call this function
// Example: <button onclick="openPaymentModal('₹9,999')">Join Now</button>

// Handle Form Submission using EmailJS or a simple Formspree link
const form = document.getElementById('verificationForm');
if (form) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Create a WhatsApp message with the details (Easiest way for manual verification)
        const name = form.name.value;
        const email = form.email.value;
        const txn = form.txn_id.value;
        const price = document.getElementById('modalPrice').innerText;
    
        const message = `Hello Zone Pro Trader! I have made the payment.%0A%0A*Name:* ${name}%0A*Email:* ${email}%0A*Amount:* ${price}%0A*Txn ID:* ${txn}%0A%0A_Please verify and grant access._`;
        
        const whatsappUrl = `https://wa.me/919361241485?text=${message}`;
        
        // Redirect to WhatsApp
        window.open(whatsappUrl, '_blank');
        alert("Details submitted! Please send the message on WhatsApp to complete verification.");
    });
}
function showSwingScanner() {
    const ott = document.getElementById('ott-content');
    const swing = document.getElementById('swing-scanner-content');
    
    // Hide Option Trading Tools and Show Swing Scanner
    ott.classList.add('hidden');
    swing.classList.remove('hidden');
}

// Optional: Close scanner if clicking outside (if you want it to reset)
// Or you can add a 'back' button inside the Swing Scanner div if needed.