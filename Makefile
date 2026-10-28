.PHONY: install run test lint

install:
	pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload

test:
	pytest -q

lint:
	ruff check .
