// State
const state = {
    budget: null,
    cart: [],
    products: [],
    categories: [],
    activeCategory: 'all',
    searchQuery: '',
    taxRate: 0.08,
};

// DOM Elements
let DOM = {};

function initDOM() {
    DOM = {
        globalBudgetDisplay: document.getElementById('global-budget-display'),
        budgetAmountDisplay: document.getElementById('budget-amount'),
        setBudgetBtn: document.getElementById('set-budget-btn'),
        budgetModal: document.getElementById('budget-modal'),
        budgetInput: document.getElementById('budget-input'),
        cancelBudgetBtn: document.getElementById('cancel-budget'),
        saveBudgetBtn: document.getElementById('save-budget'),

        searchInput: document.getElementById('search-input'),
        categoryTabs: document.getElementById('category-tabs'),
        productGrid: document.getElementById('product-grid'),

        cartItemsContainer: document.getElementById('cart-items'),
        emptyState: document.getElementById('empty-state'),
        cartItemCount: document.getElementById('cart-item-count'),
        statTotalItems: document.getElementById('stat-total-items'),
        cartWeight: document.getElementById('cart-weight'),
        cartSubtotal: document.getElementById('cart-subtotal'),
        cartTax: document.getElementById('cart-tax'),
        cartTotal: document.getElementById('cart-total'),
        checkoutBtn: document.getElementById('checkout-btn'),

        budgetProgressContainer: document.getElementById('budget-progress-container'),
        progressBarFill: document.getElementById('progress-bar-fill'),
        budgetPercentage: document.getElementById('budget-percentage'),
        budgetWarning: document.getElementById('budget-warning'),
        budgetDanger: document.getElementById('budget-danger'),

        checkoutModal: document.getElementById('checkout-modal'),
        finalPaidAmount: document.getElementById('final-paid-amount'),
        receiptQr: document.getElementById('receipt-qr'),
        newTripBtn: document.getElementById('new-trip-btn')
    };
}

async function fetchProducts() {
    try {
        const res = await fetch('/api/products');
        if (!res.ok) throw new Error("Failed to fetch products");
        state.products = await res.json();
        console.log("Products loaded:", state.products);

        // Extract unique categories
        state.categories = [...new Set(state.products.map(p => p.category).filter(Boolean))];
        renderCategories();
        renderProducts();
    } catch (err) {
        DOM.productGrid.innerHTML = `<div style="text-align:center;color:var(--danger);width:100%;">Failed to load products. Check connection.</div>`;
    }
}

function renderCategories() {
    let html = `<button class="category-tab active" data-category="all">All Items</button>`;
    state.categories.forEach(cat => {
        const titleCase = cat.charAt(0).toUpperCase() + cat.slice(1).replace('_', ' ');
        html += `<button class="category-tab" data-category="${cat}">${titleCase}</button>`;
    });
    DOM.categoryTabs.innerHTML = html;

    // Attach event listeners
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            state.activeCategory = e.target.dataset.category;
            renderProducts();
        });
    });
}

function renderProducts() {
    const query = state.searchQuery.toLowerCase();
    const filtered = state.products.filter(p => {
        const matchesCategory = state.activeCategory === 'all' || p.category === state.activeCategory;
        const matchesQuery = p.name.toLowerCase().includes(query);
        return matchesCategory && matchesQuery;
    });

    console.log("Rendering products:", filtered);

    if (filtered.length === 0) {
        DOM.productGrid.innerHTML = `<div style="text-align:center; padding: 2rem; color: var(--text-muted); width:100%;">No products found matching "${state.searchQuery}"</div>`;
        return;
    }

    DOM.productGrid.innerHTML = filtered.map(p => {
        let imagePath = p.image_url;
        if (!p.image_url.startsWith("http")) {
            imagePath = `/static/images/${p.image_url}`;
        }
        return `
        <div class="product-card" onclick="addToCart(${p.id})">
            <img class="product-image" src="${imagePath}" alt="${p.name}" onerror="this.src='/static/images/product_placeholder.png'">
            <div class="product-info">
                <span class="product-name">${p.name}</span>
                <span class="product-price">${formatCurrency(p.price)}</span>
                <span class="product-weight">${p.weight_g}g</span>
                ${p.stock < 10 ? `<span class="low-stock-badge">Low Stock</span>` : ''}
            </div>
            <div class="scan-action"></div>
        </div>
        `;
    }).join('');
}

window.handleImageError = function (img, category) {
    img.onerror = null; // Prevent infinite loops
    img.src = '/static/images/products/supermarket_product.png';
};

