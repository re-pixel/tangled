/**
 * Tree View rendering
 * 
 * Displays graph as expandable/collapsible tree structure.
 * Handles cyclic references by showing reference indicators.
 */

class TreeView {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.graphData = null;
        this.expandedNodes = new Set();
        this.visitedInPath = new Set(); // For cycle detection during rendering
        
        // Callback for node selection
        this.onNodeSelect = null;
    }
    
    /**
     * Render graph data as a tree
     * @param {Object} data - Graph data with nodes and edges
     * @param {string} rootId - Optional root node ID (random if not specified)
     */
    render(data, rootId = null) {
        if (!this.container || !data || !data.nodes || data.nodes.length === 0) {
            this.container.innerHTML = '<p class="placeholder">No data to display</p>';
            return;
        }
        
        this.graphData = data;
        
        // Build adjacency map
        this.adjacencyMap = new Map();
        data.nodes.forEach(node => {
            this.adjacencyMap.set(node.id, { node, children: [] });
        });
        
        data.edges.forEach(edge => {
            const source = this.adjacencyMap.get(edge.source);
            if (source) {
                source.children.push(edge.target);
            }
            // For undirected graphs, add reverse connection for tree traversal
            if (data.directed === false) {
                const target = this.adjacencyMap.get(edge.target);
                if (target) {
                    target.children.push(edge.source);
                }
            }
        });
        
        // Choose root node
        if (!rootId || !this.adjacencyMap.has(rootId)) {
            rootId = data.nodes[0].id;
        }
        
        // Clear and render
        this.container.innerHTML = '';
        this.visitedInPath.clear();
        
        const treeHtml = this._renderNode(rootId, 0);
        this.container.innerHTML = treeHtml;
        
        // Attach event listeners
        this._attachListeners();
    }
    
    /**
     * Render a single node and its children
     */
    _renderNode(nodeId, depth) {
        const entry = this.adjacencyMap.get(nodeId);
        if (!entry) return '';
        
        const { node, children } = entry;
        const hasChildren = children.length > 0;
        const isExpanded = this.expandedNodes.has(nodeId);
        const isCyclic = this.visitedInPath.has(nodeId);
        
        // Cycle detected - show reference indicator
        if (isCyclic) {
            return `
                <div class="tree-node" data-node-id="${nodeId}">
                    <div class="tree-node-header">
                        <span class="tree-toggle"></span>
                        <span class="tree-label">${this._getLabel(node)} ↩️ (ref)</span>
                    </div>
                </div>
            `;
        }
        
        // Mark as visited for cycle detection
        this.visitedInPath.add(nodeId);
        
        let childrenHtml = '';
        if (hasChildren && isExpanded) {
            childrenHtml = children
                .map(childId => this._renderNode(childId, depth + 1))
                .join('');
        }
        
        // Unmark after processing children
        this.visitedInPath.delete(nodeId);
        
        const toggleSymbol = hasChildren ? (isExpanded ? '−' : '+') : ' ';
        const expandedClass = isExpanded ? 'expanded' : '';
        
        return `
            <div class="tree-node" data-node-id="${nodeId}">
                <div class="tree-node-header">
                    <span class="tree-toggle" data-toggle="${nodeId}">${toggleSymbol}</span>
                    <span class="tree-label">${this._getLabel(node)}</span>
                </div>
                ${hasChildren ? `<div class="tree-children ${expandedClass}">${childrenHtml}</div>` : ''}
            </div>
        `;
    }
    
    /**
     * Get display label for a node
     */
    _getLabel(node) {
        if (node.label) return node.label;
        if (node.attributes) {
            const firstAttr = Object.values(node.attributes)[0];
            if (firstAttr) return `${node.id}: ${firstAttr}`;
        }
        return node.id;
    }
    
    /**
     * Attach click listeners for toggle and selection
     */
    _attachListeners() {
        // Toggle expand/collapse
        this.container.querySelectorAll('.tree-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const nodeId = toggle.dataset.toggle;
                if (!nodeId) return;
                
                if (this.expandedNodes.has(nodeId)) {
                    this.expandedNodes.delete(nodeId);
                } else {
                    this.expandedNodes.add(nodeId);
                }
                
                // Re-render
                const rootId = this.graphData.nodes[0].id;
                this.render(this.graphData, rootId);
            });
        });
        
        // Node selection
        this.container.querySelectorAll('.tree-node-header').forEach(header => {
            header.addEventListener('click', () => {
                const nodeElement = header.closest('.tree-node');
                const nodeId = nodeElement?.dataset.nodeId;
                if (!nodeId) return;
                
                // Update visual selection
                this.container.querySelectorAll('.tree-node-header').forEach(h => {
                    h.classList.remove('selected');
                });
                header.classList.add('selected');
                
                // Callback
                if (this.onNodeSelect) {
                    const node = this.graphData.nodes.find(n => n.id === nodeId);
                    this.onNodeSelect(node);
                }
            });
        });
    }
    
    /**
     * Select node by ID (for cross-view synchronization)
     */
    selectNodeById(nodeId) {
        this.container.querySelectorAll('.tree-node-header').forEach(header => {
            const nodeElement = header.closest('.tree-node');
            header.classList.toggle('selected', nodeElement?.dataset.nodeId === nodeId);
        });
        
        // Expand path to selected node
        // TODO: Implement path expansion
    }
}

// Export for use in workspace.js
window.TreeView = TreeView;
