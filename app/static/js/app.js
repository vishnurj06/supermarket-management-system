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
        
        // 1. Smart Stock Logic
        const isOutOfStock = p.stock <= 0;
        let stockBadge = '';
        if (isOutOfStock) {
            stockBadge = `<span class="status-badge status-alert" style="margin-left: 0.3rem;">Out of Stock</span>`;
        } else if (p.stock < 10) {
            stockBadge = `<span class="low-stock-badge">Low Stock</span>`;
        }

        // 2. Disable clicks and fade out if out of stock
        const clickEvent = isOutOfStock ? '' : `onclick="addToCart(${p.id})"`;
        const cardStyle = isOutOfStock ? 'opacity: 0.5; cursor: not-allowed; filter: grayscale(100%);' : '';
        const scanIcon = isOutOfStock ? '' : `<div class="scan-action"></div>`;

        return `
        <div class="product-card" ${clickEvent} style="${cardStyle}">
            <img class="product-image" src="${imagePath}" alt="${p.name}" onerror="this.src='/static/images/product_placeholder.png'">
            <div class="product-info">
                <span class="product-name">${p.name}</span>
                <span class="product-price">${formatCurrency(p.price)}</span>
                <span class="product-weight">${p.weight_g}g</span>
                <div>${stockBadge}</div>
            </div>
            ${scanIcon}
        </div>
        `;
    }).join('');
}

window.handleImageError = function (img, category) {
    img.onerror = null; // Prevent infinite loops
    img.src = '/static/images/products/supermarket_product.png';
};

function init() {
    loadFromMemory();
    fetchProducts();
    setupEventListeners();
}

