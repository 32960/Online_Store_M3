document.addEventListener('DOMContentLoaded', function() {

    // --- Logic for the Main Page (home.html) ---
    const homePageContent = document.querySelector('.main-content-grid');
    if (homePageContent) {
        // 1. Pagination Logic
        const paginationList = document.querySelector('.pagination-list');
        if (paginationList) {
            const paginationLinks = paginationList.querySelectorAll('.pagination__link');
            paginationLinks.forEach(link => {
                link.addEventListener('click', function(event) {
                    event.preventDefault();
                    paginationLinks.forEach(lnk => lnk.classList.remove('active'));
                    this.classList.add('active');
                });
            });
        }

//        // 2. Filter Logic (Keywords and Checkboxes)
//        const checkboxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]');
//        const filterButton = document.querySelector('#filter-button');
//
//        if (checkboxes.length > 0 && filterButton) {
//            filterButton.addEventListener('click', function() {
//                let checked = [];
//                checkboxes.forEach(checkbox => {
//                    if (checkbox.checked) {
//                        checked.push(checkbox.dataset.keyword);
//                    }
//                });
//                const url = new URLSearchParams(window.location.search);
//                url.set('categories', checked.join(','));
//                window.location.search = url.toString();
//            });
//        }

        // 2. Filter Logic (Categories + Price Range)
        const checkboxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]');
        const filterButton = document.querySelector('#filter-button');
        const priceMinInput = document.getElementById('price_min');
        const priceMaxInput = document.getElementById('price_max');

        if (filterButton) {
            filterButton.addEventListener('click', function() {
                // Collect checked categories
                let checkedCategories = [];
                checkboxes.forEach(checkbox => {
                    if (checkbox.checked) {
                        checkedCategories.push(checkbox.dataset.keyword);
                    }
                });

                // Build URL with all filters
                const url = new URLSearchParams(window.location.search);

                // Categories
                if (checkedCategories.length > 0) {
                    url.set('categories', checkedCategories.join(','));
                } else {
                    url.delete('categories');
                }

                // Price range
                const priceMin = priceMinInput ? priceMinInput.value.trim() : '';
                const priceMax = priceMaxInput ? priceMaxInput.value.trim() : '';

                if (priceMin) {
                    url.set('price_min', priceMin);
                } else {
                    url.delete('price_min');
                }

                if (priceMax) {
                    url.set('price_max', priceMax);
                } else {
                    url.delete('price_max');
                }

                // Navigate to filtered URL
                window.location.search = url.toString();
            });
        }

        // 3. Search Logic
        const searchInput = document.querySelector('.search-input');
        const searchBtn = document.querySelector('.search-button');

        if (searchBtn && searchInput) {
            searchBtn.addEventListener('click', function() {
                const q = searchInput.value;
                const url = new URLSearchParams(window.location.search);
                url.set('q', q);
                window.location.search = url.toString();
            });

            searchInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    searchBtn.click();
                }
            });
        }
    }

    // --- Logic for Product Detail Pages (product-*.html) ---
    const productPageContent = document.querySelector('.page-product');
    if (productPageContent) {
        // Accordion
        const accordionTitles = document.querySelectorAll('.accordion-title');
        accordionTitles.forEach(title => {
            title.addEventListener('click', function() {
                this.closest('.accordion-item').classList.toggle('active');
            });
        });
    }

    // --- Logic for Cart Page (cart.html) ---
    const cartPageContent = document.querySelector('.cart-page-wrapper');
    if (cartPageContent) {
        const cartTotalPriceElem = document.getElementById('cart-total-price');
        function updateCartTotal() {
            let total = 0;
            document.querySelectorAll('.cart-item').forEach(item => {
                const priceText = item.querySelector('[data-item-total-price]')?.textContent;
                if (priceText) {
                    total += parseFloat(priceText.replace('$', ''));
                }
            });
            if (cartTotalPriceElem) cartTotalPriceElem.textContent = `$${total.toFixed(2)}`;
        }

        updateCartTotal();
    }

    // --- Logic for Account and Admin Pages ---
    const accountAdminWrapper = document.querySelector('.account-page-wrapper, .admin-page-wrapper');
    if (accountAdminWrapper) {
        // Account Page Tabs
        const accountTabs = document.querySelectorAll('.account-tab');
        const tabPanes = document.querySelectorAll('.tab-pane');
        if (accountTabs.length > 0 && tabPanes.length > 0) {
            accountTabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    accountTabs.forEach(item => item.classList.remove('active'));
                    tabPanes.forEach(pane => pane.classList.remove('active'));
                    const targetPane = document.querySelector(this.dataset.tabTarget);
                    this.classList.add('active');
                    if (targetPane) targetPane.classList.add('active');
                });
            });
        }

        // Admin Panel - Category Tags
        const categoryTagsContainer = document.querySelector('.category-tags');
        if (categoryTagsContainer) {
            categoryTagsContainer.addEventListener('click', function(e) {
                const clickedTag = e.target.closest('.category-tag');
                if (clickedTag) {
                    categoryTagsContainer.querySelectorAll('.category-tag').forEach(t => t.classList.remove('active'));
                    clickedTag.classList.add('active');
                }
            });
        }

        // Image Upload Simulation
        const uploadButton = document.getElementById('upload-image-btn');
        const fileInput = document.getElementById('image-upload-input');

        if (uploadButton && fileInput) {
            uploadButton.addEventListener('click', function() {
                fileInput.click();
            });

            fileInput.addEventListener('change', function(event) {
                const file = event.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    const placeholder = document.querySelector('.image-upload-placeholder');

                    reader.onload = function(e) {
                        placeholder.innerHTML = '';
                        placeholder.style.backgroundImage = `url('${e.target.result}')`;
                        placeholder.style.backgroundSize = 'cover';
                        placeholder.style.backgroundPosition = 'center';
                    };
                    reader.readAsDataURL(file);
                }
            });
        }
    }

    // --- Logic for Reviews Page ---
    const starRating = document.getElementById('star-rating');

    if (starRating) {
        const stars = starRating.querySelectorAll('.star-label');
        const radios = starRating.querySelectorAll('.star-radio');

        let currentRating = 0;

        function updateStars(rating) {
            stars.forEach((star, index) => {
                const icon = star.querySelector('i');
                if (index < rating) {
                    icon.className = 'fa-solid fa-star';
                    icon.style.color = '#fbbf24';
                } else {
                    icon.className = 'fa-regular fa-star';
                    icon.style.color = '#d1d5db';
                }
            });
        }

        stars.forEach(star => {
            star.addEventListener('click', function(e) {
                e.preventDefault();
                const rating = parseInt(this.dataset.rating);
                const radio = document.getElementById(`star-${rating}`);
                if (radio) radio.checked = true;
                currentRating = rating;
                updateStars(rating);
            });

            star.addEventListener('mouseenter', function() {
                const rating = parseInt(this.dataset.rating);
                updateStars(rating);
            });

            star.addEventListener('mouseleave', function() {
                updateStars(currentRating);
            });
        });

        const checkedRadio = document.querySelector('.star-radio:checked');
        if (checkedRadio) {
            currentRating = parseInt(checkedRadio.value);
            updateStars(currentRating);
        } else {
            currentRating = 0;
            updateStars(0);
        }
    }
});
