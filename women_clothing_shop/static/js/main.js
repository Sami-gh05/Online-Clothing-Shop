document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Sliders
    initializeSliders();

    // 2. Organize Filters into Groups
    organizeFilters();

    // 3. NEW: Initialize the product detail gallery
    initializeProductGallery();

    // 4. NEW: Format the product detail feature list
    formatProductFeatures();
});

/**
 * Initializes the Swiper sliders for Hero and Product sections
 */
function initializeSliders() {
    // Check if Swiper is defined
    if (typeof Swiper === 'undefined') {
        return;
    }

    // --- Initialize Hero Slider ---
    const heroSliderElement = document.querySelector('.hero-slider');
    if (heroSliderElement) {
        const heroSlider = new Swiper('.hero-slider', {
            direction: 'horizontal',
            loop: true,
            autoplay: {
                delay: 5000,
                disableOnInteraction: false,
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
        });
    }

    // --- Initialize Product Slider ---
    const productSliderElement = document.querySelector('.product-slider');
    if (productSliderElement) {
        const productSlider = new Swiper('.product-slider', {
            direction: 'horizontal',
            loop: false,
            slidesPerView: 1,
            spaceBetween: 20,
            breakpoints: {
                768: {slidesPerView: 2, spaceBetween: 30},
                1024: {slidesPerView: 3, spaceBetween: 30},
                1200: {slidesPerView: 4, spaceBetween: 30}
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
        });
    }
}

/**
 * Groups filters based on their names.
 */
function organizeFilters() {
    const filterContainer = document.querySelector('.filter-sidebar form');
    if (!filterContainer) return;

    const groups = {};
    const allDetails = filterContainer.querySelectorAll('details.filter-group-accordion');

    allDetails.forEach(detail => {
        const summary = detail.querySelector('summary');
        if (!summary) return;

        const originalTitle = summary.textContent.trim();

        if (originalTitle.includes(' - ')) {
            const parts = originalTitle.split(' - ');
            const parentName = parts[0].trim();
            const childName = parts[1].trim();

            if (!groups[parentName]) {
                const parentGroup = document.createElement('details');
                parentGroup.className = 'filter-group-accordion parent-group-styled';
                parentGroup.open = true;

                const parentSummary = document.createElement('summary');
                parentSummary.textContent = parentName;
                parentSummary.style.fontWeight = 'bold';
                parentSummary.style.color = '#222';
                parentSummary.style.backgroundColor = '#f9f9f9';
                parentSummary.style.padding = '10px';
                parentSummary.style.borderBottom = '1px solid #ddd';

                parentGroup.appendChild(parentSummary);
                detail.parentNode.insertBefore(parentGroup, detail);
                groups[parentName] = parentGroup;
            }

            summary.textContent = childName;
            detail.style.marginRight = '15px';
            detail.style.borderBottom = 'none';
            detail.style.padding = '5px 0';
            groups[parentName].appendChild(detail);
        }
    });
}

/**
 * NEW: Initializes the product detail image gallery.
 * Listens for clicks on thumbnails and swaps the main image src.
 */
function initializeProductGallery() {
    // Find the main image and the thumbnail container
    const mainImage = document.querySelector('.product-main-image');
    const galleryContainer = document.querySelector('.product-gallery-thumbnails');

    // If they don't exist (i.e., we're not on the product detail page), do nothing.
    if (!mainImage || !galleryContainer) {
        return;
    }

    // Get all thumbnail images
    const thumbnails = galleryContainer.querySelectorAll('img');

    // Add a click event listener to each thumbnail
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function () {
            // When a thumb is clicked, set the main image's source
            // to the thumbnail's source.
            mainImage.src = thumb.src;
        });
    });
}

/**
 * NEW: Formats the product detail feature list.
 * Finds list items with a ":" and bolds the part before it.
 */
function formatProductFeatures() {
    // Find all feature list items
    const featureItems = document.querySelectorAll('.feature-group-list li');

    if (!featureItems.length) {
        return; // We're not on the product detail page
    }

    featureItems.forEach(item => {
        const text = item.textContent.trim();
        const colonIndex = text.indexOf(':');

        // Check if a colon exists and it's not the first character
        if (colonIndex > 0) {
            const key = text.substring(0, colonIndex);
            const value = text.substring(colonIndex + 1);

            // Re-write the HTML for the list item, keeping the colon in the strong tag
            item.innerHTML = `<strong>${key}:</strong> ${value}`;
        }
    });
}