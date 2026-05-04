"""
Main Backend Application
=========================
Unified Flask server combining:
- Localization Engine (WiFi fingerprinting + KNN)
- Navigation Engine (A* pathfinding + directions)
- Sensor Fusion (PDR smoothing)

Author: All team members
Run with: python app.py
Server: http://localhost:5000
"""

import json
import os
import sys
import time
import threading

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Make wifi_scanner importable from data_collection/
_DATA_COLLECTION_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data_collection"
)
sys.path.insert(0, _DATA_COLLECTION_DIR)

from localization.localization_engine import LocalizationEngine
from navigation.navigation_engine import NavigationEngine
from sensor_fusion.fusion import SensorFusion

# ============================================================
# Initialize Flask App
# ============================================================
app = Flask(__name__, static_folder=None)
CORS(app)


@app.after_request
def add_no_cache_headers(response):
    """Prevent browser from caching any response (dev mode)."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ============================================================
# Initialize Engines
# ============================================================
nav_engine = NavigationEngine()
loc_engine = LocalizationEngine()
fusion_engine = SensorFusion()

# Frontend directory (serve static files)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


# ============================================================
# Serve Frontend (Static Files)
# ============================================================
@app.route("/")
def serve_index():
    """Serve the main frontend page."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    """Serve static frontend files (CSS, JS, assets)."""
    return send_from_directory(FRONTEND_DIR, filename)


# ============================================================
# Localization API Endpoints
# ============================================================
@app.route("/api/localize", methods=["POST"])
def localize():
    """
    Estimate position from WiFi readings.
    
    Request body:
    {
        "wifi_readings": {
            "AA:BB:CC:11:22:01": -45,
            "AA:BB:CC:11:22:02": -60
        },
        "smoothed": true  // optional, use history smoothing
    }
    """
    data = request.get_json()
    if not data or "wifi_readings" not in data:
        return jsonify({"success": False, "error": "wifi_readings required"}), 400
    
    wifi_readings = data["wifi_readings"]
    use_smoothing = data.get("smoothed", False)
    
    try:
        if use_smoothing:
            result = loc_engine.localize_with_history(wifi_readings)
        else:
            result = loc_engine.localize(wifi_readings)
        
        # Update sensor fusion with new WiFi fix
        fusion_engine.update_wifi(
            result["x"], result["y"],
            result["confidence"],
            time.time()
        )
        
        return jsonify({"success": True, **result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/localization/info", methods=["GET"])
def localization_info():
    """Get info about the loaded radio map."""
    return jsonify({"success": True, **loc_engine.get_radio_map_info()})


# ============================================================
# Navigation API Endpoints
# ============================================================
@app.route("/api/navigate", methods=["POST"])
def navigate():
    """
    Get navigation path from current position to destination.
    
    Request body:
    {
        "start_x": 25.0,
        "start_y": 2.0,
        "destination": "B-412"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No JSON body provided"}), 400
    
    start_x = data.get("start_x")
    start_y = data.get("start_y")
    destination = data.get("destination")
    
    if start_x is None or start_y is None:
        return jsonify({"success": False, "error": "start_x and start_y required"}), 400
    if not destination:
        return jsonify({"success": False, "error": "destination required"}), 400
    
    try:
        start_x = float(start_x)
        start_y = float(start_y)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "start_x/start_y must be numeric"}), 400
    
    result = nav_engine.navigate(start_x, start_y, destination)
    return jsonify(result), 200 if result["success"] else 404


@app.route("/api/destinations", methods=["GET"])
def get_destinations():
    """Return list of all navigable destinations."""
    return jsonify({
        "success": True,
        "destinations": nav_engine.get_available_destinations()
    })


@app.route("/api/graph", methods=["GET"])
def get_graph():
    """Return full graph data for map rendering."""
    return jsonify({
        "success": True,
        "nodes": nav_engine.nodes,
        "edges": nav_engine.edges,
        "destinations": nav_engine.destinations
    })


