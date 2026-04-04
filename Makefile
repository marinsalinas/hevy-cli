.PHONY: help install dev lint format typecheck test build clean pre-commit

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	uv sync

dev: ## Install with dev dependencies
	uv sync --group dev
	uv run pre-commit install

lint: ## Run ruff linter and formatter check
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format: ## Auto-format code with ruff
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

typecheck: ## Run mypy type checking
	uv run mypy src/

test: ## Run tests with coverage
	uv run pytest --cov --cov-report=term-missing

build: ## Build the package
	uv build

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.egg-info src/*.egg-info .mypy_cache .pytest_cache .ruff_cache coverage.xml .coverage

pre-commit: ## Run pre-commit on all files
	uv run pre-commit run --all-files

check: lint typecheck test ## Run all checks (lint + typecheck + test)
