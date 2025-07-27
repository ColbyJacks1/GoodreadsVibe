.PHONY: help install dev test lint format clean sample-db start

help: ## Show this help message
	@echo "Book Mirror Plus - Development Commands"
	@echo "======================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install

dev: ## Start FastAPI development server
	poetry run dev

streamlit: ## Start Streamlit UI
	poetry run streamlit

start: ## Start both backend and frontend
	python start_app.py

test: ## Run all tests
	poetry run test

test-ingest: ## Run ingestion tests
	poetry run pytest tests/test_ingest.py -v

test-cluster: ## Run clustering tests
	poetry run pytest tests/test_cluster.py -v

test-insights: ## Run insights tests
	poetry run pytest tests/test_insights.py -v

lint: ## Run linting
	poetry run ruff check .
	poetry run mypy .

format: ## Format code
	poetry run black .
	poetry run ruff format .

clean: ## Clean up generated files
	rm -f embed_data.sqlite
	rm -f temp_*.csv
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

sample-db: ## Create sample database with dummy data
	python create_sample_db.py

setup: install sample-db ## Full setup: install dependencies and create sample DB
	@echo "✅ Setup complete! Run 'make dev' to start the FastAPI server"

all: format lint test ## Run all quality checks
	@echo "✅ All checks passed!"

# Development workflow
workflow: format lint test ## Run full development workflow
	@echo "✅ Development workflow complete!" 