# ============================================================
# Sensor Fusion API Endpoints
# ============================================================
@app.route("/api/fusion/imu", methods=["POST"])
def update_imu():
    """
    Update sensor fusion with IMU data.
    
    Request body:
    {
        "accel_x": 0.1, "accel_y": 0.2, "accel_z": 9.8,
        "gyro_z": 0.05,
        "dt": 0.02
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    
    try:
        fusion_engine.update_imu(
            accel_x=float(data.get("accel_x", 0)),
            accel_y=float(data.get("accel_y", 0)),
            accel_z=float(data.get("accel_z", 9.81)),
            gyro_z=float(data.get("gyro_z", 0)),
            dt=float(data.get("dt", 0.02))
        )
        
        position = fusion_engine.get_position()
        return jsonify({"success": True, "position": position})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/fusion/status", methods=["GET"])
def fusion_status():
    """Get current sensor fusion status."""
    return jsonify({"success": True, **fusion_engine.get_status()})


@app.route("/api/position", methods=["GET"])
def get_position():
    """
    Get current best position estimate (fused from all sources).
    This is what the frontend should poll regularly.
    """
    pos = fusion_engine.get_position()
    if pos is None:
        return jsonify({"success": False, "error": "No position available yet"}), 404
    
    return jsonify({
        "success": True,
        "x": pos["x"],
        "y": pos["y"],
        "heading": fusion_engine.get_heading_degrees(),
        "step_count": fusion_engine.get_step_count()
    })


# ============================================================
# Combined: Localize + Navigate in one call
# ============================================================
@app.route("/api/localize_and_navigate", methods=["POST"])
def localize_and_navigate():
    """
    Combined endpoint: takes WiFi readings + destination,
    returns both position and navigation path.
    
    Request body:
    {
        "wifi_readings": {"AA:BB:CC:11:22:01": -45, ...},
        "destination": "B-412"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    
    wifi_readings = data.get("wifi_readings")
    destination = data.get("destination")
    
    if not wifi_readings:
        return jsonify({"success": False, "error": "wifi_readings required"}), 400
    if not destination:
        return jsonify({"success": False, "error": "destination required"}), 400
    
    # Step 1: Localize
    loc_result = loc_engine.localize(wifi_readings)
    
    # Step 2: Navigate from estimated position
    nav_result = nav_engine.navigate(loc_result["x"], loc_result["y"], destination)
    
    return jsonify({
        "success": True,
        "localization": loc_result,
        "navigation": nav_result
    })


# ============================================================
# Health Check
# ============================================================
@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "wifi-indoor-navigation",
        "components": {
            "localization": f"{len(loc_engine.radio_map)} fingerprints loaded",
            "navigation": f"{len(nav_engine.nodes)} nodes, {len(nav_engine.edges)} edges",
            "sensor_fusion": "active"
        }
    })


# ============================================================
# Real-Time WiFi Scan + Localize Endpoint
# ============================================================

# Shared state for the latest scanned position (thread-safe)
_latest_position = {"x": None, "y": None, "confidence": 0, "label": "", "timestamp": 0}
_position_lock = threading.Lock()

def _do_wifi_scan_and_localize():
    """
    Perform a live WiFi scan on the server machine and run localization.
    Returns the position dict or raises an exception.
    """
    try:
        from wifi_scanner import scan_wifi
    except ImportError:
        raise RuntimeError(
            "wifi_scanner module not found. Make sure data_collection/ is on PYTHONPATH."
        )

    networks = scan_wifi()
    if not networks:
        raise RuntimeError("WiFi scan returned no results. Check WiFi adapter and permissions.")

    # Build {bssid: rssi} dict expected by localization engine
    wifi_readings = {net["bssid"].lower(): net["rssi"] for net in networks}

    result = loc_engine.localize(wifi_readings)

    # Update sensor fusion
    fusion_engine.update_wifi(result["x"], result["y"], result["confidence"], time.time())

    # Cache the result
    with _position_lock:
        _latest_position.update({
            "x": result["x"],
            "y": result["y"],
            "confidence": result["confidence"],
            "label": result["neighbors"][0]["label"] if result.get("neighbors") else "",
            "timestamp": time.time()
        })

    return result


