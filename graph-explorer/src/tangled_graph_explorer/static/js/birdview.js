/**
 * Bird View (minimap) rendering
 * 
 * Shows scaled-down version of the graph with viewport indicator.
 * Viewport syncs with Main View zoom/pan.
 */

class BirdView {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.svg = null;
        this.viewportRect = null;
        this.scale = 1;
        
        // Main view dimensions for viewport calculation
        this.mainViewWidth = 0;
        this.mainViewHeight = 0;
    }
    
    /**
     * Initialize the minimap
     */
    init() {
        if (!this.container) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        // Clear existing
        const existingViewport = this.container.querySelector('#viewport-rect');
        this.container.innerHTML = '';
        
        // Create SVG
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        this.mainGroup = this.svg.append('g');
        
        // Re-add viewport rect
        this.viewportRect = document.createElement('div');
        this.viewportRect.id = 'viewport-rect';
        this.container.appendChild(this.viewportRect);
    }
    
    /**
     * Render scaled-down version of the graph
     * @param {Object} data - Graph data with nodes and edges
     */
    render(data) {
        if (!this.svg) this.init();
        if (!data || !data.nodes || data.nodes.length === 0) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight - 10; // Account for viewport rect
        
        // Calculate bounds of the graph
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        
        data.nodes.forEach(node => {
            if (node.x !== undefined) {
                minX = Math.min(minX, node.x);
                maxX = Math.max(maxX, node.x);
                minY = Math.min(minY, node.y);
                maxY = Math.max(maxY, node.y);
            }
        });
        
        // If no positions, use default bounds
        if (!isFinite(minX)) {
            minX = 0; maxX = 500;
            minY = 0; maxY = 400;
        }
        
        // Calculate scale to fit
        const graphWidth = maxX - minX + 60;
        const graphHeight = maxY - minY + 60;
        this.scale = Math.min(width / graphWidth, height / graphHeight, 1);
        
        // Clear and render
        this.mainGroup.selectAll('*').remove();
        
        // Apply transform
        const offsetX = (width - graphWidth * this.scale) / 2 - minX * this.scale + 30 * this.scale;
        const offsetY = (height - graphHeight * this.scale) / 2 - minY * this.scale + 30 * this.scale;
        this.mainGroup.attr('transform', `translate(${offsetX},${offsetY}) scale(${this.scale})`);
        
        // Draw edges (simplified)
        this.mainGroup.append('g')
            .selectAll('line')
            .data(data.edges)
            .enter()
            .append('line')
            .attr('x1', d => d.source.x || 0)
            .attr('y1', d => d.source.y || 0)
            .attr('x2', d => d.target.x || 0)
            .attr('y2', d => d.target.y || 0)
            .attr('stroke', '#ccc')
            .attr('stroke-width', 1);
        
        // Draw nodes (simplified - just dots)
        this.mainGroup.append('g')
            .selectAll('circle')
            .data(data.nodes)
            .enter()
            .append('circle')
            .attr('cx', d => d.x || 0)
            .attr('cy', d => d.y || 0)
            .attr('r', 4)
            .attr('fill', '#4a90d9');
    }
    
    /**
     * Update viewport rectangle based on main view transform
     * @param {Object} transform - D3 zoom transform
     * @param {number} mainWidth - Main view width
     * @param {number} mainHeight - Main view height
     */
    updateViewport(transform, mainWidth, mainHeight) {
        if (!this.viewportRect) return;
        
        this.mainViewWidth = mainWidth;
        this.mainViewHeight = mainHeight;
        
        // Calculate viewport rectangle in minimap coordinates
        const birdWidth = this.container.clientWidth;
        const birdHeight = this.container.clientHeight;
        
        // Inverse of main view transform to get visible area
        const visibleWidth = mainWidth / transform.k;
        const visibleHeight = mainHeight / transform.k;
        const visibleX = -transform.x / transform.k;
        const visibleY = -transform.y / transform.k;
        
        // Scale to bird view
        const rectWidth = visibleWidth * this.scale;
        const rectHeight = visibleHeight * this.scale;
        const rectX = visibleX * this.scale + (birdWidth - 500 * this.scale) / 2;
        const rectY = visibleY * this.scale + (birdHeight - 400 * this.scale) / 2;
        
        this.viewportRect.style.width = `${Math.max(20, rectWidth)}px`;
        this.viewportRect.style.height = `${Math.max(20, rectHeight)}px`;
        this.viewportRect.style.left = `${rectX}px`;
        this.viewportRect.style.top = `${rectY}px`;
    }
}

// Export for use in workspace.js
window.BirdView = BirdView;
