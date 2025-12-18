// i18n.js - Internationalization helper
(function() {
    'use strict';
    
    let currentLang = 'sv';
    let translations = {};
    let isLoaded = false;

    // Load translations
    async function loadTranslations() {
        try {
            const response = await fetch('/static/translations.json');
            translations = await response.json();
            isLoaded = true;
            
            console.log('✓ Translations loaded:', Object.keys(translations));
            
            // Get saved language preference
            const savedLang = localStorage.getItem('language') || 'sv';
            setLanguage(savedLang);
        } catch (error) {
            console.error('✗ Failed to load translations:', error);
        }
    }

    // Get translation
    function t(key) {
        if (!isLoaded) {
            console.warn('Translations not loaded yet');
            return key;
        }
        
        const keys = key.split('.');
        let value = translations[currentLang];
        
        for (const k of keys) {
            if (value && value[k]) {
                value = value[k];
            } else {
                console.warn(`Translation missing: ${key} (${currentLang})`);
                return key;
            }
        }
        
        return value;
    }

    // Set language
    function setLanguage(lang) {
        console.log('→ setLanguage called:', lang);
        
        if (!isLoaded) {
            console.warn('Translations not loaded yet, queuing...');
            setTimeout(() => setLanguage(lang), 100);
            return;
        }
        
        if (!translations[lang]) {
            console.error('✗ Language not supported:', lang);
            console.log('Available languages:', Object.keys(translations));
            return;
        }
        
        currentLang = lang;
        localStorage.setItem('language', lang);
        
        console.log('→ Updating DOM elements...');
        
        // Update all elements with data-i18n attribute
        const elements = document.querySelectorAll('[data-i18n]');
        console.log('Found', elements.length, 'elements with data-i18n');
        
        let updated = 0;
        elements.forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translation = t(key);
            
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = translation;
            } else {
                el.textContent = translation;
            }
            updated++;
        });
        
        console.log('✓ Updated', updated, 'elements');
        
        // Update language selector
        document.querySelectorAll('.lang-option').forEach(opt => {
            const isActive = opt.dataset.lang === lang;
            opt.classList.toggle('active', isActive);
            console.log('Lang option', opt.dataset.lang, 'active:', isActive);
        });
        
        // Trigger custom event
        const event = new CustomEvent('languageChanged', { detail: { lang } });
        document.dispatchEvent(event);
        
        console.log('✓ Language changed to:', lang);
    }

    // Get current language
    function getCurrentLanguage() {
        return currentLang;
    }

    // Make functions globally accessible
    window.setLanguage = setLanguage;
    window.t = t;
    window.getCurrentLanguage = getCurrentLanguage;

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadTranslations);
    } else {
        // DOM already loaded
        loadTranslations();
    }
    
    console.log('i18n.js initialized');
})();