function init() {
    fetchProducts();
    setupEventListeners();
}

function setupEventListeners() {
    // Search
    DOM.searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value;
        renderProducts();
    });

    // Budget Modals
    DOM.setBudgetBtn.addEventListener('click', () => {
        if (state.budget) DOM.budgetInput.value = state.budget;
        DOM.budgetModal.classList.remove('hidden');
        DOM.budgetInput.focus();
    });

    DOM.globalBudgetDisplay.addEventListener('click', () => {
        DOM.budgetInput.value = state.budget || '';
        DOM.budgetModal.classList.remove('hidden');
        DOM.budgetInput.focus();
    });

    DOM.cancelBudgetBtn.addEventListener('click', () => {
        DOM.budgetModal.classList.add('hidden');
    });

    DOM.saveBudgetBtn.addEventListener('click', saveBudget);
    DOM.budgetInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') saveBudget();
    });

    DOM.budgetModal.addEventListener('click', (e) => {
        if (e.target === DOM.budgetModal) DOM.budgetModal.classList.add('hidden');
    });

    DOM.checkoutBtn.addEventListener('click', processCheckout);

    // Checkout Modal Reset Logic
    DOM.newTripBtn.addEventListener('click', () => {
        DOM.checkoutModal.classList.add('hidden');
        window.location.href = '/customer'; // redirect natively to customer DB
    });

    DOM.checkoutModal.addEventListener('click', (e) => {
        if (e.target === DOM.checkoutModal) {
            DOM.checkoutModal.classList.add('hidden');
            window.location.href = '/customer';
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !DOM.checkoutModal.classList.contains('hidden')) {
            DOM.checkoutModal.classList.add('hidden');
            window.location.href = '/customer';
        }
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(parseFloat(amount));
}

function playScanSound() {
    if (navigator.vibrate) navigator.vibrate(50);
}

function saveBudget() {
    const val = parseFloat(DOM.budgetInput.value);
    if (!isNaN(val) && val > 0) {
        state.budget = val;

        DOM.setBudgetBtn.style.display = 'none';
        DOM.globalBudgetDisplay.style.display = 'flex';

        updateCartUI();
        DOM.budgetModal.classList.add('hidden');
    }
}

window.addToCart = function (productId) {
    const product = state.products.find(p => p.id === productId);
    if (!product) return;

    const existingItem = state.cart.find(item => item.id === productId);

    // Stock validation check
    const currentQty = existingItem ? existingItem.quantity : 0;
    if (currentQty + 1 > product.stock) {
        alert(`Cannot add more.Only ${product.stock} items left in stock.`);
        return;
    }

    playScanSound();

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        state.cart.push({ ...product, quantity: 1 });
    }

    console.log("Product clicked:", productId);
    console.log("Cart before:", state.cart);

    renderCart();
};

window.updateQty = function (productId, delta) {
    const itemIndex = state.cart.findIndex(item => item.id === productId);
    if (itemIndex > -1) {
        const item = state.cart[itemIndex];
        const product = state.products.find(p => p.id === productId);

        // Stock Validation
        if (delta > 0 && item.quantity + delta > product.stock) {
            alert(`Cannot add more.Only ${product.stock} items left in stock.`);
            return;
        }

        state.cart[itemIndex].quantity += delta;
        if (state.cart[itemIndex].quantity <= 0) {
            state.cart.splice(itemIndex, 1);
        }
        renderCart();
    }
};

function getCartTotals() {
    let subtotal = 0;
    let weight = 0;
    state.cart.forEach(item => {
        subtotal += parseFloat(item.price) * item.quantity;
        weight += parseInt(item.weight_g) * item.quantity;
    });
    const tax = subtotal * state.taxRate;
    const total = subtotal + tax;
    return { subtotal, tax, total, weight };
}

