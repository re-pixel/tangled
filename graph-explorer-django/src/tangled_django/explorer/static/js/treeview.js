/**
 * Tree View rendering
 *
 * IDE-like package explorer for graph data.
 * Handles cyclic references with lazy expand-on-demand.
 * Supports cross-view sync, attribute display, and search/filter.
 */

class TreeView {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.graphData = null;
        this.adjacencyMap = new Map();
        this.expandedNodes = new Set();
        this.selectedNodeId = null;
        this.rootId = null;

        // Callback for node selection
        this.onNodeSelect = null;
    }

    /**
     * Render graph data as a tree
     * @param {Object} data - Graph data with nodes and edges
     * @param {string} rootId - Optional root node ID
     */
    render(data, rootId = null) {
        if (!this.container || !data || !data.nodes || data.nodes.length === 0) {
            if (this.container) {
                this.container.innerHTML = '<p class="tree-placeholder">No data to display</p>';
            }
            return;
        }

        this.graphData = data;
        this._buildAdjacencyMap(data);

        // Choose root: explicit > preferred (no incoming edges) > first node
        if (rootId && this.adjacencyMap.has(rootId)) {
            this.rootId = rootId;
        } else if (!this.rootId || !this.adjacencyMap.has(this.rootId)) {
            this.rootId = this._findBestRoot(data);
        }

        this._renderTree();
    }

    /**
     * Build adjacency map from graph data
     */
    _buildAdjacencyMap(data) {
        this.adjacencyMap.clear();
        const incomingCount = new Map();

        data.nodes.forEach(node => {
            this.adjacencyMap.set(node.id, { node, children: [] });
            incomingCount.set(node.id, 0);
        });

        data.edges.forEach(edge => {
            const sourceId = typeof edge.source === 'object' ? edge.source.id : edge.source;
            const targetId = typeof edge.target === 'object' ? edge.target.id : edge.target;

            const source = this.adjacencyMap.get(sourceId);
            if (source && this.adjacencyMap.has(targetId)) {
                source.children.push(targetId);
                incomingCount.set(targetId, (incomingCount.get(targetId) || 0) + 1);
            }

            if (data.directed === false) {
                const target = this.adjacencyMap.get(targetId);
                if (target && this.adjacencyMap.has(sourceId)) {
                    target.children.push(sourceId);
                }
            }
        });

        this._incomingCount = incomingCount;
    }

    /**
     * Find best root node — prefer nodes with no incoming edges
     */
    _findBestRoot(data) {
        if (this._incomingCount) {
            for (const [nodeId, count] of this._incomingCount) {
                if (count === 0) return nodeId;
            }
        }
        return data.nodes[0].id;
    }

    /**
     * Render the full tree from root
     */
    _renderTree() {
        this.container.innerHTML = '';

        const fragment = document.createDocumentFragment();
        const pathSet = new Set();
        const rootEl = this._createNodeElement(this.rootId, pathSet, 0);
        if (rootEl) fragment.appendChild(rootEl);

        this.container.appendChild(fragment);
    }

    /**
     * Create a DOM element for a tree node (lazy — children only built when expanded)
     */
    _createNodeElement(nodeId, pathSet, depth) {
        const entry = this.adjacencyMap.get(nodeId);
        if (!entry) return null;

        const { node, children } = entry;
        const isCyclic = pathSet.has(nodeId);
        const hasChildren = children.length > 0;
        const isExpanded = this.expandedNodes.has(nodeId);
        const hasAttributes = node.attributes && Object.keys(node.attributes).length > 0;

        // Create node container
        const nodeEl = document.createElement('div');
        nodeEl.className = 'tree-node';
        nodeEl.dataset.nodeId = nodeId;
        if (depth > 0) nodeEl.dataset.depth = depth;

        // Create header row
        const header = document.createElement('div');
        header.className = 'tree-node-header';
        if (this.selectedNodeId === nodeId) header.classList.add('selected');

        // Toggle button
        const toggle = document.createElement('span');
        toggle.className = 'tree-toggle';

        if (isCyclic) {
            toggle.innerHTML = '<span class="tree-cycle-icon" title="Cyclic reference">&#x21BA;</span>';
            toggle.classList.add('cyclic');
        } else if (hasChildren || hasAttributes) {
            toggle.textContent = isExpanded ? '\u2212' : '+';
            toggle.dataset.toggle = nodeId;
        } else {
            toggle.innerHTML = '&nbsp;';
        }

        // Label
        const label = document.createElement('span');
        label.className = 'tree-label';
        if (isCyclic) {
            label.classList.add('tree-label-cyclic');
        }
        label.textContent = this._getLabel(node);
        label.title = nodeId;

        header.appendChild(toggle);
        header.appendChild(label);
        nodeEl.appendChild(header);

        // Cyclic reference — clicking navigates to the original occurrence
        if (isCyclic) {
            header.addEventListener('click', () => {
                this._selectAndScrollTo(nodeId);
            });
            return nodeEl;
        }

        // Attach header click for selection
        header.addEventListener('click', (e) => {
            if (e.target.closest('.tree-toggle[data-toggle]')) return;
            this._handleSelect(nodeId, header);
        });

        // Attach toggle click for expand/collapse
        if (toggle.dataset.toggle) {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                this._handleToggle(nodeId);
            });
        }

        // Render expanded content (attributes + children)
        if (isExpanded && !isCyclic) {
            this._renderExpandedContent(nodeEl, nodeId, node, children, hasAttributes, pathSet, depth);
        }

        return nodeEl;
    }

    /**
     * Render attributes and children into an expanded node
     */
    _renderExpandedContent(nodeEl, nodeId, node, children, hasAttributes, pathSet, depth) {
        // Attribute list
        if (hasAttributes) {
            const attrContainer = document.createElement('div');
            attrContainer.className = 'tree-attributes';

            Object.entries(node.attributes).forEach(([key, attr]) => {
                const row = document.createElement('div');
                row.className = 'tree-attr-row';

                const keySpan = document.createElement('span');
                keySpan.className = 'tree-attr-key';
                keySpan.textContent = key;

                const valSpan = document.createElement('span');
                valSpan.className = 'tree-attr-value';
                const { display, typeClass } = this._formatAttrValue(attr);
                valSpan.textContent = display;
                if (typeClass) valSpan.classList.add(typeClass);

                row.appendChild(keySpan);
                row.appendChild(valSpan);
                attrContainer.appendChild(row);
            });

            nodeEl.appendChild(attrContainer);
        }

        // Children
        if (children.length > 0) {
            const childrenContainer = document.createElement('div');
            childrenContainer.className = 'tree-children';

            pathSet.add(nodeId);
            children.forEach(childId => {
                const childEl = this._createNodeElement(childId, pathSet, depth + 1);
                if (childEl) childrenContainer.appendChild(childEl);
            });
            pathSet.delete(nodeId);

            nodeEl.appendChild(childrenContainer);
        }
    }

    /**
     * Handle toggle expand/collapse
     */
    _handleToggle(nodeId) {
        if (this.expandedNodes.has(nodeId)) {
            this.expandedNodes.delete(nodeId);
        } else {
            this.expandedNodes.add(nodeId);
        }

        // Full re-render from root to guarantee correct cycle detection
        // (subtree re-render would lose ancestor context for cycle paths)
        this._renderTree();
    }

    /**
     * Handle node selection
     */
    _handleSelect(nodeId, headerEl) {
        // Remove previous selection
        this.container.querySelectorAll('.tree-node-header.selected').forEach(h => {
            h.classList.remove('selected');
        });
        headerEl.classList.add('selected');
        this.selectedNodeId = nodeId;

        if (this.onNodeSelect) {
            const node = this.graphData.nodes.find(n => n.id === nodeId);
            if (node) this.onNodeSelect(node);
        }
    }

    /**
     * Select and scroll to a node — used for cyclic reference clicks
     */
    _selectAndScrollTo(nodeId) {
        // Find the first non-cyclic occurrence of this node
        const allMatches = this.container.querySelectorAll(
            `.tree-node[data-node-id="${CSS.escape(nodeId)}"]`
        );
        for (const el of allMatches) {
            if (el.querySelector('.tree-cycle-icon')) continue;
            const header = el.querySelector('.tree-node-header');
            if (!header) continue;
            this._handleSelect(nodeId, header);
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }
    }

    /**
     * Select node by ID — cross-view sync with auto-expand path
     * @param {string} nodeId
     */
    selectNodeById(nodeId) {
        if (!this.graphData || !this.adjacencyMap.has(nodeId)) return;

        this.selectedNodeId = nodeId;

        // Find path from root to target using BFS
        const path = this._findPathBFS(this.rootId, nodeId);
        if (path) {
            // Expand all ancestors (not the target itself unless it was already expanded)
            let needsRerender = false;
            for (let i = 0; i < path.length - 1; i++) {
                if (!this.expandedNodes.has(path[i])) {
                    this.expandedNodes.add(path[i]);
                    needsRerender = true;
                }
            }
            if (needsRerender) {
                this._renderTree();
            }
        }

        // Highlight and scroll
        this.container.querySelectorAll('.tree-node-header.selected').forEach(h => {
            h.classList.remove('selected');
        });

        const target = this.container.querySelector(
            `.tree-node[data-node-id="${CSS.escape(nodeId)}"] > .tree-node-header`
        );
        if (target) {
            target.classList.add('selected');
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    /**
     * BFS to find path from source to target using parent map
     * @returns {Array|null} Array of node IDs from source to target, or null
     */
    _findPathBFS(sourceId, targetId) {
        if (sourceId === targetId) return [sourceId];

        const visited = new Set([sourceId]);
        const parent = new Map();
        const queue = [sourceId];

        while (queue.length > 0) {
            const current = queue.shift();
            const entry = this.adjacencyMap.get(current);
            if (!entry) continue;

            for (const childId of entry.children) {
                if (visited.has(childId)) continue;
                parent.set(childId, current);
                if (childId === targetId) {
                    // Reconstruct path
                    const path = [targetId];
                    let node = targetId;
                    while (node !== sourceId) {
                        node = parent.get(node);
                        path.unshift(node);
                    }
                    return path;
                }
                visited.add(childId);
                queue.push(childId);
            }
        }

        return null;
    }

    /**
     * Get display label for a node
     */
    _getLabel(node) {
        // Prefer common name-like attributes
        if (node.attributes) {
            for (const key of ['name', 'label', 'title', 'first']) {
                const attr = node.attributes[key];
                if (attr) {
                    const val = typeof attr === 'object' ? attr.value : attr;
                    if (val != null && val !== '') return String(val);
                }
            }
        }
        if (node.label) return node.label;
        return String(node.id);
    }

    /**
     * Format attribute value for display with type awareness
     */
    _formatAttrValue(attr) {
        if (attr === null || attr === undefined) {
            return { display: 'null', typeClass: 'attr-type-null' };
        }

        const value = typeof attr === 'object' && attr.value !== undefined ? attr.value : attr;
        const type = typeof attr === 'object' && attr.type ? attr.type : typeof value;

        switch (type) {
            case 'number':
            case 'integer':
            case 'float':
                return { display: String(value), typeClass: 'attr-type-number' };
            case 'boolean':
                return { display: String(value), typeClass: 'attr-type-boolean' };
            case 'date':
            case 'datetime': {
                const d = new Date(value);
                const display = isNaN(d.getTime()) ? String(value) : d.toLocaleDateString();
                return { display, typeClass: 'attr-type-date' };
            }
            case 'string':
            default:
                return { display: `"${value}"`, typeClass: 'attr-type-string' };
        }
    }
}

// Export for use in workspace.js
window.TreeView = TreeView;
