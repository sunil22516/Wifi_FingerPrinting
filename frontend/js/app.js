/**
 * Main Application Controller
 * =============================
 * Ties together the Map, Navigation, and Localization modules.
 * Handles UI events and coordinates the full user flow.
 * 
 * Author: Tripti (Frontend)
 */

// Initialize modules
const floorMap = new FloorMap('floor-map');
const navManager = new NavigationManager();
const locManager = new LocalizationManager();

// DOM elements
const destinationSelect = document.getElementById('destination-select');
const navigateBtn = document.getElementById('navigate-btn');
const cancelBtn = document.getElementById('cancel-btn');
const statusText = document.getElementById('status-text');
const distanceBadge = document.getElementById('distance-badge');
const directionsPanel = document.getElementById('directions-panel');
const directionsList = document.getElementById('directions-list');
const totalDistanceEl = document.getElementById('total-distance');
const etaEl = document.getElementById('eta');
const posDisplay = document.getElementById('pos-display');
const confidenceDisplay = document.getElementById('confidence-display');
const nodeDisplay = document.getElementById('node-display');

// ============================================================
// Initialize Application
// ============================================================
async function init() {
    // Load graph data for map rendering
    await floorMap.loadGraph();

    // Load destinations for dropdown
    const destinations = await navManager.loadDestinations();
    populateDestinations(destinations);

    // Set initial position (Elevator)
    locManager.setManualPosition(25.0, 2.0);

    // Register position update handler
    locManager.onPositionUpdate((pos) => {
        floorMap.setUserPosition(pos.x, pos.y);
        updatePositionDisplay(pos);

        // Auto re-route if navigating
        if (navManager.isNavigating) {
            autoReroute(pos.x, pos.y);
        }
    });

    statusText.textContent = 'Ready. Select a destination to begin navigation.';
}

// ============================================================
// Populate Destinations Dropdown
// ============================================================
function populateDestinations(destinations) {
    destinationSelect.innerHTML = '<option value="">-- Select Destination --</option>';
    destinations.forEach(dest => {
        const option = document.createElement('option');
        option.value = dest;
        option.textContent = dest;
        destinationSelect.appendChild(option);
    });
}

// ============================================================
// Event Handlers
// ============================================================

// Destination selection changed
destinationSelect.addEventListener('change', () => {
    navigateBtn.disabled = !destinationSelect.value;
});

// Navigate button clicked
navigateBtn.addEventListener('click', async () => {
    const destination = destinationSelect.value;
    if (!destination || !locManager.currentPosition) return;

    statusText.textContent = `Calculating route to ${destination}...`;
    navigateBtn.disabled = true;

    const result = await navManager.navigate(
        locManager.currentPosition.x,
        locManager.currentPosition.y,
        destination
    );

    if (result.success) {
        // Draw path on map
        floorMap.setNavigationPath(result.waypoints, result.end_node);

        // Show directions
        showDirections(result);

        // Update status
        statusText.textContent = `Navigating to ${destination}`;
        distanceBadge.textContent = `${result.total_distance}m`;
        distanceBadge.style.display = 'inline';
        cancelBtn.style.display = 'inline';
        navigateBtn.style.display = 'none';
    } else {
        statusText.textContent = `Error: ${result.error}`;
        navigateBtn.disabled = false;
    }
});

// Cancel navigation
cancelBtn.addEventListener('click', () => {
    navManager.cancelNavigation();
    floorMap.clearNavigation();
    hideDirections();
    statusText.textContent = 'Navigation cancelled. Select a new destination.';
    distanceBadge.style.display = 'none';
    cancelBtn.style.display = 'none';
    navigateBtn.style.display = 'inline';
    navigateBtn.disabled = !destinationSelect.value;
});

// ============================================================
// Demo Controls
// ============================================================

// Set position manually
document.getElementById('sim-locate-btn').addEventListener('click', () => {
    const x = parseFloat(document.getElementById('sim-x').value);
    const y = parseFloat(document.getElementById('sim-y').value);
    if (!isNaN(x) && !isNaN(y)) {
        locManager.setManualPosition(x, y);
        statusText.textContent = `Position set to (${x}, ${y})`;
    }
});

// Simulate walk along current path
document.getElementById('sim-walk-btn').addEventListener('click', async () => {
    if (navManager.currentPath && navManager.currentPath.waypoints) {
        statusText.textContent = 'Simulating walk...';
        await locManager.simulateWalk(navManager.currentPath.waypoints, 1.5);
        statusText.textContent = 'Walk simulation complete!';
    } else {
        statusText.textContent = 'No navigation path to walk. Navigate first!';
    }
});

// Preset position buttons
document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const x = parseFloat(btn.dataset.x);
        const y = parseFloat(btn.dataset.y);
        document.getElementById('sim-x').value = x;
        document.getElementById('sim-y').value = y;
        locManager.setManualPosition(x, y);
        statusText.textContent = `Position set to (${x}, ${y})`;
    });
});

// Map click - set position
document.getElementById('floor-map').addEventListener('mapClick', (e) => {
    const { x, y } = e.detail;
    if (x >= 0 && x <= 50 && y >= 0 && y <= 32) {
        const roundedX = Math.round(x * 2) / 2;
        const roundedY = Math.round(y * 2) / 2;
        document.getElementById('sim-x').value = roundedX;
        document.getElementById('sim-y').value = roundedY;
        locManager.setManualPosition(roundedX, roundedY);
        statusText.textContent = `Position set to (${roundedX}, ${roundedY}) via map click`;
    }
});

// ============================================================
// Helper Functions
// ============================================================

function showDirections(navResult) {
    directionsPanel.style.display = 'block';
    navManager.renderDirections(navResult.directions, directionsList);
    totalDistanceEl.textContent = `Total: ${navResult.total_distance}m`;
    etaEl.textContent = navManager.estimateTime(navResult.total_distance);
}

function hideDirections() {
    directionsPanel.style.display = 'none';
    directionsList.innerHTML = '';
}

function updatePositionDisplay(pos) {
    posDisplay.textContent = `(${pos.x.toFixed(1)}, ${pos.y.toFixed(1)})`;
    confidenceDisplay.textContent = pos.confidence ? 
        `${(pos.confidence * 100).toFixed(0)}%` : '--';
    
    // Find nearest node name
    if (floorMap.nodes) {
        let minDist = Infinity;
        let nearest = '--';
        Object.entries(floorMap.nodes).forEach(([id, node]) => {
            const dist = Math.sqrt((node.x - pos.x) ** 2 + (node.y - pos.y) ** 2);
            if (dist < minDist) {
                minDist = dist;
                nearest = node.label || id;
            }
        });
        nodeDisplay.textContent = nearest;
    }
}

// Auto re-route when position changes significantly
let lastRoutePosition = null;
async function autoReroute(x, y) {
    if (!lastRoutePosition) {
        lastRoutePosition = { x, y };
        return;
    }

    const dist = Math.sqrt((x - lastRoutePosition.x) ** 2 + (y - lastRoutePosition.y) ** 2);
    
    // Only re-route if moved more than 3 meters from last route calculation
    if (dist > 3) {
        lastRoutePosition = { x, y };
        const result = await navManager.recalculate(x, y);
        if (result && result.success) {
            floorMap.setNavigationPath(result.waypoints, result.end_node);
            showDirections(result);
            distanceBadge.textContent = `${result.total_distance}m`;
        }
    }
}

// ============================================================
// Start Application
// ============================================================
init();
