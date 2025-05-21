/* 
 * Keyboard navigation improvements for Medical Spytool
 * This file contains JavaScript to enhance keyboard navigation throughout the application
 * Updated: May 15, 2025 - Added more comprehensive keyboard navigation features
 */

document.addEventListener('DOMContentLoaded', function() {
    // State tracking for keyboard navigation
    let isUsingKeyboard = false;
    
    // Improve skip navigation
    addSkipNavigation();
    
    // Improve tab focus visibility
    improveFocusVisibility();
    
    // Set focus traps for modals
    setupModalFocusTraps();
    
    // Add keyboard navigation for custom components
    enhanceCustomComponents();
    
    // Implement global keyboard shortcuts
    setupGlobalShortcuts();
});

/**
 * Add skip navigation links at the top of the page
 * Allows keyboard users to skip directly to main content or navigation
 */
function addSkipNavigation() {
    // Only add skip links if they don't already exist
    if (!document.querySelector('.skip-link')) {
        // Create skip to main content link
        const skipToMainLink = document.createElement('a');
        skipToMainLink.href = '#main-content';
        skipToMainLink.className = 'skip-link';
        skipToMainLink.textContent = 'Zum Hauptinhalt springen';
        skipToMainLink.setAttribute('aria-label', 'Zum Hauptinhalt springen');
        
        // Create skip to navigation link
        const skipToNavLink = document.createElement('a');
        skipToNavLink.href = '#nav-main';
        skipToNavLink.className = 'skip-link';
        skipToNavLink.textContent = 'Zur Navigation springen';
        skipToNavLink.setAttribute('aria-label', 'Zur Navigation springen');
        
        // Add links to the DOM
        document.body.insertBefore(skipToMainLink, document.body.firstChild);
        document.body.insertBefore(skipToNavLink, document.body.firstChild);
        
        // Add event listeners to handle focus management
        [skipToMainLink, skipToNavLink].forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    targetElement.setAttribute('tabindex', '-1');
                    targetElement.focus();
                    
                    // Remove tabindex after focus
                    setTimeout(() => {
                        targetElement.removeAttribute('tabindex');
                    }, 1000);
                }
            });
        });
    }
    
    // Ensure main content has proper id
    const mainContent = document.querySelector('main') || document.querySelector('.container');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content';
    }
    
    // Ensure navigation has proper id
    const mainNav = document.querySelector('nav.navbar') || document.querySelector('nav');
    if (mainNav && !mainNav.id) {
        mainNav.id = 'nav-main';
    }
}

/**
 * Improve visibility of focused elements
 * This function enhances the visual focus indicators for keyboard navigation
 * while maintaining a cleaner look for mouse users
 */
function improveFocusVisibility() {
    let isUsingKeyboard = false;
    
    // Add a class to body when user is navigating with keyboard
    document.body.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            isUsingKeyboard = true;
            document.body.classList.add('keyboard-navigation');
            
            // Log for debugging purposes
            console.debug('Keyboard navigation mode activated');
        }
    });
    
    // Remove the class when user uses mouse
    document.body.addEventListener('mousedown', function() {
        if (isUsingKeyboard) {
            isUsingKeyboard = false;
            document.body.classList.remove('keyboard-navigation');
            
            // Log for debugging purposes
            console.debug('Keyboard navigation mode deactivated');
        }
    });
    
    // Enhance focus styles for interactive elements that may need it
    const interactiveElements = document.querySelectorAll('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
    
    interactiveElements.forEach(element => {
        // Add role="button" to clickable divs/spans if missing
        if ((element.tagName === 'DIV' || element.tagName === 'SPAN') && 
            (element.onclick || element.getAttribute('onclick')) &&
            !element.getAttribute('role')) {
            element.setAttribute('role', 'button');
        }
        
        // Ensure all interactive elements have accessible names
        if (!element.hasAttribute('aria-label') && 
            !element.hasAttribute('aria-labelledby') && 
            element.textContent.trim() === '' &&
            !element.getAttribute('title')) {
            
            // Try to use image alt text for buttons with only images
            const img = element.querySelector('img');
            if (img && img.alt) {
                element.setAttribute('aria-label', img.alt);
            }
        }
    });
}

/**
 * Setup focus traps for modal dialogs
 */
function setupModalFocusTraps() {
    // Find all modals
    const modals = document.querySelectorAll('.modal');
    
    modals.forEach(modal => {
        // When modal is shown
        modal.addEventListener('shown.bs.modal', function() {
            // Find all focusable elements
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length > 0) {
                // Set focus to first element
                const firstElement = focusableElements[0];
                firstElement.focus();
                
                // Trap focus inside modal
                const lastElement = focusableElements[focusableElements.length - 1];
                
                modal.addEventListener('keydown', function(e) {
                    if (e.key === 'Tab') {
                        if (e.shiftKey && document.activeElement === firstElement) {
                            e.preventDefault();
                            lastElement.focus();
                        } else if (!e.shiftKey && document.activeElement === lastElement) {
                            e.preventDefault();
                            firstElement.focus();
                        }
                    }
                });
            }
        });
        
        // Restore focus when modal is closed
        let previouslyFocused = null;
        
        modal.addEventListener('show.bs.modal', function() {
            previouslyFocused = document.activeElement;
        });
        
        modal.addEventListener('hidden.bs.modal', function() {
            if (previouslyFocused) {
                previouslyFocused.focus();
            }
        });
    });
}

/**
 * Enhance keyboard navigation for custom components
 */
function enhanceCustomComponents() {
    // Enhance tab navigation for search tabs
    const tabLinks = document.querySelectorAll('.nav-tabs .nav-link');
    
    tabLinks.forEach(tab => {
        tab.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                
                const tabs = Array.from(tabLinks);
                const currentIndex = tabs.indexOf(e.target);
                let newIndex;
                
                if (e.key === 'ArrowLeft') {
                    newIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
                } else {
                    newIndex = currentIndex === tabs.length - 1 ? 0 : currentIndex + 1;
                }
                
                tabs[newIndex].focus();
                tabs[newIndex].click();
            }
        });
    });
    
    // Make search results keyboard navigable
    const resultItems = document.querySelectorAll('.search-result');
    
    resultItems.forEach(item => {
        if (!item.hasAttribute('tabindex')) {
            item.setAttribute('tabindex', '0');
        }
        
        item.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                
                // Find the first link or button in the result item and click it
                const clickable = item.querySelector('a, button');
                if (clickable) {
                    clickable.click();
                }
            }
        });
    });
}
