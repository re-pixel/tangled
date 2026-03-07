.PHONY: install run run-django test reinstall clean lint help

VENV := . venv/bin/activate &&
PORT ?= 5000

help:
	@echo "Tangled - Graph Visualization Platform"
	@echo ""
	@echo "Targets:"
	@echo "  make install    - Create venv and install all packages"
	@echo "  make run       - Start the Flask app (http://localhost:$(PORT))"
	@echo "  make run-django - Start the Django app (http://localhost:$(PORT))"
	@echo "  make test      - Run pytest"
	@echo "  make lint      - Run mypy on api and platform"
	@echo "  make reinstall - Reinstall all packages (starts server)"
	@echo "  make clean     - Remove venv and build artifacts"
	@echo ""
	@echo "Variables:"
	@echo "  PORT=5000     - Port for 'make run' / 'make run-django' (default: 5000)"

install:
	./scripts/install.sh

run:
	$(VENV) tangled --port=$(PORT)

run-django:
	$(VENV) python graph-explorer-django/manage.py runserver 0.0.0.0:$(PORT)

test:
	$(VENV) pip install -q $$(find . -maxdepth 1 -mindepth 1 -type d ! -name venv ! -name .git ! -name docs ! -name scripts ! -name .mypy_cache ! -name .pytest_cache ! -name .cursor -exec test -f {}/pyproject.toml \; -printf ' -e "./%f[dev]"') && \
	$(VENV) pytest $$(find . -maxdepth 3 -type d -name tests ! -path './venv/*' ! -path './.git/*' | sort) -v

lint:
	$(VENV) pip install -q -e "./api[dev]" -e "./platform[dev]" && \
	$(VENV) mypy api/src/tangled_api platform/src/tangled_platform

reinstall:
	./scripts/reinstall.sh

clean:
	rm -rf venv .pytest_cache
	@for dir in api platform web json-datasource yaml-datasource kuzu-datasource xml-datasource simple-visualizer block-visualizer graph-explorer graph-explorer-django; do \
		find $$dir -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true; \
		find $$dir -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true; \
		find $$dir -type d -name "build" -exec rm -rf {} + 2>/dev/null || true; \
	done
