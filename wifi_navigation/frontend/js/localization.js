/**
 * Localization Module (Frontend)
 * ===============================
 * Handles real-time WiFi-based positioning.
 *
 * How real-time WiFi localization works:
 *   1. The Flask backend (app.py) runs on a laptop/PC that has a WiFi adapter.
 *   2. The frontend calls POST /api/scan every N seconds.
 *   3. The backend scans nearby WiFi networks using wifi_scanner.py
 *      (which uses pywifi for accurate dBm, or netsh/nmcli as fallback),
 *      runs KNN localization against the fingerprint database, and
 *      returns the estimated {x, y, confidence}.
 *   4. The result is shown on the map and used for navigation.
 *
 * For demo / testing without a WiFi adapter:
 *   - Use setManualPosition() to place the user at a known location.
 *   - Use simulateWalk() to animate movement along a path.
 *
 * Author: Tripti (Frontend) / Tikam (Localization)
 */

class LocalizationManager {
    constructor() {
        this.currentPosition = null;
        this.positionHistory = [];
        this.isTracking = false;
        this.scanInterval = null;
        this.updateCallbacks = [];
        this.scanIntervalMs = 3000; // scan every 3 seconds
        this.useSmoothing = true;
    }

    /**
     * Register a callback to be called whenever position updates.
     * @param {function} callback - receives {x, y, confidence, source}
     */
    onPositionUpdate(callback) {
        this.updateCallbacks.push(callback);
    }

    /**
     * Notify all registered callbacks of a position update.
     */
    notifyUpdate(position) {
        this.currentPosition = position;
        this.positionHistory.push({ ...position, timestamp: Date.now() });
        if (this.positionHistory.length > 200) {
            this.positionHistory.shift();
        }
        this.updateCallbacks.forEach(cb => cb(position));
    }

    // ---------------------------------------------------------------
    // Real-time WiFi scan (calls backend which scans the actual WiFi)
    // ---------------------------------------------------------------

    /**
     * Trigger one WiFi scan on the server and get localized position.
     * The backend must be running on a machine with a WiFi adapter.
     * @returns {object|null} position {x, y, confidence, label, source}
     */
    async scanOnce() {
        try {
            const resp = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ smoothed: this.useSmoothing })
            });
            const data = await resp.json();
            if (data.success) {
                const pos = {
                    x: data.x,
                    y: data.y,
                    confidence: data.confidence,
                    label: data.label || '',
                    source: 'realtime_wifi'
                };
                this.notifyUpdate(pos);
                return pos;
            } else {
                console.warn('Scan failed:', data.error);
            }
        } catch (err) {
            console.error('Scan request error:', err);
        }
        return null;
    }

    /**
     * Start periodic real-time WiFi scanning.
     * Calls /api/scan every this.scanIntervalMs milliseconds.
     */
    startRealTimeTracking() {
        if (this.isTracking) return;
        this.isTracking = true;

        // Immediate first scan
        this.scanOnce();

        this.scanInterval = setInterval(() => {
            this.scanOnce();
        }, this.scanIntervalMs);

        console.log(`Real-time WiFi tracking started (every ${this.scanIntervalMs / 1000}s)`);
    }

    /**
     * Stop periodic real-time WiFi scanning.
     */
    stopRealTimeTracking() {
        this.isTracking = false;
        if (this.scanInterval) {
            clearInterval(this.scanInterval);
            this.scanInterval = null;
        }
        console.log('Real-time WiFi tracking stopped');
    }

    // ---------------------------------------------------------------
    // Submit WiFi readings from external source (e.g. Android companion)
    // ---------------------------------------------------------------

    /**
     * Send WiFi readings captured externally to the backend for localization.
     * Use this when the WiFi scan is done on a phone and sent to the backend.
     * @param {object} wifiReadings - {bssid: rssi} — all lowercase BSSIDs
     */
    async localizeFromWifi(wifiReadings) {
        try {
            const response = await fetch('/api/localize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wifi_readings: wifiReadings,
                    smoothed: this.useSmoothing
                })
            });
            const data = await response.json();
            if (data.success) {
                this.notifyUpdate({
                    x: data.x,
                    y: data.y,
                    confidence: data.confidence,
                    source: 'external_wifi'
                });
                return data;
            }
        } catch (error) {
            console.error('Localization error:', error);
        }
        return null;
    }

    // ---------------------------------------------------------------
    // Manual / demo controls
    // ---------------------------------------------------------------

    /**
     * Set position manually (for demo/testing without WiFi hardware).
     */
    setManualPosition(x, y) {
        this.notifyUpdate({ x, y, confidence: 1.0, source: 'manual' });
    }

    /**
     * Simulate walking along a path at a given speed (for demo).
     * @param {Array} waypoints - [{x, y, label}, ...]
     * @param {number} speedMps - walking speed in m/s
     */
    async simulateWalk(waypoints, speedMps = 1.2) {
        if (!waypoints || waypoints.length < 2) return;
        for (let i = 0; i < waypoints.length - 1; i++) {
            const from = waypoints[i];
            const to = waypoints[i + 1];
            const dx = to.x - from.x;
            const dy = to.y - from.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const steps = Math.ceil(dist / 0.5);
            const stepTime = (dist / speedMps / steps) * 1000;

            for (let s = 0; s <= steps; s++) {
                const t = s / steps;
                this.setManualPosition(
                    parseFloat((from.x + dx * t).toFixed(2)),
                    parseFloat((from.y + dy * t).toFixed(2))
                );
                await new Promise(r => setTimeout(r, stepTime));
            }
        }
    }

    /**
     * Generate simulated WiFi readings for a given (x,y) position.
     * Uses real BSSIDs from the fingerprint data so the KNN engine
     * can actually match them during demos.
     *
     * AP approximate positions based on fingerprint data analysis:
     *   6c:31:0e:56:e1:XX  →  near A401-A403, Design Studio (x≈7, y≈8)
     *   40:01:7a:53:96:XX  →  near A404-A407, CI Lab       (x≈24, y≈8)
     *   f8:0b:cb:f3:88:XX  →  near A407-A409, MIDAS Lab    (x≈36, y≈8)
     *   40:01:7a:53:97:XX  →  near A410-A412, HMI Lab      (x≈44, y≈8)
     *   30:8b:b2:61:de:XX  →  near Lift / Open Area        (x≈52, y≈8)
     */
    getSimulatedWifiReadings(x, y) {
        const apGroups = [
            // [bssid_base, ap_x, ap_y, suffix_list]
            ['6c:31:0e:56:e1', 7,  3, ['20','21','22','23','24','25']],
            ['40:01:7a:53:96', 24, 3, ['80','81','82','83','84','8a','8f']],
            ['f8:0b:cb:f3:88', 36, 3, ['00','01','04','05','0b','0e']],
            ['40:01:7a:53:97', 44, 3, ['20','21','22','23']],
            ['30:8b:b2:61:de', 52, 7, ['00','01','02','03','05','0a','0b','0e','0f']]
        ];

        const readings = {};
        apGroups.forEach(([base, ax, ay, suffixes]) => {
            const dist = Math.max(1, Math.sqrt((ax - x) ** 2 + (ay - y) ** 2));
            // Log-distance path loss: RSSI ≈ -40 - 30*log10(dist)
            const baseRssi = -40 - 30 * Math.log10(dist);
            suffixes.forEach(sfx => {
                const noise = (Math.random() - 0.5) * 4;
                readings[`${base}:${sfx}`] = Math.round(
                    Math.max(-95, Math.min(-20, baseRssi + noise))
                );
            });
        });
        return readings;
    }
}
