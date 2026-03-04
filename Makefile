.PHONY: install run test reinstall clean lint help

VENV := . venv/bin/activate &&
PORT ?= 5000

help:
	@echo "Tangled - Graph Visualization Platform"
	@echo ""
	@echo "Targets:"
	@echo "  make install    - Create venv and install all packages"
	@echo "  make run       - Start the Flask app (http://localhost:$(PORT))"
	@echo "  make test      - Run pytest"
	@echo "  make lint      - Run mypy on api and platform"
	@echo "  make reinstall - Reinstall all packages (starts server)"
	@echo "  make clean     - Remove venv and build artifacts"
	@echo ""
	@echo "Variables:"
	@echo "  PORT=5000     - Port for 'make run' (default: 5000)"

install:
	./install.sh

run:
	$(VENV) tangled --port=$(PORT)

test:
	$(VENV) pip install -q -e "./api[dev]" -e "./platform[dev]" -e "./json-datasource[dev]" -e "./yaml-datasource[dev]" -e "./kuzu-datasource[dev]" && \
	$(VENV) pytest api/src/tests/ json-datasource/tests/ yaml-datasource/tests/ kuzu-datasource/tests/ -v

lint:
	$(VENV) pip install -q -e "./api[dev]" -e "./platform[dev]" && \
	$(VENV) mypy api/src/tangled_api platform/src/tangled_platform

reinstall:
	./reinstall.sh

clean:
	rm -rf venv .pytest_cache
	@for dir in api platform json-datasource yaml-datasource kuzu-datasource xml-datasource simple-visualizer block-visualizer graph-explorer; do \
		find $$dir -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true; \
		find $$dir -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true; \
		find $$dir -type d -name "build" -exec rm -rf {} + 2>/dev/null || true; \
	done
