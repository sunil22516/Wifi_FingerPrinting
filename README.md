# WiFi Indoor Localization and Navigation System

**Course Project — Wireless Indoor Localization & Navigation**  
**4th Floor, R&D Building**

---

## Team Members & Contributions

| Member | Role | Contribution |
|--------|------|-------------|
| **Mayank** | Data Collection | WiFi fingerprinting tool, radio map database, grid coordination |
| **Tikam** | Localization | KNN algorithm, WiFi signal matching, position estimation |
| **Sunil** | Navigation | A* pathfinding, floor graph, turn-by-turn directions |
| **Tripti** | Frontend | Web UI, map rendering, user interaction, path visualization |
| **Aviral** | Integration & Fusion | Sensor fusion (PDR), system integration, report |

---

## System Overview

This application provides **real-time indoor navigation** on the 4th floor of the R&D building using **WiFi signal fingerprinting**. A user exits the elevator, selects a destination room (e.g., B-412), and the system:

1. **Localizes** the user using WiFi RSSI fingerprints + K-Nearest Neighbors (KNN)
2. **Navigates** by computing the shortest path using A* algorithm
3. **Displays** the route on an interactive floor map with turn-by-turn directions
4. **Tracks** movement using sensor fusion (WiFi + IMU/PDR) for smooth position updates

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Web Browser)                    │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │ Floor Map │  │ Directions   │  │ Destination Selector    │   │
│  │ (Canvas)  │  │ Panel        │  │ (Dropdown)              │   │
│  └──────────┘  └──────────────┘  └─────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API (HTTP/JSON)
┌──────────────────────────┴──────────────────────────────────────┐
│                        BACKEND (Flask Server)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │ Localization │  │ Navigation   │  │ Sensor Fusion       │   │
│  │ Engine (KNN) │  │ Engine (A*)  │  │ (PDR + Kalman)      │   │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬───────────┘   │
│         │                  │                     │               │
│  ┌──────┴───────┐  ┌──────┴───────┐            │               │
│  │ Radio Map    │  │ Floor Graph  │            │               │
│  │ (JSON/CSV)   │  │ (JSON)       │            │               │
│  └──────────────┘  └──────────────┘            │               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
wifi-indoor-navigation/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
│
├── backend/                           # Backend server
│   ├── app.py                         # Main Flask application (unified API)
│   ├── localization/                  # Localization module
│   │   ├── __init__.py
│   │   ├── knn.py                     # KNN algorithm implementation
│   │   └── localization_engine.py     # Localization engine class
│   ├── navigation/                    # Navigation module
│   │   ├── __init__.py
│   │   ├── graph.json                 # 4th floor graph (nodes + edges)
│   │   ├── astar.py                   # A* pathfinding algorithm
│   │   ├── directions.py             # Turn-by-turn direction generator
│   │   └── navigation_engine.py      # Navigation engine class
│   └── sensor_fusion/                 # Sensor fusion module
│       ├── __init__.py
│       └── fusion.py                  # PDR + WiFi fusion
│
├── frontend/                          # Web-based UI
│   ├── index.html                     # Main page
│   ├── css/style.css                  # Styles
│   └── js/
│       ├── app.js                     # Main app controller
│       ├── map.js                     # Canvas-based map renderer
│       ├── navigation.js             # Navigation UI logic
│       └── localization.js           # Position tracking module
│
├── data_collection/                   # WiFi data collection tools
│   ├── wifi_scanner.py               # Cross-platform WiFi scanner
│   ├── collect_fingerprints.py       # Interactive fingerprint collection
│   └── sample_data/
│       └── radio_map.json            # Pre-collected fingerprint database
│
├── navigation/                        # Standalone navigation module (Sunil)
│   ├── graph.json
│   ├── astar.py
│   ├── directions.py
│   ├── navigation_engine.py
│   ├── api.py
│   ├── test_navigation.py
│   ├── requirements.txt
│   └── README.md
│
└── tests/
    └── test_all.py                    # Comprehensive test suite
```

---

## Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- A modern web browser (Chrome/Firefox/Edge)

### Installation

```bash
# Clone the repository
cd wifi-indoor-navigation

# Install Python dependencies
pip install -r requirements.txt

