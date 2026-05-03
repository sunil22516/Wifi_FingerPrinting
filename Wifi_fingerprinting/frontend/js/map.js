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

        // Map dimensions (meters) match graph.json metadata
        this.buildingWidth = 120.0;
        this.buildingDepth = 25.0;

        // Background map image (crop removes legend area)
        this.mapImagePath = 'assets/map.png';
        this.mapImageCrop = { x: 0.02, y: 0.03, w: 0.96, h: 0.58 };
        this.mapImage = new Image();
        this.mapImageLoaded = false;
        this.mapImage.onload = () => {
            this.mapImageLoaded = true;
            this.updateMapArea();
            this.render();
        };
        this.mapImage.src = this.mapImagePath;

        this.updateMapArea();
        
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
            userDot: '#1e40af',
            userGlow: 'rgba(30, 64, 175, 0.35)',
            destination: '#b91c1c',
            destGlow: 'rgba(185, 28, 28, 0.35)',
            path: '#15803d',
            pathGlow: 'rgba(21, 128, 61, 0.25)'
        };

        // Handle canvas click for position setting
        this.canvas.addEventListener('click', (e) => this.handleClick(e));

        // Draw the static floor plan immediately (no API call needed)
        this.render();
    }

    /**
     * Convert real-world coordinates to canvas pixel coordinates.
     */
    toPixel(x, y) {
        return {
            px: this.mapArea.x + (x / this.buildingWidth) * this.mapArea.width,
            py: this.mapArea.y + (y / this.buildingDepth) * this.mapArea.height
        };
    }

    /**
     * Convert canvas pixel coordinates back to real-world coordinates.
     */
    toWorld(px, py) {
        return {
            x: ((px - this.mapArea.x) / this.mapArea.width) * this.buildingWidth,
            y: ((py - this.mapArea.y) / this.mapArea.height) * this.buildingDepth
        };
    }

    /**
     * Compute the drawable map area and scale based on canvas and image aspect.
     */
    updateMapArea() {
        const padding = 20;
        const availW = this.canvas.width - padding * 2;
        const availH = this.canvas.height - padding * 2;

        let targetAspect = this.buildingWidth / this.buildingDepth;
        if (this.mapImageLoaded) {
            const cropW = this.mapImage.width * this.mapImageCrop.w;
            const cropH = this.mapImage.height * this.mapImageCrop.h;
            if (cropH > 0) {
                targetAspect = cropW / cropH;
            }
        }

        let drawW = availW;
        let drawH = availH;
        if (drawW / drawH > targetAspect) {
            drawW = drawH * targetAspect;
        } else {
            drawH = drawW / targetAspect;
        }

        this.mapArea = {
            x: padding + (availW - drawW) / 2,
            y: padding + (availH - drawH) / 2,
            width: drawW,
            height: drawH
        };

        this.scale = this.mapArea.width / this.buildingWidth;
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
                if (data.metadata) {
                    if (data.metadata.building_width_m) {
                        this.buildingWidth = data.metadata.building_width_m;
                    }
                    if (data.metadata.building_depth_m) {
                        this.buildingDepth = data.metadata.building_depth_m;
                    }
                    this.updateMapArea();
                }
            }
        } catch (error) {
            console.error('Failed to load graph:', error);
        }
        // Always re-render (even on error, to show the static floor plan)
        this.render();
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
     * Draw the 4th-floor A-wing floor plan.
     * Layout (1 unit = 1 metre):
     *   North side (y=0–6):  Faculty rooms A401–A412 in a row (x 0–52)
     *   Main corridor (y=6–10): walkway
     *   South side (y=10–22): Labs (Design Studio, AID, CI, MIDAS, HMI)
     *                          + Discussion rooms
     *   Lift / B-wing (x=51–65, y=0–22)
     */
    drawFloorPlan() {
        const ctx = this.ctx;
        if (this.mapImageLoaded) {
            const sx = this.mapImage.width * this.mapImageCrop.x;
            const sy = this.mapImage.height * this.mapImageCrop.y;
            const sw = this.mapImage.width * this.mapImageCrop.w;
            const sh = this.mapImage.height * this.mapImageCrop.h;

            ctx.drawImage(
                this.mapImage,
                sx, sy, sw, sh,
                this.mapArea.x, this.mapArea.y, this.mapArea.width, this.mapArea.height
            );
        } else {
            ctx.fillStyle = '#f0f4f8';
            ctx.fillRect(this.mapArea.x, this.mapArea.y, this.mapArea.width, this.mapArea.height);
        }

        ctx.strokeStyle = this.colors.wall;
        ctx.lineWidth = 2;
        ctx.strokeRect(this.mapArea.x, this.mapArea.y, this.mapArea.width, this.mapArea.height);
    }

    /**
     * Draw graph edges as light corridor lines.
     */
    drawEdges() {
        const ctx = this.ctx;
        ctx.strokeStyle = '#94a3b8';
        ctx.lineWidth = 2.5;
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
     * Draw graph nodes as small circles with labels.
     */
    drawNodes() {
        const ctx = this.ctx;

        Object.entries(this.nodes).forEach(([id, node]) => {
            const pos = this.toPixel(node.x, node.y);
            const isRoom = node.type === 'room';
            const isLandmark = node.type === 'landmark';
            const radius = isRoom ? 5 : (isLandmark ? 6 : 3);

            ctx.beginPath();
            ctx.arc(pos.px, pos.py, radius, 0, Math.PI * 2);
            ctx.fillStyle = isRoom ? '#805ad5' : (isLandmark ? '#d69e2e' : this.colors.node);
            ctx.fill();

            ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
            ctx.lineWidth = 2;
            ctx.stroke();

            if (isRoom || isLandmark) {
                ctx.fillStyle = this.colors.nodeLabel;
                ctx.font = '8px Segoe UI';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';
                ctx.fillText(node.label || id, pos.px, pos.py - 6);
            }
        });
    }

    /**
     * Draw navigation path as a thick animated green line with arrows.
     */
    drawNavigationPath() {
        if (!this.navigationPath || this.navigationPath.length < 2) return;

        const ctx = this.ctx;
        const waypoints = this.navigationPath;

        const startPx = this.toPixel(waypoints[0].x, waypoints[0].y);

        // Outline for contrast
        ctx.strokeStyle = 'rgba(15, 23, 42, 0.45)';
        ctx.lineWidth = 7;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.beginPath();
        ctx.moveTo(startPx.px, startPx.py);
        for (let i = 1; i < waypoints.length; i++) {
            const p = this.toPixel(waypoints[i].x, waypoints[i].y);
            ctx.lineTo(p.px, p.py);
        }
        ctx.stroke();

        // Glow
        ctx.strokeStyle = this.colors.pathGlow;
        ctx.lineWidth = 16;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.beginPath();
        ctx.moveTo(startPx.px, startPx.py);
        for (let i = 1; i < waypoints.length; i++) {
            const p = this.toPixel(waypoints[i].x, waypoints[i].y);
            ctx.lineTo(p.px, p.py);
        }
        ctx.stroke();

        // Line
        ctx.strokeStyle = this.colors.path;
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.moveTo(startPx.px, startPx.py);
        for (let i = 1; i < waypoints.length; i++) {
            const p = this.toPixel(waypoints[i].x, waypoints[i].y);
            ctx.lineTo(p.px, p.py);
        }
        ctx.stroke();

        // Direction arrows along path
        for (let i = 0; i < waypoints.length - 1; i++) {
            const from = this.toPixel(waypoints[i].x, waypoints[i].y);
            const to = this.toPixel(waypoints[i + 1].x, waypoints[i + 1].y);
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
        ctx.arc(pos.px, pos.py, 20, 0, Math.PI * 2);
        ctx.fillStyle = this.colors.userGlow;
        ctx.fill();

        // Inner dot
        ctx.beginPath();
        ctx.arc(pos.px, pos.py, 9, 0, Math.PI * 2);
        ctx.fillStyle = this.colors.userDot;
        ctx.fill();

        // White border
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 3;
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
        ctx.arc(pos.px, pos.py, 18, 0, Math.PI * 2);
        ctx.fillStyle = this.colors.destGlow;
        ctx.fill();

        // Pin
        ctx.beginPath();
        ctx.arc(pos.px, pos.py, 8, 0, Math.PI * 2);
        ctx.fillStyle = this.colors.destination;
        ctx.fill();
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 3;
        ctx.stroke();

        // Label
        ctx.fillStyle = this.colors.destination;
        ctx.font = 'bold 12px Segoe UI';
        ctx.textAlign = 'center';
        ctx.fillText('📍 ' + (node.label || ''), pos.px, pos.py - 16);
    }

    /**
     * Draw scale bar.
     */
    drawScaleBar() {
        const ctx = this.ctx;
        const barLength = 10 * this.scale; // 10 meters
        const x = this.mapArea.x + this.mapArea.width - barLength - 12;
        const y = this.mapArea.y + this.mapArea.height - 12;

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
