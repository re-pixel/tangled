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
    this._isCleared = false;

    this._autoRestore();
  }

  async _autoRestore() {
    try {
      const graphData = await api.get(
        `/api/workspace/${this.workspaceId}/graph`,
      );
      if (graphData.nodes && graphData.nodes.length > 0) {
        await this._refreshVisualization();
      }
    } catch (error) {
      console.error("Failed to restore workspace state:", error);
    }
  }

  _saveUIState() {
    const pluginId = document.getElementById("data-source-select").value;
    const visualizer = document.getElementById("visualizer-select").value;
    const params = {};
    document.querySelectorAll("#plugin-params input").forEach((input) => {
      if (input.value) params[input.name] = input.value;
    });

    localStorage.setItem(
      `ws_${this.workspaceId}`,
      JSON.stringify({
        pluginId,
        visualizer,
        params,
      }),
    );
  }

  _restoreUIState() {
    const saved = localStorage.getItem(`ws_${this.workspaceId}`);
    if (!saved) return;

    const { pluginId, visualizer, params } = JSON.parse(saved);

    const dataSourceSelect = document.getElementById("data-source-select");
    if (pluginId && dataSourceSelect) {
      dataSourceSelect.value = pluginId;
      this._updatePluginParams(pluginId);

      if (params) {
        Object.entries(params).forEach(([name, value]) => {
          const input = document.querySelector(
            `#plugin-params input[name="${name}"]`,
          );
          if (input) input.value = value;
        });
      }
    }

    const visualizerSelect = document.getElementById("visualizer-select");
    if (visualizer && visualizerSelect) {
      visualizerSelect.value = visualizer;
    }
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
    const cliInput = document.getElementById("cli-input");
    this._cliHistory = [];
    this._cliHistoryIndex = -1;

    cliInput?.addEventListener("keydown", (e) => {
      if (e.key === "ArrowUp") {
        e.preventDefault();
        if (this._cliHistoryIndex < this._cliHistory.length - 1) {
          this._cliHistoryIndex++;
          cliInput.value = this._cliHistory[this._cliHistoryIndex];
        }
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        if (this._cliHistoryIndex > 0) {
          this._cliHistoryIndex--;
          cliInput.value = this._cliHistory[this._cliHistoryIndex];
        } else {
          this._cliHistoryIndex = -1;
          cliInput.value = "";
        }
      }
    });

    cliForm?.addEventListener("submit", (e) => {
      e.preventDefault();
      const command = cliInput.value;
      if (command) {
        this._cliHistory.unshift(command);
        this._cliHistoryIndex = -1;
      }
      this._handleCliCommand(command);
      cliInput.value = "";
    });
  }

  /**
   * Setup cross-view synchronization
   */
  _setupViewSynchronization() {
    // Sync node selection across views
    this.graphRenderer.onNodeSelect = (node) => {
      this.treeView.selectNodeById(node.id);
      this.birdView.selectNodeById(node.id);
    };

    this.treeView.onNodeSelect = (node) => {
      this.graphRenderer.selectNodeById(node.id);
      this.birdView.selectNodeById(node.id);
    };

    this.birdView.onNodeSelect = (node) => {
      this.graphRenderer.selectNodeById(node.id);
      this.treeView.selectNodeById(node.id);
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
    this.graphRenderer.onSimulationTick = (data) => {
      this.birdView.render(data);
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
      this._restoreUIState();
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
      input.className = "glass-input";
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
        this._saveUIState();
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

        this.birdView.render(this.graphData);
        this.treeView.render(this.graphData);
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
        await this._refreshData();
      }
    } catch (error) {
      showNotification("Search failed", "error");
    }
  }

  async _refreshData() {
    try {
      const graphData = await api.get(
        `/api/workspace/${this.workspaceId}/graph`,
      );
      this.graphData = graphData;
      this.graphRenderer.update(graphData);
      this.birdView.render(graphData);
      this.treeView.render(graphData);
    } catch (error) {
      console.error("Failed to refresh data:", error);
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
        await this._refreshData();
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

        if (result.changed) {
          const clearRe = /^clear\b/i;
          const structuralRe = /^(filter|search|reset)\b/i;

          if (clearRe.test(command.trim())) {
            this._clearViews();
          } else if (structuralRe.test(command.trim())) {
            this._isCleared = false;
            await this._refreshVisualization();
          } else {
            if (!this._isCleared) {
              await this._refreshData();
            }
          }
        }
      }
    } catch (error) {
      output.innerHTML += `<div class="cli-error">Command failed</div>`;
    }

    output.scrollTop = output.scrollHeight;
  }

  _clearViews() {
    this._isCleared = true;
    this.graphData = null;
    const mainContainer = document.getElementById("main-graph-container");
    mainContainer.innerHTML =
      '<p class="placeholder">Load data to visualize graph</p>';
    this.birdView.init();
    this.treeView.clear?.();

    const dataSourceSelect = document.getElementById("data-source-select");
    if (dataSourceSelect) dataSourceSelect.value = "";
    document.getElementById("plugin-params").innerHTML = "";

    document.getElementById("search-input").value = "";
    document.getElementById("filter-input").value = "";
  }
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector(".workspace-page")) {
    new WorkspaceController();
  }
});