function setupEventListeners() {
    // Search
    if (DOM.searchInput) {
        DOM.searchInput.addEventListener('input', (e) => {
            state.searchQuery = e.target.value;
            renderProducts();
        });
    }

    // Safely handle old desktop buttons if they exist
    if (DOM.setBudgetBtn) {
        DOM.setBudgetBtn.addEventListener('click', () => {
            window.budgetSource = 'header';
            if (state.budget) DOM.budgetInput.value = state.budget;
            DOM.budgetModal.classList.remove('hidden');
            DOM.budgetInput.focus();
        });
    }

    if (DOM.globalBudgetDisplay) {
        DOM.globalBudgetDisplay.addEventListener('click', () => {
            window.budgetSource = 'header';
            DOM.budgetInput.value = state.budget || '';
            DOM.budgetModal.classList.remove('hidden');
            DOM.budgetInput.focus();
        });
    }

    // Modal Actions
    if (DOM.cancelBudgetBtn) {
        DOM.cancelBudgetBtn.addEventListener('click', () => {
            DOM.budgetModal.classList.add('hidden');
        });
    }

    if (DOM.saveBudgetBtn) {
        DOM.saveBudgetBtn.addEventListener('click', saveBudget);
    }

    if (DOM.budgetInput) {
        DOM.budgetInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') saveBudget();
        });
    }

    if (DOM.budgetModal) {
        DOM.budgetModal.addEventListener('click', (e) => {
            if (e.target === DOM.budgetModal) DOM.budgetModal.classList.add('hidden');
        });
    }

    if (DOM.checkoutBtn) DOM.checkoutBtn.addEventListener('click', processCheckout);

    // Checkout Modal Reset Logic
    if (DOM.newTripBtn) {
        DOM.newTripBtn.addEventListener('click', () => {
            DOM.checkoutModal.classList.add('hidden');
            window.location.href = '/customer'; 
        });
    }

    if (DOM.checkoutModal) {
        DOM.checkoutModal.addEventListener('click', (e) => {
            if (e.target === DOM.checkoutModal) {
                DOM.checkoutModal.classList.add('hidden');
                window.location.href = '/customer';
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && DOM.checkoutModal && !DOM.checkoutModal.classList.contains('hidden')) {
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

    saveToMemory();
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
    saveToMemory();
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

        const finalExitCode = data.exit_code;
        const qrData = `SMARTMART:${finalExitCode}`;
        const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(qrData)}`;

        // 1. Build the itemized list
        let itemsHtml = state.cart.map(item => `
            <div style="display:flex; justify-content:space-between; font-size:0.85rem; border-bottom:1px dashed #e2e8f0; padding:6px 0; color: #475569;">
                <span>${item.quantity}x ${item.name}</span>
                <span style="font-weight:600;">₹${(item.price * item.quantity).toFixed(2)}</span>
            </div>
        `).join('');

        // 2. Inject the Real Itemized Receipt + QR Image
        DOM.finalPaidAmount.textContent = formatCurrency(data.total_paid);
        DOM.receiptQr.innerHTML = `
            <div id="printable-receipt" style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: left; margin-bottom: 20px;">
                <h3 style="text-align:center; margin-top:0; color:#1e293b; font-size:1.1rem;">SmartMart Digital Receipt</h3>
                <div style="color: #64748b; font-size: 0.8rem; text-align:center; margin-bottom: 10px;">Exit Code: #${finalExitCode}</div>
                ${itemsHtml}
                <div style="display:flex; justify-content:space-between; font-weight:bold; margin-top:10px; font-size: 1rem; color: #1e293b;">
                    <span>Total Paid:</span>
                    <span>₹${data.total_paid}</span>
                </div>
            </div>
            
            <img src="${qrUrl}" alt="Exit QR Code" style="border-radius: 8px; border: 4px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 0 auto; display: block; width: 150px;">
            <div style="font-size: 1.2rem; margin-top: 10px; color: #1e293b; font-weight: bold; text-align: center;">#${finalExitCode}</div>
            
            <button onclick="printCurrentReceipt('${finalExitCode}')" style="margin-top: 20px; background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; width: 100%;">
                📄 Download / Print Receipt
            </button>
            <style>
                @media print {
                    body * { visibility: hidden; }
                    #checkout-modal, #checkout-modal * { visibility: visible; }
                    #checkout-modal { position: absolute; left: 0; top: 0; width: 100%; box-shadow: none; padding: 0; }
                    .modal-content { max-height: none !important; overflow: visible !important; width: 100% !important; max-width: 100% !important; padding: 0 !important; }
                    button, .close-btn, h2 { display: none !important; }
                }
            </style>
        `;
        
        DOM.checkoutModal.classList.remove('hidden');

        // NEW: Automatically slide down the mobile cart sheet
        if (typeof closeMobileCart === 'function') {
            closeMobileCart();
        }

        state.cart = [];
        updateCartUI();
        saveToMemory();

    } catch (err) {
        alert("Checkout failed: " + err.message);
        DOM.checkoutBtn.disabled = false;
        DOM.checkoutBtn.innerHTML = `<span>Confirm Payment</span>`;
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
                    <div class="cart-details">
                        <div class="cart-title">${item.name}</div>
                        <div class="cart-price">₹${item.price} • ${item.weight_g}g</div>
                    </div>
                    <div class="cart-qty">
                        <button onclick="updateQty(${item.id}, -1)">-</button>
                        <span class="item-qty">${item.quantity}</span>
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
    initPromoSlider();
});

// ==========================================
// QR CODE SCANNER LOGIC
// ==========================================
const scannerModal = document.getElementById('scanner-modal');
const closeScanBtn = document.getElementById('close-scanner-btn');
let html5QrCode;

if (scannerModal) {
    // Attach the camera logic to ALL scan buttons (Desktop + Mobile)
    document.querySelectorAll('.scan-trigger').forEach(btn => {
        btn.addEventListener('click', () => {
            scannerModal.classList.remove('hidden');
            
            // Initialize the scanner
            html5QrCode = new Html5Qrcode("reader");
            html5QrCode.start(
                { facingMode: "environment" }, 
                { fps: 10, qrbox: { width: 250, height: 250 } },
                (decodedText, decodedResult) => {
                    html5QrCode.stop(); // Turn off camera
                    scannerModal.classList.add('hidden');
                    handleSuccessfulScan(decodedText);
                },
                (errorMessage) => { /* Ignore background frame errors */ }
            ).catch((err) => {
                alert("Camera access denied or not available. Please allow camera permissions.");
                scannerModal.classList.add('hidden');
            });
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

    // NEW: Premium Toast Notification!
    const shortName = product.name.length > 18 ? product.name.substring(0, 18) + '...' : product.name;
    
    // Create the toast element if it doesn't exist
    let toast = document.getElementById('premium-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'premium-toast';
        toast.className = 'premium-toast';
        document.body.appendChild(toast);
    }
    
    // Set the text and slide it down
    toast.innerHTML = `✅ <span style="margin-left: 5px;">${shortName} Added</span>`;
    
    // Force reflow and add the 'show' class to trigger CSS animation
    void toast.offsetWidth; 
    toast.classList.add('show');
    
    // Slide it back up after 2.5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2500);
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
async function saveProfile(event) {
    if (event) event.preventDefault(); 

    const passwordField = document.getElementById('prof-password');
    if (!passwordField.value) {
        alert("Password is required to save changes.");
        return;
    }

    // --- (Your fetch payload logic remains the same) ---
    const payload = {
        full_name: document.getElementById('prof-name').value,
        dob: document.getElementById('prof-dob').value,
        email: document.getElementById('prof-email').value,
        mobile: document.getElementById('prof-mobile').value,
        gender: document.getElementById('prof-gender').value,
        wants_offers: document.getElementById('prof-offers').checked,
        password: passwordField.value
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
            
            // Re-lock the fields and toggle buttons
            document.querySelectorAll('.profile-input').forEach(input => input.disabled = true);
            document.getElementById('profile-password-group').classList.add('hidden');
            document.getElementById('btn-unlock-profile').classList.remove('hidden');
            document.getElementById('btn-save-profile').classList.add('hidden');
            passwordField.value = ''; 

            // SUCCESS STATE: Stay on the Edit Profile tab but in "Locked" mode
            // This prevents the "Double Menu" glitch you saw in the screenshot
            const hubView = document.getElementById('hub-view');
            const editView = document.getElementById('edit-profile-view');
            
            if (editView) editView.classList.remove('hidden');
            if (hubView) hubView.classList.add('hidden');

        } else {
            alert("Update failed: " + result.message);
        }
    } catch (error) {
        console.error("Error:", error);
    }
}

// --- Real AJAX Submit Support ---
// --- Real AJAX Submit Support (Upgraded) ---
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
            // 1. Show the Premium Toast instead of an alert
            let toast = document.getElementById('premium-toast');
            if (!toast) {
                toast = document.createElement('div');
                toast.id = 'premium-toast';
                toast.className = 'premium-toast';
                document.body.appendChild(toast);
            }
            toast.innerHTML = `✅ <span style="margin-left: 5px;">Ticket Submitted</span>`;
            void toast.offsetWidth; 
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2500);

            // 2. Instantly inject the new ticket into the UI
            const ticketsContainer = document.querySelector('#support-modal .modal-content > div:last-child > div');
            if (ticketsContainer) {
                // Clear the "No past tickets" message if it's the first ticket
                const emptyMsg = ticketsContainer.querySelector('p');
                if (emptyMsg) emptyMsg.remove();

                // Create and prepend the new ticket
                const newTicket = document.createElement('div');
                newTicket.style.cssText = "padding: 0.8rem; border: 1px solid var(--border); border-radius: var(--radius-sm); margin-bottom: 0.5rem; background: var(--bg-glass); animation: fadeSlideUp 0.3s ease;";
                newTicket.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
                        <span style="font-size: 0.8rem; color: var(--text-main);">${type}</span>
                        <span class="status-badge status-pending">OPEN</span>
                    </div>
                    <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0;">${msg}</p>
                `;
                ticketsContainer.insertBefore(newTicket, ticketsContainer.firstChild);
            }

            // 3. Clear the text box, but DO NOT close the modal
            document.getElementById('support-message').value = ''; 
            
        } else {
            alert("Failed to send: " + result.message);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("A network error occurred.");
    }
}

