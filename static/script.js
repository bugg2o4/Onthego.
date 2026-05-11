async function loadUser() {
    const res = await fetch("/me");
    const data = await res.json();

    const loginBtn = document.getElementById("loginBtn");
    const userMenu = document.getElementById("userMenu");
    const userName = document.getElementById("userName");

    if (data.logged_in) {
        loginBtn.style.display = "none";
        userMenu.classList.remove("hidden");
        userName.textContent = data.name;
    } else {
        loginBtn.style.display = "block";
        userMenu.classList.add("hidden");
    }
}

document.getElementById("logoutBtn")?.addEventListener("click", async (e) => {
    e.preventDefault();

    await fetch("/logout", { credentials: "include" });

    location.reload();
});

function normalizeProduct(p) {
    return {
        id: p.id || Math.random(),
        name: p.name,
        description: p.description || "",
        price: typeof p.price === "number"
            ? p.price
            : parseFloat(String(p.price).replace("$", "")),
        image: p.image || p.img || "",
        category: p.category
    };
}

document.addEventListener("DOMContentLoaded", () => {

    const productGrid = document.getElementById("product-grid");
    const searchInput = document.querySelector(".search-input");
    const tabs = document.querySelectorAll(".tabs a");

    let allProducts = [];
    let wishlist = [];

    async function loadData() {
    try {
        const res = await fetch("/products");
        const data = await res.json();

        allProducts = data.map(normalizeProduct);

        const w = await fetch("/wishlist", { credentials: "include" });
        if (w.ok) {
            wishlist = await w.json();
        }

        displayProducts(allProducts);

    } catch (err) {
        console.error(err);
    }
    loadUser();
}

    function displayProducts(list) {
        productGrid.innerHTML = "";

        list.forEach(product => {
           const inWish = wishlist.some(w => w.id === product.id);

            const card = document.createElement("div");
            card.className = "product-card";

            card.innerHTML = `
    <div class="product-tumb">
        <img src="${product.image}" />
        <div class="product-hover-desc">
            <p>${product.description || "No description available"}</p>
        </div>
    </div>

    <div class="product-details">
        <span class="product-catagory">${product.category || ""}</span>

        <h4>${product.name}</h4>

        <div class="product-bottom-details">

            <div class="product-price">
                $${product.price}
            </div>

            <div class="product-links">
                <a href="#" class="add-cart">
                    <i class="fa fa-shopping-cart"></i>
                </a>

                <a href="#" class="wishlist-btn">
                    <i class="fa fa-heart ${inWish ? "active-heart" : ""}"></i>
                </a>
            </div>

        </div>
    </div>
`;

            productGrid.appendChild(card);

            // ================= CART =================
            card.querySelector(".add-cart").addEventListener("click", async (e) => {
    e.preventDefault();

    try {
        const res = await fetch("/cart/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ product_id: product.id })
        });

        const data = await res.json();

        console.log("CART:", data);

        if (!data.success) {
            alert(data.message || "Please log in");
            return;
        }

        cartBounce();

    } catch (err) {
        console.error(err);
        alert("Cart error");
    }
});

            card.querySelector(".wishlist-btn").addEventListener("click", async e => {
                e.preventDefault();

                await fetch("/wishlist/toggle", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    credentials: "include",
                    body: JSON.stringify({ product_id: product.id })
                });

                const w = await fetch("/wishlist", { credentials: "include" });
                wishlist = await w.json();

                displayProducts(allProducts);
            });
        });
    }

    function snapToProducts() {
    const el = document.getElementById("product-grid");
    if (!el) return;

    const yOffset = -80;
    const y = el.getBoundingClientRect().top + window.scrollY + yOffset;

    window.scrollTo({
        top: y,
        behavior: "smooth"
    });
}

function snapToTabs() {
    const el = document.querySelector(".tabs");
    if (!el) return;

    window.scrollTo({
        top: el.getBoundingClientRect().top + window.scrollY - 115,
        behavior: "smooth"
    });
}

    searchInput?.addEventListener("input", e => {
    const query = e.target.value.toLowerCase().trim();

    const filtered = allProducts.filter(p =>
        p.name.toLowerCase().includes(query) ||
        p.category.toLowerCase().includes(query)
    );

    displayProducts(filtered);

    requestAnimationFrame(() => {
        snapToProducts();
    });
});

    tabs.forEach(tab => {
        tab.addEventListener("click", e => {
            e.preventDefault();

            const category = tab.dataset.category;

            if (category === "all") {
                displayProducts(allProducts);
            } else {
                displayProducts(allProducts.filter(p => p.category === category));
            }

            snapToTabs();
        });
    });

    function cartBounce() {
        const icon = document.querySelector(".fa-shopping-cart");
        if (!icon) return;

        icon.style.transform = "scale(1.3)";
        setTimeout(() => icon.style.transform = "scale(1)", 150);
    }

    loadData();
});

const drawer = document.getElementById("wishlist-drawer");
const overlay = document.getElementById("wishlist-overlay");
const toggleBtn = document.getElementById("wishlist-toggle");
const closeBtn = document.getElementById("close-wishlist");
const wishlistContainer = document.getElementById("wishlist-items");

let wishlist = [];

toggleBtn.addEventListener("click", async () => {
    drawer.classList.add("open");
    overlay.classList.add("show");
    await loadWishlist();
});

closeBtn.addEventListener("click", closeWishlist);
overlay.addEventListener("click", closeWishlist);

function closeWishlist() {
    drawer.classList.remove("open");
    overlay.classList.remove("show");
}

async function loadWishlist() {
    const res = await fetch("/wishlist", { credentials: "include" });
    wishlist = await res.json();

    renderWishlist();
}

function renderWishlist() {
    wishlistContainer.innerHTML = "";

    if (wishlist.length === 0) {
        wishlistContainer.innerHTML = "<p>No items in wishlist</p>";
        return;
    }

    wishlist.forEach(item => {
        const div = document.createElement("div");
        div.className = "wishlist-item";

        div.innerHTML = `
            <img src="${item.image}" />
            <div>
                <p>${item.name}</p>
                <p>$${item.price}</p>
                <button onclick="removeFromWishlist(${item.id})">Remove</button>
            </div>
        `;

        wishlistContainer.appendChild(div);
    });
}

async function toggleWishlist(productId) {
    const res = await fetch("/wishlist/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ product_id: productId })
    });

    const data = await res.json();

    if (!data.success) {
        alert(data.message);
        return;
    }

    await loadWishlist();
    displayProducts(allProducts);
}

async function removeFromWishlist(productId) {
    await fetch("/wishlist/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ product_id: productId })
    });

    await loadWishlist();
    displayProducts(allProducts);
}