.PHONY: help install lint test run clean mongo-test web add-admin run-frontend run-backend

help:
	@echo "Available commands:"
	@echo "  make install        - Install Python dependencies"
	@echo "  make lint           - Run linters (black, flake8)"
	@echo "  make test           - Run tests"
	@echo "  make run            - Run the CLI (placeholder)"
	@echo "  make mongo-test     - Test MongoDB connection"
	@echo "  make web            - Start the Python web UI"
	@echo "  make add-admin      - Add Admin@DawaiRx.us to MongoDB admins collection"
	@echo "  make run-frontend   - Start React frontend (Vite, port 5173)"
	@echo "  make run-backend    - Start Spring Boot backend (port 8080)"
	@echo "  make clean          - Clean temporary files"

install:
	pip install -r requirements.txt
	pip install -e .

lint:
	black --check src/ tests/
	flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503

format:
	black src/ tests/

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

run:
	@echo "CLI not yet implemented. Use: python -m src.cli.main --help"

web:
	python3 -m src.cli.main web

mongo-test:
	python -m src.persistence.mongo_test

add-admin:
	python scripts/add_admin.py

# React + Spring Boot app: run in two terminals:
#   Terminal 1: make run-backend
#   Terminal 2: make run-frontend
# Then open http://localhost:5173
run-frontend:
	cd frontend && npm install && npm run dev

run-backend:
	cd backend && mvn spring-boot:run

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