// --- Mobile Cart Overlay Logic ---
window.toggleMobileCart = function() {
    document.querySelector('.cart-section').classList.toggle('mobile-open');
    document.body.classList.toggle('no-scroll');
    document.body.classList.add('cart-open-state');
    
    const backdrop = document.getElementById('cart-sheet-backdrop');
    if (backdrop) backdrop.classList.toggle('visible');

};

window.closeMobileCart = function() {
    document.querySelector('.cart-section').classList.remove('mobile-open');
    document.body.classList.remove('no-scroll');
    document.body.classList.remove('cart-open-state');
    
    const backdrop = document.getElementById('cart-sheet-backdrop');
    if (backdrop) backdrop.classList.remove('visible');
};

// --- Secure Print Logic ---
window.printCurrentReceipt = function(exitCode) {
    const printWindow = window.open('', '_blank', 'width=400,height=600');
    const receiptContent = document.getElementById('printable-receipt').innerHTML;
    const qrImage = document.getElementById('receipt-qr').querySelector('img').src;

    printWindow.document.write(`
        <html><head><title>Receipt #${exitCode}</title></head>
        <body style="font-family:sans-serif; padding:20px; max-width:400px; margin:0 auto; color:#333;">
            ${receiptContent}
            <div style="text-align:center; margin-top:30px;">
                <img src="${qrImage}" style="width: 150px; height: 150px;" />
                <div style="font-size: 1.2rem; margin-top: 10px; font-weight: bold; color: #1e293b;">#${exitCode}</div>
            </div>
            <script>window.onload = function() { window.print(); window.close(); }<\/script>
        </body></html>
    `);
};

