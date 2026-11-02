"""
CartCompass-BI - API & Database Integration Tests
Tests Flask API endpoints, database initialization, foreign key constraints,
parameter validation, and isolated temporary SQLite instances.
"""

import re
import shutil
import sqlite3
from io import BytesIO
import pytest
from backend.routes import upload as upload_routes
from backend.app import create_app
from backend.config import Config
from werkzeug.security import generate_password_hash


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Create an isolated temporary SQLite database for testing."""
    temp_dir = tmp_path_factory.mktemp("cartcompass_test_db")
    db_file = temp_dir / "test_cartcompass.db"

    # Schema definition
    schema_sql = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL
    );

    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        order_date TEXT NOT NULL,
        order_status TEXT NOT NULL,
        region TEXT NOT NULL
    );

    CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        unit_price REAL NOT NULL CHECK(unit_price >= 0),
        discount REAL NOT NULL DEFAULT 0 CHECK(discount >= 0),
        return_amount REAL NOT NULL DEFAULT 0 CHECK(return_amount >= 0),
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """

    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(schema_sql)

    # Insert deterministic test data
    # Products
    conn.executemany(
        "INSERT INTO products VALUES (?, ?, ?);",
        [
            (1, "Wireless Headphones", "Electronics"),
            (2, "Coffee Maker", "Home & Kitchen"),
            (3, "Running Shoes", "Fashion & Apparel")
        ]
    )

    # Orders (Delivered, Shipped, Cancelled)
    conn.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?);",
        [
            (1, "2025-01-10", "delivered", "North"),
            (2, "2025-01-15", "delivered", "South"),
            (3, "2025-02-10", "delivered", "East"),
            (4, "2025-02-20", "shipped", "West"),
            (5, "2025-03-05", "cancelled", "Central")
        ]
    )

    # Order Items
    conn.executemany(
        "INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?, ?);",
        [
            # Order 1: 2 * 100 = 200, disc 20, ret 0 -> Net 180
            (1, 1, 1, 2, 100.0, 20.0, 0.0),
            # Order 2: 1 * 500 = 500, disc 50, ret 50 -> Net 400
            (2, 2, 2, 1, 500.0, 50.0, 50.0),
            # Order 3: 1 * 200 = 200, disc 0, ret 0 -> Net 200
            (3, 3, 3, 1, 200.0, 0.0, 0.0),
            # Order 4 (shipped): 1 * 300 = 300, disc 30, ret 0 -> Net 270
            (4, 4, 1, 1, 300.0, 30.0, 0.0),
            # Order 5 (cancelled): 1 * 1000 = 1000, disc 0, ret 0
            (5, 5, 2, 1, 1000.0, 0.0, 0.0)
        ]
    )

    conn.commit()
    conn.close()
    return db_file


@pytest.fixture
def test_app(test_db_path):
    """Create Flask application configured with the temporary database."""
    class TestAppConfig(Config):
        TESTING = True
        DEBUG = False
        DATABASE_PATH = test_db_path
        DASHBOARD_USERNAME = "test-user"
        DASHBOARD_PASSWORD_HASH = generate_password_hash("test-password")

    app = create_app(TestAppConfig)
    return app


@pytest.fixture
def client(test_app):
    """Flask test client authenticated as the test dashboard user."""
    client = test_app.test_client()
    response = client.get("/login")
    csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', response.data).group(1).decode()
    client.post(
        "/login",
        data={
            "csrf_token": csrf_token,
            "username": "test-user",
            "password": "test-password",
        },
    )
    return client


@pytest.fixture
def anonymous_client(test_app):
    """Flask test client without an authenticated session."""
    return test_app.test_client()


def test_dashboard_pages_require_login(anonymous_client):
    for path in (
        "/",
        "/index.html",
        "/revenue",
        "/revenue.html",
        "/categories",
        "/regions",
        "/reports",
        "/upload",
    ):
        response = anonymous_client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")


