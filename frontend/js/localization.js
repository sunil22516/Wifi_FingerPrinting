/**
 * Localization Module (Frontend)
 * ===============================
 * Handles WiFi scanning (where browser supports it) and 
 * communicates with the localization backend API.
 * 
 * Note: Real WiFi scanning from browser requires special permissions
 * and is limited. In practice, this is handled by a companion Android app
 * or via manual/simulated input for web demo.
 * 
 * Author: Tripti (Frontend) / Tikam (Localization)
 */

class LocalizationManager {
    constructor() {
        this.currentPosition = null;
        this.positionHistory = [];
        this.isTracking = false;
        this.pollingInterval = null;
        this.updateCallbacks = [];
    }

    /**
     * Register a callback to be called when position updates.
     */
    onPositionUpdate(callback) {
        this.updateCallbacks.push(callback);
    }

    /**
     * Notify all registered callbacks of position update.
     */
    notifyUpdate(position) {
        this.currentPosition = position;
        this.positionHistory.push({ ...position, timestamp: Date.now() });
        
        // Keep history manageable
        if (this.positionHistory.length > 100) {
            this.positionHistory.shift();
        }

        this.updateCallbacks.forEach(cb => cb(position));
    }

    /**
     * Send WiFi readings to backend for localization.
     * @param {object} wifiReadings - {bssid: rssi} map
     * @returns {object} Position estimate {x, y, confidence}
     */
    async localizeFromWifi(wifiReadings) {
        try {
            const response = await fetch('/api/localize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wifi_readings: wifiReadings,
                    smoothed: true
                })
            });

            const data = await response.json();
            if (data.success) {
                this.notifyUpdate({
                    x: data.x,
                    y: data.y,
                    confidence: data.confidence,
                    source: 'wifi'
                });
                return data;
            }
        } catch (error) {
            console.error('Localization error:', error);
        }
        return null;
    }

    /**
     * Set position manually (for demo/testing).
     */
    setManualPosition(x, y) {
        this.notifyUpdate({
            x: x,
            y: y,
            confidence: 1.0,
            source: 'manual'
        });
    }

    /**
     * Start polling the backend for position updates.
     * Used when an Android companion app is pushing WiFi data to the server.
     */
    startTracking(intervalMs = 2000) {
        this.isTracking = true;
        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/position');
                const data = await response.json();
                if (data.success) {
                    this.notifyUpdate({
                        x: data.x,
                        y: data.y,
                        confidence: 1.0,
                        heading: data.heading,
                        source: 'fusion'
                    });
                }
            } catch (error) {
                // Silent fail - backend might not have position yet
            }
        }, intervalMs);
    }

    /**
     * Stop position tracking.
     */
    stopTracking() {
        this.isTracking = false;
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    /**
     * Simulate walking along a path (for demo purposes).
     * Moves the position along waypoints at walking speed.
     */
    async simulateWalk(waypoints, speedMps = 1.2) {
        if (!waypoints || waypoints.length < 2) return;

        for (let i = 0; i < waypoints.length - 1; i++) {
            const from = waypoints[i];
            const to = waypoints[i + 1];
            const dx = to.x - from.x;
            const dy = to.y - from.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const steps = Math.ceil(dist / 0.5); // Update every 0.5m
            const stepTime = (dist / speedMps / steps) * 1000; // ms per step

            for (let s = 0; s <= steps; s++) {
                const t = s / steps;
                const x = from.x + dx * t;
                const y = from.y + dy * t;
                this.setManualPosition(x, y);
                await new Promise(resolve => setTimeout(resolve, stepTime));
            }
        }
    }

    /**
     * Get simulated WiFi readings for a position (for testing without hardware).
     * Generates fake RSSI values based on distance from known AP positions.
     */
    getSimulatedWifiReadings(x, y) {
        // Simulated AP positions (matching our radio map)
        const aps = [
            { bssid: "AA:BB:CC:11:22:01", x: 25, y: 2 },
            { bssid: "AA:BB:CC:11:22:02", x: 5, y: 10 },
            { bssid: "AA:BB:CC:11:22:03", x: 45, y: 10 },
            { bssid: "AA:BB:CC:11:22:04", x: 45, y: 25 },
            { bssid: "AA:BB:CC:11:22:05", x: 25, y: 30 }
        ];

        const readings = {};
        aps.forEach(ap => {
            const dist = Math.sqrt((ap.x - x) ** 2 + (ap.y - y) ** 2);
            // Log-distance path loss model (simplified)
            // RSSI ≈ -30 - 20*log10(dist) with noise
            const noise = (Math.random() - 0.5) * 6;
            const rssi = Math.round(-30 - 20 * Math.log10(Math.max(dist, 1)) + noise);
            readings[ap.bssid] = Math.max(rssi, -100);
        });

        return readings;
    }
}
