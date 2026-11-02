"""
CartCompass-BI - Flask Application Factory & Server
Main application entry point providing RESTful BI endpoints and serving the dashboard UI.
"""

import hmac
import secrets
import sys
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import Config
from backend.db import close_db, get_db_connection
from backend.routes.kpis import kpis_bp
from backend.routes.revenue import revenue_bp
from backend.routes.categories import categories_bp
from backend.routes.regions import regions_bp
from backend.routes.upload import upload_bp
from backend.services.analytics import get_status_distribution


def create_app(config_class=Config):
    """
    Application Factory Pattern for CartCompass-BI.
    Configures database teardown, registers blueprints, and handles static frontend delivery.
    """
    app = Flask(
        __name__,
        static_folder=None,
        template_folder=str(getattr(config_class, "FRONTEND_DIR", BASE_DIR / "frontend"))
    )
    app.config.from_object(config_class)

    # Register Database teardown hook
    app.teardown_appcontext(close_db)

    @app.before_request
    def require_dashboard_login():
        frontend_dir = Path(app.config.get("FRONTEND_DIR", BASE_DIR / "frontend"))
        path = request.view_args.get("path", "") if request.view_args else ""
        extensionless_html = frontend_dir / f"{path}.html"
        is_frontend_page = (
            request.endpoint in {
                "serve_dashboard",
                "serve_revenue",
                "serve_categories",
                "serve_regions",
                "serve_reports",
                "serve_upload",
            }
            or request.path.lower().endswith(".html")
            or (
                request.endpoint == "serve_frontend_static"
                and not Path(path).suffix
                and extensionless_html.is_file()
            )
        )
        if request.endpoint is None or request.endpoint in {"login", "logout", "health_check"}:
            return None

        is_public_asset = request.endpoint == "serve_frontend_static" and not is_frontend_page
        is_authenticated = (
            session.get("logged_in") and session.get("username")
        )
        if not is_public_asset and not is_authenticated:
            if request.path.startswith("/api/"):
                return jsonify({"status": "error", "message": "Authentication required."}), 401
            return redirect(url_for("login"))
        return None

    # Register API Blueprints
    app.register_blueprint(kpis_bp, url_prefix="/api")
    app.register_blueprint(revenue_bp, url_prefix="/api")
    app.register_blueprint(categories_bp, url_prefix="/api")
    app.register_blueprint(regions_bp, url_prefix="/api")
    app.register_blueprint(upload_bp, url_prefix="/api")

    # Health Check Endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check():
        try:
            conn = get_db_connection(app.config["DATABASE_PATH"])
            p_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            o_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            i_count = conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
            conn.close()

            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": {
                    "connected": True,
                    "engine": "SQLite",
                    "path": str(app.config["DATABASE_PATH"]),
                    "records": {
                        "products": p_count,
                        "orders": o_count,
                        "order_items": i_count
                    }
                },
                "service": "CartCompass-BI Engine",
                "version": "1.0.0"
            }), 200
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "database": {
                    "connected": False,
                    "error": "Database connection or table verification failed."
                }
            }), 503

    # Order Status Distribution Endpoint
    @app.route("/api/status-distribution", methods=["GET"])
    def fetch_status_distribution():
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        try:
            data = get_status_distribution(start_date=start_date, end_date=end_date)
            return jsonify({
                "status": "success",
                "data": data
            }), 200
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        except Exception:
            return jsonify({"status": "error", "message": "Failed to fetch status distribution."}), 500

    # Static Matplotlib Charts Serving Endpoint
    @app.route("/api/chart-images/<path:filename>", methods=["GET"])
    def serve_chart_image(filename):
        outputs_dir = app.config.get("CHART_OUTPUTS_DIR", BASE_DIR / "analysis" / "outputs")
        return send_from_directory(str(outputs_dir), filename)

    # Documentation Markdown Serving Endpoint
    @app.route("/docs/<path:filename>", methods=["GET"])
    def serve_docs(filename):
        docs_dir = BASE_DIR / "docs"
        return send_from_directory(str(docs_dir), filename, mimetype="text/markdown; charset=utf-8")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("logged_in") and session.get("username"):
            return redirect(url_for("serve_dashboard"))

        csrf_token = session.get("login_csrf_token")
        error = None
        status_code = 200
        if request.method == "POST":
            submitted_token = request.form.get("csrf_token", "")
            if not csrf_token or not hmac.compare_digest(submitted_token, csrf_token):
                error = "Your login session expired. Please try again."
                status_code = 400
            else:
                configured_username = app.config.get("DASHBOARD_USERNAME")
                password_hash = app.config.get("DASHBOARD_PASSWORD_HASH")
                username = request.form.get("username", "")
                password = request.form.get("password", "")

                if not configured_username or not password_hash:
                    error = "Dashboard authentication is not configured."
                    status_code = 503
                elif (
                    hmac.compare_digest(username, configured_username)
                    and check_password_hash(password_hash, password)
                ):
                    session.clear()
                    session["logged_in"] = True
                    session["username"] = configured_username
                    return redirect("/")
                else:
                    error = "Invalid username or password."
                    status_code = 401

            csrf_token = secrets.token_urlsafe(32)

        if not csrf_token:
            csrf_token = secrets.token_urlsafe(32)
        session["login_csrf_token"] = csrf_token
        return render_template(
            "login.html",
            csrf_token=csrf_token,
            error=error,
            username=request.form.get("username", ""),
            auth_configured=bool(
                app.config.get("DASHBOARD_USERNAME")
                and app.config.get("DASHBOARD_PASSWORD_HASH")
            ),
        ), status_code

    @app.route("/logout", methods=["GET"])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # Root route - serves the dashboard
    @app.route("/", methods=["GET"])
    @app.route("/index.html", methods=["GET"])
    def serve_dashboard():
        return render_template("index.html", username=session["username"])

    # Clean URL Page Routes
    @app.route("/revenue", methods=["GET"])
    @app.route("/revenue.html", methods=["GET"])
    def serve_revenue():
        return render_template("revenue.html", username=session["username"])

    @app.route("/categories", methods=["GET"])
    @app.route("/categories.html", methods=["GET"])
    def serve_categories():
        return render_template("categories.html", username=session["username"])

    @app.route("/regions", methods=["GET"])
    @app.route("/regions.html", methods=["GET"])
    def serve_regions():
        return render_template("regions.html", username=session["username"])

    @app.route("/reports", methods=["GET"])
    @app.route("/reports.html", methods=["GET"])
    def serve_reports():
        return render_template("reports.html", username=session["username"])

    @app.route("/upload", methods=["GET"])
    @app.route("/upload.html", methods=["GET"])
    def serve_upload():
        return render_template("upload.html", username=session["username"])

    # Static frontend files (HTML pages, CSS, JS, Assets)
    @app.route("/<path:path>", methods=["GET"])
    def serve_frontend_static(path):
        frontend_dir = app.config.get("FRONTEND_DIR", BASE_DIR / "frontend")
        if path.lower() == "login.html":
            return redirect(url_for("login"))
        file_path = frontend_dir / path
        if file_path.exists() and file_path.is_file():
            if file_path.suffix.lower() == ".html":
                return render_template(path, username=session["username"])
            return send_from_directory(str(frontend_dir), path)
        # Support extensionless routing (e.g. /revenue -> revenue.html)
        html_path = frontend_dir / f"{path}.html"
        if html_path.exists() and html_path.is_file():
            return render_template(f"{path}.html", username=session["username"])
        return jsonify({"status": "error", "message": f"Resource not found: {path}"}), 404

    # JSON Error Handlers for API endpoints
    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "error": "Bad Request", "message": str(e)}), 400
        return "Bad Request", 400

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "error": "Not Found", "message": "The requested API endpoint was not found."}), 404
        return "Not Found", 404

    @app.errorhandler(500)
    def internal_error(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "error": "Internal Server Error", "message": "An unexpected server error occurred."}), 500
        return "Internal Server Error", 500

    return app


app = create_app()

if __name__ == "__main__":
    port = Config.PORT
    host = Config.HOST
    print(f"Starting CartCompass-BI on http://{host}:{port}")
    app.run(host=host, port=port, debug=Config.DEBUG)
