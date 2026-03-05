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
    this.offsetX = 0;
    this.offsetY = 0;
    this.graphBounds = { minX: 0, minY: 0, maxX: 500, maxY: 400 };

    // Main view dimensions for viewport calculation
    this.mainViewWidth = 0;
    this.mainViewHeight = 0;

    this.onNodeSelect = null;
    this.selectedNodeId = null;
  }

  /**
   * Initialize the minimap
   */
  init() {
    if (!this.container) return;

    const width = this.container.clientWidth;
    const height = this.container.clientHeight;

    this.container.innerHTML = "";

    // Create SVG
    this.svg = d3
      .select(this.container)
      .append("svg")
      .attr("width", width)
      .attr("height", height);

    this.mainGroup = this.svg.append("g");

    this.viewportRect = this.svg
      .append("rect")
      .attr("id", "viewport-rect")
      .attr("fill", "rgba(74, 144, 217, 0.1)")
      .attr("stroke", "#4a90d9")
      .attr("stroke-width", 1.5)
      .attr("pointer-events", "none");
  }

  /**
   * Render scaled-down version of the graph
   * @param {Object} data - Graph data with nodes and edges
   */
  render(data) {
    if (!this.svg) this.init();
    if (!data || !data.nodes || data.nodes.length === 0) return;

    const width = this.container.clientWidth;
    const height = this.container.clientHeight;

    // Calculate bounds of the graph
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;

    data.nodes.forEach((node) => {
      if (node.x !== undefined) {
        minX = Math.min(minX, node.x);
        maxX = Math.max(maxX, node.x);
        minY = Math.min(minY, node.y);
        maxY = Math.max(maxY, node.y);
      }
    });

    if (!isFinite(minX)) {
      minX = 0;
      maxX = 500;
      minY = 0;
      maxY = 400;
    }

    this.graphBounds = { minX, minY, maxX, maxY };

    const padding = 30;
    const graphWidth = maxX - minX + padding * 2;
    const graphHeight = maxY - minY + padding * 2;
    this.scale = Math.min(width / graphWidth, height / graphHeight, 1);

    // Apply transform
    this.offsetX =
      (width - graphWidth * this.scale) / 2 + (padding - minX) * this.scale;
    this.offsetY =
      (height - graphHeight * this.scale) / 2 + (padding - minY) * this.scale;

    this.mainGroup.selectAll("*").remove();
    this.mainGroup.attr(
      "transform",
      `translate(${this.offsetX},${this.offsetY}) scale(${this.scale})`,
    );

    // Draw edges (simplified)
    this.mainGroup
      .append("g")
      .selectAll("line")
      .data(data.edges)
      .enter()
      .append("line")
      .attr("x1", (d) => d.source.x || 0)
      .attr("y1", (d) => d.source.y || 0)
      .attr("x2", (d) => d.target.x || 0)
      .attr("y2", (d) => d.target.y || 0)
      .attr("stroke", "#ccc")
      .attr("stroke-width", 1 / this.scale);

    // Draw nodes (simplified - just dots)
    this.mainGroup
      .append("g")
      .selectAll("circle")
      .data(data.nodes)
      .enter()
      .append("circle")
      .attr("cx", (d) => d.x || 0)
      .attr("cy", (d) => d.y || 0)
      .attr("r", 4 / this.scale)
      .attr("fill", (d) =>
        d.id === this.selectedNodeId ? "#ff69b4" : "#4a90d9",
      ) // ← roze za selektovan
      .attr("cursor", "pointer")
      .on("click", (event, d) => {
        event.preventDefault();
        this.selectedNodeId = d.id;
        this._highlightNode(d.id);
        if (this.onNodeSelect) this.onNodeSelect(d);
      });
  }

  /**
   * Update viewport rectangle based on main view transform
   * @param {Object} transform - D3 zoom transform
   * @param {number} mainWidth - Main view width
   * @param {number} mainHeight - Main view height
   */
  updateViewport(transform, mainWidth, mainHeight) {
    if (!this.viewportRect) return;

    // Inverse of main view transform to get visible area
    const visibleWidth = mainWidth / transform.k;
    const visibleHeight = mainHeight / transform.k;
    const visibleX = -transform.x / transform.k;
    const visibleY = -transform.y / transform.k;

    // Scale to bird view
    const rectX = visibleX * this.scale + this.offsetX;
    const rectY = visibleY * this.scale + this.offsetY;
    const rectWidth = Math.max(10, visibleWidth * this.scale);
    const rectHeight = Math.max(10, visibleHeight * this.scale);

    this.viewportRect
      .attr("x", rectX)
      .attr("y", rectY)
      .attr("width", rectWidth)
      .attr("height", rectHeight);
  }

  selectNodeById(nodeId) {
    this.selectedNodeId = nodeId;
    this._highlightNode(nodeId);
  }

  _highlightNode(nodeId) {
    if (!this.mainGroup) return;
    this.mainGroup
      .selectAll("circle")
      .attr("fill", (d) => (d.id === nodeId ? "#ff69b4" : "#4a90d9"));
  }
}

// Export for use in workspace.js
window.BirdView = BirdView;
