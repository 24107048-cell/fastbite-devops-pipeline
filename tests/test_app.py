import app as app_module

def setup_function():
    app_module.ORDERS.clear()
    app_module.NEXT_ORDER_ID = 1
    app_module.app.config["TESTING"] = True

def login(client):
    return client.post("/login", data={"username": "admin", "password": "fastbite123"}, follow_redirects=True)

def test_health_endpoint():
    response = app_module.app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"

def test_login_and_homepage():
    client = app_module.app.test_client()
    response = login(client)
    assert response.status_code == 200
    assert b"Good food" in response.data

def test_products_require_login():
    client = app_module.app.test_client()
    assert client.get("/api/products").status_code in (301, 302)
    login(client)
    response = client.get("/api/products")
    assert response.status_code == 200
    assert len(response.get_json()) == 6

def test_place_order():
    client = app_module.app.test_client()
    login(client)
    response = client.post("/api/orders", json={"items": [{"id": 1, "quantity": 2}]})
    assert response.status_code == 201
    assert response.get_json()["total"] == 198

def test_empty_order_rejected():
    client = app_module.app.test_client()
    login(client)
    response = client.post("/api/orders", json={"items": []})
    assert response.status_code == 400

def test_metrics_endpoint():
    response = app_module.app.test_client().get("/metrics")
    assert response.status_code == 200
    assert b"fastbite_http_requests_total" in response.data
