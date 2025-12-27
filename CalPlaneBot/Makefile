# CalPlaneBot Makefile

.PHONY: help install dev start stop clean test lint format docker-build docker-up docker-down

help: ## Show this help message
	@echo "CalPlaneBot - Plane to CalDAV integration service"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run in development mode
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload

start: ## Start the application
	./scripts/start.sh

stop: ## Stop Docker containers
	docker-compose down

clean: ## Clean up temporary files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

test: ## Run tests
	pytest tests/ -v --cov=app --cov-report=html

lint: ## Run linters
	black --check app/
	isort --check-only app/
	mypy app/

format: ## Format code
	black app/
	isort app/

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f calplanebot

health: ## Check service health
	curl -f http://localhost:8765/health || echo "Service is not running"

sync: ## Trigger manual sync
	curl -X POST http://localhost:8765/webhooks/sync

status: ## Check sync status
	curl http://localhost:8765/webhooks/status
