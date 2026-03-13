APP_NAME=mailview
GREEN := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RESET := $(shell tput -Txterm sgr0)
VENV := .venv/bin/activate
DEPS_MARKER := .venv/.deps-installed

.DEFAULT_GOAL := help

# 🧩 Setup
.PHONY: local.install

$(VENV):
	@echo "$(GREEN)Creating venv...$(RESET)"
	uv venv

$(DEPS_MARKER): $(VENV) pyproject.toml
	@echo "$(GREEN)Installing $(APP_NAME) with dev dependencies...$(RESET)"
	uv pip install -e ".[dev]"
	@touch $(DEPS_MARKER)

local.install: $(DEPS_MARKER) ## Create venv and install with dev dependencies
	@echo "$(GREEN)Done! Run 'source .venv/bin/activate' to activate$(RESET)"

# 🧪 Testing
.PHONY: local.test local.test.cov local.bench

local.test: $(DEPS_MARKER) ## Run tests
	@echo "$(GREEN)Running tests...$(RESET)"
	.venv/bin/pytest --benchmark-skip

local.test.cov: $(DEPS_MARKER) ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	.venv/bin/pytest --cov=mailview --cov-report=html --cov-report=term --benchmark-skip

local.bench: $(DEPS_MARKER) ## Run performance benchmarks
	@echo "$(GREEN)Running benchmarks...$(RESET)"
	.venv/bin/pytest tests/performance/ -v --benchmark-only

# 🔍 Linting & Security
.PHONY: local.lint local.security

local.lint: $(DEPS_MARKER) ## Run linter
	@echo "$(GREEN)Running ruff...$(RESET)"
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

local.security: $(DEPS_MARKER) ## Run security scan
	@echo "$(GREEN)Running bandit...$(RESET)"
	.venv/bin/bandit -r mailview -ll

# ✅ Combined Checks
.PHONY: local.check

local.check: local.lint local.security local.test ## Run all checks (lint + security + test)
	@echo "$(GREEN)All checks passed!$(RESET)"

# 📦 Release (CI publishes automatically, these are for local testing/fallback)
.PHONY: release.build release.check release.test release.publish

release.build: $(DEPS_MARKER) ## Build package (sdist + wheel)
	@echo "$(GREEN)Cleaning dist/...$(RESET)"
	rm -rf dist/
	@echo "$(GREEN)Building package...$(RESET)"
	.venv/bin/python -m build
	@echo "$(GREEN)Built:$(RESET)"
	@ls -la dist/

release.check: release.build ## Validate package with twine
	@echo "$(GREEN)Checking package...$(RESET)"
	.venv/bin/twine check dist/*

release.test: release.check ## Upload to TestPyPI (manual fallback)
	@echo "$(YELLOW)Uploading to TestPyPI...$(RESET)"
	.venv/bin/twine upload --repository testpypi dist/*
	@echo "$(GREEN)Done! Test with:$(RESET)"
	@echo "  pip install --index-url https://test.pypi.org/simple/ mailview"

release.publish: release.check ## Upload to PyPI (manual fallback)
	@echo "$(YELLOW)Uploading to PyPI...$(RESET)"
	.venv/bin/twine upload dist/*
	@echo "$(GREEN)Published! Install with:$(RESET)"
	@echo "  pip install mailview"

# 📖 Help
.PHONY: help

help: ## Show all available make targets
	@echo "$(GREEN)$(APP_NAME) - Available targets:$(RESET)"
	@grep -E '^[a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}'
