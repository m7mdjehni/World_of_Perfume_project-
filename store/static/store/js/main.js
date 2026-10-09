// main.js
// Fixed/completed version of the original script:
//  - "carouselInner" was referenced but never declared -> added.
//  - "fetchProducts" was called at the end but the function declaration /
//    try block opener and the initial product fetch were missing -> added.
//  - The header's #time element had no JS driving it. A small live clock was added.
//  - Product data now comes from the Django API instead of a hardcoded array,
//    and "Add New Card" posts to the backend so new perfumes persist.
//  - Real photos: only the 7 perfumes below are shown, each with its photo
//    from static/store/img/photos/<slug>.jpg
 
const container = document.getElementById("perfume-list");
const carouselInner = document.querySelector("#perfumeCarousel .carousel-inner");
 
const PHOTO_DIR = "/static/store/img/photos/";
const PHOTO_SLUGS = [
  "amber-mist",
  "citrus-breeze",
  "dusk-leather",
  "emerald-spice",
  "golden-petal",
  "midnight-oud",
  "moonlit-cedar",
];
 
function slugify(name) {
  return String(name || "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
 
function productImage(p) {
  // The 7 featured perfumes use their photo from /photos/; any other
  // perfume uses the image saved with it (URL entered when adding).
  if (PHOTO_SLUGS.includes(slugify(p.name))) {
    return `${PHOTO_DIR}${slugify(p.name)}.jpg`;
  }
  return resolveImageUrl(p.image);
}
 
const DEFAULT_IMAGE = "/static/store/img/perfume1.png";
 
// Used when the main image fails to load: the saved image if it differs,
// otherwise the default placeholder (so a bad URL never shows a broken icon).
function fallbackImage(p) {
  const saved = resolveImageUrl(p.image);
  return saved !== productImage(p) ? saved : DEFAULT_IMAGE;
}
 
function liveClock() {
  const timeBox = document.getElementById("time");
  if (!timeBox) return;
  const update = () => {
    timeBox.textContent = new Date().toLocaleTimeString();
  };
  update();
  setInterval(update, 1000);
}
 
function resolveImageUrl(value) {
  if (!value) return "/static/store/img/perfume1.png";
  if (/^https?:\/\//i.test(value) || value.startsWith("/")) return value;
  // API data from older versions may return "static/..." without a leading slash.
  return `/${value}`;
}
 
function renderPerfumeCard(p) {
  const card = document.createElement("div");
  card.className = "perfume-card";
  card.innerHTML = `
    <img class="product-img" src="${productImage(p)}" alt="${p.name}" onerror="this.onerror=null;this.src='${fallbackImage(p)}';">
    <h3>${p.name}</h3>
    <p>${p.description}</p>
    <p class="price">${p.price}</p>
    <button class="order-btn" data-id="${p.id}" data-name="${p.name}" data-price="${p.price}">Add to Cart</button>
  `;
  container.appendChild(card);
}
 
function renderCarouselItem(p, isFirst) {
  const item = document.createElement("div");
  item.className = "carousel-item" + (isFirst ? " active" : "");
  item.style.setProperty("--bg", `url("${productImage(p)}")`);
  item.innerHTML = `
    <img src="${productImage(p)}" class="d-block w-100 rounded-lg" alt="${p.name}" onerror="this.onerror=null;this.src='${fallbackImage(p)}';">
    <div class="carousel-caption d-none d-md-block bg-black/50 rounded-lg p-2">
      <h5>${p.name}</h5>
      <p>${p.description}</p>
    </div>
  `;
  carouselInner.appendChild(item);
}
 
async function fetchProducts() {
  try {
    const response = await fetch(window.PRODUCTS_API_URL || "/api/products/");
    if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
    const data = await response.json();
    const products = Array.isArray(data) ? data : (data.results || []);
 
    container.innerHTML = "";
    carouselInner.innerHTML = "";
 
    products.forEach((p) => {
      renderPerfumeCard(p);
      if (p.show_in_carousel) {
        renderCarouselItem(p, carouselInner.children.length === 0);
      }
    });
 
    if (carouselInner.children.length === 0 && products.length > 0) {
      renderCarouselItem(products[0], true);
    }
  } catch (error) {
    console.error("Failed to load products:", error);
  }
}
 
function getCsrfToken() {
  if (window.CSRF_TOKEN) return window.CSRF_TOKEN;
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
}
 
async function addProduct(newCard) {
  const formData = new FormData();
  Object.entries(newCard).forEach(([key, value]) => formData.append(key, value));
 
  const response = await fetch(window.ADD_PRODUCT_API_URL || "/api/products/add/", {
    method: "POST",
    headers: { "X-CSRFToken": getCsrfToken() },
    body: formData,
  });
 
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  return response.json();
}
 
async function submitOrder(cartItems) {
  const response = await fetch(window.ORDER_API_URL || "/api/orders/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({
      cart_items: cartItems.map((item) => ({ perfume: item.id, quantity: item.quantity })),
    }),
  });
 
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  return response.json();
}
 
