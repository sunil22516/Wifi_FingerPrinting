/**
 * Main Application Controller
 * =============================
 * Ties together the Map, Navigation, and Localization modules.
 * Handles UI events and coordinates the full user flow.
 */

document.addEventListener('DOMContentLoaded', function () {
    console.log('[APP] DOMContentLoaded fired');

    // ============================================================
    // Initialize Modules
    // ============================================================
    var floorMap, navManager, locManager;

    try {
        floorMap = new FloorMap('floor-map');
        console.log('[APP] FloorMap created');
    } catch (e) {
        console.error('[APP] FloorMap FAILED:', e);
        alert('Error: FloorMap failed to initialize. ' + e.message);
        return;
    }

    try {
        navManager = new NavigationManager();
        console.log('[APP] NavigationManager created');
    } catch (e) {
        console.error('[APP] NavigationManager FAILED:', e);
    }

    try {
        locManager = new LocalizationManager();
        console.log('[APP] LocalizationManager created');
    } catch (e) {
        console.error('[APP] LocalizationManager FAILED:', e);
        alert('Error: LocalizationManager failed. ' + e.message);
        return;
    }

    // ============================================================
    // DOM Elements
    // ============================================================
    var destinationSelect = document.getElementById('destination-select');
    var navigateBtn = document.getElementById('navigate-btn');
    var cancelBtn = document.getElementById('cancel-btn');
    var statusText = document.getElementById('status-text');
    var distanceBadge = document.getElementById('distance-badge');
    var directionsPanel = document.getElementById('directions-panel');
    var directionsList = document.getElementById('directions-list');
    var totalDistanceEl = document.getElementById('total-distance');
    var etaEl = document.getElementById('eta');
    var posDisplay = document.getElementById('pos-display');
    var confidenceDisplay = document.getElementById('confidence-display');
    var nodeDisplay = document.getElementById('node-display');
    var wifiScanBtn = document.getElementById('wifi-scan-btn');
    var wifiStatusEl = document.getElementById('wifi-status');

    console.log('[APP] DOM elements found:', {
        select: !!destinationSelect,
        navBtn: !!navigateBtn,
        cancelBtn: !!cancelBtn,
        status: !!statusText,
        wifi: !!wifiScanBtn
    });

    // ============================================================
    // Populate Destinations Dropdown
    // ============================================================
    function populateDestinations(destinations) {
        if (!destinationSelect) return;
        destinationSelect.innerHTML = '<option value="">-- Select Destination --</option>';

        // Deduplicate: skip raw numbers that duplicate named entries
        var seen = {};
        var filtered = [];
        for (var i = 0; i < destinations.length; i++) {
            var d = destinations[i];
            if (/^\d+$/.test(d)) continue; // skip "401", "402" etc
            if (seen[d]) continue;
            seen[d] = true;
            filtered.push(d);
        }
        filtered.sort();

        for (var j = 0; j < filtered.length; j++) {
            var option = document.createElement('option');
            option.value = filtered[j];
            option.textContent = filtered[j];
            destinationSelect.appendChild(option);
        }
        console.log('[APP] Destinations populated:', filtered.length, 'items');

        // Enable navigate button logic
        if (navigateBtn) navigateBtn.disabled = true;
    }

    // ============================================================
    // Helper Functions
    // ============================================================
    function showDirections(navResult) {
        if (!directionsPanel) return;
        directionsPanel.style.display = 'block';
        if (navResult.directions && directionsList && navManager) {
            navManager.renderDirections(navResult.directions, directionsList);
        }
        if (totalDistanceEl) totalDistanceEl.textContent = 'Total: ' + navResult.total_distance + 'm';
        if (etaEl && navManager) etaEl.textContent = navManager.estimateTime(navResult.total_distance);
    }

    function hideDirections() {
        if (directionsPanel) directionsPanel.style.display = 'none';
        if (directionsList) directionsList.innerHTML = '';
    }

    function updatePositionDisplay(pos) {
        if (posDisplay) posDisplay.textContent = '(' + pos.x.toFixed(1) + ', ' + pos.y.toFixed(1) + ')';
        if (confidenceDisplay) {
            confidenceDisplay.textContent = pos.confidence !== undefined
                ? (pos.confidence * 100).toFixed(0) + '%' : '--';
        }

        if (pos.label && nodeDisplay) {
            nodeDisplay.textContent = pos.label;
        } else if (floorMap && floorMap.nodes && nodeDisplay) {
            var minDist = Infinity;
            var nearest = '--';
            var entries = Object.entries(floorMap.nodes);
            for (var i = 0; i < entries.length; i++) {
                var id = entries[i][0], node = entries[i][1];
                var dist = Math.sqrt(Math.pow(node.x - pos.x, 2) + Math.pow(node.y - pos.y, 2));
                if (dist < minDist) {
                    minDist = dist;
                    nearest = node.label || id;
                }
            }
            nodeDisplay.textContent = nearest;
        }

        if (wifiStatusEl && locManager && locManager.isTracking) {
            var src = pos.source === 'realtime_wifi' ? 'Live WiFi' : (pos.source || 'manual');
            var conf = pos.confidence !== undefined ? ' | ' + (pos.confidence * 100).toFixed(0) + '%' : '';
            wifiStatusEl.textContent = src + conf;
        }
    }

    // ============================================================
    // Event: Destination Selection Changed
    // ============================================================
    if (destinationSelect) {
        destinationSelect.addEventListener('change', function () {
            var val = destinationSelect.value;
            console.log('[APP] Destination changed:', val);
            if (navigateBtn) navigateBtn.disabled = !val;
        });
    }

    // ============================================================
    // Event: Navigate Button
    // ============================================================
    if (navigateBtn) {
        navigateBtn.addEventListener('click', async function () {
            console.log('[APP] Navigate clicked');
            var destination = destinationSelect ? destinationSelect.value : '';

            if (!destination) {
                if (statusText) statusText.textContent = 'Please select a destination first.';
                console.log('[APP] No destination selected');
                return;
            }
            if (!locManager || !locManager.currentPosition) {
                if (statusText) statusText.textContent = 'Position not set. Click a preset button or Set Position.';
                console.log('[APP] No position set');
                return;
            }

            console.log('[APP] Navigating from', locManager.currentPosition, 'to', destination);
            if (statusText) statusText.textContent = 'Calculating route to ' + destination + '...';
            navigateBtn.disabled = true;

            try {
                var result = await navManager.navigate(
                    locManager.currentPosition.x,
                    locManager.currentPosition.y,
                    destination
                );

                console.log('[APP] Navigate result:', result);

                if (result && result.success) {
                    floorMap.setNavigationPath(result.waypoints, result.end_node);
                    showDirections(result);
                    if (statusText) statusText.textContent = 'Navigating to ' + destination;
                    if (distanceBadge) {
                        distanceBadge.textContent = result.total_distance + 'm';
                        distanceBadge.style.display = 'inline';
                    }
                    if (cancelBtn) cancelBtn.style.display = 'inline';
                    navigateBtn.style.display = 'none';
                } else {
                    var errMsg = result ? result.error : 'Navigation failed (server down?)';
                    if (statusText) statusText.textContent = 'Error: ' + errMsg;
                    navigateBtn.disabled = false;
                }
            } catch (err) {
                console.error('[APP] Navigate exception:', err);
                if (statusText) statusText.textContent = 'Error: ' + err.message;
                navigateBtn.disabled = false;
            }
        });
    }

    // ============================================================
    // Event: Cancel Navigation
    // ============================================================
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function () {
            console.log('[APP] Cancel clicked');
            if (navManager) navManager.cancelNavigation();
            if (floorMap) floorMap.clearNavigation();
            hideDirections();
            if (statusText) statusText.textContent = 'Navigation cancelled.';
            if (distanceBadge) distanceBadge.style.display = 'none';
            cancelBtn.style.display = 'none';
            if (navigateBtn) {
                navigateBtn.style.display = 'inline';
                navigateBtn.disabled = !(destinationSelect && destinationSelect.value);
            }
        });
    }

    // ============================================================
    // Event: WiFi Tracking Button
    // ============================================================
    if (wifiScanBtn) {
        wifiScanBtn.addEventListener('click', function () {
            console.log('[APP] WiFi button clicked');
            if (locManager.isTracking) {
                locManager.stopRealTimeTracking();
                wifiScanBtn.textContent = 'Start WiFi Tracking';
                wifiScanBtn.classList.remove('btn-wifi-active');
                if (wifiStatusEl) wifiStatusEl.textContent = 'Tracking stopped';
                if (statusText) statusText.textContent = 'WiFi tracking stopped.';
            } else {
                locManager.startRealTimeTracking();
                wifiScanBtn.textContent = 'Stop WiFi Tracking';
                wifiScanBtn.classList.add('btn-wifi-active');
                if (wifiStatusEl) wifiStatusEl.textContent = 'Scanning every 3s...';
                if (statusText) statusText.textContent = 'Real-time WiFi tracking active.';
            }
        });
    }

    // ============================================================
    // Event: Set Position Manually
    // ============================================================
    var simLocateBtn = document.getElementById('sim-locate-btn');
    if (simLocateBtn) {
        simLocateBtn.addEventListener('click', function () {
            var x = parseFloat(document.getElementById('sim-x').value);
            var y = parseFloat(document.getElementById('sim-y').value);
            console.log('[APP] Set Position clicked:', x, y);
            if (!isNaN(x) && !isNaN(y)) {
                locManager.setManualPosition(x, y);
                if (statusText) statusText.textContent = 'Position set to (' + x + ', ' + y + ')';
            }
        });
    }

    // ============================================================
    // Event: Simulate Walk
    // ============================================================
    var simWalkBtn = document.getElementById('sim-walk-btn');
    if (simWalkBtn) {
        simWalkBtn.addEventListener('click', async function () {
            if (navManager && navManager.currentPath && navManager.currentPath.waypoints) {
                if (statusText) statusText.textContent = 'Simulating walk...';
                await locManager.simulateWalk(navManager.currentPath.waypoints, 1.5);
                if (statusText) statusText.textContent = 'Walk simulation complete!';
            } else {
                if (statusText) statusText.textContent = 'No navigation path. Navigate first!';
            }
        });
    }

    // ============================================================
    // Event: Preset Position Buttons
    // ============================================================
    var presetBtns = document.querySelectorAll('.preset-btn');
    for (var i = 0; i < presetBtns.length; i++) {
        (function (btn) {
            btn.addEventListener('click', function () {
                var x = parseFloat(btn.getAttribute('data-x'));
                var y = parseFloat(btn.getAttribute('data-y'));
                console.log('[APP] Preset clicked:', x, y);
                var simX = document.getElementById('sim-x');
                var simY = document.getElementById('sim-y');
                if (simX) simX.value = x;
                if (simY) simY.value = y;
                locManager.setManualPosition(x, y);
                if (statusText) statusText.textContent = 'Position set to (' + x + ', ' + y + ')';
            });
        })(presetBtns[i]);
    }

    // ============================================================
    // Event: Map Click -> Set Position
    // ============================================================
    var mapCanvas = document.getElementById('floor-map');
    if (mapCanvas) {
        mapCanvas.addEventListener('mapClick', function (e) {
            var detail = e.detail;
            if (detail.x >= 0 && detail.x <= floorMap.buildingWidth && detail.y >= 0 && detail.y <= floorMap.buildingDepth) {
                var rx = Math.round(detail.x * 2) / 2;
                var ry = Math.round(detail.y * 2) / 2;
                var simX = document.getElementById('sim-x');
                var simY = document.getElementById('sim-y');
                if (simX) simX.value = rx;
                if (simY) simY.value = ry;
                locManager.setManualPosition(rx, ry);
                if (statusText) statusText.textContent = 'Position set to (' + rx + ', ' + ry + ')';
            }
        });
    }

    // ============================================================
    // Auto Re-route
    // ============================================================
    var lastRoutePosition = null;
    async function autoReroute(x, y) {
        if (!lastRoutePosition) {
            lastRoutePosition = { x: x, y: y };
            return;
        }
        var dist = Math.sqrt(Math.pow(x - lastRoutePosition.x, 2) + Math.pow(y - lastRoutePosition.y, 2));
        if (dist > 3) {
            lastRoutePosition = { x: x, y: y };
            var result = await navManager.recalculate(x, y);
            if (result && result.success) {
                floorMap.setNavigationPath(result.waypoints, result.end_node);
                showDirections(result);
                if (distanceBadge) distanceBadge.textContent = result.total_distance + 'm';
            }
        }
    }

    // ============================================================
    // Init: Load data and set initial state
    // ============================================================
    async function init() {
        console.log('[APP] init() starting');

        try {
            await floorMap.loadGraph();
            console.log('[APP] Graph loaded, nodes:', Object.keys(floorMap.nodes || {}).length);
        } catch (e) {
            console.warn('[APP] loadGraph failed:', e);
        }

        try {
            var destinations = await navManager.loadDestinations();
            populateDestinations(destinations || []);
        } catch (e) {
            console.warn('[APP] loadDestinations failed:', e);
        }

        // Set initial position (Lift Area)
        locManager.setManualPosition(62.0, 5.0);
        console.log('[APP] Initial position set to Lift Area (62, 5)');

        // Register position update callback
        locManager.onPositionUpdate(function (pos) {
            try {
                floorMap.setUserPosition(pos.x, pos.y);
                updatePositionDisplay(pos);
                if (navManager && navManager.isNavigating) {
                    autoReroute(pos.x, pos.y);
                }
            } catch (e) {
                console.error('[APP] Position update error:', e);
            }
        });

        // Force render with initial position
        floorMap.setUserPosition(62.0, 5.0);

        if (statusText) statusText.textContent = 'Ready. Select a destination and click Navigate.';
        console.log('[APP] init() complete - app is ready');
    }

    // Run init
    init().catch(function (err) {
        console.error('[APP] init() failed:', err);
        if (statusText) statusText.textContent = 'Error: ' + err.message;
    });
});
