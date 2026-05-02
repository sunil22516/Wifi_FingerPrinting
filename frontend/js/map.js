/**
 * Floor Map Renderer
 * ==================
 * Draws the 4th floor map on an HTML5 Canvas.
 * Renders: walls, rooms, corridors, nodes, edges, user position, navigation path.
 * 
 * Author: Tripti (Frontend)
 */

class FloorMap {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // Map scaling: convert real-world meters to canvas pixels
        this.scale = 16;  // 1 meter = 16 pixels
        this.offsetX = 30; // Left padding
        this.offsetY = 30; // Top padding
        
        // State
        this.nodes = {};
        this.edges = [];
        this.userPosition = null;
        this.destinationNode = null;
        this.navigationPath = null;
        
        // Colors
        this.colors = {
            wall: '#2d3748',
            room: '#edf2f7',
            roomBorder: '#a0aec0',
            corridor: '#f7fafc',
            node: '#a0aec0',
            nodeLabel: '#4a5568',
            edge: '#e2e8f0',
            userDot: '#4299e1',
            userGlow: 'rgba(66, 153, 225, 0.3)',
            destination: '#e53e3e',
            destGlow: 'rgba(229, 62, 62, 0.3)',
            path: '#48bb78',
            pathGlow: 'rgba(72, 187, 120, 0.2)'
        };