@app.route("/api/scan", methods=["POST"])
def wifi_scan_and_localize():
    """
    Trigger a real-time WiFi scan on the server machine, run KNN localization,
    and return the estimated position.

    Optional body:
    {
        "smoothed": true   // use EMA smoothing (default false)
    }

    This endpoint is called by the frontend every few seconds to get live position.
    The server must be running on the same machine that has a WiFi adapter
    (e.g., a laptop carried by the user).
    """
    data = request.get_json(silent=True) or {}
    use_smoothing = data.get("smoothed", False)

    try:
        from wifi_scanner import scan_wifi
    except ImportError:
        return jsonify({
            "success": False,
            "error": "wifi_scanner not available. Install pywifi or run on a machine with WiFi."
        }), 503

    try:
        networks = scan_wifi()
    except Exception as e:
        return jsonify({"success": False, "error": f"WiFi scan failed: {e}"}), 500

    if not networks:
        return jsonify({
            "success": False,
            "error": "WiFi scan returned no networks. Check adapter and permissions."
        }), 500

    wifi_readings = {net["bssid"].lower(): net["rssi"] for net in networks}

    try:
        if use_smoothing:
            result = loc_engine.localize_with_history(wifi_readings)
        else:
            result = loc_engine.localize(wifi_readings)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    fusion_engine.update_wifi(result["x"], result["y"], result["confidence"], time.time())

    with _position_lock:
        _latest_position.update({
            "x": result["x"],
            "y": result["y"],
            "confidence": result["confidence"],
            "label": result["neighbors"][0]["label"] if result.get("neighbors") else "",
            "timestamp": time.time()
        })

    return jsonify({
        "success": True,
        "x": result["x"],
        "y": result["y"],
        "confidence": result["confidence"],
        "label": result["neighbors"][0]["label"] if result.get("neighbors") else "",
        "neighbors": result.get("neighbors", []),
        "raw_networks_seen": len(networks),
        "source": "realtime_wifi"
    })


@app.route("/api/scan_and_navigate", methods=["POST"])
def scan_and_navigate():
    """
    Combined: real-time WiFi scan → localize → navigate to destination.

    Request body:
    {
        "destination": "A-407",
        "smoothed": true
    }
    """
    data = request.get_json()
    if not data or not data.get("destination"):
        return jsonify({"success": False, "error": "destination required"}), 400

    try:
        from wifi_scanner import scan_wifi
        networks = scan_wifi()
        if not networks:
            return jsonify({"success": False, "error": "No WiFi networks found"}), 500
        wifi_readings = {net["bssid"].lower(): net["rssi"] for net in networks}
        loc_result = loc_engine.localize(wifi_readings)
    except ImportError:
        return jsonify({"success": False,
                        "error": "wifi_scanner not available on this machine."}), 503
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    nav_result = nav_engine.navigate(loc_result["x"], loc_result["y"], data["destination"])

    return jsonify({
        "success": True,
        "localization": loc_result,
        "navigation": nav_result
    })


@app.route("/api/latest_position", methods=["GET"])
def latest_position():
    """Return the most recently scanned and localized position."""
    with _position_lock:
        pos = dict(_latest_position)

    if pos["x"] is None:
        # Try reading from sensor fusion as fallback
        fused = fusion_engine.get_position()
        if fused:
            return jsonify({"success": True, "source": "fusion", **fused})
        return jsonify({"success": False, "error": "No position available yet. Call /api/scan first."}), 404

    return jsonify({"success": True, "source": "wifi_scan", **pos})


# ============================================================
# Run Server
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("WiFi Indoor Navigation System - Backend Server")
    print("=" * 60)
    print(f"\nLocalization: {len(loc_engine.radio_map)} fingerprints loaded")
    print(f"Navigation:   {len(nav_engine.nodes)} nodes, {len(nav_engine.edges)} edges")
    print(f"Destinations: {len(nav_engine.destinations)} available")
    print(f"\nFrontend:     {FRONTEND_DIR}")
    print(f"\nServer starting at http://localhost:5001")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
