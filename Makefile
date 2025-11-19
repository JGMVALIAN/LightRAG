.PHONY: help install dev test clean docker-up docker-down setup index

help: ## Show this help message
	@echo "Spanish Legal RAG System - Makefile Commands"
	@echo "=============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt
	python -m spacy download es_core_news_lg

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black flake8 mypy

test: ## Run tests
	pytest tests/ -v --cov=src --cov-report=term-missing

test-integration: ## Run integration tests only
	pytest tests/test_integration.py -v

lint: ## Run linters
	black src/ tests/
	flake8 src/ tests/
	mypy src/

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start all services
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Grafana: http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## View logs
	docker-compose logs -f legal-rag-api

docker-clean: ## Stop and remove all containers, volumes
	docker-compose down -v
	docker system prune -f

setup: docker-up ## Setup databases and initial configuration
	@echo "Setting up databases..."
	@sleep 15
	chmod +x scripts/setup_databases.sh
	./scripts/setup_databases.sh

index: ## Index Spanish legal corpus
	python scripts/index_spanish_laws.py

health: ## Check system health
	curl -s http://localhost:8000/health | jq

stats: ## Show system statistics
	curl -s http://localhost:8000/stats | jq

query-example: ## Run example query
	curl -X POST http://localhost:8000/query \
		-H "Content-Type: application/json" \
		-d '{"question": "¿Qué plazo tengo para recurrir una adjudicación?", "area": "contratacion", "mode": "hybrid"}' \
		| jq

run-local: ## Run API locally (without Docker)
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

clean: ## Clean Python cache and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

format: ## Format code with black
	black src/ tests/

check: lint test ## Run all checks (lint + test)

deploy-k8s: ## Deploy to Kubernetes
	kubectl create namespace legal-rag --dry-run=client -o yaml | kubectl apply -f -
	kubectl apply -f k8s/

k8s-status: ## Check Kubernetes deployment status
	kubectl get pods -n legal-rag
	kubectl get services -n legal-rag

k8s-logs: ## View Kubernetes logs
	kubectl logs -n legal-rag -l app=legal-rag-api --tail=100 -f

backup: ## Create backup of databases
	@echo "Creating backup..."
	docker-compose exec postgres pg_dump -U $$POSTGRES_USER $$POSTGRES_DB > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup completed!"

restore: ## Restore from backup (usage: make restore BACKUP=backup_file.sql)
	@if [ -z "$(BACKUP)" ]; then \
		echo "Error: Please specify BACKUP file: make restore BACKUP=backup.sql"; \
		exit 1; \
	fi
	docker-compose exec -T postgres psql -U $$POSTGRES_USER $$POSTGRES_DB < $(BACKUP)

monitor: ## Open monitoring dashboard
	@echo "Opening Grafana..."
	@echo "URL: http://localhost:3000"
	@echo "Default credentials: admin/admin"

docs: ## Generate documentation
	@echo "API documentation available at:"
	@echo "  - Swagger: http://localhost:8000/docs"
	@echo "  - ReDoc: http://localhost:8000/redoc"

all: install docker-up setup index ## Complete setup (install, docker, setup, index)
