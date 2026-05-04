"""
Navigation API Server (Flask)
==============================
Provides REST API endpoints for the frontend (Tripti) to call.
The frontend sends the current position + destination, and gets back
the path waypoints and directions.

Endpoints:
    GET  /api/destinations       - List all available destinations
    POST /api/navigate           - Get path from current position to destination
    POST /api/navigate_by_nodes  - Get path between two node IDs
    GET  /api/graph              - Get full graph data (for map rendering)

Run with: python api.py
Server starts at: http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from navigation_engine import NavigationEngine

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# Initialize navigation engine once at startup
engine = NavigationEngine()


@app.route("/api/destinations", methods=["GET"])
def get_destinations():
    """Return list of all navigable destinations."""
    destinations = engine.get_available_destinations()
    return jsonify({
        "success": True,
        "destinations": destinations
    })


@app.route("/api/navigate", methods=["POST"])
def navigate():
    """
    Main navigation endpoint.

    Expected JSON body:
    {
        "start_x": 25.0,       // Current X from localization
        "start_y": 2.0,        // Current Y from localization
        "destination": "B-412" // Room name or number
    }

    Returns path waypoints and turn-by-turn directions.
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No JSON body provided"}), 400

    start_x = data.get("start_x")
    start_y = data.get("start_y")
    destination = data.get("destination")

    if start_x is None or start_y is None:
        return jsonify({"success": False, "error": "start_x and start_y are required"}), 400
    if not destination:
        return jsonify({"success": False, "error": "destination is required"}), 400

    try:
        start_x = float(start_x)
        start_y = float(start_y)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "start_x and start_y must be numeric"}), 400

    result = engine.navigate(start_x, start_y, destination)
    status_code = 200 if result["success"] else 404
    return jsonify(result), status_code


@app.route("/api/navigate_by_nodes", methods=["POST"])
def navigate_by_nodes():
    """
    Navigate between two known node IDs.

    Expected JSON body:
    {
        "start_node": "ELEVATOR",
        "end_node": "ROOM_412_DOOR"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No JSON body provided"}), 400

    start_node = data.get("start_node")
    end_node = data.get("end_node")

    if not start_node or not end_node:
        return jsonify({"success": False, "error": "start_node and end_node are required"}), 400

    result = engine.navigate_by_nodes(start_node, end_node)
    status_code = 200 if result["success"] else 404
    return jsonify(result), status_code


@app.route("/api/graph", methods=["GET"])
def get_graph():
    """
    Return full graph data for frontend map rendering.
    Frontend can use this to draw nodes and edges on the floor plan.
    """
    return jsonify({
        "success": True,
        "nodes": engine.nodes,
        "edges": engine.edges,
        "destinations": engine.destinations
    })


@app.route("/api/nearest_node", methods=["POST"])
def nearest_node():
    """
    Find the nearest graph node to a given X,Y position.
    Useful for snapping localization output to the graph.

    Expected JSON body:
    {
        "x": 25.0,
        "y": 8.0
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No JSON body provided"}), 400

    x = data.get("x")
    y = data.get("y")

    if x is None or y is None:
        return jsonify({"success": False, "error": "x and y are required"}), 400

    try:
        x = float(x)
        y = float(y)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "x and y must be numeric"}), 400

    from astar import find_nearest_node
    node_id = find_nearest_node(engine.nodes, x, y)
    node_data = engine.nodes[node_id]

    return jsonify({
        "success": True,
        "node_id": node_id,
        "node": node_data
    })


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "navigation-engine",
        "nodes_loaded": len(engine.nodes),
        "edges_loaded": len(engine.edges)
    })


if __name__ == "__main__":
    print("=" * 50)
    print("Navigation Engine API Server")
    print(f"Loaded {len(engine.nodes)} nodes, {len(engine.edges)} edges")
    print(f"Available destinations: {len(engine.destinations)}")
    print("=" * 50)
    print("\nEndpoints:")
    print("  GET  /api/health")
    print("  GET  /api/destinations")
    print("  GET  /api/graph")
    print("  POST /api/navigate")
    print("  POST /api/navigate_by_nodes")
    print("  POST /api/nearest_node")
    print("\nStarting server on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
