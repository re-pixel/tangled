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

    this.onNodeSelect = null;
    this.onViewportChange = null;
    this.onSimulationTick = null;
    this._hasZoomedToFit = false;
  }

  attach(svgId, data) {
    const svgEl = document.getElementById(svgId);
    if (!svgEl) return;

    const w = svgEl.parentElement.clientWidth || 800;
    const h = svgEl.parentElement.clientHeight || 600;

    this.svg = d3.select(svgEl).attr("width", w).attr("height", h);
    this.mainGroup = this.svg.select("g");

    const nodeSelector = this._resolveNodeSelector(svgEl, data.nodes.length);
    const linkSelector = this._resolveLinkSelector(svgEl);

    if (!nodeSelector) {
      console.warn("GraphRenderer: could not find node elements in SVG.");
      return;
    }

    this._hasZoomedToFit = false;
    const nodeById = new Map(data.nodes.map((n) => [n.id, n]));

    // Place nodes in a circle initially, centered at origin
    data.nodes.forEach((node, i) => {
      const angle = (i / data.nodes.length) * 2 * Math.PI;
      const r = Math.min(w, h) * 0.3;
      node.x = r * Math.cos(angle);
      node.y = r * Math.sin(angle);
    });

    if (linkSelector) {
      this.mainGroup.selectAll(linkSelector).remove();
    }

    // Arrowhead marker
    let defs = this.svg.select("defs");
    if (defs.empty()) defs = this.svg.insert("defs", ":first-child");
    defs.selectAll("#arrowhead-platform").remove();
    defs
      .append("marker")
      .attr("id", "arrowhead-platform")
      .attr("viewBox", "0 -6 12 12")
      .attr("refX", 12)
      .attr("refY", 0)
      .attr("markerWidth", 10)
      .attr("markerHeight", 10)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-6 L12,0 L0,6 Z")
      .attr("fill", "#1a699e");

    const linkGroup = this.mainGroup
      .insert("g", ":first-child")
      .attr("class", "platform-links");

    const linkSelection = linkGroup
      .selectAll("line")
      .data(data.edges)
      .enter()
      .append("line")
      .style("stroke", "#1a699e82")
      .style("stroke-width", "1.5px")
      .attr("marker-end", data.directed ? "url(#arrowhead-platform)" : null);

    const nodeBounds = this._measureNodeBounds(svgEl, nodeSelector, data.nodes);
    this._lastNodeBounds = nodeBounds;
    const nodeRadius = this._detectNodeRadius(svgEl, nodeSelector);

    let currentTransform = d3.zoomIdentity;

    // 150px screen-space buffer prevents pop-in at edges
    const getVisibleWorldRect = (t) => {
      const { k, x: tx, y: ty } = t;
      const buf = 150 / k;
      return {
        left: (0 - tx) / k - buf,
        right: (w - tx) / k + buf,
        top: (0 - ty) / k - buf,
        bottom: (h - ty) / k + buf,
      };
    };

    const applyCulling = (t) => {
      const rect = getVisibleWorldRect(t);

      nodeDomElements.each(function () {
        const id = d3.select(this).attr("id");
        const node = nodeById.get(id);
        if (!node) return;
        const visible =
          node.x >= rect.left &&
          node.x <= rect.right &&
          node.y >= rect.top &&
          node.y <= rect.bottom;
        this.style.visibility = visible ? "visible" : "hidden";
      });

      linkSelection.each(function (d) {
        const srcVisible =
          d.source.x >= rect.left &&
          d.source.x <= rect.right &&
          d.source.y >= rect.top &&
          d.source.y <= rect.bottom;
        const tgtVisible =
          d.target.x >= rect.left &&
          d.target.x <= rect.right &&
          d.target.y >= rect.top &&
          d.target.y <= rect.bottom;
        this.style.visibility = srcVisible || tgtVisible ? "visible" : "hidden";
      });
    };

    const nodeDomElements = this.mainGroup.selectAll(nodeSelector);

    // Hide everything initially; culling will reveal what's in view
    nodeDomElements.each(function () {
      this.style.visibility = "hidden";
    });
    linkSelection.each(function () {
      this.style.visibility = "hidden";
    });

    nodeDomElements
      .call(
        d3
          .drag()
          .subject((event) => {
            const g = event.sourceEvent.target.closest("g[id]");
            return g ? nodeById.get(g.id) || null : null;
          })
          .on("start", (event) => {
            if (!event.subject) return;
            if (!event.active) this.simulation.alphaTarget(0.05).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
          })
          .on("drag", (event) => {
            if (!event.subject) return;
            // Clamp to current visible world rect so nodes can't be dragged off screen
            const bound = nodeBounds.get(event.subject.id) || {
              hw: nodeRadius,
              hh: nodeRadius,
            };
            const { k, x: tx, y: ty } = currentTransform;
            const pad = 10;
            const worldLeft = (0 - tx) / k + (bound.hw + pad) / k;
            const worldRight = (w - tx) / k - (bound.hw + pad) / k;
            const worldTop = (0 - ty) / k + (bound.hh + pad) / k;
            const worldBottom = (h - ty) / k - (bound.hh + pad) / k;
            event.subject.fx = Math.max(
              worldLeft,
              Math.min(worldRight, event.x),
            );
            event.subject.fy = Math.max(
              worldTop,
              Math.min(worldBottom, event.y),
            );
          })
          .on("end", (event) => {
            if (!event.subject) return;
            if (!event.active) this.simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
          }),
      )
      .on("click.platform", (event) => {
        const el = event.currentTarget;
        const id = d3.select(el).attr("id");
        const node = nodeById.get(id);
        if (node) this._selectNode(node);
      })
      .on("mouseover.platform", (event) => {
        const id = d3.select(event.currentTarget).attr("id");
        const node = nodeById.get(id);
        if (node) this._showTooltip(event, node);
      })
      .on("mouseout.platform", () => this._hideTooltip());

    this.zoom = d3
      .zoom()
      .scaleExtent([0.05, 4])
      .on("zoom", (event) => {
        currentTransform = event.transform;
        this.mainGroup.attr("transform", currentTransform);
        applyCulling(currentTransform);
        if (this.onViewportChange) this.onViewportChange(currentTransform);
      });
    this.svg.call(this.zoom);

    this.simulation = d3
      .forceSimulation(data.nodes)
      .alphaDecay(0.04)
      .velocityDecay(0.85)
      .force(
        "link",
        d3
          .forceLink(data.edges)
          .id((d) => d.id)
          .distance(220)
          .strength(0.6),
      )
      .force("charge", d3.forceManyBody().strength(-200).distanceMax(400))
      .force(
        "collide",
        d3
          .forceCollide()
          .radius(nodeRadius + 15)
          .strength(0.7)
          .iterations(2),
      )
      .force("x", d3.forceX(0).strength(0.03))
      .force("y", d3.forceY(0).strength(0.03))
      .on("tick", () => {
        linkSelection.each(function (d) {
          const sx = d.source.x,
            sy = d.source.y;
          const tx = d.target.x,
            ty = d.target.y;
          const p1 = GraphRenderer._boxEdgePoint(
            sx,
            sy,
            tx,
            ty,
            nodeBounds.get(d.source.id),
          );
          const p2 = GraphRenderer._boxEdgePoint(
            tx,
            ty,
            sx,
            sy,
            nodeBounds.get(d.target.id),
          );
          d3.select(this)
            .attr("x1", p1.x)
            .attr("y1", p1.y)
            .attr("x2", p2.x)
            .attr("y2", p2.y);
        });

        nodeDomElements.each(function () {
          const id = d3.select(this).attr("id");
          const node = nodeById.get(id);
          if (node && isFinite(node.x) && isFinite(node.y)) {
            d3.select(this).attr("transform", `translate(${node.x},${node.y})`);
          }
        });

        applyCulling(currentTransform);

        if (this.onSimulationTick) this.onSimulationTick(data);
      })
      .on("end", () => {
        if (!this._hasZoomedToFit) {
          this._hasZoomedToFit = true;
          this._zoomToFit(w, h, data.nodes);
        }
        if (this.onSimulationTick) this.onSimulationTick(data);
      });

    const initTransform = d3.zoomIdentity.translate(w / 2, h / 2);
    this.svg.call(this.zoom.transform, initTransform);

    setTimeout(() => applyCulling(currentTransform), 100);
  }

  // Zoom and pan so all nodes fit in the viewport
  _zoomToFit(w, h, nodes) {
    if (!nodes.length) return;

    const svgEl = this.svg.node();
    let minX = Infinity,
      maxX = -Infinity;
    let minY = Infinity,
      maxY = -Infinity;

    nodes.forEach((n) => {
      if (!isFinite(n.x) || !isFinite(n.y)) return;

      let hw = 100,
        hh = 40;
      const el = svgEl.querySelector(`[id="${n.id}"]`);
      if (el) {
        const rect = el.querySelector("rect");
        if (rect) {
          const rw = parseFloat(rect.getAttribute("width") || 0);
          const rh = parseFloat(rect.getAttribute("height") || 0);
          if (rw > 0 && rh > 0) {
            hw = rw / 2;
            hh = rh / 2;
          }
        }
      }

      minX = Math.min(minX, n.x - hw);
      maxX = Math.max(maxX, n.x + hw);
      minY = Math.min(minY, n.y - hh);
      maxY = Math.max(maxY, n.y + hh);
    });

    const padding = 80;
    const graphW = maxX - minX + padding * 2;
    const graphH = maxY - minY + padding * 2;

    const k = Math.min(w / graphW, h / graphH, 1);
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    const tx = w / 2 - k * centerX;
    const ty = h / 2 - k * centerY;

    this.svg
      .transition()
      .duration(600)
      .call(this.zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(k));
  }

  static _boxEdgePoint(fx, fy, tx, ty, box) {
    if (!box) return { x: fx, y: fy };
    const { hw, hh } = box;
    const dx = tx - fx,
      dy = ty - fy;
    if (dx === 0 && dy === 0) return { x: fx, y: fy };
    const scaleX = dx !== 0 ? hw / Math.abs(dx) : Infinity;
    const scaleY = dy !== 0 ? hh / Math.abs(dy) : Infinity;
    const scale = Math.min(scaleX, scaleY);
    return { x: fx + dx * scale, y: fy + dy * scale };
  }

  _measureNodeBounds(svgEl, nodeSelector, nodes) {
    const bounds = new Map();
    nodes.forEach((node) => {
      const el = svgEl.querySelector(`${nodeSelector}[id="${node.id}"]`);
      if (el) {
        const rect = el.querySelector("rect");
        if (rect) {
          const w = parseFloat(rect.getAttribute("width") || 0);
          const h = parseFloat(rect.getAttribute("height") || 0);
          if (w > 0 && h > 0) {
            bounds.set(node.id, { hw: w / 2, hh: h / 2 });
            return;
          }
        }
        const circle = el.querySelector("circle");
        if (circle) {
          const r = parseFloat(circle.getAttribute("r") || 20);
          bounds.set(node.id, { hw: r, hh: r });
          return;
        }
      }
      const fallback = this._detectNodeRadius(svgEl, nodeSelector);
      bounds.set(node.id, { hw: fallback, hh: fallback });
    });
    return bounds;
  }

  _detectNodeRadius(svgEl, nodeSelector) {
    if (svgEl.dataset.nodeRadius) return parseFloat(svgEl.dataset.nodeRadius);
    const firstNode = svgEl.querySelector(nodeSelector);
    if (firstNode) {
      const circle = firstNode.querySelector("circle");
      if (circle) return parseFloat(circle.getAttribute("r") || 20);
      const rect = firstNode.querySelector("rect");
      if (rect) {
        const rw = parseFloat(rect.getAttribute("width") || 100);
        const rh = parseFloat(rect.getAttribute("height") || 50);
        return Math.sqrt((rw / 2) ** 2 + (rh / 2) ** 2);
      }
    }
    return 40;
  }

  _resolveNodeSelector(svgEl, nodeCount) {
    if (svgEl.dataset.nodeSelector) return svgEl.dataset.nodeSelector;
    const mainG = svgEl.querySelector("g");
    if (!mainG) return null;
    const classCounts = {};
    mainG.querySelectorAll(":scope > g[class]").forEach((el) => {
      el.classList.forEach((cls) => {
        classCounts[cls] = (classCounts[cls] || 0) + 1;
      });
    });
    let bestClass = null,
      bestDiff = Infinity;
    for (const [cls, count] of Object.entries(classCounts)) {
      const diff = Math.abs(count - nodeCount);
      if (diff < bestDiff) {
        bestDiff = diff;
        bestClass = cls;
      }
    }
    return bestClass ? `.${bestClass}` : null;
  }

  _resolveLinkSelector(svgEl) {
    if (svgEl.dataset.linkSelector) return svgEl.dataset.linkSelector;
    const mainG = svgEl.querySelector("g");
    if (!mainG) return null;
    if (mainG.querySelectorAll(":scope > line").length > 0)
      return ":scope > line";
    if (mainG.querySelectorAll(":scope > path").length > 0)
      return ":scope > path";
    if (mainG.querySelectorAll(":scope > g > line").length > 0) return "line";
    if (mainG.querySelectorAll(":scope > g > path").length > 0) return "path";
    return null;
  }

  _selectNode(node) {
    this.selectedNode = node;
    if (this.onNodeSelect) this.onNodeSelect(node);
  }

  selectNodeById(nodeId) {
    const node = this.simulation?.nodes().find((n) => n.id === nodeId);
    if (node) this._selectNode(node);
  }

  _showTooltip(event, node) {
    console.log("Node:", node);
  }
  _hideTooltip() {}

  getTransform() {
    return d3.zoomTransform(this.svg.node());
  }
}

window.GraphRenderer = GraphRenderer;
