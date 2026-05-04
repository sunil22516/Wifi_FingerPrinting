# Navigation Engine

**Indoor Navigation Module** for WiFi Fingerprinting-based Localization System  
4th Floor, R&D Building

**Author:** Sunil (Navigation)

---

## Overview

This module implements the **Navigation Engine** — a graph-based pathfinding system that takes a user's current position (from the Localization Engine) and a destination room, then computes the shortest path with turn-by-turn directions.

### Key Components

| File | Purpose |
|------|---------|
| `graph.json` | Floor graph — nodes (locations) and edges (walkable paths) |
| `astar.py` | A* pathfinding algorithm implementation |
| `directions.py` | Turn-by-turn direction generator |
| `navigation_engine.py` | Main engine class tying everything together |
| `api.py` | Flask REST API for frontend integration |
| `test_navigation.py` | Test suite |

---

## How It Works

1. **User's position** (X, Y) comes from Tikam's localization engine
2. Position is **snapped** to the nearest node in the floor graph
3. **A\* algorithm** finds the shortest path from current node to destination
4. **Direction generator** converts the path into human-readable instructions
5. Result is sent to Tripti's frontend as waypoints + directions

### Algorithm: A* (A-Star)

```
f(n) = g(n) + h(n)
```
- `g(n)` = actual distance from start to node n (sum of edge weights)
- `h(n)` = heuristic: Euclidean (straight-line) distance from n to goal
- Always expands the node with lowest `f(n)`
- Guarantees optimal (shortest) path

---

## Setup & Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_navigation.py

# Run standalone demo
python navigation_engine.py

# Start API server (for frontend)
python api.py
```

Server runs at `http://localhost:5000`

---

## API Endpoints

### `GET /api/destinations`
Returns all navigable destinations.

### `POST /api/navigate`
Main endpoint. Request body:
```json
{
    "start_x": 25.0,
    "start_y": 2.0,
    "destination": "B-412"
}
```

Response:
```json
{
    "success": true,
    "path": ["ELEVATOR", "LOBBY", "HALLWAY_NORTH_2", "JUNCTION_EAST", "HALLWAY_EAST_1", "HALLWAY_EAST_2", "ROOM_412_DOOR"],
    "waypoints": [{"id": "ELEVATOR", "x": 25.0, "y": 2.0, "label": "Elevator Exit"}, ...],
    "directions": [...],
    "directions_text": "1. Start at Elevator Exit...",
    "total_distance": 45.0,
    "start_node": "ELEVATOR",
    "end_node": "ROOM_412_DOOR"
}
```

### `POST /api/navigate_by_nodes`
Navigate between two node IDs directly:
```json
{
    "start_node": "ELEVATOR",
    "end_node": "ROOM_412_DOOR"
}
```

### `GET /api/graph`
Returns full graph data (nodes + edges) for map rendering on frontend.

### `POST /api/nearest_node`
Find closest node to a coordinate:
```json
{"x": 25.0, "y": 8.0}
```

---

## Integration Guide

### For Tikam (Localization → Navigation)

Your localization output (X, Y coordinates) is consumed by navigation:
```python
from navigation_engine import NavigationEngine

engine = NavigationEngine()
result = engine.navigate(start_x=tikam_x, start_y=tikam_y, destination="B-412")
```

The coordinate system must match — ensure your (0,0) origin and scale (meters) align with `graph.json`.

### For Tripti (Navigation → Frontend)

Call the API from your frontend:
```javascript
// Fetch available destinations (for dropdown)
fetch('/api/destinations')
    .then(res => res.json())
    .then(data => populateDropdown(data.destinations));

// Get navigation path
fetch('/api/navigate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        start_x: currentX,  // from localization
        start_y: currentY,
        destination: selectedRoom  // from dropdown
    })
})
.then(res => res.json())
.then(data => {
    drawPathOnMap(data.waypoints);  // Array of {x, y} points
    showDirections(data.directions_text);
    showDistance(data.total_distance);
});
```

### For Aviral (Report)

The algorithm explanation is in the code comments and this README. Key points:
- A* with Euclidean heuristic
- Graph has ~32 nodes, ~32 edges
- Handles all rooms on 4th floor
- Supports dynamic re-routing

---

## Graph Structure

The floor is modeled as nodes (decision points) connected by edges (walkable paths):

- **Nodes**: Elevator, lobby, corridor junctions, room doors, staircases
- **Edges**: Physical walkable connections with distance weights (meters)
- **Destinations map**: Human-friendly names → node IDs

### Updating the Graph

After physically walking the floor, update `graph.json`:
1. Adjust X,Y coordinates to match the actual floor plan
2. Add/remove nodes for any missed locations
3. Update edge weights with measured distances
4. Add new room entries to the `destinations` map

---

## Features

- [x] A* shortest-path algorithm
- [x] Turn-by-turn directions (left/right/straight)
- [x] Snap localization coordinates to nearest node
- [x] Handle invalid destinations gracefully
- [x] Dynamic re-routing when position changes
- [x] REST API for frontend
- [x] All rooms on 4th floor covered
- [x] Distance estimation on path
- [x] Comprehensive test suite

---

## Coordinate System Agreement

**IMPORTANT**: The team must agree on:
- **Origin (0,0)**: Top-left corner of floor plan
- **Scale**: 1 unit = 1 meter
- **X-axis**: Increases to the right (East)
- **Y-axis**: Increases downward (South)

Update `graph.json` once Mayank confirms the fingerprinting grid coordinates.
