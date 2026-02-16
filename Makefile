.PHONY: help install-frontend run run-frontend run-backend build build-backend build-frontend test-backend clean

help:
	@echo "DawaiRx - Java + React"
	@echo ""
	@echo "  make install-frontend  - Install frontend dependencies (npm ci)"
	@echo "  make run-frontend      - Start React dev server (port 5173)"
	@echo "  make run-backend        - Start Spring Boot backend (port 8080)"
	@echo "  make run               - Run backend (use 'make run-frontend' in another terminal for full app)"
	@echo "  make build             - Build backend and frontend for production"
	@echo "  make build-backend     - Package backend (Maven)"
	@echo "  make build-frontend    - Build frontend (Vite)"
	@echo "  make test-backend      - Run backend tests"
	@echo "  make clean             - Remove build artifacts"

install-frontend:
	cd frontend && npm ci

run: run-backend

run-frontend:
	cd frontend && npm run dev

run-backend:
	cd backend && mvn spring-boot:run

build: build-backend build-frontend

build-backend:
	cd backend && mvn -q -DskipTests package

build-frontend:
	cd frontend && npm run build

test-backend:
	cd backend && mvn test

clean:
	cd backend && mvn -q clean 2>/dev/null || true
	rm -rf frontend/dist