function updateCartUI() {
    const { subtotal, tax, total, weight } = getCartTotals();
    const totalItems = state.cart.reduce((sum, item) => sum + item.quantity, 0);

    // Update numbers
    DOM.cartItemCount.textContent = totalItems.toString();
    DOM.statTotalItems.textContent = totalItems.toString();
    DOM.cartWeight.textContent = weight + 'g';
    DOM.cartSubtotal.textContent = formatCurrency(subtotal);
    DOM.cartTax.textContent = formatCurrency(tax);
    DOM.cartTotal.textContent = formatCurrency(total);

    // Update List
    if (state.cart.length === 0) {
        DOM.checkoutBtn.disabled = true;
    } else {
        DOM.checkoutBtn.disabled = false;
    }

    // Update Budget Logic
    if (state.budget) {
        DOM.budgetProgressContainer.classList.remove('hidden');
        const remaining = state.budget - total;
        DOM.budgetAmountDisplay.textContent = formatCurrency(remaining);

        const percentage = Math.min((total / state.budget) * 100, 100);
        DOM.progressBarFill.style.width = `${percentage}% `;
        DOM.budgetPercentage.textContent = `${percentage.toFixed(0)}% `;

        DOM.globalBudgetDisplay.classList.remove('warning', 'danger');
        DOM.progressBarFill.style.backgroundColor = 'var(--primary)';
        DOM.budgetWarning.style.display = 'none';
        DOM.budgetDanger.style.display = 'none';

        if (percentage >= 100) {
            DOM.globalBudgetDisplay.classList.add('danger');
            DOM.progressBarFill.style.backgroundColor = 'var(--danger)';
            DOM.budgetDanger.style.display = 'block';
        } else if (percentage >= 80) {
            DOM.globalBudgetDisplay.classList.add('warning');
            DOM.progressBarFill.style.backgroundColor = 'var(--warning)';
            DOM.budgetWarning.style.display = 'block';
        }
    }
}

async function processCheckout() {
    DOM.checkoutBtn.disabled = true;
    DOM.checkoutBtn.innerHTML = '<div class="loader" style="width:1rem;height:1rem;border-top-color:white;border-right-color:white;border-bottom-color:white;border-left-color:transparent;"></div>';

    const checkoutCart = state.cart.map(item => ({ id: item.id, qty: item.quantity }));

    try {
        const res = await fetch('/api/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cart: checkoutCart })
        });

        const data = await res.json();
        if (data.error) throw new Error(data.error);

        DOM.finalPaidAmount.textContent = formatCurrency(data.total_paid);
        DOM.receiptQr.textContent = data.exit_code;
        DOM.checkoutModal.classList.remove('hidden');

        // Reset state after checkout to prevent lingering cart data
        state.cart = [];
        updateCartUI();

    } catch (err) {
        alert("Checkout failed: " + err.message);
        DOM.checkoutBtn.disabled = false;
        DOM.checkoutBtn.innerHTML = `< span > Confirm Payment</span > `;
    }
}

function renderCart() {
    try {
        console.log("renderCart called");
        console.log("Cart state:", state.cart);

        const cartContainer = DOM.cartItemsContainer;
        const emptyState = DOM.emptyState;

        if (!cartContainer || !emptyState){
            console.error("Cart container #cart-items or #empty-state not found!");
            setTimeout(renderCart, 100);
            return;
        } 

        cartContainer.querySelectorAll(".cart-item").forEach(el => el.remove());

        if (state.cart.length === 0) {
            emptyState.style.display = "flex";
        } else {
            emptyState.style.display = "none";
            
            state.cart.forEach(item => {
                let imagePath = item.image_url;

                if (!item.image_url.startsWith("http")) {
                    imagePath = `/static/images/${item.image_url}`;
                }

                const cartItem = document.createElement("div");
                cartItem.className = "cart-item";

                cartItem.innerHTML = `
                    <img src="${imagePath}" class="cart-thumb" onerror="this.src='/static/images/product_placeholder.png'">
                    <div class="cart-info">
                        <div class="cart-title">${item.name}</div>
                        <div class="cart-meta">₹${item.price} • ${item.weight_g}g</div>
                    </div>
                    <div class="cart-controls">
                        <button onclick="updateQty(${item.id}, -1)">-</button>
                        <span>${item.quantity}</span>
                        <button onclick="updateQty(${item.id}, 1)">+</button>
                    </div>
                `;

                cartContainer.appendChild(cartItem);
            });
        }

        updateCartUI();
    } catch(e) {
        console.error("Cart render error:", e);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initDOM();
    init();
    renderCart();
});


// ==========================================
// QR CODE SCANNER LOGIC
// ==========================================
const scannerModal = document.getElementById('scanner-modal');
const startScanBtn = document.getElementById('start-scan-btn');
const closeScanBtn = document.getElementById('close-scanner-btn');
let html5QrCode;

