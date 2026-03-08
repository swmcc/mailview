APP_NAME=mailview
GREEN := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RESET := $(shell tput -Txterm sgr0)
VENV := .venv/bin/activate

.DEFAULT_GOAL := help

# 🧩 Setup
.PHONY: local.install

$(VENV):
	@echo "$(GREEN)Creating venv and installing $(APP_NAME) with dev dependencies...$(RESET)"
	uv venv
	uv pip install -e ".[dev]"

local.install: $(VENV) ## Create venv and install with dev dependencies
	@echo "$(GREEN)Done! Run 'source .venv/bin/activate' to activate$(RESET)"

# 🧪 Testing
.PHONY: local.test local.test.cov

local.test: $(VENV) ## Run tests
	@echo "$(GREEN)Running tests...$(RESET)"
	.venv/bin/pytest

local.test.cov: $(VENV) ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	.venv/bin/pytest --cov=mailview --cov-report=html --cov-report=term

# 🔍 Linting & Security
.PHONY: local.lint local.security

local.lint: $(VENV) ## Run linter
	@echo "$(GREEN)Running ruff...$(RESET)"
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

local.security: $(VENV) ## Run security scan
	@echo "$(GREEN)Running bandit...$(RESET)"
	.venv/bin/bandit -r mailview -ll

# ✅ Combined Checks
.PHONY: local.check

local.check: local.lint local.security local.test ## Run all checks (lint + security + test)
	@echo "$(GREEN)All checks passed!$(RESET)"

# 📖 Help
.PHONY: help

help: ## Show all available make targets
	@echo "$(GREEN)$(APP_NAME) - Available targets:$(RESET)"
	@grep -E '^[a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}'