// ---- Cart (client-side, persisted in localStorage until the order is placed) ----
 
const CART_STORAGE_KEY = "tariq_perfume_cart";
 
function loadCart() {
  try {
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (error) {
    console.error("Failed to read cart from storage:", error);
    return [];
  }
}
 
let cart = loadCart();
 
function saveCart() {
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
}
 
/** Pull the leading number out of a free-text price like "$49.99". */
function parsePriceAmount(priceText) {
  const match = String(priceText || "").match(/[\d.]+/);
  return match ? parseFloat(match[0]) : null;
}
 
function priceCurrencyParts(priceText) {
  const text = String(priceText || "");
  const match = text.match(/[\d.]+/);
  if (!match) return { prefix: "", suffix: "" };
  return {
    prefix: text.slice(0, match.index),
    suffix: text.slice(match.index + match[0].length),
  };
}
 
function addToCart(id, name, price) {
  const existing = cart.find((item) => item.id === id);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({ id, name, price, quantity: 1 });
  }
  saveCart();
  renderCart();
}
 
function changeCartQuantity(id, delta) {
  const item = cart.find((i) => i.id === id);
  if (!item) return;
  item.quantity += delta;
  if (item.quantity <= 0) {
    cart = cart.filter((i) => i.id !== id);
  }
  saveCart();
  renderCart();
}
 
function removeFromCart(id) {
  cart = cart.filter((i) => i.id !== id);
  saveCart();
  renderCart();
}
 
function renderCart() {
  const cartItemsEl = document.getElementById("cartItems");
  const cartEmptyMsg = document.getElementById("cartEmptyMsg");
  const cartCount = document.getElementById("cartCount");
  const cartTotal = document.getElementById("cartTotal");
  const submitBtn = document.getElementById("submitOrderBtn");
  if (!cartItemsEl) return;
 
  const totalQuantity = cart.reduce((sum, item) => sum + item.quantity, 0);
  cartCount.textContent = totalQuantity;
 
  if (cart.length === 0) {
    cartItemsEl.innerHTML = "";
    cartEmptyMsg.style.display = "block";
    cartTotal.textContent = "0";
    submitBtn.disabled = true;
    return;
  }
 
  cartEmptyMsg.style.display = "none";
  submitBtn.disabled = false;
 
  let grandTotal = 0;
  let currency = { prefix: "", suffix: "" };
 
  cartItemsEl.innerHTML = cart
    .map((item) => {
      const amount = parsePriceAmount(item.price);
      const parts = priceCurrencyParts(item.price);
      let lineTotalText = "N/A";
      if (amount !== null) {
        const lineTotal = amount * item.quantity;
        grandTotal += lineTotal;
        currency = parts;
        lineTotalText = `${parts.prefix}${lineTotal}${parts.suffix}`;
      }
      return `
        <div class="flex justify-between items-center border-b border-white/20 py-2" data-cart-id="${item.id}">
          <div>
            <p class="font-semibold">${item.name}</p>
            <p class="text-sm text-gray-300">${item.price} &times; ${item.quantity}</p>
          </div>
          <div class="flex items-center gap-2">
            <button class="cart-decrease px-2 bg-white/20 rounded" data-id="${item.id}">-</button>
            <span>${item.quantity}</span>
            <button class="cart-increase px-2 bg-white/20 rounded" data-id="${item.id}">+</button>
            <span class="w-16 text-right">${lineTotalText}</span>
            <button class="cart-remove px-2 text-red-400" data-id="${item.id}">&times;</button>
          </div>
        </div>
      `;
    })
    .join("");
 
  cartTotal.textContent = grandTotal > 0 ? `${currency.prefix}${grandTotal}${currency.suffix}` : "N/A";
}
 
