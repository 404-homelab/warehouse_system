/**
 * SAFE IMAGE PATH UTILITY
 * =======================
 * 
 * This utility provides a safe way to get image paths that prevents
 * infinite loops when images are missing or have invalid values.
 * 
 * PROBLEM:
 * --------
 * When database contains 'null' as a string or undefined/empty values,
 * JavaScript creates paths like:
 * - /static/uploads/null
 * - /static/uploads/undefined
 * - /static/uploads/
 * 
 * These don't exist, causing onerror to trigger repeatedly.
 * 
 * SOLUTION:
 * ---------
 * Use this utility to validate image filenames before creating paths.
 */

/**
 * Check if a value is a valid image filename
 * @param {*} value - The value to check
 * @returns {boolean} - True if valid filename
 */
function isValidImageFilename(value) {
    // Check if value exists and is a string
    if (!value || typeof value !== 'string') {
        return false;
    }
    
    // Check if it's a literal 'null' or 'undefined' string
    if (value === 'null' || value === 'undefined') {
        return false;
    }
    
    // Check if it's empty after trimming
    if (value.trim() === '') {
        return false;
    }
    
    return true;
}

/**
 * Get safe image path with fallback to placeholder
 * @param {string} imageCropped - Cropped image filename
 * @param {string} imageOriginal - Original image filename
 * @param {string} placeholder - Placeholder path (default: '/static/uploads/placeholder.svg')
 * @returns {string} - Safe image path
 */
function getSafeImagePath(imageCropped, imageOriginal, placeholder = '/static/uploads/placeholder.svg') {
    // Try cropped image first
    if (isValidImageFilename(imageCropped)) {
        return `/static/uploads/${imageCropped}`;
    }
    
    // Try original image
    if (isValidImageFilename(imageOriginal)) {
        return `/static/uploads/${imageOriginal}`;
    }
    
    // Fallback to placeholder
    return placeholder;
}

/**
 * Create safe image tag with proper onerror handling
 * @param {object} options - Configuration object
 * @param {string} options.imageCropped - Cropped image filename
 * @param {string} options.imageOriginal - Original image filename
 * @param {string} options.altText - Alt text for image (default: 'Product')
 * @param {string} options.className - CSS class name(s)
 * @param {string} options.style - Inline styles
 * @returns {string} - HTML img tag
 */
function createSafeImageTag(options = {}) {
    const {
        imageCropped,
        imageOriginal,
        altText = 'Product',
        className = '',
        style = ''
    } = options;
    
    const src = getSafeImagePath(imageCropped, imageOriginal);
    const classAttr = className ? ` class="${className}"` : '';
    const styleAttr = style ? ` style="${style}"` : '';
    
    return `<img src="${src}" alt="${altText}"${classAttr}${styleAttr} onerror="this.onerror=null; this.src='/static/uploads/placeholder.svg'">`;
}

// Export for use in templates
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        isValidImageFilename,
        getSafeImagePath,
        createSafeImageTag
    };
}

// Example usage in templates:
/*
// BEFORE (UNSAFE):
let imageSrc = item.image_cropped ? `/static/uploads/${item.image_cropped}` : '/static/uploads/placeholder.svg';

// AFTER (SAFE):
let imageSrc = getSafeImagePath(item.image_cropped, item.image_original);

// OR even simpler:
const imgTag = createSafeImageTag({
    imageCropped: item.image_cropped,
    imageOriginal: item.image_original,
    className: 'product-image',
    altText: item.description
});
*/
