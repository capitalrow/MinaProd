.PHONY: install dev fmt lint test run clean help

# Default target
help:
	@echo "Mina - Meeting Insights & Action Platform"
	@echo "Available commands:"
	@echo "  install  - Install dependencies"
	@echo "  dev      - Run development server with hot reload"
	@echo "  fmt      - Format code with black"
	@echo "  lint     - Run linting with flake8"
	@echo "  test     - Run test suite"
	@echo "  run      - Run production server"
	@echo "  clean    - Clean up temporary files"

# Install dependencies
install:
	pip install -e .
	pip install -r requirements-dev.txt

# Run development server with hot reload
dev:
	FLASK_ENV=development python main.py

# Format code with black
fmt:
	black --line-length=88 --target-version=py39 .
	isort --profile=black .

# Run linting
lint:
	flake8 --max-line-length=88 --extend-ignore=E203,W503 .
	mypy --ignore-missing-imports .

# Run test suite
test:
	pytest tests/ -v --tb=short

# Run test suite with coverage
test-cov:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

# Run production server (use with gunicorn in production)
run:
	python main.py

# Run with uvicorn (alternative ASGI server)
run-uvicorn:
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

# Clean up temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ dist/ build/

# Database operations
db-init:
	python -c "from app_refactored import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"

db-reset:
	python -c "from app_refactored import create_app, db; app = create_app(); app.app_context().push(); db.drop_all(); db.create_all(); print('Database reset')"

# Development utilities
shell:
	python -c "from app_refactored import create_app; app = create_app(); app.app_context().push(); import IPython; IPython.start_ipython(argv=[])"

# Docker support (if needed)
docker-build:
	docker build -t mina-transcription .

docker-run:
	docker run -p 5000:5000 -e FLASK_ENV=development mina-transcription