# Run tests to verify everything works
python tests/test_all.py
```

### Running the Application

```bash
# Start the backend server
cd backend
python app.py
```

Open your browser to **http://localhost:5000** — the full application (map + navigation) loads automatically.

### Quick Demo

1. Open http://localhost:5000
2. Your position starts at the Elevator (blue dot on map)
3. Select a destination from the dropdown (e.g., "B-412")
4. Click "Navigate" — path appears on map with directions
5. Use preset buttons or click the map to change position
6. Click "Simulate Walk" to see animated walking along the path

---

## Algorithms

### 1. Localization: K-Nearest Neighbors (KNN)

**Input:** Live WiFi scan → `{BSSID: RSSI}` for each visible access point  
**Output:** Estimated (X, Y) coordinates

**How it works:**
1. Pre-collect WiFi fingerprints at known grid points (radio map)
2. At runtime, scan WiFi and get RSSI from all visible APs
3. Compute signal-space Euclidean distance between live scan and every stored fingerprint:
   $$d = \sqrt{\sum_{i=1}^{n} (RSSI_{live,i} - RSSI_{stored,i})^2}$$
4. Select K nearest matches (lowest distance)
5. **Weighted average** their coordinates (closer = higher weight):
   $$\hat{x} = \frac{\sum_{k=1}^{K} \frac{1}{d_k} \cdot x_k}{\sum_{k=1}^{K} \frac{1}{d_k}}$$

**Parameters:** K=3, Weighted KNN (WKNN), missing APs penalized at -100 dBm

### 2. Navigation: A* (A-Star) Pathfinding

**Input:** Start node + destination node on floor graph  
**Output:** Shortest path (ordered list of waypoints)

**How it works:**
- Floor modeled as a graph: nodes (junctions, room doors) + edges (walkable paths with distance weights)
- A* explores nodes using: $f(n) = g(n) + h(n)$
  - $g(n)$: actual distance from start to n
  - $h(n)$: heuristic (Euclidean distance to goal) — admissible, never overestimates
- Guarantees optimal shortest path
- Graph: 32 nodes, 32 edges covering all rooms/corridors

### 3. Sensor Fusion: Pedestrian Dead Reckoning (PDR)

**Purpose:** Smooth position tracking between WiFi scans (which take 2-4 seconds)

**Components:**
- **Step detection:** Peak detection on accelerometer magnitude
- **Heading estimation:** Gyroscope Z-axis integration
- **Position projection:** Step length × heading direction
- **Fusion:** Time-decayed weighted average of WiFi + PDR estimates

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/destinations` | GET | List all navigable rooms |
| `/api/graph` | GET | Full graph (for map rendering) |
| `/api/localize` | POST | WiFi → position estimation |
| `/api/navigate` | POST | Position + destination → path |
| `/api/position` | GET | Current fused position |
| `/api/localize_and_navigate` | POST | Combined: WiFi → position → path |

### Example: Navigate

```bash
curl -X POST http://localhost:5000/api/navigate \
  -H "Content-Type: application/json" \
  -d '{"start_x": 25.0, "start_y": 2.0, "destination": "B-412"}'
```

Response:
```json
{
  "success": true,
  "path": ["ELEVATOR", "LOBBY", "HALLWAY_NORTH_2", "JUNCTION_EAST", "HALLWAY_EAST_1", "HALLWAY_EAST_2", "ROOM_412_DOOR"],
  "total_distance": 48.0,
  "directions_text": "1. Start at Elevator Exit...",
  "waypoints": [{"id": "ELEVATOR", "x": 25.0, "y": 2.0, "label": "Elevator Exit"}, ...]
}
```

---

## Data Collection Process

1. **Setup grid** on 4th floor map (2m spacing)
2. **Run scanner** at each grid point:
   ```bash
   cd data_collection
   python collect_fingerprints.py
   ```
3. Enter X,Y coordinates at each point; tool records 5 WiFi scans and averages
4. Output: `radio_map.json` with all fingerprints

---

## Coordinate System

- **Origin (0,0):** Top-left corner of floor plan
- **X-axis:** Increases to the right (East)
- **Y-axis:** Increases downward (South)
- **Scale:** 1 unit = 1 meter
- **Floor bounds:** ~50m × 32m

---

## Key Design Decisions

1. **WiFi Fingerprinting over Trilateration** — More robust in multipath-heavy indoor environments
2. **WKNN over plain KNN** — Closer fingerprints weighted more heavily → better accuracy
3. **A\* over Dijkstra** — Heuristic guides search → faster for large graphs (academically correct)
4. **Web frontend over native Android** — Cross-platform, easier demo, no app installation needed
5. **Graph-based navigation** — Simple, efficient for structured indoor environments
6. **Sensor fusion** — Smooths WiFi "jumping" for realistic movement visualization

---

## Challenges & Lessons Learned

1. **WiFi signal variability** — RSSI fluctuates ±5dBm even while stationary; averaging multiple scans helps
2. **Coordinate alignment** — Critical that fingerprinting grid, localization, and navigation graph all use same coordinate system
3. **Graph completeness** — Must include ALL reachable rooms as nodes, not just obvious ones
4. **Turn direction accuracy** — Computing angles from node coordinates requires careful math
5. **Real-time performance** — KNN with 25 fingerprints is fast; would need optimization for 500+

---

## Future Improvements

- Particle filter for more robust localization
- BLE beacons for higher precision
- Floor transition (stairs/elevator between floors)
- Crowd-sourced fingerprint updates
- AR overlay for directions (camera-based)

---

## How to Run Tests

```bash
# Full test suite (all components)
python tests/test_all.py

# Navigation module only
python navigation/test_navigation.py
```

---

## Dependencies

- **Flask** — Lightweight web framework for REST API
- **flask-cors** — Cross-Origin Resource Sharing for frontend
- **NumPy** — Numerical operations (optional, for advanced processing)
- Standard library: `math`, `heapq`, `json`, `os`, `subprocess`

---

## License

Academic project — IIIT Delhi, Wireless Networks 2026
