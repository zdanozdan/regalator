.PHONY: help install test lint format clean docker-build docker-run docker-stop migrate collectstatic superuser shell

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt[dev]
	pre-commit install

test: ## Run tests
	cd regalator && python manage.py test --verbosity=2

test-coverage: ## Run tests with coverage
	cd regalator && coverage run --source='.' manage.py test
	coverage report
	coverage html

lint: ## Run linting checks
	flake8 regalator/ --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check regalator/
	isort --check-only regalator/

format: ## Format code
	black regalator/
	isort regalator/

clean: ## Clean Python cache files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete

migrate: ## Run database migrations
	cd regalator && python manage.py migrate

makemigrations: ## Create database migrations
	cd regalator && python manage.py makemigrations

collectstatic: ## Collect static files
	cd regalator && python manage.py collectstatic --noinput

superuser: ## Create superuser
	cd regalator && python manage.py createsuperuser

shell: ## Open Django shell
	cd regalator && python manage.py shell

runserver: ## Run development server
	cd regalator && python manage.py runserver

sync-subiekt: ## Sync products with Subiekt
	cd regalator && python manage.py sync_subiekt

load-demo: ## Load demo data
	cd regalator && python manage.py load_demo_data

docker-build: ## Build Docker image
	docker build -t regalator .

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-stop: ## Stop Docker Compose
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-shell: ## Open shell in Docker container
	docker-compose exec web bash

docker-db-shell: ## Open shell in database container
	docker-compose exec db psql -U postgres -d regalator

security-check: ## Run security checks
	safety check
	bandit -r regalator/ -f json -o bandit-report.json || true

check: ## Run all checks (lint, test, security)
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) security-check

setup: ## Initial project setup
	$(MAKE) install
	$(MAKE) install-dev
	$(MAKE) migrate
	$(MAKE) collectstatic
	@echo "Setup complete! Run 'make runserver' to start the development server."

deploy: ## Deploy to production (example)
	@echo "Deploying to production..."
	$(MAKE) docker-build
	$(MAKE) docker-run
	@echo "Deployment complete!"

backup: ## Create database backup
	cd regalator && python manage.py dumpdata > backup_$(shell date +%Y%m%d_%H%M%S).json

restore: ## Restore database from backup
	cd regalator && python manage.py loaddata backup_*.json

logs: ## View application logs
	tail -f logs/regalator.log

monitor: ## Monitor system resources
	@echo "System monitoring..."
	@echo "Memory usage:"
	@free -h
	@echo "Disk usage:"
	@df -h
	@echo "Docker containers:"
	@docker ps

help-dev: ## Show development help
	@echo "Development Commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make runserver    - Start development server"
	@echo "  make shell        - Open Django shell"
	@echo "  make migrate      - Run migrations"
	@echo "  make superuser    - Create superuser" 