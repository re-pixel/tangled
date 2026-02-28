/**
 * Workspace page controller
 *
 * Coordinates all views (Main, Tree, Bird) and handles user interactions.
 */

class WorkspaceController {
  constructor() {
    this.workspaceId =
      document.querySelector(".workspace-page")?.dataset.workspaceId;

    // Initialize view components
    this.graphRenderer = new GraphRenderer("main-graph-container");
    this.treeView = new TreeView("tree-container");
    this.birdView = new BirdView("bird-container");

    this.graphData = null;

    this._setupEventHandlers();
    this._setupViewSynchronization();
    this._loadDataSources();
  }

  /**
   * Setup form and button event handlers
   */
  _setupEventHandlers() {
    // Load data form
    const loadForm = document.getElementById("load-data-form");
    loadForm?.addEventListener("submit", (e) => {
      e.preventDefault();
      this._handleLoadData();
    });

    // Data source selection
    const dataSourceSelect = document.getElementById("data-source-select");
    dataSourceSelect?.addEventListener("change", (e) => {
      this._updatePluginParams(e.target.value);
    });

    // Visualizer selection
    const visualizerSelect = document.getElementById("visualizer-select");
    visualizerSelect?.addEventListener("change", () => {
      this._refreshVisualization();
    });

    // Search form
    const searchForm = document.getElementById("search-form");
    searchForm?.addEventListener("submit", (e) => {
      e.preventDefault();
      const query = document.getElementById("search-input").value;
      this._handleSearch(query);
    });

    // Filter form
    const filterForm = document.getElementById("filter-form");
    filterForm?.addEventListener("submit", (e) => {
      e.preventDefault();
      const query = document.getElementById("filter-input").value;
      this._handleFilter(query);
    });

    // Reset button
    const resetBtn = document.getElementById("reset-btn");
    resetBtn?.addEventListener("click", () => {
      this._handleReset();
    });

    // CLI form
    const cliForm = document.getElementById("cli-form");
    cliForm?.addEventListener("submit", (e) => {
      e.preventDefault();
      const command = document.getElementById("cli-input").value;
      this._handleCliCommand(command);
      document.getElementById("cli-input").value = "";
    });
  }

  /**
   * Setup cross-view synchronization
   */
  _setupViewSynchronization() {
    // Sync node selection across views
    this.graphRenderer.onNodeSelect = (node) => {
      this.treeView.selectNodeById(node.id);
      // Bird view doesn't need selection sync
    };

    this.treeView.onNodeSelect = (node) => {
      this.graphRenderer.selectNodeById(node.id);
    };

    // Sync viewport changes to bird view
    this.graphRenderer.onViewportChange = (transform) => {
      const container = document.getElementById("main-graph-container");
      this.birdView.updateViewport(
        transform,
        container.clientWidth,
        container.clientHeight,
      );
    };
  }

  /**
   * Load available data sources and populate dropdown
   */
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
    } catch (error) {
      console.error("Failed to load data sources:", error);
    }
  }

  /**
   * Update parameter inputs based on selected plugin
   */
  _updatePluginParams(pluginId) {
    const paramsContainer = document.getElementById("plugin-params");
    paramsContainer.innerHTML = "";

    if (!pluginId) return;

    const option = document.querySelector(`option[value="${pluginId}"]`);
    const params = JSON.parse(option.dataset.params || "[]");

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
      paramsContainer.appendChild(div);
    });
  }

  /**
   * Handle load data form submission
   */
  async _handleLoadData() {
    const select = document.getElementById("data-source-select");
    const pluginId = select.value;

    if (!pluginId) {
      showNotification("Please select a data source", "error");
      return;
    }

    // Collect parameters
    const params = {};
    document.querySelectorAll("#plugin-params input").forEach((input) => {
      if (input.value) {
        params[input.name] = input.value;
      }
    });

    try {
      const result = await api.post(`/api/workspace/${this.workspaceId}/load`, {
        plugin: pluginId,
        params: params,
      });

      if (result.error) {
        showNotification(result.error, "error");
      } else {
        showNotification(`Loaded ${result.node_count} nodes`, "success");
        await this._refreshVisualization();
      }
    } catch (error) {
      showNotification("Failed to load data", "error");
      console.error(error);
    }
  }

  /**
   * Refresh all visualizations
   */
  async _refreshVisualization() {
    try {
      const graphData = await api.get(
        `/api/workspace/${this.workspaceId}/graph`,
      );
      this.graphData = graphData;

      const visualizer = document.getElementById("visualizer-select").value;
      const renderResult = await api.get(
        `/api/workspace/${this.workspaceId}/render?visualizer=${visualizer}`,
      );

      const mainContainer = document.getElementById("main-graph-container");
      mainContainer.innerHTML = renderResult.html || "";

      mainContainer.querySelectorAll("script").forEach((old) => {
        const s = document.createElement("script");
        s.textContent = old.textContent;
        document.body.appendChild(s);
        document.body.removeChild(s);
      });

      setTimeout(() => {
        const existingSvg = mainContainer.querySelector("svg");

        if (graphData.nodes.length > 0) {
          if (existingSvg) {
            console.log("calling attach...");
            this.graphRenderer.attach(existingSvg.id, graphData);
          } else {
            console.log("NO SVG FOUND");
          }
        } else {
          console.log("NO NODES");
        }
      }, 50);
    } catch (error) {
      console.error("Failed to refresh visualization:", error);
    }
  }
  /**
   * Handle search
   */
  async _handleSearch(query) {
    if (!query) return;

    try {
      const result = await api.post(
        `/api/workspace/${this.workspaceId}/search`,
        { query },
      );

      if (result.error) {
        showNotification(result.error, "error");
      } else {
        showNotification(`Found ${result.node_count} nodes`, "info");
        await this._refreshVisualization();
      }
    } catch (error) {
      showNotification("Search failed", "error");
      console.error(error);
    }
  }

  /**
   * Handle filter
   */
  async _handleFilter(query) {
    if (!query) return;

    try {
      const result = await api.post(
        `/api/workspace/${this.workspaceId}/filter`,
        { query },
      );

      if (result.error) {
        showNotification(result.error, "error");
      } else {
        showNotification(`Filtered to ${result.node_count} nodes`, "info");
        await this._refreshVisualization();
      }
    } catch (error) {
      showNotification("Filter failed", "error");
      console.error(error);
    }
  }

  /**
   * Handle reset
   */
  async _handleReset() {
    try {
      await api.post(`/api/workspace/${this.workspaceId}/reset`);
      document.getElementById("search-input").value = "";
      document.getElementById("filter-input").value = "";
      await this._refreshVisualization();
      showNotification("Reset to original graph", "info");
    } catch (error) {
      showNotification("Reset failed", "error");
      console.error(error);
    }
  }

  /**
   * Handle CLI command
   */
  async _handleCliCommand(command) {
    if (!command) return;

    const output = document.getElementById("cli-output");
    output.innerHTML += `<div class="cli-command">&gt; ${command}</div>`;

    try {
      const result = await api.post(`/api/workspace/${this.workspaceId}/cli`, {
        command,
      });

      if (result.error) {
        output.innerHTML += `<div class="cli-error">${result.error}</div>`;
      } else {
        output.innerHTML += `<div class="cli-result">${result.result || "OK"}</div>`;
        await this._refreshVisualization();
      }
    } catch (error) {
      output.innerHTML += `<div class="cli-error">Command failed</div>`;
    }

    // Scroll to bottom
    output.scrollTop = output.scrollHeight;
  }
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector(".workspace-page")) {
    new WorkspaceController();
  }
});
