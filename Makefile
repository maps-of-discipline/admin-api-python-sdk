.PHONY: lint format typecheck test check

ruff_check:
	uv run ruff check .

ruff_fix:
	uv run ruff check . --fix

format:
	uv run ruff format .

typecheck:
	uv run mypy src

test:
	uv run pytest

check: lint typecheck test