def test_authenticated_dashboard_pages_render(client):
    for path in (
        "/",
        "/index.html",
        "/revenue",
        "/revenue.html",
        "/categories",
        "/categories.html",
        "/regions",
        "/regions.html",
        "/reports",
        "/reports.html",
        "/upload",
        "/upload.html",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert b"Active Session" in response.data
        assert b"data-print-username=\"test-user\"" in response.data
        assert b'id="sidebar-order-count"' in response.data


def test_login_logout_and_sidebar_account(anonymous_client):
    login_page = anonymous_client.get("/login")
    csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', login_page.data).group(1).decode()

    login_response = anonymous_client.post(
        "/login",
        data={
            "csrf_token": csrf_token,
            "username": "test-user",
            "password": "test-password",
        },
    )
    assert login_response.status_code == 302
    assert login_response.headers["Location"] == "/"

    dashboard = anonymous_client.get("/")
    assert dashboard.status_code == 200
    assert b"data-print-username=\"test-user\"" in dashboard.data
    assert b"Active Session" in dashboard.data
    assert b">test-user</span>" in dashboard.data

    logout_response = anonymous_client.get("/logout")
    assert logout_response.status_code == 302
    assert logout_response.headers["Location"].endswith("/login")
    assert anonymous_client.get("/").status_code == 302


def test_login_rejects_invalid_password(anonymous_client):
    login_page = anonymous_client.get("/login")
    csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', login_page.data).group(1).decode()

    response = anonymous_client.post(
        "/login",
        data={
            "csrf_token": csrf_token,
            "username": "test-user",
            "password": "wrong-password",
        },
    )
    assert response.status_code == 401
    assert b"Invalid username or password." in response.data


def test_unauthenticated_api_requires_login(anonymous_client):
    response = anonymous_client.get("/api/kpis")
    assert response.status_code == 401
    assert response.get_json()["message"] == "Authentication required."


def test_upload_refreshes_database_and_dashboard_summary(
    test_db_path, tmp_path, monkeypatch
):
    database_path = tmp_path / "uploaded_data.db"
    shutil.copy2(test_db_path, database_path)

    class UploadTestConfig(Config):
        TESTING = True
        DEBUG = False
        DATABASE_PATH = database_path
        DASHBOARD_USERNAME = "test-user"
        DASHBOARD_PASSWORD_HASH = generate_password_hash("test-password")

    monkeypatch.setattr(upload_routes, "BASE_DIR", tmp_path)
    monkeypatch.setattr(upload_routes, "OUTPUTS_DIR", tmp_path / "outputs")
    monkeypatch.setattr(upload_routes, "ASSETS_CHARTS_DIR", tmp_path / "assets")
    monkeypatch.setattr(upload_routes, "run_pipeline", lambda: None)
    monkeypatch.setattr(upload_routes, "run_kpi_analysis", lambda: None)
    monkeypatch.setattr(upload_routes, "run_all_charts", lambda: None)

    client = create_app(UploadTestConfig).test_client()
    login_page = client.get("/login")
    csrf_token = re.search(
        rb'name="csrf_token" value="([^"]+)"', login_page.data
    ).group(1).decode()
    client.post(
        "/login",
        data={
            "csrf_token": csrf_token,
            "username": "test-user",
            "password": "test-password",
        },
    )

    csv_data = (
        "order_id,date,status,region,product,category,quantity,price\n"
        "new-1,2026-03-01,delivered,West,New Product,New Category,2,100\n"
        "new-2,2026-03-02,shipped,East,Other Product,Other Category,1,50\n"
    )
    upload_response = client.post(
        "/api/upload",
        data={"file": (BytesIO(csv_data.encode()), "new-orders.csv")},
        content_type="multipart/form-data",
    )

    assert upload_response.status_code == 200
    upload_summary = upload_response.get_json()["summary"]
    assert upload_summary["total_orders"] == 2
    assert upload_summary["total_items"] == 2

    dashboard_summary = client.get("/api/dashboard-summary").get_json()["data"]
    assert dashboard_summary["total_orders"] == 2
    assert dashboard_summary["delivered_orders"] == 1
    assert dashboard_summary["total_items"] == 3
    assert dashboard_summary["total_products"] == 2

    kpis = client.get("/api/kpis?status_mode=all").get_json()["data"]
    assert kpis["total_orders"] == 2
    assert kpis["total_items_sold"] == 3
    assert kpis["gross_sales"] == 250.0

    categories = client.get("/api/categories?status_mode=all").get_json()["data"]
    assert {row["category"] for row in categories} == {"New Category", "Other Category"}

    regions = client.get("/api/regions?status_mode=all").get_json()["data"]
    assert {row["region"] for row in regions} == {"West", "East"}

    monthly = client.get("/api/revenue/monthly?status_mode=all").get_json()["data"]
    assert {row["year_month"] for row in monthly} == {"2026-03"}

    status_summary = client.get("/api/status-distribution").get_json()["data"]
    assert status_summary["total_orders"] == 2


def test_foreign_key_enforcement(test_db_path):
    """Verify SQLite foreign key enforcement rejects orphan records."""
    conn = sqlite3.connect(str(test_db_path))
    conn.execute("PRAGMA foreign_keys = ON;")

    # Attempt to insert item for non-existent order_id 9999
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?, ?);",
            (999, 9999, 1, 1, 100.0, 0.0, 0.0)
        )

    # Attempt to insert item for non-existent product_id 9999
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?, ?);",
            (998, 1, 9999, 1, 100.0, 0.0, 0.0)
        )

    conn.close()


