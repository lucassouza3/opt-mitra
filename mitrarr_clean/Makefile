.PHONY: setup lint test format typecheck

setup:
	poetry install

lint:
	poetry run ruff check .

format:
	poetry run black .

Typecheck:
	poetry run mypy .

test:
	poetry run pytest