if (startScanBtn && scannerModal) {
    startScanBtn.addEventListener('click', () => {
        scannerModal.classList.remove('hidden');
        
        // Initialize the scanner
        html5QrCode = new Html5Qrcode("reader");
        html5QrCode.start(
            { facingMode: "environment" }, // Prefer back camera on phones
            {
                fps: 10,
                qrbox: { width: 250, height: 250 }
            },
            (decodedText, decodedResult) => {
                // SUCCESSFUL SCAN!
                html5QrCode.stop(); // Turn off camera
                scannerModal.classList.add('hidden');
                handleSuccessfulScan(decodedText);
            },
            (errorMessage) => {
                // Ignore background frame errors, it happens constantly while searching for a QR code
            }
        ).catch((err) => {
            alert("Camera access denied or not available. Please allow camera permissions.");
            scannerModal.classList.add('hidden');
        });
    });

    closeScanBtn.addEventListener('click', () => {
        if (html5QrCode) {
            html5QrCode.stop().catch(err => console.error(err));
        }
        scannerModal.classList.add('hidden');
    });
}

async function handleSuccessfulScan(scannedText) {
    if (!scannedText.startsWith('SMARTMART:')) {
        alert('Invalid QR Code. Please scan a valid SmartMart product tag.');
        return;
    }

    // Extract the barcode/SKU from the QR Code
    const productIdentifier = scannedText.split(':')[1];
    
    // Find the product in our locally loaded database
    const product = state.products.find(p => 
        String(p.id) === String(productIdentifier) || 
        String(p.barcode) === String(productIdentifier)
    );

    if (!product) {
        alert('Product not found in the current store catalog.');
        return;
    }

    // Add it to the JS Cart exactly as if the user clicked it!
    addToCart(product.id);

    // Flash a nice success message on the button
    const scanBtn = document.getElementById('start-scan-btn');
    const originalText = scanBtn.innerHTML;
    
    scanBtn.innerHTML = `✅ ${product.name} Added!`;
    scanBtn.style.background = '#059669'; // Turn button green
    scanBtn.style.color = 'white';
    
    // Change the button back to normal after 2 seconds
    setTimeout(() => {
        scanBtn.innerHTML = originalText;
        scanBtn.style.background = 'var(--text-main)';
    }, 2000);
}


// --- Modal Visibility Controls ---
function openProfileModal() { document.getElementById('profile-modal').classList.remove('hidden'); }
function openSupportModal() { document.getElementById('support-modal').classList.remove('hidden'); }
function closeAppModal(modalId) { document.getElementById(modalId).classList.add('hidden'); }

// --- Profile Unlock Logic ---
function unlockProfile() {
    // 1. Remove the 'disabled' attribute from all inputs
    document.querySelectorAll('.profile-input').forEach(input => input.disabled = false);
    
    // 2. Show the password box and swap the buttons
    document.getElementById('profile-password-group').classList.remove('hidden');
    document.getElementById('btn-unlock-profile').classList.add('hidden');
    document.getElementById('btn-save-profile').classList.remove('hidden');
    
    // 3. Focus the first input
    document.getElementById('prof-name').focus();
}

// --- Real AJAX Save Profile ---
async function saveProfile() {
    const password = document.getElementById('prof-password').value;
    if (!password) {
        alert("Password is required to save changes.");
        return;
    }

    const payload = {
        full_name: document.getElementById('prof-name').value,
        dob: document.getElementById('prof-dob').value,
        email: document.getElementById('prof-email').value,
        mobile: document.getElementById('prof-mobile').value,
        gender: document.getElementById('prof-gender').value,
        wants_offers: document.getElementById('prof-offers').checked,
        password: password
    };

    try {
        const response = await fetch('/update_profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert("Profile successfully updated!");
            
            // Re-lock the UI
            document.querySelectorAll('.profile-input').forEach(input => input.disabled = true);
            document.getElementById('profile-password-group').classList.add('hidden');
            document.getElementById('btn-unlock-profile').classList.remove('hidden');
            document.getElementById('btn-save-profile').classList.add('hidden');
            document.getElementById('prof-password').value = ''; // clear password
            
            closeAppModal('profile-modal');
        } else {
            alert("Update failed: " + result.message);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("A network error occurred.");
    }
}

// --- Real AJAX Submit Support ---
async function submitSupport() {
    const type = document.getElementById('support-type').value;
    const msg = document.getElementById('support-message').value;
    
    if (!msg.trim()) {
        alert("Please enter a message before submitting.");
        return;
    }
    
    try {
        const response = await fetch('/submit_support', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: type, message: msg })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert("Message sent successfully! Our team will review it.");
            document.getElementById('support-message').value = ''; // Clear box
            closeAppModal('support-modal');
        } else {
            alert("Failed to send: " + result.message);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("A network error occurred.");
    }
}