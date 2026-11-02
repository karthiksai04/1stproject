"""
CartCompass-BI - KPI API Routes
Provides endpoints for summary KPIs and performance indicators.
"""

from flask import Blueprint, request, jsonify
from backend.db import query_db
from backend.services.analytics import get_kpis

kpis_bp = Blueprint("kpis", __name__)


@kpis_bp.route("/kpis", methods=["GET"])
def fetch_kpis():
    """
    GET /api/kpis
    Optional Query Parameters:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - status_mode ('delivered' [default], 'all_active', 'all')
    """
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status_mode = request.args.get("status_mode", "delivered").lower()

    try:
        data = get_kpis(
            start_date=start_date,
            end_date=end_date,
            status_mode=status_mode
        )
        return jsonify({
            "status": "success",
            "data": data
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "An error occurred while computing KPIs."
        }), 500


@kpis_bp.route("/dashboard-summary", methods=["GET"])
def fetch_dashboard_summary():
    """Return live dataset counts used by the shared sidebar widget."""
    try:
        summary = query_db(
            """
            SELECT
                (SELECT COUNT(*) FROM orders) AS total_orders,
                (SELECT COUNT(*) FROM orders WHERE order_status = 'delivered') AS delivered_orders,
                (SELECT COUNT(*) FROM products) AS total_products,
                (SELECT COALESCE(SUM(quantity), 0) FROM order_items) AS total_items;
            """,
            one=True
        )
        return jsonify({"status": "success", "data": summary}), 200
    except Exception:
        return jsonify({
            "status": "error",
            "message": "An error occurred while loading dataset counts."
        }), 500
