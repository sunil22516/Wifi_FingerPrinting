/**
 * Navigation Module
 * ==================
 * Handles communication with backend navigation API.
 * Manages destination selection, path requests, and direction display.
 * 
 * Author: Tripti (Frontend)
 */

class NavigationManager {
    constructor() {
        this.currentDestination = null;
        this.currentPath = null;
        this.destinations = [];
        this.isNavigating = false;
    }

    /**
     * Load available destinations from backend.
     */
    async loadDestinations() {
        try {
            const response = await fetch('/api/destinations');
            const data = await response.json();
            if (data.success) {
                this.destinations = data.destinations;
                return data.destinations;
            }
        } catch (error) {
            console.error('Failed to load destinations:', error);
        }
        return [];
    }

    /**
     * Request navigation path from backend.
     * @param {number} startX - Current X position
     * @param {number} startY - Current Y position
     * @param {string} destination - Destination name/room number
     * @returns {object} Navigation result with path and directions
     */
    async navigate(startX, startY, destination) {
        try {
            const response = await fetch('/api/navigate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_x: startX,
                    start_y: startY,
                    destination: destination
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.currentPath = data;
                this.currentDestination = destination;
                this.isNavigating = true;
            }
            
            return data;
        } catch (error) {
            console.error('Navigation request failed:', error);
            return { success: false, error: 'Network error' };
        }
    }

    /**
     * Cancel current navigation.
     */
    cancelNavigation() {
        this.currentPath = null;
        this.currentDestination = null;
        this.isNavigating = false;
    }

    /**
     * Recalculate path from new position (re-routing).
     */
    async recalculate(newX, newY) {
        if (!this.currentDestination) return null;
        return await this.navigate(newX, newY, this.currentDestination);
    }

    /**
     * Render directions list in the DOM.
     * @param {Array} directions - Direction steps from backend
     * @param {HTMLElement} container - DOM element to render into
     */
    renderDirections(directions, container) {
        container.innerHTML = '';

        directions.forEach((step, index) => {
            const div = document.createElement('div');
            div.className = 'direction-step';

            const isArrived = step.action === 'arrived';
            const icon = this.getDirectionIcon(step.action);

            div.innerHTML = `
                <div class="step-number ${isArrived ? 'arrived' : ''}">${icon}</div>
                <div>
                    <div class="step-text">${step.instruction}</div>
                    ${step.distance > 0 ? `<div class="step-distance">${step.distance}m</div>` : ''}
                </div>
            `;

            container.appendChild(div);
        });
    }

    /**
     * Get icon/emoji for direction action.
     */
    getDirectionIcon(action) {
        const icons = {
            'start': '🚶',
            'straight': '⬆️',
            'left': '⬅️',
            'right': '➡️',
            'slight left': '↖️',
            'slight right': '↗️',
            'sharp left': '↩️',
            'sharp right': '↪️',
            'u-turn': '🔄',
            'arrived': '✅'
        };
        return icons[action] || '•';
    }

    /**
     * Format total distance for display.
     */
    formatDistance(meters) {
        if (meters < 1000) {
            return `${Math.round(meters)}m`;
        }
        return `${(meters / 1000).toFixed(1)}km`;
    }

    /**
     * Estimate walking time (average 1.2 m/s walking speed).
     */
    estimateTime(meters) {
        const seconds = meters / 1.2;
        if (seconds < 60) {
            return `~${Math.round(seconds)}s`;
        }
        return `~${Math.ceil(seconds / 60)} min`;
    }
}