// --- Profile Hub View Toggle ---
window.toggleProfileView = function(view) {
    if (view === 'edit') {
        document.getElementById('hub-view').classList.add('hidden');
        document.getElementById('edit-view').classList.remove('hidden');
    } else {
        document.getElementById('edit-view').classList.add('hidden');
        document.getElementById('hub-view').classList.remove('hidden');
        
        // Re-lock the form when going back
        document.querySelectorAll('.profile-input').forEach(input => input.disabled = true);
        document.getElementById('profile-password-group').classList.add('hidden');
        document.getElementById('btn-unlock-profile').classList.remove('hidden');
        document.getElementById('btn-save-profile').classList.add('hidden');
    }
};

// --- Profile Reset Fix ---
window.closeProfileModal = function() {
    // 1. Physically close the modal
    const modal = document.getElementById('profile-modal');
    if (modal) modal.classList.add('hidden');

    // 2. Reset the views so it's clean for the next time it opens
    const hubView = document.getElementById('hub-view');
    const editView = document.getElementById('edit-profile-view');
    
    if (hubView) hubView.classList.remove('hidden');
    if (editView) editView.classList.add('hidden');
};

// --- Browser Memory (Keeps Cart & Budget on Refresh) ---
function saveToMemory() {
    localStorage.setItem('smartmart_cart', JSON.stringify(state.cart));
    
    // LOGIC FIX: Delete the file if budget is empty
    if (state.budget && state.budget > 0) {
        localStorage.setItem('smartmart_budget', state.budget);
    } else {
        localStorage.removeItem('smartmart_budget');
    }
}

function loadFromMemory() {
    const savedCart = localStorage.getItem('smartmart_cart');
    const savedBudget = localStorage.getItem('smartmart_budget');
    
    if (savedCart) state.cart = JSON.parse(savedCart);
    
    if (savedBudget) {
        const parsed = parseFloat(savedBudget);
        if (!isNaN(parsed) && parsed > 0) state.budget = parsed;
    }
}

// --- Global Modal Backdrop Click ---
// Automatically close any modal when the dark background is clicked
document.addEventListener('click', (e) => {
    // If the element clicked has the class 'modal' (which is the dark backdrop)
    if (e.target.classList.contains('modal')) {
        closeAppModal(e.target.id);
        
        // If they click the background of Edit Profile, reset it to Hub safely
        if (e.target.id === 'profile-modal') {
            toggleProfileView('hub'); 
        }
    }
});

// --- Smart Profile Back Button ---
window.handleProfileBack = function() {
    const nameInput = document.getElementById('prof-name');
    
    if (!nameInput.disabled) {
        // The form is currently UNLOCKED. Just lock it, don't leave the page.
        document.querySelectorAll('.profile-input').forEach(input => input.disabled = true);
        document.getElementById('profile-password-group').classList.add('hidden');
        document.getElementById('btn-unlock-profile').classList.remove('hidden');
        document.getElementById('btn-save-profile').classList.add('hidden');
        document.getElementById('prof-password').value = '';
    } else {
        // The form is ALREADY LOCKED. Safe to go back to the Hub.
        toggleProfileView('hub');
    }
};

