# FastBite — End-to-End DevOps Pipeline

FastBite is a small Flask fast-food ordering website built for a DevOps coursework demonstration. It includes a demo login, product menu, browser-side cart, order history, Docker packaging, GitHub Actions tests/image publishing, Prometheus metrics, and a pre-provisioned Grafana dashboard.

## Demo credentials

- Username: `admin`
- Password: `fastbite123`

These are hard-coded coursework demo credentials, not suitable for a real application. Orders are stored in memory and reset when the app restarts.

## Architecture

```text
Developer / VS Code
        |
        v
   Git commit / push
        |
        v
 GitHub repository
        |
        v
 GitHub Actions: pytest
        |
        v
 Build and publish image to GHCR
        |
        v
 Ubuntu Docker Compose (local demo)
        |
        +---- FastBite Flask app :5001
        |          | /health /metrics
        |          v
        +---- Prometheus :9096
                   ^
                   |
               Grafana :3002
```

The workflow automatically runs tests and publishes an image to GitHub Container Registry on pushes to `main`. The Compose deployment on your Ubuntu computer is a separate manual step (`docker compose up -d --build`); this repository does not automatically deploy to a remote server.

## Run locally with Python (optional)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Test

```bash
python3 -m pip install -r requirements.txt
pytest -v
```

## Build and run app + monitoring

Run these commands from the project root:

```bash
docker compose up -d --build
docker compose ps
```

Open:
- FastBite: `http://localhost:5001`
- Prometheus: `http://localhost:9096`
- Grafana: `http://localhost:3002`

Grafana demo login: `admin` / `fastbiteadmin`.

The Prometheus configuration scrapes `app:5000` from inside the Compose network. Grafana is provisioned with the Prometheus datasource and FastBite Overview dashboard.

## Useful checks

```bash
curl http://localhost:5001/health
curl http://localhost:5001/metrics
```

In Prometheus, query:
- `fastbite_http_requests_total`
- `fastbite_orders_total`
- `fastbite_order_value_rupees_total`

Use the website to log in and place orders, then refresh Prometheus/Grafana to see metrics update.

## GitHub setup

Create a new empty repository named `fastbite-devops-pipeline` under your GitHub account, then from this folder:

```bash
git config --global user.name "24107048-cell"
git config --global user.email "24107048@apsit.du.in"
git init
git add .
git commit -m "Initial FastBite application and DevOps pipeline"
git branch -M main
git remote add origin https://github.com/24107048-cell/fastbite-devops-pipeline.git
git push -u origin main
```

GitHub may ask you to authenticate using a browser or an access token. Never share your password or token in chat.

## What the pipeline does

1. On pushes and pull requests to `main`, GitHub Actions installs dependencies and runs `pytest -v`.
2. If tests pass on a push to `main`, Actions builds the Docker image and pushes `ghcr.io/<owner>/<repository>:latest`.
3. Prometheus scrapes the FastBite `/metrics` endpoint every 10 seconds.
4. Grafana reads metrics from Prometheus and displays requests, orders, order value, and latency.

## Evidence to capture for your report

1. Website login page and demo credentials.
2. Menu with products, cart, and a successful order.
3. `docker compose ps` showing all three services.
4. GitHub Actions successful workflow run.
5. GitHub Container Registry package/image.
6. Prometheus query result for `fastbite_orders_total`.
7. Grafana FastBite Overview dashboard after generating some website traffic.
8. GitHub Issues/Projects board for Agile planning.
