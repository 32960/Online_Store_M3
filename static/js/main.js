document.addEventListener('DOMContentLoaded', function() {

    // --- General logic for all pages (Login/Logout Simulation) ---
    const loginForm = document.getElementById('login-form');
    const logoutButton = document.getElementById('logout-button');
    function checkLoginStatus() {
        if (localStorage.getItem('isLoggedIn') === 'true') {
            document.body.classList.add('user-logged-in');
        } else {
            document.body.classList.remove('user-logged-in');
        }
    }
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            localStorage.setItem('isLoggedIn', 'true');
            const nextUrl = new URLSearchParams(window.location.search).get('next');
            window.location.href = nextUrl || 'home.html';
        });
    }
    if (logoutButton) {
        logoutButton.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.removeItem('isLoggedIn');
            window.location.href = 'home.html';
        });
    }
    checkLoginStatus();


    // --- Logic for the Main Page (home.html) ---
    const homePageContent = document.querySelector('.main-content-grid');
    if (homePageContent) {
        // 1. Sort Options Logic (moved to django template)

        // 2. Pagination Logic
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

        // 3. Filter Logic (Keywords and Checkboxes)
        const checkboxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]');
        const filterButton = document.querySelector('#filter-button');

        if (checkboxes.length > 0) {
            filterButton.addEventListener('click', function() {
                let checked = [];
                checkboxes.forEach(checkbox => {
                    if (checkbox.checked) {
                        checked.push(checkbox.dataset.keyword);
                    }
                });
                const url = new URLSearchParams(window.location.search);
                url.set('categories', checked.join(','));
                window.location.search = url.toString();
            })
        }

        // 4. Search Logic
        const searchInput = document.querySelector('.search-input');
        const searchBtn = document.querySelector('.search-button');

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

    // --- Logic for Product Detail Pages (product-*.html) ---
    const productPageContent = document.querySelector('.page-product');
    if (productPageContent) {
        // Accordion
        const accordionTitle = document.querySelector('.accordion-title');
        if (accordionTitle) {
            accordionTitle.addEventListener('click', function() {
                this.closest('.accordion-item').classList.toggle('active');
            });
        }
        // "Add to Cart" Button and Counter
        const cartControls = document.querySelector('.cart-controls');
        if (cartControls) {
            const addToCartBtn = cartControls.querySelector('#add-to-cart-btn');
            const quantityCounter = cartControls.querySelector('#quantity-counter');
            const decreaseBtn = quantityCounter.querySelector('[data-action="decrease"]');
            const increaseBtn = quantityCounter.querySelector('[data-action="increase"]');
            const quantityValueSpan = quantityCounter.querySelector('.quantity-value');
            let quantity = 0;
            function updateView() {
                if (quantity === 0) {
                    addToCartBtn.classList.remove('is-hidden');
                    quantityCounter.classList.add('is-hidden');
                } else {
                    addToCartBtn.classList.add('is-hidden');
                    quantityCounter.classList.remove('is-hidden');
                    quantityValueSpan.textContent = `${quantity} in cart`;
                }
            }
            addToCartBtn.addEventListener('click', function() { quantity = 1; updateView(); });
            decreaseBtn.addEventListener('click', function() { if (quantity > 0) { quantity--; updateView(); } });
            increaseBtn.addEventListener('click', function() { quantity++; updateView(); });
            updateView();
        }
    }

    // --- Logic for Cart Page (cart.html) ---
    const cartPageContent = document.querySelector('.cart-page-wrapper');
    if (cartPageContent) {
        const cartItemsList = document.getElementById('cart-items-list');
        const cartTotalPriceElem = document.getElementById('cart-total-price');
        function updateCartTotal() {
            let total = 0;
            document.querySelectorAll('.cart-item').forEach(item => {
                const priceText = item.querySelector('[data-item-total-price]').textContent;
                if (priceText) {
                    total += parseFloat(priceText.replace('$', ''));
                }
            });
            if (cartTotalPriceElem) cartTotalPriceElem.textContent = `$${total.toFixed(2)}`;
        }
        if (cartItemsList) {
            cartItemsList.addEventListener('click', function(event) {
                const cartItem = event.target.closest('.cart-item');
                if (!cartItem) return;
                const quantityElem = cartItem.querySelector('.quantity-value-cart');
                const itemTotalElem = cartItem.querySelector('[data-item-total-price]');
                const basePrice = parseFloat(cartItem.dataset.price);
                let quantity = parseInt(quantityElem.textContent);
                if (event.target.closest('[data-action="increase"]')) {
                    quantity++;
                } else if (event.target.closest('[data-action="decrease"]')) {
                    quantity = quantity > 1 ? quantity - 1 : 0;
                }
                if (event.target.closest('[data-action="remove"]') || quantity === 0) {
                    cartItem.remove();
                } else {
                    quantityElem.textContent = quantity;
                    itemTotalElem.textContent = `$${(basePrice * quantity).toFixed(2)}`;
                }
                updateCartTotal();
            });
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
                    }
                    reader.readAsDataURL(file);
                }
            });
        }
    }
});