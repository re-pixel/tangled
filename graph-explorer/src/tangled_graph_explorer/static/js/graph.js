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

    const nodeById = new Map(data.nodes.map((n) => [n.id, n]));

    data.nodes.forEach((node, i) => {
      const angle = (i / data.nodes.length) * 2 * Math.PI;
      const r = Math.min(w, h) * 0.3;
      node.x = w / 2 + r * Math.cos(angle);
      node.y = h / 2 + r * Math.sin(angle);
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
    const nodeRadius = this._detectNodeRadius(svgEl, nodeSelector);

    let currentTransform = d3.zoomIdentity;

    const getVisibleWorldRect = (t) => {
      const { k, x: tx, y: ty } = t;
      const bufX = w / k;
      const bufY = h / k;
      return {
        left: (0 - tx) / k - bufX,
        right: (w - tx) / k + bufX,
        top: (0 - ty) / k - bufY,
        bottom: (h - ty) / k + bufY,
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
        this.style.visibility = visible ? "" : "hidden";
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
        this.style.visibility = srcVisible || tgtVisible ? "" : "hidden";
      });
    };

    const nodeDomElements = this.mainGroup.selectAll(nodeSelector);

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
            if (!event.active) this.simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
          })
          .on("drag", (event) => {
            if (!event.subject) return;
            const bound = nodeBounds.get(event.subject.id) || {
              hw: nodeRadius,
              hh: nodeRadius,
            };
            const { minX, maxX, minY, maxY } = GraphRenderer._worldBounds(
              w,
              h,
              currentTransform,
              bound,
            );
            event.subject.fx = Math.max(minX, Math.min(maxX, event.x));
            event.subject.fy = Math.max(minY, Math.min(maxY, event.y));
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
      .scaleExtent([0.1, 4])
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
      .velocityDecay(0.55)
      .force(
        "link",
        d3
          .forceLink(data.edges)
          .id((d) => d.id)
          .distance(250)
          .strength(0.3),
      )
      .force("charge", d3.forceManyBody().strength(-400).distanceMax(600))
      .force(
        "collide",
        d3
          .forceCollide()
          .radius(nodeRadius + 20)
          .strength(0.8)
          .iterations(3),
      )
      .force("center", d3.forceCenter(w / 2, h / 2).strength(0.05))
      .on("tick", () => {
        data.nodes.forEach((node) => {
          const bound = nodeBounds.get(node.id) || {
            hw: nodeRadius,
            hh: nodeRadius,
          };
          const { minX, maxX, minY, maxY } = GraphRenderer._worldBounds(
            w,
            h,
            currentTransform,
            bound,
          );
          node.x = Math.max(minX, Math.min(maxX, node.x));
          node.y = Math.max(minY, Math.min(maxY, node.y));
        });

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
        if (this.onSimulationTick) this.onSimulationTick(data);
      });
  }

  static _worldBounds(svgW, svgH, t, bound) {
    const padding = 10;
    const { k, x: tx, y: ty } = t;

    const worldLeft = (0 - tx) / k;
    const worldRight = (svgW - tx) / k;
    const worldTop = (0 - ty) / k;
    const worldBottom = (svgH - ty) / k;

    const hwWorld = (bound.hw + padding) / k;
    const hhWorld = (bound.hh + padding) / k;

    return {
      minX: worldLeft + hwWorld,
      maxX: worldRight - hwWorld,
      minY: worldTop + hhWorld,
      maxY: worldBottom - hhWorld,
    };
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
        // Circle fallback
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