// --- Auto-Sliding Promo Carousel ---
// --- Auto-Sliding Promo Carousel (Upgraded Engine) ---
// --- Bulletproof Auto-Sliding Promo Carousel ---
// --- Auto-Sliding Promo Carousel (Upgraded Engine) ---
// --- Bulletproof Mathematical Promo Carousel ---
window.initPromoSlider = function() {
    const slider = document.getElementById('promo-slider');
    const dots = document.querySelectorAll('.slider-dots .dot');
    if (!slider || dots.length === 0) return;

    let totalSlides = dots.length;
    let autoSlideInterval;

    // 1. Pure Math Dot Updater
    function updateDots() {
        // Calculate exactly which slide is visible based on raw scroll pixels
        let currentIndex = Math.round(slider.scrollLeft / slider.clientWidth);
        
        // Safety check to prevent index out of bounds
        if (currentIndex < 0) currentIndex = 0;
        if (currentIndex >= totalSlides) currentIndex = totalSlides - 1;

        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === currentIndex);
        });
    }

    // 2. Listen to the native scroll event (Fires continuously when swiped)
    slider.addEventListener('scroll', updateDots, { passive: true });

    // 3. Simple Auto-Advance Engine
    function startAutoSlide() {
        clearInterval(autoSlideInterval);
        autoSlideInterval = setInterval(() => {
            let currentIndex = Math.round(slider.scrollLeft / slider.clientWidth);
            let nextIndex = (currentIndex + 1) % totalSlides;
            
            slider.scrollTo({
                left: nextIndex * slider.clientWidth,
                behavior: 'smooth'
            });
        }, 3500); // 3.5 seconds
    }

    // 4. Pause if the user touches the screen
    slider.addEventListener('touchstart', () => clearInterval(autoSlideInterval), { passive: true });
    slider.addEventListener('touchend', () => {
        setTimeout(startAutoSlide, 3000); // Resume 3 seconds after letting go
    }, { passive: true });

    // Kickstart
    updateDots();
    startAutoSlide();
};

// --- Smart Budget Back Button ---
window.handleBudgetBack = function() {
    closeAppModal('budget-modal');
    if (window.budgetSource === 'profile') {
        openProfileModal();
    }
};

function saveBudget() {
    const val = parseFloat(DOM.budgetInput.value);
    
    // LOGIC FIX: If it's a valid number, save it. Otherwise, CLEAR IT.
    if (!isNaN(val) && val > 0) {
        state.budget = val;
    } else {
        state.budget = null; 
    }

    if (DOM.setBudgetBtn) DOM.setBudgetBtn.style.display = 'none';
    if (DOM.globalBudgetDisplay) DOM.globalBudgetDisplay.style.display = 'flex';

    updateCartUI();
    if (DOM.budgetModal) DOM.budgetModal.classList.add('hidden');
    saveToMemory();
}

