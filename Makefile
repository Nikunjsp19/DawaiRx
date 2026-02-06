.PHONY: help install lint test run clean mongo-test web

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make lint         - Run linters (black, flake8)"
	@echo "  make test         - Run tests"
	@echo "  make run          - Run the CLI (placeholder)"
	@echo "  make mongo-test   - Test MongoDB connection"
	@echo "  make web          - Start the web UI"
	@echo "  make clean        - Clean temporary files"

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
	python -m src.cli.main web

mongo-test:
	python -m src.persistence.mongo_test

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
