# Medical Spytool Makefile
# This Makefile provides shortcuts for common development tasks

.PHONY: help run install test clean lint docker docker-stop docker-logs backup init-db update-deps check-deps health-check docs

# Default help command that shows available commands
help:
	@echo "Medical Spytool - Development Commands"
	@echo "===================================="
	@echo "make help             - Show this help message"
	@echo "make run              - Run the application in development mode"
	@echo "make install          - Install dependencies"
	@echo "make test             - Run tests"
	@echo "make test-cov         - Run tests with coverage report"
	@echo "make clean            - Remove cache files and temp data"
	@echo "make lint             - Run code linter"
	@echo "make docker           - Start application with Docker"
	@echo "make docker-stop      - Stop Docker containers"
	@echo "make docker-logs      - Show Docker container logs"
	@echo "make backup           - Create a backup of the database"
	@echo "make init-db          - Initialize/reset the database"
	@echo "make update-deps      - Update dependencies"
	@echo "make check-deps       - Check dependencies for issues"
	@echo "make health-check     - Run health check on the system"
	@echo "make docs             - Generate API documentation"
	@echo "make setup-dev        - Setup development environment"

# Run the application
run:
	python run.py

# Install dependencies
install:
	pip install -r project_requirements.txt

# Run tests
test:
	python run_tests.py

# Run tests with coverage
test-cov:
	python run_tests.py --coverage --html-report

# Clean project
clean:
	-rm -rf __pycache__
	-rm -rf backend/__pycache__
	-rm -rf tests/__pycache__
	-rm -rf .pytest_cache
	-rm -rf coverage_report
	-rm -rf .coverage
	@echo "Cleaned up cache files and temporary data"

# Run linter
lint:
	flake8 backend tests

# Start with Docker
docker:
	docker-compose up -d
	@echo "Application started on http://localhost:5000"

# Stop Docker containers
docker-stop:
	docker-compose down

# Show Docker logs
docker-logs:
	docker-compose logs -f

# Create database backup
backup:
	python scripts/backup_database.py

# Initialize database
init-db:
	python init_db.py

# Update dependencies to latest versions
update-deps:
	pip install -U pip
	pip install -U -r project_requirements.txt

# Check dependencies
check-deps:
	python scripts/check_dependencies.py

# Run health check
health-check:
	python scripts/health_check.py

# Generate API documentation
docs:
	python scripts/generate_api_docs.py

# Setup development environment
setup-dev:
	python scripts/setup_dev_env.py