function updateCartUI() {
    const { subtotal, tax, total, weight } = getCartTotals();
    const totalItems = state.cart.reduce((sum, item) => sum + item.quantity, 0);

    if (DOM.cartItemCount) DOM.cartItemCount.textContent = totalItems.toString();
    if (DOM.statTotalItems) DOM.statTotalItems.textContent = totalItems.toString();
    if (DOM.cartWeight) DOM.cartWeight.textContent = weight + 'g';
    if (DOM.cartSubtotal) DOM.cartSubtotal.textContent = formatCurrency(subtotal);
    if (DOM.cartTax) DOM.cartTax.textContent = formatCurrency(tax);
    if (DOM.cartTotal) DOM.cartTotal.textContent = formatCurrency(total);

    const bottomBadge = document.getElementById('bottom-nav-badge');
    if(bottomBadge) {
        bottomBadge.textContent = totalItems.toString();
        bottomBadge.style.display = totalItems > 0 ? 'flex' : 'none';
    }

    if (DOM.checkoutBtn) {
        DOM.checkoutBtn.disabled = state.cart.length === 0;
    }

    // ==========================================
    // SMART BUDGET TRACKER LOGIC
    // ==========================================
    const sbb = document.getElementById('sticky-budget-bar');
    const sbbAmount = document.getElementById('sbb-amount');
    const sbbFill = document.getElementById('sbb-fill');
    const sbbWarning = document.getElementById('sbb-warning-container');
    const headerBudgetText = document.getElementById('header-budget-display-text');

    // LOGIC FIX: If no budget, actively HIDE all UI elements
    if (!state.budget || state.budget <= 0) {
        if (sbb) sbb.classList.add('hidden');
        if (DOM.budgetProgressContainer) DOM.budgetProgressContainer.classList.add('hidden');
        if (headerBudgetText) headerBudgetText.textContent = "Set Limit";
        
        const hubBudget = document.getElementById('hub-budget-value');
        if (hubBudget) hubBudget.textContent = 'Not Set';
        return; // Stop the function here so the old bar doesn't load!
    }

    // Budget is active: run the math
    if (headerBudgetText) headerBudgetText.textContent = formatCurrency(state.budget);
    if (DOM.budgetProgressContainer) DOM.budgetProgressContainer.classList.remove('hidden');
    
    const remaining = state.budget - total;
    const percentage = total === 0 ? 0 : Math.min((total / state.budget) * 100, 100);

    if (DOM.budgetAmountDisplay) DOM.budgetAmountDisplay.textContent = formatCurrency(remaining);
    if (DOM.progressBarFill) DOM.progressBarFill.style.width = `${percentage}%`;
    if (DOM.budgetPercentage) DOM.budgetPercentage.textContent = `${percentage.toFixed(0)}%`;

    if (sbb && sbbAmount && sbbFill) {
        sbb.classList.remove('hidden'); 
        sbbAmount.textContent = formatCurrency(remaining);
        sbbFill.style.width = `${percentage}%`;
        
        sbb.classList.remove('status-safe', 'status-warning', 'status-danger');
        
        if (sbbWarning) {
            sbbWarning.innerHTML = '';
            sbbWarning.style.display = 'none';
        }

        if (percentage >= 100) {
            sbb.classList.add('status-danger');
            if (sbbWarning) {
                sbbWarning.style.display = 'flex';
                sbbWarning.innerHTML = '🛑 Over';
            }
        } else if (percentage >= 80) {
            sbb.classList.add('status-warning');
            if (sbbWarning) {
                sbbWarning.style.display = 'flex';
                sbbWarning.innerHTML = '⚠️ High';
            }
        } else {
            sbb.classList.add('status-safe');
        }
    }

    const hubBudget = document.getElementById('hub-budget-value');
    if (hubBudget) hubBudget.textContent = formatCurrency(state.budget);
}

(function () {
    const cartSheet   = document.querySelector('.cart-section');
    const budgetBar   = document.getElementById('sticky-budget-bar');
    const bottomNav   = document.querySelector('.mobile-bottom-nav');

    if (!cartSheet || !budgetBar) return;

    /* Height of the bottom nav (fallback 72px) */
    const navH = () => (bottomNav ? bottomNav.offsetHeight : 72);

    function liftBudgetBar() {
        /*
         * The cart sheet has just received .active but the browser
         * hasn't painted it yet — its offsetHeight is still 0.
         *
         * Strategy: read the height AFTER two animation frames so
         * the browser has performed layout, then set the CSS custom
         * property that drives the bar's `bottom` value.
         */
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                const cartH   = cartSheet.offsetHeight;
                const target  = navH() + cartH;          // px above nav bottom edge

                budgetBar.style.setProperty('--sbb-lifted-bottom', target + 'px');
                budgetBar.classList.add('cart-open');
            });
        });
    }

    function dropBudgetBar() {
        /* Remove lifted state — CSS transition glides it back */
        budgetBar.classList.remove('cart-open');
        budgetBar.style.removeProperty('--sbb-lifted-bottom');
    }

    /* ── MutationObserver: watch for .active on the cart sheet ── */
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((m) => {
            if (m.attributeName !== 'class') return;
            cartSheet.classList.contains('active')
                ? liftBudgetBar()
                : dropBudgetBar();
        });
    });

    observer.observe(cartSheet, { attributes: true });

    /* ── Also handle window resize (keyboard open on mobile) ──── */
    let resizeRaf;
    window.addEventListener('resize', () => {
        cancelAnimationFrame(resizeRaf);
        resizeRaf = requestAnimationFrame(() => {
            if (cartSheet.classList.contains('active')) liftBudgetBar();
        });
    }, { passive: true });
})();
