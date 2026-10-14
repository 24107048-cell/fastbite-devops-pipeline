const cart = new Map();
let products = [];

const money = value => `₹${Number(value).toLocaleString("en-IN")}`;
const escapeHtml = value => String(value).replace(/[&<>"']/g, ch => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[ch]));

async function loadProducts() {
  const response = await fetch("/api/products");
  if (response.status === 401 || response.redirected) { window.location = "/login"; return; }
  products = await response.json();
  document.querySelector("#product-grid").innerHTML = products.map(p => `
    <article class="product-card">
      <div class="food-art">${p.emoji}</div>
      <h3>${escapeHtml(p.name)}</h3><p>${escapeHtml(p.description)}</p>
      <div class="product-bottom"><span class="price">${money(p.price)}</span>
      <button class="add-btn" data-add="${p.id}">+ Add</button></div>
    </article>`).join("");
}

function renderCart() {
  const entries = [...cart.entries()];
  const count = entries.reduce((sum, [, quantity]) => sum + quantity, 0);
  const total = entries.reduce((sum, [id, quantity]) => {
    const product = products.find(p => p.id === id);
    return sum + (product ? product.price * quantity : 0);
  }, 0);
  document.querySelector("#cart-count").textContent = `${count} ${count === 1 ? "item" : "items"}`;
  document.querySelector("#cart-total").textContent = money(total);
  document.querySelector("#cart-items").innerHTML = entries.length ? entries.map(([id, quantity]) => {
    const p = products.find(item => item.id === id);
    if (!p) return "";
    return `<div class="cart-row"><div><strong>${escapeHtml(p.name)}</strong><small>${money(p.price)} each</small></div>
      <div class="qty-controls"><button data-minus="${id}" aria-label="Remove one">−</button><span>${quantity}</span><button data-plus="${id}" aria-label="Add one">+</button></div></div>`;
  }).join("") : '<p class="muted">Your cart is empty.</p>';
}

async function loadOrders() {
  const response = await fetch("/api/orders");
  if (!response.ok) return;
  const orders = await response.json();
  document.querySelector("#order-history").innerHTML = orders.length ? orders.map(order => `
    <div class="order-row"><div><strong>Order #${order.id}</strong><small>${escapeHtml(order.created_at)} · ${order.items.reduce((n, i) => n + i.quantity, 0)} items</small></div>
    <div style="text-align:right"><strong>${money(order.total)}</strong><small><span class="order-status">${escapeHtml(order.status)}</span></small></div></div>`).join("") : '<p class="muted">No orders yet. Place your first order!</p>';
}

document.addEventListener("click", async event => {
  const add = event.target.closest("[data-add]");
  const plus = event.target.closest("[data-plus]");
  const minus = event.target.closest("[data-minus]");
  if (add) { const id = Number(add.dataset.add); cart.set(id, (cart.get(id) || 0) + 1); renderCart(); }
  if (plus) { const id = Number(plus.dataset.plus); cart.set(id, (cart.get(id) || 0) + 1); renderCart(); }
  if (minus) { const id = Number(minus.dataset.minus); const quantity = (cart.get(id) || 0) - 1; quantity > 0 ? cart.set(id, quantity) : cart.delete(id); renderCart(); }
  if (event.target.closest("#refresh-orders")) await loadOrders();
  if (event.target.closest("#checkout-btn")) {
    const message = document.querySelector("#cart-message");
    if (!cart.size) { message.textContent = "Add something delicious before placing an order."; return; }
    const button = document.querySelector("#checkout-btn");
    button.disabled = true; message.textContent = "Placing your order…";
    try {
      const response = await fetch("/api/orders", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({items: [...cart.entries()].map(([id, quantity]) => ({id, quantity}))})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Order could not be placed.");
      cart.clear(); renderCart(); await loadOrders();
      message.textContent = `Order #${data.id} placed successfully!`;
    } catch (error) { message.textContent = error.message; }
    finally { button.disabled = false; }
  }
});

(async function init() {
  await loadProducts();
  renderCart();
  await loadOrders();
})();
