/**
 * Main View graph rendering using D3.js
 * 
 * Handles:
 * - Force-directed layout
 * - Pan and zoom
 * - Drag and drop
 * - Node selection
 * - Mouseover details
 */

class GraphRenderer {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.svg = null;
        this.simulation = null;
        this.zoom = null;
        this.selectedNode = null;
        
        // Callbacks for view synchronization
        this.onNodeSelect = null;
        this.onViewportChange = null;
    }
    
    /**
     * Initialize the SVG and D3 components
     */
    init() {
        if (!this.container) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        // Clear existing content
        this.container.innerHTML = '';
        
        // Create SVG
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        // Add arrow marker for directed edges
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .append('path')
            .attr('d', 'M 0,-5 L 10,0 L 0,5')
            .attr('fill', '#999');
        
        // Create main group for zoom/pan
        this.mainGroup = this.svg.append('g');
        
        // Setup zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.mainGroup.attr('transform', event.transform);
                if (this.onViewportChange) {
                    this.onViewportChange(event.transform);
                }
            });
        
        this.svg.call(this.zoom);
    }
    
    /**
     * Render graph data
     * @param {Object} data - Graph data with nodes and edges arrays
     */
    render(data) {
        if (!this.svg) this.init();
        if (!data || !data.nodes) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        // Clear previous graph
        this.mainGroup.selectAll('*').remove();
        
        // Create simulation
        this.simulation = d3.forceSimulation(data.nodes)
            .force('link', d3.forceLink(data.edges).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2));
        
        // Draw edges (arrows only for directed graphs)
        const isDirected = data.directed !== false;
        const edges = this.mainGroup.append('g')
            .attr('class', 'edges')
            .selectAll('line')
            .data(data.edges)
            .enter()
            .append('line')
            .attr('class', d => `edge ${isDirected ? 'directed' : ''}`)
            .attr('marker-end', d => isDirected ? 'url(#arrowhead)' : null);
        
        // Draw nodes
        const nodes = this.mainGroup.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(data.nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .call(this._drag());
        
        // Node circles
        nodes.append('circle')
            .attr('r', 15)
            .on('click', (event, d) => this._selectNode(d))
            .on('mouseover', (event, d) => this._showTooltip(event, d))
            .on('mouseout', () => this._hideTooltip());
        
        // Node labels
        nodes.append('text')
            .attr('dy', 4)
            .attr('text-anchor', 'middle')
            .text(d => d.label || d.id);
        
        // Update positions on simulation tick
        this.simulation.on('tick', () => {
            edges
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            nodes.attr('transform', d => `translate(${d.x},${d.y})`);
        });
    }
    
    /**
     * Create drag behavior
     */
    _drag() {
        return d3.drag()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }
    
    /**
     * Handle node selection
     */
    _selectNode(node) {
        // Update visual selection
        this.mainGroup.selectAll('.node circle')
            .classed('selected', d => d.id === node.id);
        
        this.selectedNode = node;
        
        if (this.onNodeSelect) {
            this.onNodeSelect(node);
        }
    }
    
    /**
     * Select node by ID (for cross-view synchronization)
     */
    selectNodeById(nodeId) {
        const node = this.simulation?.nodes().find(n => n.id === nodeId);
        if (node) {
            this._selectNode(node);
        }
    }
    
    /**
     * Show tooltip on hover
     */
    _showTooltip(event, node) {
        // TODO: Implement tooltip UI
        console.log('Node:', node);
    }
    
    /**
     * Hide tooltip
     */
    _hideTooltip() {
        // TODO: Implement tooltip UI
    }
    
    /**
     * Get current viewport transform
     */
    getTransform() {
        return d3.zoomTransform(this.svg.node());
    }
}

// Export for use in workspace.js
window.GraphRenderer = GraphRenderer;