def test_health_endpoint(client):
    """Verify GET /api/health returns 200 and database counts."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True
    assert data["database"]["records"]["products"] == 3
    assert data["database"]["records"]["orders"] == 5
    assert data["database"]["records"]["order_items"] == 5


def test_kpis_endpoint(client):
    """Verify GET /api/kpis computes realized metrics correctly."""
    res = client.get("/api/kpis")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["status"] == "success"
    data = json_data["data"]

    # Delivered orders: 1, 2, 3
    # Gross: 200 + 500 + 200 = 900
    # Discounts: 20 + 50 + 0 = 70
    # Returns: 0 + 50 + 0 = 50
    # Net Sales: 900 - 70 - 50 = 780
    assert data["gross_sales"] == 900.0
    assert data["discount_amount"] == 70.0
    assert data["return_amount"] == 50.0
    assert data["net_sales"] == 780.0
    assert data["total_orders"] == 3
    assert data["average_order_value"] == round(780.0 / 3, 2)


def test_kpis_date_filtering(client):
    """Verify date filtering on GET /api/kpis."""
    res = client.get("/api/kpis?start_date=2025-01-01&end_date=2025-01-31")
    assert res.status_code == 200
    data = res.get_json()["data"]

    # In Jan 2025: Orders 1 & 2
    # Gross: 200 + 500 = 700. Net: 700 - 70 - 50 = 580
    assert data["gross_sales"] == 700.0
    assert data["net_sales"] == 580.0
    assert data["total_orders"] == 2


def test_monthly_revenue_endpoint(client):
    """Verify GET /api/revenue/monthly returns aggregated months."""
    res = client.get("/api/revenue/monthly")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["status"] == "success"
    data = json_data["data"]

    months = [d["year_month"] for d in data]
    assert "2025-01" in months
    assert "2025-02" in months


def test_categories_endpoint(client):
    """Verify GET /api/categories returns product categories."""
    res = client.get("/api/categories")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert len(data) >= 1
    for cat in data:
        assert "category" in cat
        assert "net_sales" in cat
        assert "revenue_share_pct" in cat


def test_regions_endpoint(client):
    """Verify GET /api/regions returns regional breakdown."""
    res = client.get("/api/regions")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert len(data) >= 1
    for reg in data:
        assert "region" in reg
        assert "net_sales" in reg
        assert "total_orders" in reg


def test_revenue_growth_endpoint(client):
    """Verify GET /api/revenue/growth response schema."""
    res = client.get("/api/revenue/growth")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "current_period" in data
    assert "previous_metrics" in data
    assert "growth" in data


def test_status_distribution_endpoint(client):
    """Verify GET /api/status-distribution returns all statuses."""
    res = client.get("/api/status-distribution")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["total_orders"] == 5
    statuses = [s["status"] for s in data["distribution"]]
    assert "delivered" in statuses
    assert "shipped" in statuses
    assert "cancelled" in statuses


def test_invalid_date_validation_error(client):
    """Verify 400 Bad Request with informative message on invalid date parameter."""
    res = client.get("/api/kpis?start_date=2025/13/45")
    assert res.status_code == 400
    json_data = res.get_json()
    assert json_data["status"] == "error"
    assert "Invalid start_date format" in json_data["message"]


def test_nonexistent_api_endpoint_404(client):
    """Verify 404 Not Found returns JSON for API routes."""
    res = client.get("/api/unknown_endpoint")
    assert res.status_code == 404
    json_data = res.get_json()
    assert json_data["status"] == "error"


def test_sample_template_download(client):
    """Verify GET /api/template/sample-csv returns sample CSV file."""
    res = client.get("/api/template/sample-csv")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    assert len(res.data) > 0


def test_upload_missing_file_error(client):
    """Verify 400 error when POST /api/upload is called without a file."""
    res = client.post("/api/upload", data={})
    assert res.status_code == 400
    assert res.get_json()["status"] == "error"
