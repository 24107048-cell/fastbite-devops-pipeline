import os
import time
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "coursework-demo-secret-change-me")

HTTP_REQUESTS = Counter(
    "fastbite_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "fastbite_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"]
)
ORDERS_TOTAL = Counter("fastbite_orders_total", "Total orders placed")
ORDER_VALUE_TOTAL = Counter(
    "fastbite_order_value_rupees_total",
    "Total value of orders in rupees"
)
ACTIVE_SESSIONS = Gauge("fastbite_active_sessions", "Current logged-in session count")

PRODUCTS = [
    {"id": 1, "name": "Classic Burger", "description": "Juicy burger with fresh lettuce", "price": 99, "emoji": "🍔"},
    {"id": 2, "name": "Veggie Burger", "description": "Crispy vegetable patty and sauce", "price": 79, "emoji": "🥬"},
    {"id": 3, "name": "Masala Fries", "description": "Golden fries with Indian spices", "price": 69, "emoji": "🍟"},
    {"id": 4, "name": "Cheese Sandwich", "description": "Toasted sandwich with melted cheese", "price": 59, "emoji": "🥪"},
    {"id": 5, "name": "Chocolate Shake", "description": "Creamy chocolate milkshake", "price": 89, "emoji": "🥤"},
    {"id": 6, "name": "Lemon Soda", "description": "Refreshing sweet and salty soda", "price": 39, "emoji": "🍋"},
]
ORDERS = []
NEXT_ORDER_ID = 1
_started = time.time()

@app.before_request
def before_request():
    request._fastbite_start = time.time()

@app.after_request
def after_request(response):
    endpoint = request.endpoint or "unknown"
    HTTP_REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
    duration = time.time() - getattr(request, "_fastbite_start", time.time())
    if endpoint not in ("metrics",):
        REQUEST_LATENCY.labels(endpoint).observe(duration)
    return response

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("username"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == "admin" and password == "fastbite123":
            session["username"] = username
            ACTIVE_SESSIONS.set(1)
            return redirect(url_for("index"))
        flash("Incorrect username or password. Try the demo credentials.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    ACTIVE_SESSIONS.set(0)
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    return render_template("index.html", username=session.get("username"))

@app.route("/health")
def health():
    return jsonify(status="healthy", application="FastBite")

@app.route("/ready")
def ready():
    return jsonify(status="ready")

@app.route("/api/products")
@login_required
def products():
    return jsonify(PRODUCTS)

@app.route("/api/orders", methods=["GET", "POST"])
@login_required
def orders():
    global NEXT_ORDER_ID
    if request.method == "GET":
        return jsonify(list(reversed(ORDERS)))
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    if not isinstance(items, list) or not items:
        return jsonify(error="Your cart is empty."), 400
    product_map = {p["id"]: p for p in PRODUCTS}
    order_items, total = [], 0
    for item in items:
        try:
            product_id = int(item.get("id"))
            quantity = int(item.get("quantity", 1))
        except (TypeError, ValueError, AttributeError):
            return jsonify(error="Invalid cart item."), 400
        if product_id not in product_map or quantity < 1 or quantity > 50:
            return jsonify(error="Invalid product or quantity."), 400
        product = product_map[product_id]
        order_items.append({
            "id": product_id, "name": product["name"],
            "quantity": quantity, "price": product["price"]
        })
        total += product["price"] * quantity
    order = {
        "id": NEXT_ORDER_ID,
        "items": order_items,
        "total": total,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Accepted"
    }
    NEXT_ORDER_ID += 1
    ORDERS.append(order)
    ORDERS_TOTAL.inc()
    ORDER_VALUE_TOTAL.inc(total)
    return jsonify(order), 201

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
