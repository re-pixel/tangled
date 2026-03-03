/**
 * Workspace page controller
 *
 * Coordinates all views (Main, Tree, Bird) and handles user interactions.
 */
class WorkspaceController {
  constructor() {
    this.workspaceId =
      document.querySelector(".workspace-page")?.dataset.workspaceId;
    this.graphRenderer = new GraphRenderer("main-graph-container");
    this.treeView = new TreeView("tree-container");
    this.birdView = new BirdView("bird-container");
    this.graphData = null;

    this._setupEventHandlers();
    this._setupViewSynchronization();
    this._loadDataSources();
  }

  _setupEventHandlers() {
    document
      .getElementById("load-data-form")
      ?.addEventListener("submit", (e) => {
        e.preventDefault();
        this._handleLoadData();
      });
    document
      .getElementById("data-source-select")
      ?.addEventListener("change", (e) => {
        this._updatePluginParams(e.target.value);
      });
    document
      .getElementById("visualizer-select")
      ?.addEventListener("change", () => {
        this._refreshVisualization();
      });
    document.getElementById("search-form")?.addEventListener("submit", (e) => {
      e.preventDefault();
      this._handleSearch(document.getElementById("search-input").value);
    });
    document.getElementById("filter-form")?.addEventListener("submit", (e) => {
      e.preventDefault();
      this._handleFilter(document.getElementById("filter-input").value);
    });
    document
      .getElementById("reset-btn")
      ?.addEventListener("click", () => this._handleReset());
    document.getElementById("cli-form")?.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = document.getElementById("cli-input");
      this._handleCliCommand(input.value);
      input.value = "";
    });
  }

  _setupViewSynchronization() {
    this.graphRenderer.onNodeSelect = (node) =>
      this.treeView.selectNodeById(node.id);
    this.treeView.onNodeSelect = (node) =>
      this.graphRenderer.selectNodeById(node.id);
    this.graphRenderer.onViewportChange = (transform) => {
      const c = document.getElementById("main-graph-container");
      this.birdView.updateViewport(transform, c.clientWidth, c.clientHeight);
    };
    this.graphRenderer.onSimulationTick = (data) => this.birdView.render(data);
  }

  async _loadDataSources() {
    try {
      const sources = await api.get("/api/plugins/datasources");
      const select = document.getElementById("data-source-select");
      sources.forEach((source) => {
        const option = document.createElement("option");
        option.value = source.id;
        option.textContent = source.name;
        option.dataset.params = JSON.stringify(source.parameters);
        select.appendChild(option);
      });
    } catch (e) {
      console.error("Failed to load data sources:", e);
    }
  }

  _updatePluginParams(pluginId) {
    const container = document.getElementById("plugin-params");
    container.innerHTML = "";
    if (!pluginId) return;
    const params = JSON.parse(
      document.querySelector(`option[value="${pluginId}"]`)?.dataset.params ||
        "[]",
    );
    params.forEach((param) => {
      const div = document.createElement("div");
      div.className = "param-input";
      const label = document.createElement("label");
      label.textContent = param.name + (param.required ? " *" : "");
      label.title = param.description;
      const input = document.createElement("input");
      input.type = "text";
      input.name = param.name;
      input.placeholder = param.description;
      if (param.default) input.value = param.default;
      if (param.required) input.required = true;
      div.appendChild(label);
      div.appendChild(input);
      container.appendChild(div);
    });
  }

  async _handleLoadData() {
    const pluginId = document.getElementById("data-source-select").value;
    if (!pluginId) {
      showNotification("Please select a data source", "error");
      return;
    }
    const params = {};
    document.querySelectorAll("#plugin-params input").forEach((i) => {
      if (i.value) params[i.name] = i.value;
    });
    try {
      const result = await api.post(`/api/workspace/${this.workspaceId}/load`, {
        plugin: pluginId,
        params,
      });
      result.error
        ? showNotification(result.error, "error")
        : (showNotification(`Loaded ${result.node_count} nodes`, "success"),
          await this._refreshVisualization());
    } catch (e) {
      showNotification("Failed to load data", "error");
      console.error(e);
    }
  }

  async _refreshVisualization() {
    try {
      this.graphData = await api.get(
        `/api/workspace/${this.workspaceId}/graph`,
      );
      const visualizer = document.getElementById("visualizer-select").value;
      const renderResult = await api.get(
        `/api/workspace/${this.workspaceId}/render?visualizer=${visualizer}`,
      );

      const mainContainer = document.getElementById("main-graph-container");
      mainContainer.innerHTML = renderResult.html || "";

      // Make graph data available to plugins that want it
      window.__graphData = this.graphData;

      mainContainer
        .querySelectorAll("script:not([type]), script[type='text/javascript']")
        .forEach((old) => {
          const s = document.createElement("script");
          s.textContent = old.textContent;
          document.body.appendChild(s);
          document.body.removeChild(s);
        });

      setTimeout(() => {
        const svgEl = mainContainer.querySelector("svg");
        if (this.graphData.nodes.length > 0 && svgEl) {
          this.graphRenderer.attach(svgEl.id, this.graphData);
        }
        this.birdView.render(this.graphData);
      }, 50);
    } catch (e) {
      console.error("Failed to refresh visualization:", e);
    }
  }

  async _handleSearch(query) {
    if (!query) return;
    try {
      const result = await api.post(
        `/api/workspace/${this.workspaceId}/search`,
        { query },
      );
      result.error
        ? showNotification(result.error, "error")
        : (showNotification(`Found ${result.node_count} nodes`, "info"),
          await this._refreshVisualization());
    } catch (e) {
      showNotification("Search failed", "error");
    }
  }

  async _handleFilter(query) {
    if (!query) return;
    try {
      const result = await api.post(
        `/api/workspace/${this.workspaceId}/filter`,
        { query },
      );
      result.error
        ? showNotification(result.error, "error")
        : (showNotification(`Filtered to ${result.node_count} nodes`, "info"),
          await this._refreshVisualization());
    } catch (e) {
      showNotification("Filter failed", "error");
    }
  }

  async _handleReset() {
    try {
      await api.post(`/api/workspace/${this.workspaceId}/reset`);
      document.getElementById("search-input").value = "";
      document.getElementById("filter-input").value = "";
      await this._refreshVisualization();
      showNotification("Reset to original graph", "info");
    } catch (e) {
      showNotification("Reset failed", "error");
    }
  }

  async _handleCliCommand(command) {
    if (!command) return;
    const output = document.getElementById("cli-output");
    output.innerHTML += `<div class="cli-command">&gt; ${command}</div>`;
    try {
      const result = await api.post(`/api/workspace/${this.workspaceId}/cli`, {
        command,
      });
      output.innerHTML += result.error
        ? `<div class="cli-error">${result.error}</div>`
        : `<div class="cli-result">${result.result || "OK"}</div>`;
      if (!result.error) await this._refreshVisualization();
    } catch (e) {
      output.innerHTML += `<div class="cli-error">Command failed</div>`;
    }
    output.scrollTop = output.scrollHeight;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector(".workspace-page")) new WorkspaceController();
});
