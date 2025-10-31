.PHONY: lint format test run-local

lint:
	@echo " Running Ruff linting..."
	ruff check .

format:
	@echo " Running Black formatting..."
	black .

test:
	@echo " Running pytest for all services..."
	pytest -v --maxfail=1 --disable-warnings