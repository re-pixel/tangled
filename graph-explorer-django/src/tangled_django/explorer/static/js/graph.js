/**
 * Main View graph rendering using D3.js
 *
 * Handles:
 * - Force-directed layout
 * - Pan and zoom
 * - Drag and drop
 * - Node selection
 * - Mouseover details
 * - Incremental update via D3 data join (enter / update / exit)
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
    this._w = 800;
    this._h = 600;
    this._nodeById = new Map();
    this._nodeBounds = new Map();
    this._nodeRadius = 40;
    this._currentTransform = d3.zoomIdentity;
    this._nodeSelector = null;
    this._directed = false;
    this._edges = [];
    this._linkGroup = null;
    this._nodeGroup = null;
    this._linkSelection = null;
    this._nodeDomElements = null;
  }

  attach(svgId, data) {
    const svgEl = document.getElementById(svgId);
    if (!svgEl) return;

    this._w = svgEl.parentElement.clientWidth || 800;
    this._h = svgEl.parentElement.clientHeight || 600;
    const { _w: w, _h: h } = this;

    this.svg = d3.select(svgEl).attr("width", w).attr("height", h);
    this.mainGroup = this.svg.select("g");

    this._nodeSelector = this._resolveNodeSelector(svgEl, data.nodes.length);
    if (!this._nodeSelector) {
      console.warn("GraphRenderer: could not find node elements in SVG.");
      return;
    }

    this._directed = !!data.directed;
    this._hasZoomedToFit = false;
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
    this._linkGroup = this.mainGroup.select("g.platform-links");
    if (this._linkGroup.empty()) {
      this._linkGroup = this.mainGroup
        .insert("g", ":first-child")
        .attr("class", "platform-links");
    }

    this._nodeGroup = this.mainGroup;

    this._placeNewNodes(data.nodes);

    this._nodeById = new Map(data.nodes.map((n) => [n.id, n]));
    this._nodeRadius = this._detectNodeRadius(svgEl, this._nodeSelector);
    this._nodeBounds = this._measureNodeBounds(
      svgEl,
      this._nodeSelector,
      data.nodes,
    );

    this._edges = this._joinLinks(data.edges);
    this._joinNodes(data.nodes, svgEl);

    this.zoom = d3
      .zoom()
      .scaleExtent([0.05, 4])
      .on("zoom", (event) => {
        this._currentTransform = event.transform;
        this.mainGroup.attr("transform", this._currentTransform);
        this._applyCulling();
        if (this.onViewportChange)
          this.onViewportChange(this._currentTransform);
      });
    this.svg.call(this.zoom);

    this._buildSimulation(data);

    const initTransform = d3.zoomIdentity.translate(w / 2, h / 2);
    this.svg.call(this.zoom.transform, initTransform);

    setTimeout(() => this._applyCulling(), 100);
  }

  update(data) {
    if (!this.svg) return;

    this._directed = !!data.directed;
    const prevById = this._nodeById;
    data.nodes.forEach((n) => {
      const prev = prevById.get(n.id);
      if (prev && isFinite(prev.x)) {
        n.x = prev.x;
        n.y = prev.y;
        n.vx = prev.vx || 0;
        n.vy = prev.vy || 0;
      }
    });
    this._placeNewNodes(data.nodes);
    this._nodeById = new Map(data.nodes.map((n) => [n.id, n]));

    const svgEl = this.svg.node();
    const currentIds = new Set(data.nodes.map((n) => n.id));

    this._nodeDomElements.each(function () {
      const id = d3.select(this).attr("id");
      if (!currentIds.has(id)) {
        d3.select(this).transition().duration(200).style("opacity", 0).remove();
      }
    });

    data.nodes.forEach((n) => {
      const existing = svgEl.querySelector(
        `${this._nodeSelector}[id="${n.id}"]`,
      );
      if (existing) {
        const attrs = Object.entries(n.attributes || {})
          .map(([k, v]) => ({
            name: k,
            value: typeof v === "object" ? v.value : v,
          }))
          .filter((a) => a.value != null && String(a.value).trim() !== "");

        const valTexts = existing.querySelectorAll("text:not(.attr-name)");
        const keyTexts = existing.querySelectorAll("text.attr-name");

        attrs.forEach((attr, i) => {
          if (keyTexts[i]) keyTexts[i].textContent = attr.name;
          if (valTexts[i + 1]) valTexts[i + 1].textContent = String(attr.value);
        });
      } else {
        this._createFallbackNodeDom(n);
      }
    });

    this._nodeBounds = this._measureNodeBounds(
      svgEl,
      this._nodeSelector,
      data.nodes,
    );
    this._nodeRadius = this._detectNodeRadius(svgEl, this._nodeSelector);
    const normalizedEdges = this._joinLinks(data.edges);
    this._joinNodes(data.nodes, svgEl);
    this.simulation
      .nodes(data.nodes)
      .force(
        "link",
        d3
          .forceLink(normalizedEdges)
          .id((d) => d.id)
          .distance(220)
          .strength(0.6),
      )
      .alpha(0.3)
      .restart();

    this._applyCulling();
    if (this.onSimulationTick)
      this.onSimulationTick({ nodes: data.nodes, edges: this._liveEdges() });
  }

  _joinLinks(edges) {
    const normalized = edges.map((e) => ({
      ...e,
      source: typeof e.source === "object" ? e.source.id : e.source,
      target: typeof e.target === "object" ? e.target.id : e.target,
    }));

    const joined = this._linkGroup
      .selectAll("line")
      .data(normalized, (d) => d.id);
    joined.exit().transition().duration(200).style("opacity", 0).remove();
    const entered = joined
      .enter()
      .append("line")
      .style("stroke", "#1a699e82")
      .style("stroke-width", "1.5px")
      .style("opacity", 0)
      .attr("marker-end", this._directed ? "url(#arrowhead-platform)" : null);

    entered.transition().duration(300).style("opacity", 1);
    this._linkSelection = entered
      .merge(joined)
      .attr("marker-end", this._directed ? "url(#arrowhead-platform)" : null);
    return normalized;
  }

  _joinNodes(nodes, svgEl) {
    this._nodeDomElements = this._nodeGroup.selectAll(this._nodeSelector);

    this._nodeDomElements.each(function () {
      this.style.visibility = "hidden";
    });

    this._nodeDomElements
      .call(
        d3
          .drag()
          .subject((event) => {
            const g = event.sourceEvent.target.closest("g[id]");
            return g ? this._nodeById.get(g.id) || null : null;
          })
          .on("start", (event) => {
            if (!event.subject) return;
            if (!event.active) this.simulation.alphaTarget(0.35).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
          })
          .on("drag", (event) => {
            if (!event.subject) return;
            const bound = this._nodeBounds.get(event.subject.id) || {
              hw: this._nodeRadius,
              hh: this._nodeRadius,
            };
            const { k, x: tx, y: ty } = this._currentTransform;
            const pad = 10;
            event.subject.fx = Math.max(
              (0 - tx) / k + (bound.hw + pad) / k,
              Math.min((this._w - tx) / k - (bound.hw + pad) / k, event.x),
            );
            event.subject.fy = Math.max(
              (0 - ty) / k + (bound.hh + pad) / k,
              Math.min((this._h - ty) / k - (bound.hh + pad) / k, event.y),
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
        const id = d3.select(event.currentTarget).attr("id");
        const node = this._nodeById.get(id);
        if (node) this.selectNodeById(node.id);
      })
      .on("mouseover.platform", (event) => {
        const id = d3.select(event.currentTarget).attr("id");
        const node = this._nodeById.get(id);
        if (node) this._showTooltip(event, node);
      })
      .on("mouseout.platform", () => this._hideTooltip());
  }
  _createFallbackNodeDom(node) {
    const HEADER_H = 28;
    const ROW_H = 20;
    const PAD_X = 14;
    const BLUE = "#3a7bc8";

    const attrs = Array.isArray(node.attributes)
      ? node.attributes.filter(
          (a) => a.value != null && String(a.value).trim() !== "",
        )
      : Object.entries(node.attributes || {})
          .map(([k, v]) => ({
            name: k,
            value: typeof v === "object" ? v.value : v,
          }))
          .filter((a) => a.value != null && String(a.value).trim() !== "");

    const label = String(node.id);
    const nw = Math.max(160, label.length * 8 + PAD_X * 2);
    const nh = HEADER_H + Math.max(1, attrs.length) * ROW_H + 4;
    const topY = -nh / 2;

    const ns = "http://www.w3.org/2000/svg";
    const g = document.createElementNS(ns, "g");
    g.setAttribute("class", this._nodeSelector.replace(/^\./, ""));
    g.setAttribute("id", node.id);
    g.style.cursor = "pointer";
    g.style.opacity = "0";
    const border = document.createElementNS(ns, "rect");
    border.setAttribute("class", "node-border");
    border.setAttribute("x", -nw / 2);
    border.setAttribute("y", topY);
    border.setAttribute("width", nw);
    border.setAttribute("height", nh);
    border.setAttribute("rx", 4);
    border.setAttribute("ry", 4);
    border.style.fill = "white";
    border.style.stroke = BLUE;
    border.style.strokeWidth = "1.5px";
    g.appendChild(border);
    const header = document.createElementNS(ns, "rect");
    header.setAttribute("class", "header-bg");
    header.setAttribute("x", -nw / 2);
    header.setAttribute("y", topY);
    header.setAttribute("width", nw);
    header.setAttribute("height", HEADER_H);
    header.setAttribute("rx", 4);
    header.setAttribute("ry", 4);
    header.style.fill = BLUE;
    g.appendChild(header);
    const clipId = `clip-header-fallback-${node.id}`;
    const clipPath = document.createElementNS(ns, "clipPath");
    clipPath.setAttribute("id", clipId);
    const clipRect = document.createElementNS(ns, "rect");
    clipRect.setAttribute("x", -nw / 2);
    clipRect.setAttribute("y", topY);
    clipRect.setAttribute("width", nw);
    clipRect.setAttribute("height", HEADER_H);
    clipPath.appendChild(clipRect);
    this.svg.select("defs").node().appendChild(clipPath);
    header.setAttribute("clip-path", `url(#${clipId})`);
    const title = document.createElementNS(ns, "text");
    title.setAttribute("text-anchor", "middle");
    title.setAttribute("dominant-baseline", "middle");
    title.setAttribute("font-size", "13");
    title.setAttribute("font-weight", "bold");
    title.setAttribute("fill", "#ffffff");
    title.setAttribute("x", 0);
    title.setAttribute("y", topY + HEADER_H / 2);
    title.setAttribute("font-family", "Arial, sans-serif");
    title.textContent = label;
    g.appendChild(title);
    attrs.forEach((attr, i) => {
      const rowY = topY + HEADER_H + i * ROW_H;
      if (i % 2 === 1) {
        const stripe = document.createElementNS(ns, "rect");
        stripe.setAttribute("x", -nw / 2);
        stripe.setAttribute("y", rowY);
        stripe.setAttribute("width", nw);
        stripe.setAttribute("height", ROW_H);
        stripe.style.fill = "#f5f9ff";
        g.appendChild(stripe);
      }
      const keyText = document.createElementNS(ns, "text");
      keyText.setAttribute("class", "attr-name");
      keyText.setAttribute("x", -nw / 2 + PAD_X);
      keyText.setAttribute("y", rowY + ROW_H - 6);
      keyText.setAttribute("font-family", "Arial, sans-serif");
      keyText.setAttribute("font-size", "11");
      keyText.setAttribute("fill", BLUE);
      keyText.setAttribute("font-weight", "600");
      keyText.textContent = String(attr.name);
      g.appendChild(keyText);

      const valText = document.createElementNS(ns, "text");
      valText.setAttribute("x", -nw / 2 + PAD_X + 88);
      valText.setAttribute("y", rowY + ROW_H - 6);
      valText.setAttribute("font-family", "Arial, sans-serif");
      valText.setAttribute("font-size", "11");
      valText.setAttribute("fill", "#333");
      valText.textContent = String(attr.value);
      g.appendChild(valText);
    });

    g.setAttribute("data-fallback", "1");
    this._nodeGroup.node().appendChild(g);

    d3.select(g).transition().duration(300).style("opacity", 1);
    return g;
  }

  _liveEdges() {
    const force = this.simulation && this.simulation.force("link");
    return force ? force.links() : [];
  }

  _buildSimulation(data) {
    if (this.simulation) this.simulation.stop();

    this.simulation = d3
      .forceSimulation(data.nodes)
      .alphaDecay(0.04)
      .velocityDecay(0.85)
      .force(
        "link",
        d3
          .forceLink(this._edges)
          .id((d) => d.id)
          .distance(220)
          .strength(0.6),
      )
      .force("charge", d3.forceManyBody().strength(-200).distanceMax(400))
      .force(
        "collide",
        d3
          .forceCollide()
          .radius(this._nodeRadius + 15)
          .strength(0.7)
          .iterations(2),
      )
      .force("x", d3.forceX(0).strength(0.03))
      .force("y", d3.forceY(0).strength(0.03))
      .on("tick", () => this._onTick())
      .on("end", () => {
        if (!this._hasZoomedToFit) {
          this._hasZoomedToFit = true;
          this._zoomToFit(this._w, this._h, this.simulation.nodes());
        }
        if (this.onSimulationTick)
          this.onSimulationTick({
            nodes: this.simulation.nodes(),
            edges: this._liveEdges(),
          });
      });
  }

  _onTick() {
    if (!this._linkSelection || !this._nodeDomElements) return;

    this._linkSelection.each((d, i, els) => {
      const p1 = GraphRenderer._boxEdgePoint(
        d.source.x,
        d.source.y,
        d.target.x,
        d.target.y,
        this._nodeBounds.get(d.source.id),
      );
      const p2 = GraphRenderer._boxEdgePoint(
        d.target.x,
        d.target.y,
        d.source.x,
        d.source.y,
        this._nodeBounds.get(d.target.id),
      );
      d3.select(els[i])
        .attr("x1", p1.x)
        .attr("y1", p1.y)
        .attr("x2", p2.x)
        .attr("y2", p2.y);
    });

    this._nodeDomElements.each((d, i, els) => {
      const id = d3.select(els[i]).attr("id");
      const node = this._nodeById.get(id);
      if (node && isFinite(node.x) && isFinite(node.y)) {
        d3.select(els[i]).attr("transform", `translate(${node.x},${node.y})`);
      }
    });

    this._applyCulling();
    if (this.onSimulationTick)
      this.onSimulationTick({
        nodes: this.simulation.nodes(),
        edges: this._liveEdges(),
      });
  }

  _applyCulling() {
    if (!this._linkSelection || !this._nodeDomElements) return;

    const { k, x: tx, y: ty } = this._currentTransform;
    const rect = {
      left: (0 - tx) / k,
      right: (this._w - tx) / k,
      top: (0 - ty) / k,
      bottom: (this._h - ty) / k,
    };

    const overlaps = (cx, cy, hw, hh) =>
      cx + hw >= rect.left &&
      cx - hw <= rect.right &&
      cy + hh >= rect.top &&
      cy - hh <= rect.bottom;

    const FHW = this._nodeRadius,
      FHH = this._nodeRadius;

    this._nodeDomElements.each((d, i, els) => {
      const id = d3.select(els[i]).attr("id");
      const node = this._nodeById.get(id);
      if (!node) return;
      const b = this._nodeBounds.get(id);
      els[i].style.visibility = overlaps(
        node.x,
        node.y,
        b ? b.hw : FHW,
        b ? b.hh : FHH,
      )
        ? "visible"
        : "hidden";
    });

    this._linkSelection.each((d, i, els) => {
      const sb = this._nodeBounds.get(d.source.id);
      const tb = this._nodeBounds.get(d.target.id);
      els[i].style.visibility =
        overlaps(d.source.x, d.source.y, sb ? sb.hw : FHW, sb ? sb.hh : FHH) ||
        overlaps(d.target.x, d.target.y, tb ? tb.hw : FHW, tb ? tb.hh : FHH)
          ? "visible"
          : "hidden";
    });
  }

  _placeNewNodes(nodes) {
    const existing = nodes.filter((n) => isFinite(n.x));
    const cx = existing.length
      ? existing.reduce((s, n) => s + n.x, 0) / existing.length
      : 0;
    const cy = existing.length
      ? existing.reduce((s, n) => s + n.y, 0) / existing.length
      : 0;

    const fresh = nodes.filter((n) => !isFinite(n.x));
    const r = Math.min(this._w, this._h) * 0.3;
    fresh.forEach((node, i) => {
      const angle = (i / Math.max(1, fresh.length)) * 2 * Math.PI;
      node.x = cx + r * Math.cos(angle);
      node.y = cy + r * Math.sin(angle);
    });
  }

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

    const pad = 80;
    const k = Math.min(
      w / (maxX - minX + pad * 2),
      h / (maxY - minY + pad * 2),
      1,
    );
    const tx = w / 2 - k * ((minX + maxX) / 2);
    const ty = h / 2 - k * ((minY + maxY) / 2);

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
    const scale = Math.min(
      dx !== 0 ? hw / Math.abs(dx) : Infinity,
      dy !== 0 ? hh / Math.abs(dy) : Infinity,
    );
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
          bounds.set(node.id, {
            hw: parseFloat(circle.getAttribute("r") || 20),
            hh: parseFloat(circle.getAttribute("r") || 20),
          });
          return;
        }
      }
      const fb = this._detectNodeRadius(svgEl, nodeSelector);
      bounds.set(node.id, { hw: fb, hh: fb });
    });
    return bounds;
  }

  _detectNodeRadius(svgEl, nodeSelector) {
    if (svgEl.dataset.nodeRadius) return parseFloat(svgEl.dataset.nodeRadius);
    const first = svgEl.querySelector(nodeSelector);
    if (first) {
      const c = first.querySelector("circle");
      if (c) return parseFloat(c.getAttribute("r") || 20);
      const r = first.querySelector("rect");
      if (r) {
        const rw = parseFloat(r.getAttribute("width") || 100);
        const rh = parseFloat(r.getAttribute("height") || 50);
        return Math.sqrt((rw / 2) ** 2 + (rh / 2) ** 2);
      }
    }
    return 40;
  }

  _resolveNodeSelector(svgEl, nodeCount) {
    if (svgEl.dataset.nodeSelector) return svgEl.dataset.nodeSelector;
    const mainG = svgEl.querySelector("g");
    if (!mainG) return null;
    const counts = {};
    mainG.querySelectorAll(":scope > g[class]").forEach((el) => {
      el.classList.forEach((cls) => {
        counts[cls] = (counts[cls] || 0) + 1;
      });
    });
    let best = null,
      bestDiff = Infinity;
    for (const [cls, count] of Object.entries(counts)) {
      const diff = Math.abs(count - nodeCount);
      if (diff < bestDiff) {
        bestDiff = diff;
        best = cls;
      }
    }
    return best ? `.${best}` : null;
  }

  _selectNode(node) {
    if (this.selectedNode) {
      const prevEl = this.svg
        ?.node()
        .querySelector(
          `${this._nodeSelector}[id="${this.selectedNode.id}"] .node-border`,
        );
      if (prevEl) prevEl.style.stroke = "#3a7bc8";
    }

    this.selectedNode = node;

    const el = this.svg
      ?.node()
      .querySelector(`${this._nodeSelector}[id="${node.id}"] .node-border`);
    if (el) el.style.stroke = "#ff69b4";

    if (this.onNodeSelect) this.onNodeSelect(node);
  }

  selectNodeById(nodeId) {
    const node = this.simulation?.nodes().find((n) => n.id === nodeId);
    if (node) {
      this._selectNode(node);
      this._zoomToNode(node);
    }
  }

  _zoomToNode(node) {
    if (!this.svg || !this.zoom) return;
    if (!isFinite(node.x) || !isFinite(node.y)) return;

    const scale = 1.5;
    const tx = this._w / 2 - node.x * scale;
    const ty = this._h / 2 - node.y * scale;

    this.svg
      .transition()
      .duration(500)
      .call(
        this.zoom.transform,
        d3.zoomIdentity.translate(tx, ty).scale(scale),
      );
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