        // Handle canvas click for position setting
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
    }

    /**
     * Convert real-world coordinates to canvas pixel coordinates.
     */
    toPixel(x, y) {
        return {
            px: this.offsetX + x * this.scale,
            py: this.offsetY + y * this.scale
        };
    }

    /**
     * Convert canvas pixel coordinates back to real-world coordinates.
     */
    toWorld(px, py) {
        return {
            x: (px - this.offsetX) / this.scale,
            y: (py - this.offsetY) / this.scale
        };
    }

    /**
     * Load graph data from backend.
     */
    async loadGraph() {
        try {
            const response = await fetch('/api/graph');
            const data = await response.json();
            if (data.success) {
                this.nodes = data.nodes;
                this.edges = data.edges;
                this.render();
            }
        } catch (error) {
            console.error('Failed to load graph:', error);
        }
    }

    /**
     * Full render of the map.
     */
    render() {
        const ctx = this.ctx;
        const width = this.canvas.width;
        const height = this.canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Background
        ctx.fillStyle = '#f7fafc';
        ctx.fillRect(0, 0, width, height);

        // Draw floor outline
        this.drawFloorPlan();

        // Draw edges (corridors)
        this.drawEdges();

        // Draw navigation path (if any)
        if (this.navigationPath) {
            this.drawNavigationPath();
        }

        // Draw nodes
        this.drawNodes();

        // Draw destination marker
        if (this.destinationNode) {
            this.drawDestination();
        }

        // Draw user position
        if (this.userPosition) {
            this.drawUserPosition();
        }

        // Draw scale bar
        this.drawScaleBar();
    }

    /**
     * Draw the floor plan outline and rooms.
     */
    drawFloorPlan() {
        const ctx = this.ctx;

        // Main floor boundary
        const topLeft = this.toPixel(0, 0);
        const botRight = this.toPixel(50, 32);

        ctx.strokeStyle = this.colors.wall;
        ctx.lineWidth = 3;
        ctx.strokeRect(topLeft.px, topLeft.py, 
                       botRight.px - topLeft.px, botRight.py - topLeft.py);

        // Draw rooms as labeled rectangles
        const rooms = [
            { x: 7, y: 4, w: 8, h: 6, label: "Lab 1\n(401)" },
            { x: 35, y: 4, w: 8, h: 6, label: "Lab 2\n(402)" },
            { x: 1, y: 10, w: 7, h: 4, label: "403" },
            { x: 1, y: 16, w: 7, h: 5, label: "404" },
            { x: 42, y: 10, w: 7, h: 4, label: "405" },
            { x: 42, y: 16, w: 7, h: 5, label: "406" },
            { x: 42, y: 22, w: 7, h: 4, label: "407\n(Server)" },
            { x: 10, y: 27, w: 8, h: 5, label: "408\n(Meeting)" },
            { x: 32, y: 27, w: 8, h: 5, label: "409" },
            { x: 7, y: 12, w: 6, h: 5, label: "410" },
            { x: 7, y: 22, w: 6, h: 5, label: "411" },
            { x: 36, y: 22, w: 6, h: 5, label: "B-412" },
            { x: 19, y: 27, w: 5, h: 5, label: "Pantry" },
            { x: 26, y: 27, w: 5, h: 5, label: "WC" },
        ];

        rooms.forEach(room => {
            const pos = this.toPixel(room.x, room.y);
            const w = room.w * this.scale;
            const h = room.h * this.scale;

            // Room fill
            ctx.fillStyle = this.colors.room;
            ctx.fillRect(pos.px, pos.py, w, h);

            // Room border
            ctx.strokeStyle = this.colors.roomBorder;
            ctx.lineWidth = 1.5;
            ctx.strokeRect(pos.px, pos.py, w, h);

            // Room label
            ctx.fillStyle = '#4a5568';
            ctx.font = '11px Segoe UI';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            const lines = room.label.split('\n');
            lines.forEach((line, i) => {
                ctx.fillText(line, pos.px + w/2, pos.py + h/2 + (i - (lines.length-1)/2) * 13);
            });
        });

        // Elevator
        const elev = this.toPixel(22, 0);
        ctx.fillStyle = '#bee3f8';
        ctx.fillRect(elev.px, elev.py, 6 * this.scale, 3 * this.scale);
        ctx.strokeStyle = '#2b6cb0';
        ctx.lineWidth = 2;
        ctx.strokeRect(elev.px, elev.py, 6 * this.scale, 3 * this.scale);
        ctx.fillStyle = '#2b6cb0';
        ctx.font = 'bold 12px Segoe UI';
        ctx.textAlign = 'center';
        ctx.fillText('🛗 ELEVATOR', elev.px + 3 * this.scale, elev.py + 1.5 * this.scale);
    }

    /**
     * Draw graph edges as light corridor lines.
     */
    drawEdges() {
        const ctx = this.ctx;
        ctx.strokeStyle = this.colors.edge;
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 4]);

        this.edges.forEach(edge => {
            const fromNode = this.nodes[edge.from];
            const toNode = this.nodes[edge.to];
            if (!fromNode || !toNode) return;

            const from = this.toPixel(fromNode.x, fromNode.y);
            const to = this.toPixel(toNode.x, toNode.y);

            ctx.beginPath();
            ctx.moveTo(from.px, from.py);
            ctx.lineTo(to.px, to.py);
            ctx.stroke();
        });

        ctx.setLineDash([]);
    }

    /**
     * Draw graph nodes as small circles.
     */
    drawNodes() {
        const ctx = this.ctx;

        Object.entries(this.nodes).forEach(([id, node]) => {
            const pos = this.toPixel(node.x, node.y);
            const isRoom = node.type === 'room';
            const isLandmark = node.type === 'landmark';

            // Node dot
            ctx.beginPath();
            ctx.arc(pos.px, pos.py, isRoom ? 5 : (isLandmark ? 6 : 4), 0, Math.PI * 2);
            ctx.fillStyle = isRoom ? '#805ad5' : (isLandmark ? '#d69e2e' : this.colors.node);
            ctx.fill();

            // Label for important nodes
            if (isRoom || isLandmark) {
                ctx.fillStyle = this.colors.nodeLabel;
                ctx.font = '9px Segoe UI';
                ctx.textAlign = 'center';
                ctx.fillText(node.label || id, pos.px, pos.py - 10);
            }
        });
    }

    /**
     * Draw navigation path as a thick green line.
     */
    drawNavigationPath() {
        if (!this.navigationPath || this.navigationPath.length < 2) return;

        const ctx = this.ctx;
        const waypoints = this.navigationPath;

        // Path glow
        ctx.strokeStyle = this.colors.pathGlow;
        ctx.lineWidth = 12;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.beginPath();
        const start = this.toPixel(waypoints[0].x, waypoints[0].y);
        ctx.moveTo(start.px, start.py);
        for (let i = 1; i < waypoints.length; i++) {
            const p = this.toPixel(waypoints[i].x, waypoints[i].y);
            ctx.lineTo(p.px, p.py);
        }
        ctx.stroke();

        // Path line
        ctx.strokeStyle = this.colors.path;
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(start.px, start.py);
        for (let i = 1; i < waypoints.length; i++) {
            const p = this.toPixel(waypoints[i].x, waypoints[i].y);
            ctx.lineTo(p.px, p.py);
        }
        ctx.stroke();

        // Direction arrows along path
        for (let i = 0; i < waypoints.length - 1; i++) {
            const from = this.toPixel(waypoints[i].x, waypoints[i].y);
            const to = this.toPixel(waypoints[i+1].x, waypoints[i+1].y);
            const midX = (from.px + to.px) / 2;
            const midY = (from.py + to.py) / 2;
            const angle = Math.atan2(to.py - from.py, to.px - from.px);

            ctx.save();
            ctx.translate(midX, midY);
            ctx.rotate(angle);
            ctx.fillStyle = this.colors.path;
            ctx.beginPath();
            ctx.moveTo(6, 0);
            ctx.lineTo(-4, -4);
            ctx.lineTo(-4, 4);
            ctx.closePath();
            ctx.fill();
            ctx.restore();
        }
    }

    /**
     * Draw user position as a pulsing blue dot.
     */
    drawUserPosition() {
        const ctx = this.ctx;
        const pos = this.toPixel(this.userPosition.x, this.userPosition.y);

        // Glow
        ctx.beginPath();
        ctx.arc(pos.px, pos.py, 18, 0, Math.PI * 2);
        ctx.fillStyle = this.colors.userGlow;
        ctx.fill();

        // Inner dot
        ctx.beginPath();
        ctx.arc(pos.px, pos.py, 8, 0, Math.PI * 2);
        ctx.fillStyle = this.colors.userDot;
        ctx.fill();

        // White border
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    /**
     * Draw destination marker.
     */
    drawDestination() {
        const ctx = this.ctx;
        const node = this.nodes[this.destinationNode];
        if (!node) return;

        const pos = this.toPixel(node.x, node.y);

        // Glow
        ctx.beginPath();
        ctx.arc(pos.px, pos.py, 16, 0, Math.PI * 2);
        ctx.fillStyle = this.colors.destGlow;
        ctx.fill();

        // Pin
        ctx.beginPath();
        ctx.arc(pos.px, pos.py, 7, 0, Math.PI * 2);
        ctx.fillStyle = this.colors.destination;
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Label
        ctx.fillStyle = this.colors.destination;
        ctx.font = 'bold 11px Segoe UI';
        ctx.textAlign = 'center';
        ctx.fillText('📍 ' + (node.label || ''), pos.px, pos.py - 16);
    }

    /**
     * Draw scale bar.
     */
    drawScaleBar() {
        const ctx = this.ctx;
        const barLength = 10 * this.scale; // 10 meters
        const x = this.canvas.width - barLength - 20;
        const y = this.canvas.height - 20;

        ctx.strokeStyle = '#4a5568';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + barLength, y);
        ctx.stroke();

        // End caps
        ctx.beginPath();
        ctx.moveTo(x, y - 4);
        ctx.lineTo(x, y + 4);
        ctx.moveTo(x + barLength, y - 4);
        ctx.lineTo(x + barLength, y + 4);
        ctx.stroke();

        ctx.fillStyle = '#4a5568';
        ctx.font = '10px Segoe UI';
        ctx.textAlign = 'center';
        ctx.fillText('10 meters', x + barLength / 2, y - 8);
    }

    /**
     * Set user position and re-render.
     */
    setUserPosition(x, y) {
        this.userPosition = { x, y };
        this.render();
    }

    /**
     * Set navigation path and re-render.
     */
    setNavigationPath(waypoints, destNodeId) {
        this.navigationPath = waypoints;
        this.destinationNode = destNodeId;
        this.render();
    }

    /**
     * Clear navigation path.
     */
    clearNavigation() {
        this.navigationPath = null;
        this.destinationNode = null;
        this.render();
    }

    /**
     * Handle canvas click (set position for testing).
     */
    handleClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        const px = (event.clientX - rect.left) * scaleX;
        const py = (event.clientY - rect.top) * scaleY;
        const world = this.toWorld(px, py);

        // Dispatch custom event with world coordinates
        const customEvent = new CustomEvent('mapClick', { detail: world });
        this.canvas.dispatchEvent(customEvent);
    }
}