async function generateDescription(name, notes) {
  const response = await fetch(window.GENERATE_DESCRIPTION_API_URL || "/api/products/generate-description/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({ name, notes }),
  });
 
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  const data = await response.json();
  return data.description;
}
 
document.addEventListener("DOMContentLoaded", () => {
  liveClock();
  fetchProducts();
  renderCart();
 
  // The button only exists in the template for admins (superusers).
  const addBtn = document.getElementById("addCardBtn");
  if (addBtn) {
    addBtn.addEventListener("click", async () => {
      const name = prompt("Enter perfume name:");
      if (!name) return;
 
      const notes = prompt("Enter scent notes for the AI description (e.g. amber, oud, vanilla) — optional:") || "";
 
      let description;
      try {
        description = await generateDescription(name, notes);
      } catch (error) {
        console.error("AI description generation failed:", error);
        description = null;
      }
 
      // Let the user review/edit the AI-generated text, or type it manually
      // if generation failed.
      description = prompt(
        "Description (AI-generated, feel free to edit):",
        description || ""
      ) || "No description";
 
      const price = prompt("Enter price:") || "N/A";
      const image = prompt("Enter image URL:") || "img/perfume1.jpg";
      const showInCarousel = confirm("Show this perfume in the carousel too?");
 
      const newCard = {
        name,
        description,
        price,
        image,
        show_in_carousel: showInCarousel ? "true" : "false",
      };
 
      try {
        const saved = await addProduct(newCard);
        renderPerfumeCard(saved);
        if (saved.show_in_carousel) {
          renderCarouselItem(saved, carouselInner.children.length === 0);
        }
      } catch (error) {
        console.error("Failed to add product:", error);
        alert("Could not save the new perfume. Please try again.");
      }
    });
  }
 
  container.addEventListener("click", (event) => {
    const btn = event.target.closest(".order-btn");
    if (!btn) return;
 
    const perfumeId = parseInt(btn.dataset.id, 10);
    const perfumeName = btn.dataset.name;
    const perfumePrice = btn.dataset.price;
    addToCart(perfumeId, perfumeName, perfumePrice);
  });
 
  const cartItemsEl = document.getElementById("cartItems");
  cartItemsEl.addEventListener("click", (event) => {
    const decreaseBtn = event.target.closest(".cart-decrease");
    const increaseBtn = event.target.closest(".cart-increase");
    const removeBtn = event.target.closest(".cart-remove");
 
    if (decreaseBtn) changeCartQuantity(parseInt(decreaseBtn.dataset.id, 10), -1);
    if (increaseBtn) changeCartQuantity(parseInt(increaseBtn.dataset.id, 10), 1);
    if (removeBtn) removeFromCart(parseInt(removeBtn.dataset.id, 10));
  });
 
  const submitBtn = document.getElementById("submitOrderBtn");
  submitBtn.addEventListener("click", async () => {
    if (cart.length === 0) return;
 
    if (!window.IS_AUTHENTICATED) {
      alert("Please log in to place your order.");
      window.location.href = window.LOGIN_URL || "/accounts/login/";
      return;
    }
 
    submitBtn.disabled = true;
    submitBtn.textContent = "Placing order...";
    try {
      await submitOrder(cart);
      cart = [];
      saveCart();
      renderCart();
      alert("Your order has been placed!");
      const modalEl = document.getElementById("cartModal");
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.hide();
    } catch (error) {
      console.error("Failed to place order:", error);
      alert("Could not place the order. Please try again.");
    } finally {
      submitBtn.disabled = cart.length === 0;
      submitBtn.textContent = "Place Order";
    }
  });
});
 